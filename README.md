# Codex Skills

This repository contains Codex skills for building, reviewing, and querying Cin7 Core Inventory data, plus utilities for managing local Codex skill installations.

## Included Skills

### `cin7-core-api`

A Codex skill that helps choose the correct Cin7 Core endpoint, shape requests, apply required headers, and use the bundled API blueprint and reference files.

### `cin7-core-live-data`

A Codex skill plus bundled read-only MCP server for live Cin7 Core questions such as product cost, inventory availability, sale drill-down, purchase drill-down, units-sold lookups, and units-ordered lookups.

## Utilities

### Claude Skill Sync

`tools/claude_skill_sync.py` scans Claude-installed plugin skills, classifies Codex portability, copies low-risk skills into Codex, converts MCP/connector-only skills into Codex-aware wrappers, and reports skills that still require manual work.

Imported Claude skills are named with the `claude-` prefix by default, and the imported `SKILL.md` frontmatter `name:` is rewritten to match. For example, Claude's `aws-cdk` skill imports as `claude-aws-cdk`. This makes imported Claude-origin skills easy to identify in Codex.

The utility never overwrites an existing Codex skill unless `--overwrite` is explicitly passed. It does not install MCP servers, connectors, global dependencies, or external app integrations.

Default paths:

- Claude source: `/Users/frankbluemke/.claude/plugins/cache`
- Codex destination: `/Users/frankbluemke/.codex/skills`
- Reports: `reports/claude-skill-sync`

#### Scan Only

Run a compatibility scan without changing the Codex skill directory:

```bash
python3 tools/claude_skill_sync.py scan
```

Write scan reports to a specific folder:

```bash
python3 tools/claude_skill_sync.py --report-dir /tmp/claude-skill-sync scan
```

Print the full JSON payload to stdout:

```bash
python3 tools/claude_skill_sync.py --json scan
```

#### Dry-Run Sync

Show what would be copied and converted without writing skills:

```bash
python3 tools/claude_skill_sync.py sync --dry-run
```

Use explicit source and destination folders:

```bash
python3 tools/claude_skill_sync.py \
  --source /Users/frankbluemke/.claude/plugins/cache \
  --dest /Users/frankbluemke/.codex/skills \
  sync \
  --dry-run
```

#### Active Sync

Copy easy skills and convert portable MCP/connector-only skills using the default `claude-` import prefix:

```bash
python3 tools/claude_skill_sync.py sync
```

Also copy skills that include bundled scripts but have no other hard Claude-only markers:

```bash
python3 tools/claude_skill_sync.py sync --include-script-review
```

Disable conversion and only copy low-risk skills:

```bash
python3 tools/claude_skill_sync.py sync --no-convert
```

Create prefixed copies for older unprefixed Claude imports without deleting the old folders:

```bash
python3 tools/claude_skill_sync.py sync --migrate-legacy
```

Preserve original Claude skill names instead of prefixing them:

```bash
python3 tools/claude_skill_sync.py --import-prefix "" sync
```

#### Required Arguments

There are no required arguments when using the default local Claude and Codex locations.

Optional global arguments:

- `--source`: Claude plugin cache or skill source directory.
- `--dest`: Codex skill destination directory.
- `--codex-root`: Additional Codex-visible skill root for duplicate detection. May be passed multiple times.
- `--report-dir`: Directory for JSON and Markdown reports.
- `--import-prefix`: Prefix for imported Claude skill names. Defaults to `claude-`.
- `--json`: Print full JSON output to stdout.

Optional `sync` arguments:

- `--dry-run`: Do not copy or convert skills.
- `--include-script-review`: Copy script-bearing skills that otherwise look portable.
- `--no-convert`: Do not convert MCP/connector-only skills.
- `--migrate-legacy`: Create prefixed imports for older unprefixed imports.
- `--overwrite`: Replace existing destination skill folders. Use only after review.

#### Environment And Configuration

No environment variables are required.

The script expects these local directories to exist for the default workflow:

- `/Users/frankbluemke/.claude/plugins/cache`
- `/Users/frankbluemke/.codex/skills`

Codex must be restarted before newly copied or converted global skills are discovered in new sessions.

#### Expected Outputs

Each run writes two report files:

```text
reports/claude-skill-sync/claude-skill-sync-YYYYMMDD-HHMMSS.json
reports/claude-skill-sync/claude-skill-sync-YYYYMMDD-HHMMSS.md
```

Reports include:

- `copy`: skills copied directly.
- `convert`: skills copied with Codex import notes prepended.
- `legacy_unprefixed`: skills previously imported before `claude-` prefix naming was added.
- `manual`: skills requiring manual work because they reference Claude hooks, Claude runtime behavior, Claude tool-call syntax, slash-command workflows, or unconverted integrations.
- `already_available`: skills already visible to Codex by name.
- `skipped`: skills not changed because a destination already exists or conversion was disabled.
- `changed`: count of destination folders written in the current run.

## Install

Clone this repository into your local Codex skills directory:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/<your-org>/<your-repo>.git ~/.codex/skills/<your-repo>
```

## Planning Artifacts

This repository also tracks work items and status with:

- `EPIC-*.md`
- `FEATURE-*.md`
- `STORY-*.md`
- `status.md`
