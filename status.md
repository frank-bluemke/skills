# Status

## Epics

| ID | Name | Status |
| --- | --- | --- |
| EPIC-001 | Cin7 Live Query Skill | Completed |
| EPIC-002 | Claude Skill Sync For Codex | Completed |

## Features

| ID | Epic | Name | Status |
| --- | --- | --- | --- |
| FEATURE-001 | EPIC-001 | Read-Only Cin7 MCP Server | Completed |
| FEATURE-002 | EPIC-002 | Skill Compatibility Scanner | Completed |

## Stories

| ID | Feature | Name | Status |
| --- | --- | --- | --- |
| STORY-001 | FEATURE-001 | Live Cin7 Chat Lookups | Completed |
| STORY-002 | FEATURE-001 | Inventory Availability Lookups | Completed |
| STORY-003 | FEATURE-001 | Purchase Order Quantity Lookups | Completed |
| STORY-004 | FEATURE-002 | Scan And Classify Claude Skills | Completed |
| STORY-005 | FEATURE-002 | Copy Easy Skills To Codex | Completed |
| STORY-006 | FEATURE-002 | Convert Portable Claude Skills | Completed |
| STORY-007 | FEATURE-002 | Daily Automation Reporting | Completed |

## Current Implementation Notes

- Existing blueprint-only skill: `cin7-core-api`
- Added live read-only skill: `cin7-core-live-data`
- Current release covers product lookup, cost lookup, inventory availability, sale drill-down, purchase drill-down, units-sold questions, and units-ordered questions
- Added Claude skill sync utility: `tools/claude_skill_sync.py`
- Claude-origin imports use the `claude-` skill name prefix by default.
