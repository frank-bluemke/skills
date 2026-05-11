# FEATURE-002: Skill Compatibility Scanner

## Parent

[EPIC-002: Claude Skill Sync For Codex](EPIC-002-claude-skill-sync.md)

## Goal

Provide a CLI that scans Claude skill folders, classifies portability, performs safe imports/conversions, and writes operator-friendly reports.

## Stories

- [STORY-004: Scan And Classify Claude Skills](STORY-004-scan-and-classify-claude-skills.md)
- [STORY-005: Copy Easy Skills To Codex](STORY-005-copy-easy-skills-to-codex.md)
- [STORY-006: Convert Portable Claude Skills](STORY-006-convert-portable-claude-skills.md)
- [STORY-007: Daily Automation Reporting](STORY-007-daily-automation-reporting.md)

## Downstream Impacts

- Skills that rely on Claude-specific hooks need explicit Codex alternatives before they can be treated as fully portable.
- Skills that rely on MCP or connectors may require installed Codex plugins or MCP server configuration before they are operational.
- Imported skills are copied into `/Users/frankbluemke/.codex/skills` with a `claude-` prefix by default; Codex must be restarted to discover newly installed skills in interactive sessions.
- Existing unprefixed legacy imports are reported separately unless `--migrate-legacy` is used to create prefixed copies.

## Status

Completed
