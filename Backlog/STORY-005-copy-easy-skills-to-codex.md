# STORY-005: Copy Easy Skills To Codex

## User Story

As a Codex operator, I want low-risk Claude skills copied into Codex automatically so reusable instructions are available without manual folder copying.

## Acceptance Criteria

- The sync command copies only skills classified as low-risk copy candidates by default.
- Existing Codex skill folders are not overwritten unless an explicit flag is used.
- The destination defaults to `/Users/frankbluemke/.codex/skills`.
- Imported Claude skills use a `claude-` prefix by default.
- Imported `SKILL.md` frontmatter `name:` values are rewritten to match the prefixed folder name.
- Copied skills preserve their folder contents.
- Copied skills are included in the run report.

## Status

Done
