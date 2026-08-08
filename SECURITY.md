# Security Policy

## Supported versions

Security fixes are provided for the latest tagged minor release. Before `1.0.0`, minor releases may intentionally evolve workflow behavior, but incompatible packet, CLI, or hook changes still require a major version increment under this repository's version policy.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting or Security Advisory feature for this repository. Do not open a public Issue containing exploit details, credentials, personal data, packet artifacts, or runtime logs.

Include the affected version, minimal reproduction, expected impact, and any known mitigation. You may use synthetic paths and redacted evidence. The maintainer will acknowledge the report, assess severity and affected versions, coordinate a fix, and publish release notes after remediation is available.

## Trust boundary

This plugin runs local hooks after the user explicitly trusts their definitions. The hooks are designed to activate only for a repository with an explicit `.codex/dev-flow/current` pointer. They have no MCP server, network integration, authentication flow, or secret requirement. Review `hooks/hooks.json` and the referenced Python script before granting trust, especially after an update.
