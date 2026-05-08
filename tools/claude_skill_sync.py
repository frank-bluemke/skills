#!/usr/bin/env python3
"""Scan Claude skills and import portable ones into Codex."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE = Path.home() / ".claude" / "plugins" / "cache"
DEFAULT_DEST = Path.home() / ".codex" / "skills"
DEFAULT_REPORT_DIR = Path("reports") / "claude-skill-sync"
DEFAULT_IMPORT_PREFIX = "claude-"
DEFAULT_CODEX_ROOTS = [
    Path.home() / ".codex" / "skills",
    Path.home() / ".codex" / "plugins" / "cache",
    Path.home() / ".agents" / "skills",
]

HARD_PATTERNS = {
    "claude_hook": re.compile(
        r"\b(PostToolUse|PreToolUse|Stop hook|Notification hook|hook validates|hooks/)\b",
        re.IGNORECASE,
    ),
    "claude_tool_syntax": re.compile(
        r"\b(Task|Bash|Read|Write|Edit|MultiEdit|Grep|Glob|TodoWrite|WebFetch|WebSearch|NotebookEdit)\s*\("
    ),
    "claude_runtime": re.compile(
        r"\.claude|Claude Code|Claude Desktop|claude --continue|CLAUDE\.md",
        re.IGNORECASE,
    ),
    "slash_command": re.compile(
        r"(?m)(?:^|[`\s])/[a-z][\w-]+(?::[\w-]+)?(?:\s|`|$)"
    ),
}

PORTABLE_PATTERNS = {
    "mcp": re.compile(r"\bmcp__|\bmcp_[a-zA-Z]|\bMCP\b|/mcp\b", re.IGNORECASE),
    "connector": re.compile(
        r"\bconnector\b|\bapp integration\b|\bplugin tool\b", re.IGNORECASE
    ),
}

NO_MCP_PATTERN = re.compile(
    r"uses no MCP tools|MCP tools \| None|MCP Tools\s*\n\s*This skill uses no MCP",
    re.IGNORECASE,
)

SCRIPT_SUFFIXES = {".py", ".js", ".ts", ".sh", ".ps1", ".mjs", ".cjs"}
SCRIPT_FILENAMES = {"package.json", "requirements.txt", "pyproject.toml"}


@dataclass
class SkillRecord:
    name: str
    source_name: str
    source_path: str
    plugin: str
    action: str
    reasons: list[str] = field(default_factory=list)
    duplicate_sources: int = 1
    destination_path: str | None = None
    changed: bool = False
    note: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan Claude skills and import portable skills into Codex."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Claude plugin cache or skill source. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help=f"Codex skill destination. Default: {DEFAULT_DEST}",
    )
    parser.add_argument(
        "--codex-root",
        action="append",
        type=Path,
        default=[],
        help="Additional Codex skill roots to use when checking already available skills.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help=f"Directory for JSON and Markdown reports. Default: {DEFAULT_REPORT_DIR}",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON output to stdout.",
    )
    parser.add_argument(
        "--import-prefix",
        default=DEFAULT_IMPORT_PREFIX,
        help=(
            "Prefix for imported Claude skill folder names and frontmatter names. "
            f"Default: {DEFAULT_IMPORT_PREFIX!r}. Use an empty string to preserve source names."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("scan", help="Classify Claude skills without copying.")

    sync = subparsers.add_parser("sync", help="Copy and convert portable skills.")
    sync.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without writing skills.",
    )
    sync.add_argument(
        "--include-script-review",
        action="store_true",
        help="Copy script-bearing skills that otherwise look portable.",
    )
    sync.add_argument(
        "--no-convert",
        action="store_true",
        help="Do not create converted MCP/connector-only skills.",
    )
    sync.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing destination skill folders. Use with care.",
    )
    sync.add_argument(
        "--migrate-legacy",
        action="store_true",
        help=(
            "Create prefixed imports for legacy unprefixed Claude skill folders "
            "that already exist in the destination. Does not delete old folders."
        ),
    )

    return parser.parse_args()


def discover_skill_dirs(source: Path) -> dict[str, list[Path]]:
    by_name: dict[str, list[Path]] = {}
    for skill_file in sorted(source.glob("**/skills/**/SKILL.md")):
        skill_dir = skill_file.parent
        by_name.setdefault(skill_dir.name, []).append(skill_dir)
    return by_name


def choose_source(candidates: list[Path]) -> Path:
    non_github = [path for path in candidates if ".github" not in path.parts]
    preferred = non_github or candidates
    return sorted(preferred, key=lambda path: (len(path.parts), str(path)))[0]


def plugin_name(source_root: Path, skill_dir: Path) -> str:
    try:
        parts = skill_dir.relative_to(source_root).parts
    except ValueError:
        return "unknown"
    if len(parts) >= 3:
        return "/".join(parts[:3])
    return "unknown"


def discover_codex_skill_names(roots: Iterable[Path]) -> set[str]:
    names: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for skill_file in root.glob("**/SKILL.md"):
            names.add(skill_file.parent.name)
    return names


def has_script_files(skill_dir: Path) -> bool:
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in SCRIPT_SUFFIXES or path.name in SCRIPT_FILENAMES:
            return True
    return False


def imported_name(source_name: str, import_prefix: str) -> str:
    if not import_prefix or source_name.startswith(import_prefix):
        return source_name
    return f"{import_prefix}{source_name}"


def classify_skill(
    source_root: Path,
    skill_dir: Path,
    duplicate_sources: int,
    codex_names: set[str],
    dest: Path,
    include_script_review: bool,
    convert_enabled: bool,
    import_prefix: str,
    migrate_legacy: bool,
) -> SkillRecord:
    source_name = skill_dir.name
    name = imported_name(source_name, import_prefix)
    text = (skill_dir / "SKILL.md").read_text(errors="ignore")
    reasons: list[str] = []

    for reason, pattern in HARD_PATTERNS.items():
        if pattern.search(text):
            reasons.append(reason)

    portable_reasons: list[str] = []
    for reason, pattern in PORTABLE_PATTERNS.items():
        if pattern.search(text):
            portable_reasons.append(reason)

    if "mcp" in portable_reasons and NO_MCP_PATTERN.search(text):
        portable_reasons.remove("mcp")
        reasons.append("mentions_mcp_but_declares_none")

    scripts = has_script_files(skill_dir)
    if scripts:
        reasons.append("bundled_scripts")

    dest_path = dest / name
    legacy_dest_path = dest / source_name
    destination_path = str(dest_path)
    legacy_unprefixed = (
        bool(import_prefix)
        and source_name != name
        and (legacy_dest_path / "SKILL.md").exists()
    )
    already_in_codex = (
        name in codex_names
        or (dest_path / "SKILL.md").exists()
        or (source_name in codex_names and not legacy_unprefixed)
    )

    if already_in_codex:
        action = "already_available"
        note = "Skill name already exists in a Codex-visible skill root."
    elif legacy_unprefixed and not migrate_legacy:
        action = "legacy_unprefixed"
        note = (
            "This Claude skill appears to have been imported before import-prefix naming was added. "
            "It was not renamed automatically."
        )
    elif legacy_unprefixed:
        reasons.append("legacy_unprefixed_destination_exists")
        if any(reason in reasons for reason in HARD_PATTERNS):
            action = "manual"
            note = (
                "Legacy unprefixed import exists, but the source now requires manual "
                "Claude-specific conversion."
            )
        elif portable_reasons and convert_enabled:
            action = "convert"
            reasons.extend(portable_reasons)
            note = "Migrating legacy unprefixed skill into a prefixed converted Codex skill."
        elif portable_reasons:
            action = "manual"
            reasons.extend(portable_reasons)
            note = "Legacy unprefixed import exists; conversion disabled."
        elif scripts and not include_script_review:
            action = "manual"
            note = "Legacy unprefixed import exists; bundled scripts need review."
        else:
            action = "copy"
            note = "Migrating legacy unprefixed skill into a prefixed Codex skill."
    elif any(reason in reasons for reason in HARD_PATTERNS):
        action = "manual"
        note = "Contains Claude-specific runtime, hook, slash-command, or tool-call syntax."
    elif portable_reasons and convert_enabled:
        action = "convert"
        reasons.extend(portable_reasons)
        note = "Portable only after Codex MCP/connector guidance is added."
    elif portable_reasons:
        action = "manual"
        reasons.extend(portable_reasons)
        note = "Conversion disabled; MCP or connector mapping required."
    elif scripts and not include_script_review:
        action = "manual"
        note = "Bundled scripts need review before automated import."
    else:
        action = "copy"
        note = "No hard Claude-specific markers found."

    return SkillRecord(
        name=name,
        source_name=source_name,
        source_path=str(skill_dir),
        plugin=plugin_name(source_root, skill_dir),
        action=action,
        reasons=sorted(set(reasons)),
        duplicate_sources=duplicate_sources,
        destination_path=destination_path,
        note=note,
    )


def build_records(
    source: Path,
    dest: Path,
    codex_roots: list[Path],
    include_script_review: bool = False,
    convert_enabled: bool = True,
    import_prefix: str = DEFAULT_IMPORT_PREFIX,
    migrate_legacy: bool = False,
) -> list[SkillRecord]:
    by_name = discover_skill_dirs(source)
    codex_names = discover_codex_skill_names(codex_roots)
    records: list[SkillRecord] = []
    for name, candidates in by_name.items():
        selected = choose_source(candidates)
        records.append(
            classify_skill(
                source,
                selected,
                len(candidates),
                codex_names,
                dest,
                include_script_review,
                convert_enabled,
                import_prefix,
                migrate_legacy,
            )
        )
    return sorted(records, key=lambda record: (record.action, record.plugin, record.name))


def rewrite_skill_name(skill_text: str, record: SkillRecord) -> str:
    frontmatter = re.match(r"(?s)\A(---\n.*?\n---\n)(.*)\Z", skill_text)
    if not frontmatter:
        return skill_text
    header = frontmatter.group(1)
    body = frontmatter.group(2)
    if re.search(r"(?m)^name:\s*", header):
        header = re.sub(r"(?m)^name:\s*.*$", f"name: {record.name}", header, count=1)
    else:
        header = header.replace("---\n", f"---\nname: {record.name}\n", 1)
    return header + body


def prepend_portability_note(skill_text: str, record: SkillRecord) -> str:
    conversion_reason = ", ".join(record.reasons) or "direct copy"
    note = f"""## Codex Import Notes

