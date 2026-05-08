# EPIC-002: Claude Skill Sync For Codex

## Goal

Create a repeatable way to scan Claude-installed skills, classify Codex compatibility, import low-risk skills into Codex, convert portable skills where possible, and report skills that still need manual work.

## Business Value

The user has many useful Claude skills already installed. Codex should be able to reuse compatible instruction assets without unsafe blind copying or losing track of skills that need connector, MCP, hook, or runtime adaptation.

## Scope

- Scan Claude plugin cache locations for `SKILL.md` files.
- Compare discovered skills against Codex-visible skill names.
- Copy easy skills into the global Codex skill directory using a `claude-` import prefix.
- Deterministically convert skills that only need MCP or connector guidance into Codex-aware wrappers.
- Rewrite imported skill frontmatter `name:` values so Codex-visible names match imported folder names.
- Report copied, converted, skipped, already available, and manual-review skills.
- Support daily Codex automation execution.

## Out Of Scope

- Installing new global system dependencies.
- Installing or configuring third-party MCP servers automatically.
- Rewriting complex Claude hooks into live Codex tool integrations without review.
- Deleting or replacing existing Codex skills.

## Features

- [FEATURE-002: Skill Compatibility Scanner](FEATURE-002-skill-compatibility-scanner.md)

## Status

Completed
