"""Code-shaped false-positive regressions; all credential controls are synthetic."""

import base64
import json
import subprocess
import sys
import unittest

from evals.test_data_security import dlp, synthetic_token
from evals.test_dlp_hook_audit import _base_event, _invoke


FIELD = "pass" + "word"


class SourceReferenceTests(unittest.TestCase):
    def test_comments_cannot_terminate_sensitive_wrapper_inspection(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for name, comment in (
            ("python", "# ) ; ignored punctuation\n"),
            ("line", "// ) ; ignored punctuation\n"),
            ("block", "/* ) ; ignored punctuation */"),
            ("python_adjacent", "encoding=utf8# ) ; ignored punctuation\n, "),
        ):
            expression = "String(" + comment + "value=" + json.dumps(literal) + ")"
            with self.subTest(comment=name):
                redacted, findings = dlp.redact_text(FIELD + " = " + expression)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(literal, redacted)
                comment_literal = comment.replace("ignored punctuation", json.dumps(literal))
                expression = "String(" + comment_literal + "credential_value)"
                redacted, findings = dlp.redact_text(FIELD + " = " + expression)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(literal, redacted)

    def test_rust_raw_wrapper_preserves_complete_literal_span(self):
        literal = "N7rQ4zP9mL2xV8cB"
        body = 'prefix"' + literal + '"suffix'
        for count in (1, 2, 8):
            raw = "r" + "#" * count + '"' + body + '"' + "#" * count
            for form, expression in (("plain", raw), ("wrapper", "String(value=" + raw + ")")):
                with self.subTest(hashes=count, form=form):
                    redacted, findings = dlp.redact_text(FIELD + " = " + expression)
                    self.assertTrue(dlp.contains_high_confidence(findings))
                    self.assertNotIn(literal, redacted)

    def test_long_and_unclosed_triple_literals_stay_inside_hook_budget(self):
        code = "\n".join((
            "from evals.test_dlp_code_false_positives import FIELD, dlp",
            "value = 'N7rQ4zP9mL2xV8cB' * 2048",
            "quote = chr(34) * 3",
            "for ending in (quote, ''):",
            "    redacted, findings = dlp.redact_text(FIELD + ' = ' + quote + value + ending)",
            "    assert dlp.contains_high_confidence(findings)",
            "    assert value not in redacted",
        ))
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=4, check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_heuristic_quote_prefix_and_wrapper_cross_product(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for quote_name, quote in (("double", '"'), ("single", "'"), ("triple_double", '"""'), ("triple_single", "'''")):
            for prefix in ("", "r", "b", "f"):
                expression = prefix + quote + literal + quote
                for wrapper_name, wrapper in (
                    ("plain", "{}"),
                    ("positional", "String({})"),
                    ("named", "String(value={})"),
                    ("later_named", 'String(encoding="utf8", value={})'),
                ):
                    with self.subTest(quote=quote_name, prefix=prefix, wrapper=wrapper_name):
                        source = FIELD + " = " + wrapper.format(expression)
                        redacted, findings = dlp.redact_text(source)
                        self.assertTrue(dlp.contains_high_confidence(findings))
                        self.assertNotIn(literal, redacted)

    def test_source_references_change_class_only_at_literal_data_boundaries(self):
        reference = "credential_value"
        for name, expression in (
            ("named", reference),
            ("parenthesized", "(" + reference + ")"),
            ("wrapped", "String(value=" + reference + ")"),
            ("formatted", 'String(value=f"{' + reference + '}")'),
        ):
            with self.subTest(reference=name):
                self.assertFalse(dlp.scan_text(f"copy({FIELD} = {expression})"))
        for payload in ({FIELD: reference}, FIELD + " = " + json.dumps(reference)):
            self.assertTrue(dlp.contains_high_confidence(dlp.scan_value(payload)))

    def test_quote_and_wrapper_transformations_preserve_literal_detection(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for form, expression in (
            ("triple_double", '"""' + literal + '"""'),
            ("triple_single", "'''" + literal + "'''"),
            ("raw_triple", 'r"""' + literal + '"""'),
            ("formatted_triple", 'f"""' + literal + '"""'),
            ("wrapper_named_first", "String(value=" + json.dumps(literal) + ")"),
            ("wrapper_named_spaced", "String(value = " + json.dumps(literal) + ")"),
            ("wrapper_later_literal", 'String(encoding="utf8", value=' + json.dumps(literal) + ")"),
            ("nested_named_wrapper", "String(value=str(" + json.dumps(literal) + "))"),
        ):
            with self.subTest(form=form):
                redacted, findings = dlp.redact_text(FIELD + " = " + expression)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(literal, redacted)

    def test_named_arguments_keep_reference_syntax(self):
        references = {
            "bare": "replacement",
            "snake": "credential_value",
            "camel_digit": "cachedPassword2",
            "borrow": "&replacement",
            "dereference": "*replacement",
            "rust_raw_identifier": "r#replacement",
            "implicit_member": ".currentPassword",
            "closure_argument": "$0.credential",
            "index": "settings[credentialIndex]",
            "optional": "replacement?",
            "nonnull": "replacement!!",
        }
        for name, reference in references.items():
            for syntax, source in (
                ("kotlin_python", f"draft.copy({FIELD} = {reference})"),
                ("swift", f"Credential({FIELD}: {reference})"),
                ("nested", f"consume(draft.copy({FIELD} = {reference}))"),
                ("array", f"[draft.copy({FIELD} = {reference})]"),
                ("multiline", f"draft.copy(\n    {FIELD} = {reference}\n)"),
                ("later_argument", f"draft.copy(name = currentName, {FIELD} = {reference})"),
                ("fluent", f"draft.copy({FIELD} = {reference}).build()"),
            ):
                with self.subTest(reference=name, syntax=syntax):
                    self.assertFalse(dlp.scan_text(source, include_identifiers=False))

    def test_source_delimiters_do_not_exempt_credential_literals(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for form, value in (
            ("quoted", json.dumps(literal)),
            ("single_quoted", "'" + literal + "'"),
            ("unquoted", literal),
            ("wrapper", "String(" + json.dumps(literal) + ")"),
            ("borrowed", "&" + json.dumps(literal)),
        ):
            for syntax, source in (
                ("plain", FIELD + " = " + value),
                ("named", f"draft.copy({FIELD} = {value})"),
                ("swift", f"Credential({FIELD}: {value})"),
            ):
                with self.subTest(form=form, syntax=syntax):
                    redacted, findings = dlp.redact_text(source)
                    self.assertTrue(dlp.contains_high_confidence(findings))
                    self.assertNotIn(literal, redacted)

        # Structured strings remain literal data even when they resemble source.
        for name, value in (
            ("closer", "replacement)"),
            ("index", "settings[credentialIndex]"),
            ("optional", "replacement!!"),
        ):
            with self.subTest(structured_value=name):
                self.assertTrue(dlp.contains_high_confidence(dlp.scan_value({FIELD: value})))

        # Delimiters in ordinary unquoted values are not source-call context.
        for value in ("lowercasecredential)", "lowercasecredential!!", "lowercasecredential]"):
            with self.subTest(unquoted_delimiter=value[-2:]):
                self.assertTrue(dlp.contains_high_confidence(dlp.scan_text(FIELD + " = " + value)))

    def test_original_patch_passes_hook_while_literal_replacement_is_denied(self):
        source = f"draft.copy({FIELD} = replacement)"
        patch = "*** Begin Patch\n*** Add File: Example.kt\n+" + source + "\n*** End Patch"
        event = _base_event("PreToolUse") | {"tool_name": "apply_patch", "tool_input": patch}
        self.assertEqual(_invoke(event), (0, b"", b""))
        token = synthetic_token()
        event["tool_input"] = patch.replace("replacement", json.dumps(token))
        code, stdout, stderr = _invoke(event)
        self.assertEqual((code, stderr), (0, b""))
        self.assertEqual(json.loads(stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertNotIn(token.encode(), stdout)

    def test_prefixed_and_spaced_wrapper_literals_remain_protected(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for form, expression in (
            ("spaced_call", "String ( " + json.dumps(literal) + ")"),
            ("raw_python", "r" + json.dumps(literal)),
            ("bytes_python", "b" + json.dumps(literal)),
            ("raw_rust", 'r#"' + literal + '"#'),
            ("formatted_literal", "f" + json.dumps(literal)),
        ):
            with self.subTest(form=form):
                redacted, findings = dlp.redact_text(FIELD + " = " + expression)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(literal, redacted)

        reference = 'f"{credential_value}"'
        self.assertFalse(dlp.scan_text(FIELD + " = " + reference))


class SourceTemplateTests(unittest.TestCase):
    def test_format_markers_inside_plain_strings_are_not_source_context(self):
        reference = "{credential_value}"
        uri = "postgres://user:" + reference + "@host.invalid/db"
        source = "report = " + json.dumps("example f'" + uri + "'")
        redacted, findings = dlp.redact_text(source)
        self.assertTrue(dlp.contains_high_confidence(findings))
        self.assertNotIn(reference, redacted)

    def test_url_reference_formatting_transformations_remain_source(self):
        # Mutate the same public reference-template fixture used below.
        for form, expression in (
            ("conversion", "credential_value!s"),
            ("format_spec", "credential_value:>20"),
            ("numeric_index", "credentials[0]"),
        ):
            source = 'url = f"postgres://{username}:{' + expression + '}@{host}/db"'
            with self.subTest(form=form):
                self.assertFalse(dlp.scan_text(source, include_identifiers=False))
        source = 'url = f"postgres://{username}:{' + FIELD + '}@{host}/db"'
        for form, transformed in (
            ("triple", source.replace('f"', 'f"""').replace('/db"', '/db"""')),
            ("leading_text", source.replace('f"', 'f"connection ')),
        ):
            with self.subTest(form=form):
                self.assertFalse(dlp.scan_text(transformed, include_identifiers=False))

    def test_url_templates_contain_references_not_password_literals(self):
        for name, source in (
            ("python_fstring", 'url = f"postgres://{username}:{' + FIELD + '}@{host}/db"'),
            ("python_format", 'url = "postgres://{username}:{' + FIELD + '}@{host}/db".format(**values)'),
            ("python_raw_fstring", 'url = rf"postgres://{username}:{' + FIELD + '}@{host}/db"'),
            ("python_fraw_string", 'url = fr"postgres://{username}:{' + FIELD + '}@{host}/db"'),
            ("javascript", 'url = `postgres://${username}:${' + FIELD + '}@${host}/db`'),
            ("shell", 'url="postgres://$DB_USER:$DB_PASSWORD@$DB_HOST/db"'),
        ):
            with self.subTest(template=name):
                self.assertFalse(dlp.scan_text(source, include_identifiers=False))
                encoded = base64.b64encode(source.encode()).decode()
                self.assertFalse(dlp.scan_text(encoded, include_identifiers=False))

    def test_url_literals_and_mixed_template_literals_remain_protected(self):
        literal = "N7rQ4zP9mL2xV8cB"
        for name, value in (
            ("literal", literal),
            ("mixed_prefix", literal + "{suffix}"),
            ("mixed_suffix", "{prefix}" + literal),
        ):
            source = 'url = f"postgres://{username}:' + value + '@{host}/db"'
            with self.subTest(form=name):
                redacted, findings = dlp.redact_text(source)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(literal, redacted)
                encoded = base64.b64encode(source.encode()).decode()
                redacted, findings = dlp.redact_text(encoded)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(encoded, redacted)

    def test_unrelated_formatting_does_not_exempt_literal_url_credentials(self):
        literal = "{credential_value}"
        source = 'url = "postgres://user:' + literal + '@host.invalid/db"'
        for name, tail in (
            ("plain", ""),
            ("later_statement", '; label = "{}".format(value)'),
            ("next_line", '\nlabel = "{}".format(value)'),
        ):
            with self.subTest(context=name):
                redacted, findings = dlp.redact_text(source + tail)
                self.assertTrue(dlp.contains_high_confidence(findings))
                self.assertNotIn(literal, redacted)


class CommandOperandTests(unittest.TestCase):
    def test_python_script_arguments_cannot_reopen_interpreter_option_parsing(self):
        for name, command in (
            ("after_script", "python3 script.py -c settings.key"),
            ("after_source", "python3 -c 'import sys; open(sys.argv[2])' -c settings.key"),
            ("after_double_dash", "python3 -- script.py -c settings.key"),
            ("after_module", "python3 -m module -c settings.key"),
        ):
            with self.subTest(command=name):
                self.assertIn("credential_store_path", dlp.sensitive_path_categories({"cmd": command}))

    def test_whole_command_and_nested_shell_limits_remain_fail_closed(self):
        command = "echo " + "abc " * (dlp.MAX_TEXT_BYTES // 4 + 1)
        with self.assertRaises(dlp.InspectionLimit):
            dlp.sensitive_path_categories({"cmd": command})
        with self.assertRaises(dlp.InspectionLimit):
            list(dlp._shell_path_strings("echo harmless", depth=dlp.MAX_DEPTH + 1))

    def test_code_and_search_operands_are_not_credential_files(self):
        commands = {
            "python_source": "python3 -c 'result = record.key'",
            "python_import": "python3 -c 'import package.key'",
            "search_pattern": "rg 'record.key' README.md",
            "search_explicit_pattern": "rg -e record.key README.md",
            "git_message_pattern": "git log --grep=record.key -- README.md",
        }
        for name, command in commands.items():
            with self.subTest(command=name):
                self.assertEqual(dlp.sensitive_path_categories({"cmd": command}), [])

    def test_actual_sensitive_operands_remain_blocked(self):
        for name, command in (
            ("cat", "cat identity.key"),
            ("search_file", "rg harmless identity.key"),
            ("search_pattern_and_file", "rg record.key identity.key"),
            ("git_diff", "git diff -- identity.key"),
            ("nested_shell", "sh -c 'cat identity.key; true'"),
            ("environment_suffix", "cat .env.production.local"),
            ("python_sensitive_open", "python3 -c 'open(\"identity.key\").read()'"),
            ("pattern_file", "rg -f patterns.txt identity.key"),
            ("redirection", "cat < identity.key"),
            ("sensitive_glob", "rg --glob '*.key' harmless src"),
            ("unknown_option", "rg --unknown-option identity.key README.md"),
            ("unknown_git_form", "git show --grep record.key identity.key"),
        ):
            with self.subTest(command=name):
                self.assertIn("credential_store_path", dlp.sensitive_path_categories({"cmd": command}))


if __name__ == "__main__":
    unittest.main()
