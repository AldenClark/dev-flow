# Security Policy

## Supported versions

Security fixes are provided for the latest tagged major/minor release line. Incompatible Skill names, packet, CLI, or hook contracts require a major version increment under this repository's version policy.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting or Security Advisory feature for this repository. Do not open a public Issue containing exploit details, credentials, personal data, packet artifacts, or runtime logs.

Include the affected version, minimal reproduction, expected impact, and any known mitigation. You may use synthetic paths and redacted evidence. The maintainer will acknowledge the report, assess severity and affected versions, coordinate a fix, and publish release notes after remediation is available.

## Trust boundary

This plugin runs local Hooks only after the user explicitly trusts their exact definitions. Dev Flow 2.0 has no process, lifecycle, command-authorization, or packet Hook. The independent data-security handler runs on documented `UserPromptSubmit`, `PreToolUse`, and `PostToolUse` paths wherever the trusted plugin is active; it performs bounded in-memory inspection/redaction and intentionally retains no raw finding, mapping, payload log, credential, or transcript.

The plugin has no MCP server, network integration, authentication flow, credential requirement, or endpoint/network egress interceptor. Hosted and specialized tool paths can be outside local Hook coverage, and a `PostToolUse` Hook cannot undo side effects that already occurred. Work and ordinary Chat instruction templates are guidance, not deterministic pre-send controls.

Review `hooks/hooks.json`, `hooks/data_security_hook.py`, and the protected-file baseline before granting trust, especially after an update. Run:

```bash
python3 skills/company-data-security/scripts/doctor.py --plugin-root .
python3 -m unittest evals.test_data_security -v
```

Doctor proves packaged byte/semantic state at check time. It reports Hook trust and live Chat/Work/Chat configuration as `not_observed` or `self_attested`; it is not a signed anti-tamper mechanism or enterprise compliance attestation.
