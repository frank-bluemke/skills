# STORY-004: Scan And Classify Claude Skills

## User Story

As a Codex operator, I want a CLI to scan Claude-installed skills and classify each skill by compatibility so I can see what can be copied, converted, or needs manual work.

## Acceptance Criteria

- The CLI discovers `SKILL.md` files under a configurable Claude skill source.
- Duplicate skill names are de-duplicated with stable source preference.
- The CLI compares discovered names against Codex-visible skills.
- Each skill is assigned a clear bucket:
  - `already_available`
  - `copy`
  - `convert`
  - `manual`
  - `skipped`
- The CLI can run in dry-run mode without modifying the Codex skill directory.

## Status

Done
