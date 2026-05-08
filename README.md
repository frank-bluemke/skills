# Codex Skills for Cin7 Core

This repository contains Codex skills for building, reviewing, and querying Cin7 Core Inventory data.

## Included Skills

### `cin7-core-api`

A Codex skill that helps choose the correct Cin7 Core endpoint, shape requests, apply required headers, and use the bundled API blueprint and reference files.

### `cin7-core-live-data`

A Codex skill plus bundled read-only MCP server for live Cin7 Core questions such as product cost, inventory availability, sale drill-down, purchase drill-down, units-sold lookups, and units-ordered lookups.

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