This skill was imported from a Claude plugin skill by `tools/claude_skill_sync.py`.

- Codex skill name: `{record.name}`
- Original Claude skill name: `{record.source_name}`
- Source plugin: `{record.plugin}`
- Source path: `{record.source_path}`
- Import reason: `{conversion_reason}`
- Use Codex-native tools, installed Codex plugins, local CLIs, or configured MCP servers for live operations.
- If a referenced Claude MCP server, connector, slash command, or plugin tool is not available in Codex, stop and report the missing integration instead of pretending the tool exists.
- Do not rely on Claude-specific hooks or session commands. Run validation steps explicitly.

"""
    frontmatter = re.match(r"(?s)\A(---\n.*?\n---\n)(.*)\Z", skill_text)
    if frontmatter:
        return f"{frontmatter.group(1)}\n{note}{frontmatter.group(2)}"
    return note + skill_text


def copy_skill(record: SkillRecord, dry_run: bool, overwrite: bool, converted: bool) -> None:
    source = Path(record.source_path)
    dest = Path(record.destination_path or "")

    if dry_run:
        record.changed = False
        record.note = f"Dry run: would {'convert' if converted else 'copy'} to {dest}."
        return

    if dest.exists():
        if not overwrite:
            record.changed = False
            record.action = "skipped"
            record.note = f"Destination already exists and --overwrite was not set: {dest}"
            return
        shutil.rmtree(dest)

    shutil.copytree(source, dest)
    skill_file = dest / "SKILL.md"
    skill_text = skill_file.read_text(errors="ignore")
    skill_text = rewrite_skill_name(skill_text, record)
    skill_file.write_text(prepend_portability_note(skill_text, record))
    record.changed = True


def run_sync(records: list[SkillRecord], dry_run: bool, overwrite: bool) -> None:
    for record in records:
        if record.action == "copy":
            copy_skill(record, dry_run=dry_run, overwrite=overwrite, converted=False)
        elif record.action == "convert":
            copy_skill(record, dry_run=dry_run, overwrite=overwrite, converted=True)


def summary(records: list[SkillRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.action] = counts.get(record.action, 0) + 1
    counts["changed"] = sum(1 for record in records if record.changed)
    return counts


def report_payload(command: str, args: argparse.Namespace, records: list[SkillRecord]) -> dict:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "command": command,
        "source": str(args.source),
        "dest": str(args.dest),
        "report_dir": str(args.report_dir),
        "summary": summary(records),
        "records": [asdict(record) for record in records],
    }


def write_reports(payload: dict, report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = report_dir / f"claude-skill-sync-{stamp}.json"
    md_path = report_dir / f"claude-skill-sync-{stamp}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    md_path.write_text(render_markdown(payload))
    return json_path, md_path


def render_markdown(payload: dict) -> str:
    lines = [
        "# Claude Skill Sync Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"Command: `{payload['command']}`",
        f"Source: `{payload['source']}`",
        f"Destination: `{payload['dest']}`",
        "",
        "## Summary",
        "",
    ]
    for key in sorted(payload["summary"]):
        lines.append(f"- `{key}`: {payload['summary'][key]}")
    lines.extend(["", "## Details", ""])
    for action in ["copy", "convert", "legacy_unprefixed", "manual", "already_available", "skipped"]:
        rows = [record for record in payload["records"] if record["action"] == action]
        if not rows:
            continue
        lines.extend([f"### {action}", "", "| Skill | Original | Plugin | Reasons | Changed | Note |", "| --- | --- | --- | --- | --- | --- |"])
        for record in rows:
            reasons = ", ".join(record["reasons"])
            note = record["note"].replace("|", "\\|")
            lines.append(
                f"| `{record['name']}` | `{record['source_name']}` | `{record['plugin']}` | {reasons} | {record['changed']} | {note} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def print_summary(payload: dict, json_paths: tuple[Path, Path] | None = None) -> None:
    print("Claude skill sync summary")
    for key in sorted(payload["summary"]):
        print(f"  {key}: {payload['summary'][key]}")
    if json_paths:
        print(f"JSON report: {json_paths[0]}")
        print(f"Markdown report: {json_paths[1]}")


def main() -> int:
    args = parse_args()
    source = args.source.expanduser()
    dest = args.dest.expanduser()
    codex_roots = [root.expanduser() for root in (args.codex_root or [])]
    if not codex_roots:
        codex_roots = DEFAULT_CODEX_ROOTS
    elif dest not in codex_roots:
        codex_roots.append(dest)

    if not source.exists():
        print(f"Source does not exist: {source}", file=sys.stderr)
        return 2

    include_script_review = bool(
        getattr(args, "include_script_review", False)
    )
    convert_enabled = not bool(getattr(args, "no_convert", False))
    migrate_legacy = bool(getattr(args, "migrate_legacy", False))
    records = build_records(
        source=source,
        dest=dest,
        codex_roots=codex_roots,
        include_script_review=include_script_review,
        convert_enabled=convert_enabled,
        import_prefix=args.import_prefix,
        migrate_legacy=migrate_legacy,
    )

    if args.command == "sync":
        run_sync(
            records,
            dry_run=bool(args.dry_run),
            overwrite=bool(args.overwrite),
        )

    payload = report_payload(args.command, args, records)
    report_paths = write_reports(payload, args.report_dir)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_summary(payload, report_paths)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
