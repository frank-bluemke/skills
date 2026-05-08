# STORY-007: Daily Automation Reporting

## User Story

As a Codex operator, I want a daily automation to run the skill sync and report copied, converted, and manual-review skills so new Claude skills can be evaluated continuously.

## Acceptance Criteria

- The CLI writes JSON and Markdown reports for each run.
- Reports list copied, converted, already available, skipped, and manual-review skills.
- Reports list older unprefixed imports as `legacy_unprefixed`.
- The automation can run the CLI in dry-run or active mode.
- The automation output clearly states whether it changed the Codex skill directory.

## Status

Done
