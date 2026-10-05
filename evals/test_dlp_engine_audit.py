"""Regression oracles for the DLP audit; every credential is synthetic."""

import base64
import json
import subprocess
import sys
import unittest

from evals.test_data_security import dlp, hook_event, invoke_hook, synthetic_token


class AssignmentAuditTests(unittest.TestCase):
    def test_json_separator_whitespace_preserves_literal_context(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for name in ("password", "Authorization"):
            value = "Bearer " + literal if name == "Authorization" else literal
            for before, after in (("", "\n"), ("\r\n", "\r\n  "), ("\t", "\n\t")):
                payload = '{"' + name + '"' + before + ':' + after + json.dumps(value) + '}'
                self.assertTrue(dlp.contains_high_confidence(dlp.scan_value(json.loads(payload))))
                redacted, findings = dlp.redact_text(payload)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(literal, redacted)
        for value in ('"<PASSWORD>"', "credential_value", "Zeroizing::new(value)"):
            self.assertFalse(dlp.scan_text("password:\n  " + value))

    def test_bearer_token_alphabet_is_fully_redacted(self):
        prefix, tail = "N7rQ4zP9mL2xV8cB", "TailThatMustDisappear"
        for separator in ("~", "-", ".", "_", "+", "/"):
            value = prefix + separator + tail + "=="
            for payload in ("Authorization: Bearer " + value, {"Authorization": "Bearer " + value}, json.dumps({"Authorization": "Bearer " + value})):
                redacted, findings = dlp.redact_value(payload)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(prefix, json.dumps(redacted))
                self.assertNotIn(tail, json.dumps(redacted))

    def test_source_expressions_are_not_secret_values(self):
        field = "pass" + "word"
        for expression in ("Zeroizing::new(value.to_owned())", "credential_value", "credentialValue", "cachedPassword2", "credential_value_v2", "self.credential_value", "&credential_value", "&self.credential_value", "*credential_value_ptr", "account?.credential", "options->credential_value", "String::from(value)", "Option<String>"):
            for separator in (": ", " = "):
                source = field + separator + expression
                with self.subTest(expression=expression, separator=separator):
                    self.assertFalse(dlp.scan_text(source, include_identifiers=False))

    def test_literals_and_structured_assignments_remain_detected_and_redacted(self):
        field = "pass" + "word"
        value = "N7rQ4zP9mL2xV8cB"
        for payload in (field + "=" + value, field + "='" + value + "'", json.dumps({field: value}), {field: value}, {"nested": [{field: value}]}):
            with self.subTest(kind=type(payload).__name__):
                self.assertTrue(dlp.contains_high_confidence(dlp.scan_value(payload)))
                redacted, findings = dlp.redact_value(payload)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(value, json.dumps(redacted))

    def test_placeholder_words_inside_credentials_are_not_exemptions(self):
        for payload in ("https://user:" + "long-test-P4ssword" + "@host.invalid", "Authorization: Bearer " + "long-test-P4ssword", "pass" + "word='" + "long-test-P4ssword" + "'", "pass" + "word='" + "yourActualCredential42" + "'"):
            self.assertTrue(dlp.contains_high_confidence(dlp.scan_text(payload)))

    def test_real_tokens_inside_source_expressions_are_still_detected(self):
        token = synthetic_token()
        source = "pass" + "word: Zeroizing::new(\"" + token + "\".to_owned())"
        redacted, findings = dlp.redact_text(source)
        self.assertTrue(dlp.contains_high_confidence(findings))
        self.assertNotIn(token, redacted)
        literal = "N7rQ4zP9mL2xV8cB"
        for expression in ('Zeroizing::new("' + literal + '".to_owned())', '&"' + literal + '"'):
            source = "pass" + "word: " + expression
            redacted, findings = dlp.redact_text(source)
            self.assertTrue(dlp.contains_high_confidence(findings))
            self.assertNotIn(literal, redacted)

    def test_wrapper_literal_whitespace_preserves_detection(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for wrapper in ("Zeroizing::new(", "&"):
            for spacing in ("", " ", "\t", "\n", "\r\n  "):
                with self.subTest(wrapper=wrapper, spacing=repr(spacing)):
                    source = "pass" + "word = " + wrapper + spacing + '"' + literal + '"'
                    redacted, findings = dlp.redact_text(source)
                    self.assertTrue(dlp.contains_high_confidence(findings))
                    self.assertNotIn(literal, redacted)
                    reference = "pass" + "word = " + wrapper + spacing + "credential_value"
                    self.assertFalse(dlp.scan_text(reference))

    def test_structured_authorization_headers_are_detected_and_redacted(self):
        token = "N7rQ4zP9mL2xV8cB"
        for name in ("Authorization", "Proxy-Authorization"):
            value = {"headers": {name: "Bearer " + token}}
            for payload in (value, json.dumps(value)):
                self.assertTrue(dlp.contains_high_confidence(dlp.scan_value(payload)))
                redacted, _ = dlp.redact_value(payload)
                self.assertNotIn(token, json.dumps(redacted))

    def test_conventional_environment_and_header_names_share_literal_detection(self):
        value = "N7rQ4zP9mL2xV8cB"
        for name in ("DB_PASSWORD", "DATABASE_PASSWORD", "AWS_SECRET_ACCESS_KEY", "X-API-Key", "clientSecret"):
            for payload in (name + "=" + value, {name: value}):
                self.assertTrue(dlp.contains_high_confidence(dlp.scan_value(payload)))
                redacted, _ = dlp.redact_value(payload)
                self.assertNotIn(value, json.dumps(redacted))

    def test_normalized_structured_keys_retain_sensitive_context(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for name in ("password", "DB_PASSWORD", "Authorization", "Proxy-Authorization"):
            wide = "".join(chr(ord(char) + 65248) for char in name)
            value = "Bearer " + literal if "Authorization" in name else literal
            payload = {wide: value, "note": "testing-only"}
            findings = dlp.scan_value(payload)
            self.assertTrue(any(item.category == "obfuscated_secret" for item in findings))
            redacted, _ = dlp.redact_value(payload)
            self.assertNotIn(literal, json.dumps(redacted))
            code, out, err = invoke_hook(hook_event("PreToolUse", tool_name="Bash", tool_input=payload))
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertNotIn("DEV_FLOW_DLP_CONFIRM", out)

    def test_chinese_phone_context_survives_json_representation(self):
        number = "202" + "555" + "0179"
        for name in ("手机", "电话"):
            for payload in (name + ": " + number, {name: number}):
                findings = dlp.scan_value(payload)
                self.assertTrue(any(item.category == "phone" for item in findings))
                redacted, _ = dlp.redact_value(payload)
                self.assertNotIn(number, json.dumps(redacted))

    def test_numeric_phone_context_is_redacted_without_reclassifying_counters(self):
        number = int("202" + "555" + "0179")
        for name in ("phone", "mobile", "手机", "电话"):
            payload = {name: number, "count": number, "enabled": True}
            findings = dlp.scan_value(payload)
            self.assertTrue(any(item.category == "phone" for item in findings))
            redacted, _ = dlp.redact_value(payload)
            self.assertTrue(redacted[name].startswith("{{DLP:PHONE:"))
            self.assertEqual(redacted["count"], number)
            self.assertIs(redacted["enabled"], True)
            self.assertFalse(dlp.scan_value({"count": number}))
        self.assertEqual(dlp.redact_value({"phone": 123, "mobile": True})[0], {"phone": 123, "mobile": True})


class RedactionAuditTests(unittest.TestCase):
    def test_generated_redaction_labels_are_stable_exact_placeholders(self):
        field = "pass" + "word"
        token = synthetic_token()
        for payload in ({field: token}, field + '=\"' + token + '\"'):
            redacted, findings = dlp.redact_value(payload, salt=b"stable-test-salt")
            self.assertTrue(findings)
            self.assertFalse(dlp.scan_value(redacted))
            again, later_findings = dlp.redact_value(redacted, salt=b"stable-test-salt")
            self.assertEqual(again, redacted)
            self.assertFalse(later_findings)
        label, _ = dlp.redact_text(token, salt=b"stable-test-salt")
        mixed = {field: label + token}
        redacted, findings = dlp.redact_value(mixed)
        self.assertTrue(dlp.contains_high_confidence(findings))
        self.assertNotIn(token, json.dumps(redacted))

    def test_private_key_body_reflow_cannot_leave_a_raw_tail(self):
        body = "Z7aQ" * 8 + "P1bR" * 8
        for width in (16, 32, 64):
            for indent in ("", " ", "\t"):
                wrapped = "\n".join(indent + body[index:index + width] for index in range(0, len(body), width))
                text = "-----BEGIN PRIVATE KEY-----\n" + wrapped + "\n-----END PRIVATE KEY-----"
                self.assertEqual(base64.b64decode(wrapped), base64.b64decode(body))
                redacted, findings = dlp.redact_text(text)
                self.assertTrue(any(item.category == "private_key" for item in findings))
                for line in wrapped.splitlines():
                    self.assertNotIn(line.strip(), redacted)
        first = "Z7aQ" * 8
        tail = "P1bR" * 8
        text = "-----BEGIN PRIVATE KEY-----\n" + first + "\n " + tail + "\n-----END PRIVATE KEY-----"
        redacted, findings = dlp.redact_text(text)
        self.assertTrue(findings)
        self.assertNotIn(first, redacted)
        self.assertNotIn(tail, redacted)

    def test_finding_overflow_fails_closed_instead_of_leaving_a_raw_tail(self):
        token = synthetic_token()
        for payload in (" ".join([token] * (dlp.MAX_FINDINGS + 1)), [token] * (dlp.MAX_FINDINGS + 1)):
            for operation in (dlp.scan_value, dlp.redact_value):
                with self.subTest(kind=type(payload).__name__, operation=operation.__name__):
                    with self.assertRaises(dlp.InspectionLimit):
                        operation(payload)

    def test_identifiers_cannot_hide_later_secret_at_cap(self):
        payload = [f"person{index}@corp.invalid" for index in range(dlp.MAX_FINDINGS)] + [synthetic_token()]
        with self.assertRaises(dlp.InspectionLimit):
            dlp.scan_value(payload)

    def test_normalization_redacts_obfuscated_value_even_with_existing_match(self):
        token = synthetic_token()
        value = "Q7r-" * 8
        source = token + " \ufb01 Authorization\uff1a Bearer " + value
        redacted, _ = dlp.redact_text(source)
        self.assertNotIn(token, redacted)
        self.assertNotIn(value, redacted)

    def test_unrelated_unicode_does_not_reclassify_an_ascii_test_token(self):
        token = synthetic_token()
        for prefix in ("测试令牌： ", "\ufb01 ", "e\u0301 "):
            findings = dlp.scan_text(prefix + token)
            self.assertEqual([item.category for item in findings], ["access_token"])

    def test_equal_plain_and_obfuscated_values_are_redacted_in_both_orders(self):
        token = synthetic_token()
        wide = "".join(chr(ord(char) + 65248) for char in token)
        for prefix in ("", "\ufb01 ", "e\u0301 "):
            for values in ((wide, token), (token, wide)):
                payload = prefix + " ".join(values)
                redacted, findings = dlp.redact_text(payload)
                self.assertTrue(any(item.category == "obfuscated_secret" for item in findings))
                self.assertNotIn(token, redacted)
                self.assertNotIn(wide, redacted)
                code, out, err = invoke_hook(hook_event("PostToolUse", tool_response=payload))
                self.assertEqual(code, 0)
                self.assertFalse(err)
                self.assertNotIn(wide, out)

    def test_overlapping_credential_url_redacts_entire_password(self):
        value = synthetic_token() + ".PrivateTail42"
        redacted, _ = dlp.redact_text("https://user:" + value + "@host.invalid")
        self.assertNotIn("PrivateTail42", redacted)

    def test_timestamps_dates_versions_and_multiline_numbers_are_not_phones(self):
        for text in ("1791157535", "1791157535123", "2026-10-05 12:34:56", "1.2.3.4.5.6.7.8.9.0", "12345\n67890", "12345 67890", "server=192.168.10.10", "route=10.100.100.100", "version: 123.456.7890"):
            with self.subTest(text=text):
                self.assertFalse(dlp.scan_text(text))
        self.assertTrue(dlp.scan_text("+1 202 555 0179"))
        self.assertTrue(dlp.scan_text("+86 138 0013 8000"))
        self.assertTrue(dlp.scan_text("phone: 2025550179"))
        self.assertTrue(dlp.scan_text("phone: 202.555.0179"))
        redacted, findings = dlp.redact_value({"phone": "2025550179"})
        self.assertTrue(findings)
        self.assertNotIn("2025550179", json.dumps(redacted))

    def test_invalid_json_values_use_bounded_failure(self):
        for payload in ("\ud800", float("nan"), float("inf"), (synthetic_token(),), {1: synthetic_token()}):
            with self.subTest(kind=type(payload).__name__):
                with self.assertRaises(dlp.InspectionLimit):
                    dlp.scan_value(payload)

    def test_encoded_secret_after_many_identifiers_cannot_escape(self):
        token = synthetic_token()
        encoded = base64.b64encode(token.encode()).decode()
        payload = " ".join([f"p{index}@corp.invalid" for index in range(dlp.MAX_FINDINGS)] + [encoded])
        with self.assertRaises(dlp.InspectionLimit):
            dlp.redact_text(payload)

    def test_posttool_overflow_does_not_forward_raw_result(self):
        payload = " ".join([synthetic_token()] * (dlp.MAX_FINDINGS + 1))
        code, out, err = invoke_hook(hook_event("PostToolUse", tool_response=payload))
        self.assertEqual(code, 0)
        self.assertFalse(err)
        self.assertNotIn(synthetic_token(), out)
        self.assertIn("inspection limit", out)

    def test_supported_base64_bound_is_actually_inspected(self):
        token = synthetic_token()
        payload = " " * 3000 + token
        encoded = base64.b64encode(payload.encode()).decode()
        redacted, findings = dlp.redact_text(encoded)
        self.assertTrue(dlp.contains_high_confidence(findings))
        self.assertNotIn(encoded, redacted)

    def test_repeated_unclosed_private_key_markers_finish_within_hook_budget(self):
        code = "from evals.test_data_security import dlp; marker='-----BEGIN PRIVATE KEY-----'; assert not dlp.scan_text((marker+'\\n')*14000)"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=4, check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_exact_cap_redacts_all_values(self):
        token = synthetic_token()
        payload = " ".join([token] * dlp.MAX_FINDINGS)
        redacted, findings = dlp.redact_text(payload)
        self.assertEqual(len(findings), dlp.MAX_FINDINGS)
        self.assertNotIn(token, redacted)

    def test_truncated_private_key_body_is_redacted_without_footer(self):
        body = "Z7aQ" * 12
        text = "-----BEGIN PRIVATE KEY-----\n" + body
        redacted, findings = dlp.redact_text(text)
        self.assertTrue(any(item.category == "private_key" for item in findings))
        self.assertNotIn(body, redacted)

    def test_private_key_marker_constants_are_source_but_encrypted_body_is_secret(self):
        begin = "-----BEGIN RSA PRIVATE KEY-----"
        end = "-----END RSA PRIVATE KEY-----"
        source = 'const PRIVATE_KEY_BEGIN_MARKER: &str = "' + begin + '";\nconst PRIVATE_KEY_END_MARKER: &str = "' + end + '";'
        self.assertFalse(dlp.scan_text(source, include_identifiers=False))
        body = "Z7aQ" * 12
        key = begin + "\nProc-Type: 4,ENCRYPTED\nDEK-Info: AES-256-CBC," + "A1" * 16 + "\n\n" + body + "\n" + end
        redacted, findings = dlp.redact_text(key)
        self.assertTrue(any(item.category == "private_key" for item in findings))
        self.assertNotIn(body, redacted)

    def test_current_github_token_families_are_fully_redacted(self):
        tokens = ["github_" + "pat_" + "A7b9" * 20, "gh" + "s_12345_eyJ" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12]
        for token in tokens:
            redacted, findings = dlp.redact_text(token)
            self.assertTrue(dlp.contains_high_confidence(findings))
            self.assertTrue(redacted.startswith("{{DLP:SECRET:"))
            self.assertNotIn(token, redacted)


class PathAuditTests(unittest.TestCase):
    def test_static_equals_arguments_and_drive_relative_paths_are_inspected(self):
        for path in ("." + "env", ".aws" + "/credentials", ".docker" + "/config.json", "C:." + "env", "C:.aws" + "\\credentials"):
            for prefix in ("", "--input=", "INPUT="):
                with self.subTest(path=path, prefix=prefix):
                    self.assertEqual(dlp.sensitive_path_categories({"cmd": "reader " + prefix + path}), ["credential_store_path"])
        for path in (".env.example", "C:.env.template", ".ssh/id_ed25519.pub", "C:.ssh\\id_ed25519.pub", "client.key.rs"):
            for prefix in ("", "--input=", "INPUT="):
                self.assertEqual(dlp.sensitive_path_categories({"cmd": "reader " + prefix + path}), [])

    def test_large_shell_lexemes_fail_closed_inside_hook_budget(self):
        code = "from evals.test_data_security import dlp; value='echo '+('a'*(dlp.MAX_TEXT_BYTES-5));\ntry: dlp.sensitive_path_categories({'cmd':value})\nexcept dlp.InspectionLimit: pass\nelse: raise AssertionError('unbounded lexeme accepted')\nassert not dlp.sensitive_path_categories({'input':value})\nassert not dlp.sensitive_path_categories({'cmd': 'echo ' + ('abc ' * 40000)})"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=4, check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_patch_targets_are_distinct_from_source_path_references(self):
        suffix = "." + "key"
        source = '+const KEY_FILE: &str = "client' + suffix + '";\n+// *** Add File: ignored' + suffix
        safe = "*** Begin Patch\n*** Add File: source.rs\n" + source + "\n*** End Patch"
        for mode in ("personal", "strict"):
            for name in ("apply_patch", "functions.apply_patch"):
                for payload in (safe, {"input": safe}, {"command": safe}, {"patch": safe}):
                    self.assertEqual(invoke_hook(hook_event("PreToolUse", tool_name=name, tool_input=payload), mode=mode), (0, "", ""))
            for header in ("Add File", "Update File", "Delete File", "Move to"):
                for path in ("identity" + suffix, "my identity" + suffix, "C:." + "env", ".aws" + "/credentials"):
                    operation = "*** " + header + ": " + path
                    if header == "Move to":
                        operation = "*** Update File: source.rs\n" + operation
                    if header != "Delete File":
                        operation += ("\n@@" if header != "Add File" else "") + "\n+ordinary"
                    patch = "*** Begin Patch\n" + operation + "\n*** End Patch"
                    code, out, err = invoke_hook(hook_event("PreToolUse", tool_name="apply_patch", tool_input={"command": patch}), mode=mode)
                    self.assertEqual((code, err), (0, ""))
                    self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
            secret_patch = safe.replace(source, "+" + synthetic_token())
            code, out, err = invoke_hook(hook_event("PreToolUse", tool_name="apply_patch", tool_input={"input": secret_patch}), mode=mode)
            self.assertEqual((code, err), (0, ""))
            self.assertTrue(out, "credential in patch source must still be blocked")
            self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_patch_shape_exemption_does_not_apply_to_unknown_tools_or_payloads(self):
        path = "client." + "key"
        safe = '*** Begin Patch\n*** Add File: source.rs\n+let value = "' + path + '"\n*** End Patch'
        cases = (
            ("unknown_tool", {"input": safe}),
            ("apply_patch", {"code": safe}),
            ("apply_patch", {"input": safe, "patch": safe}),
            ("apply_patch", {"input": safe, "extra": path}),
            ("apply_patch", {"input": safe.removesuffix("*** End Patch")}),
        )
        for name, payload in cases:
            with self.subTest(name=name, fields=list(payload)):
                code, out, err = invoke_hook(hook_event("PreToolUse", tool_name=name, tool_input=payload))
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_documented_patch_command_field_is_source_not_shell(self):
        member = "." + "key"
        body = "let ok = top" + member + " == clip" + member
        rust = "pass" + "word: Zeroizing::new(value.to_owned()),"
        for source in (body, rust):
            patch = "*** Begin Patch\n*** Update File: /workspace/Source.txt\n@@\n+" + source + "\n*** End Patch"
            for mode in ("personal", "strict"):
                code, out, err = invoke_hook(hook_event("PreToolUse", tool_name="apply_patch", tool_input={"command": patch}), mode=mode)
                self.assertEqual((code, out, err), (0, "", ""))
        for mode in ("personal", "strict"):
            code, out, err = invoke_hook(hook_event("PreToolUse", tool_name="Bash", tool_input={"command": "cat identity." + "key"}), mode=mode)
            self.assertEqual(code, 0)
            self.assertFalse(err)
            self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_shell_operators_and_escapes_do_not_hide_sensitive_files(self):
        keyfile = "identity." + "key"
        envfile = "." + "env"
        for command in ("cat " + keyfile + ";true", "cat " + keyfile + "|wc -c", "cat " + keyfile + "||true", "cat<" + envfile, "cat identity.k\\ey", "cat .e\\nv", 'cat "' + keyfile + '";true'):
            with self.subTest(command=command):
                self.assertEqual(dlp.sensitive_path_categories({"cmd": command}), ["credential_store_path"])

    def test_fixture_words_are_not_path_exemptions(self):
        for basename in ("fixture-client." + "key", "dummy." + "pem", ".env.example-real", ".ssh/id_dummy"):
            with self.subTest(basename=basename):
                self.assertEqual(dlp.sensitive_path_categories({"path": "/synthetic-probe/" + basename}), ["credential_store_path"])

    def test_exact_templates_and_public_ssh_keys_are_allowed(self):
        for basename in (".env.example", ".env.sample", ".env.template", ".ssh/id_ed25519.pub", ".ssh/id_rsa-cert.pub"):
            with self.subTest(basename=basename):
                self.assertEqual(dlp.sensitive_path_categories({"path": "/synthetic-probe/" + basename}), [])

    def test_literal_file_arguments_do_not_inherit_truncated_safe_basenames(self):
        for basename in (".env.example", ".env.template", ".ssh/id_ed25519.pub"):
            for suffix in ("", " backup", "-backup"):
                path = "/synthetic probe/" + basename + suffix
                expected = ["credential_store_path"] if suffix else []
                for command in ('reader "' + path + '"', "reader --input='" + path + "'"):
                    with self.subTest(basename=basename, suffix=suffix, command=command):
                        self.assertEqual(dlp.sensitive_path_categories({"cmd": command}), expected)
                patch = "*** Begin Patch\n*** Delete File: " + path + "\n*** End Patch"
                code, out, err = invoke_hook(hook_event("PreToolUse", tool_name="apply_patch", tool_input={"input": patch}), mode="strict")
                self.assertEqual((code, err), (0, ""))
                if suffix:
                    self.assertTrue(out, "a different filename cannot inherit a safe basename exemption")
                    self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
                else:
                    self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
