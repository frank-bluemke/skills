# STORY-006: Convert Portable Claude Skills

## User Story

As a Codex operator, I want Claude skills that only need MCP or connector guidance converted into Codex-aware skills so Codex can use the instructions while clearly surfacing remaining integration requirements.

## Acceptance Criteria

- The sync command can convert skills that do not contain hard Claude-only runtime, hook, or tool-call requirements.
- Converted skills prepend Codex portability notes to `SKILL.md`.
- Converted skills use a `claude-` prefix by default and rewrite frontmatter `name:` values to match.
- Converted skills preserve source references and supporting files.
- Skills with Claude hooks, Claude runtime instructions, or Claude tool-call syntax remain in the manual-review bucket.
- Converted skills are included in the run report.

## Status

Done
