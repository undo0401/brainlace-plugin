"""Brainlace Hermes plugin.

Brainlace is a filesystem-first second-brain bridge: humans can keep editing
Markdown notes in Obsidian or any future editor, while LIN/Hermes gets stable
agent-readable tools for indexing, searching, linking, moving, planning, and
writing notes.
"""

from __future__ import annotations

import difflib
import importlib.util
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PLUGIN_DIR = Path(__file__).resolve().parent
_SCHEMAS_SPEC = importlib.util.spec_from_file_location("brainlace_plugin_schemas", PLUGIN_DIR / "schemas.py")
assert _SCHEMAS_SPEC is not None and _SCHEMAS_SPEC.loader is not None
schemas = importlib.util.module_from_spec(_SCHEMAS_SPEC)
_SCHEMAS_SPEC.loader.exec_module(schemas)

PLUGIN_NAME = "brainlace"
DEFAULT_HERMES_HOME = Path(os.environ.get("HERMES_HOME", "/opt/data")).expanduser()
DEFAULT_NOTES_ROOT = os.environ.get("BRAINLACE_NOTES_ROOT", "notes")
INDEX_VERSION = 3
WIKILINK_RE = re.compile(r"(!?)\[\[([^\]|#]+)(#[^\]|]+)?(?:\|([^\]]+))?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]{2,}|[\u3040-\u30ff\u3400-\u9fff]{2,}")
SOURCE_SKIP_DIRS = {".obsidian", ".git", "archive", "archives", ".archive", "legacy"}
TARGET_SKIP_DIRS = {".obsidian", ".git"}


def _json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _resolve_vault_root(raw_root: str | None = None) -> Path:
    root_value = raw_root or os.environ.get("BRAINLACE_VAULT_ROOT") or os.environ.get("OBSIDIAN_VAULT_PATH") or "/opt/data/workspace"
    root = Path(str(root_value)).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"Brainlace vault root not found: {root}")
    return root


def _resolve_notes_root(vault_root: Path, raw_notes_root: str | None = None) -> Path:
    value = str(raw_notes_root or DEFAULT_NOTES_ROOT or ".").strip() or "."
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = vault_root / candidate
    candidate = candidate.resolve()
    _assert_under(candidate, vault_root, label="notes_root")
    if not candidate.exists() or not candidate.is_dir():
        raise RuntimeError(f"Brainlace notes root not found: {candidate}")
    return candidate


def _brainlace_data_dir() -> Path:
    path = PLUGIN_DIR / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path() -> Path:
    return _brainlace_data_dir() / "index.json"


def _assert_under(path: Path, root: Path, *, label: str = "path") -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"Brainlace {label} escapes vault root: {path}") from exc


def _safe_filename(title: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "-", str(title).strip())
    text = re.sub(r"\s+", " ", text).strip(" .")
    if not text:
        raise RuntimeError("note title is empty after filename normalization")
    if not text.lower().endswith(".md"):
        text += ".md"
    return text


def _normalize_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, Iterable):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + len("\n---"):].lstrip("\n")
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(line[4:].strip().strip('"\''))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip('"\'') for item in value[1:-1].split(",") if item.strip()]
            data[key] = items
        else:
            data[key] = value.strip('"\'')
    return data, body


def _frontmatter(title: str, tags: list[str], aliases: list[str]) -> str:
    lines = ["---", f"title: {title}"]
    if aliases:
        lines.append("aliases:")
        lines.extend(f"  - {alias}" for alias in aliases)
    if tags:
        lines.append("tags:")
        lines.extend(f"  - {tag}" for tag in tags)
    lines.extend([f"created: {_now_iso()}", "---", ""])
    return "\n".join(lines)


def _path_has_part(path: Path, names: set[str]) -> bool:
    return any(part.lower() in names for part in path.parts)


def _should_skip(path: Path, *, include_archives: bool) -> bool:
    parts = {part.lower() for part in path.parts}
    if ".obsidian" in parts or ".git" in parts:
        return True
    if include_archives:
        return False
    return any(part in {"archive", "archives", ".archive", "legacy"} for part in parts)


def _should_skip_target(path: Path) -> bool:
    return _path_has_part(path, TARGET_SKIP_DIRS)


def _plain_summary(body: str, limit: int = 420) -> str:
    plain = re.sub(r"```.*?```", " ", body, flags=re.S)
    plain = re.sub(r"[#>*_`\[\](){}]", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:limit]


def _frontmatter_value(frontmatter: dict[str, Any], key: str) -> str | None:
    value = frontmatter.get(key)
    if value is None or value == "":
        return None
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip()) or None
    return str(value)


def _catalog_card(row: dict[str, Any]) -> dict[str, Any]:
    raw_frontmatter = row.get("frontmatter")
    frontmatter: dict[str, Any] = raw_frontmatter if isinstance(raw_frontmatter, dict) else {}
    rel = str(row.get("rel_notes_path") or row.get("rel_path") or "")
    category = str(row.get("category") or "")
    haystack = "\n".join([
        str(row.get("title") or ""),
        rel,
        category,
        str(row.get("summary") or ""),
        "\n".join(str(v) for v in row.get("tags") or []),
        "\n".join(str(v) for v in row.get("headings") or []),
        "\n".join(str(v) for v in row.get("links") or []),
    ]).lower()
    explicit_role = _frontmatter_value(frontmatter, "context_role")
    explicit_freshness = _frontmatter_value(frontmatter, "freshness")
    explicit_source_quality = _frontmatter_value(frontmatter, "source_quality")

    inferred_role = "reference"
    if row.get("is_index"):
        inferred_role = "index"
    elif row.get("is_moc"):
        inferred_role = "map"
    elif any(part in haystack for part in ("design", "設計", "architecture", "仕様", "brainlace", "hermes", "plugin")):
        inferred_role = "design"
    elif any(part in haystack for part in ("diary", "日記", "memory", "感情")):
        inferred_role = "episodic"
    elif category.lower() in {"lin", "chibi-lin"}:
        inferred_role = "lore"
    elif any(part in haystack for part in ("source:", "参照", "github", "docs", "http")):
        inferred_role = "source"

    freshness_guess = "current"
    rel_lower = rel.lower()
    if any(part in rel_lower for part in ("archive/", ".archive/", "legacy/")):
        freshness_guess = "archived"
    elif any(part in haystack for part in ("stale", "deprecated", "retired", "古い", "廃止")):
        freshness_guess = "stale"

    source_quality_guess = "interpretation"
    if explicit_source_quality:
        source_quality_guess = explicit_source_quality
    elif any(part in haystack for part in ("source:", "参照 repo", "github", "docs", "https://", "http://")):
        source_quality_guess = "source-backed"
    elif inferred_role in {"lore", "episodic"}:
        source_quality_guess = "personal"

    when_to_use: list[str] = []
    if inferred_role == "design":
        when_to_use.extend(["planning", "architecture", "implementation-prep"])
    elif inferred_role == "index":
        when_to_use.extend(["navigation", "category-overview"])
    elif inferred_role == "map":
        when_to_use.extend(["concept-map", "topic-overview"])
    elif inferred_role == "lore":
        when_to_use.extend(["identity", "relationship-context"])
    elif inferred_role == "episodic":
        when_to_use.extend(["recent-context", "emotional-continuity"])
    elif inferred_role == "source":
        when_to_use.extend(["source-check", "research"])
    else:
        when_to_use.append("reference")

    when_not_to_use = ["live_system_state"]
    if freshness_guess in {"stale", "archived"}:
        when_not_to_use.append("current_operations")
    if source_quality_guess != "source-backed":
        when_not_to_use.append("source-of-truth-claim")

    confidence = 0.45
    if explicit_role:
        confidence += 0.25
    if row.get("summary"):
        confidence += 0.12
    if row.get("tags"):
        confidence += 0.08
    if row.get("headings"):
        confidence += 0.05
    if inferred_role != "reference":
        confidence += 0.1
    confidence = min(0.95, confidence)

    return {
        "context_role": explicit_role,
        "freshness": explicit_freshness,
        "source_quality": explicit_source_quality,
        "inferred_context_role": explicit_role or inferred_role,
        "freshness_guess": explicit_freshness or freshness_guess,
        "source_quality_guess": source_quality_guess,
        "when_to_use": when_to_use,
        "when_not_to_use": sorted(set(when_not_to_use)),
        "read_cost": "summary_only" if row.get("summary") else "headings_only",
        "recommended_action": "describe",
        "confidence": round(confidence, 2),
    }


def _extract_note(path: Path, notes_root: Path, vault_root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = _parse_frontmatter(text)
    rel_notes = path.relative_to(notes_root).as_posix()
    rel_vault = path.relative_to(vault_root).as_posix()
    title = str(frontmatter.get("title") or path.stem).strip()
    tags = _normalize_list(frontmatter.get("tags"))
    aliases = _normalize_list(frontmatter.get("aliases"))
    links = []
    embedded_links = []
    seen_links: set[str] = set()
    for match in WIKILINK_RE.finditer(text):
        link = match.group(2).strip()
        if not link or link in seen_links:
            continue
        seen_links.add(link)
        links.append(link)
        if match.group(1) == "!":
            embedded_links.append(link)
    headings = [m.group(2).strip() for m in HEADING_RE.finditer(body)][:30]
    category = path.relative_to(notes_root).parts[0] if len(path.relative_to(notes_root).parts) > 1 else ""
    return {
        "title": title,
        "path": str(path),
        "rel_path": rel_vault,
        "rel_notes_path": rel_notes,
        "category": category,
        "stem": path.stem,
        "tags": tags,
        "aliases": aliases,
        "links": links,
        "embedded_links": embedded_links,
        "headings": headings,
        "first_heading": headings[0] if headings else None,
        "summary": _plain_summary(body),
        "frontmatter": frontmatter,
        "frontmatter_updated": frontmatter.get("updated"),
        "frontmatter_created": frontmatter.get("created"),
        "catalog": _catalog_card({
            "title": title,
            "path": str(path),
            "rel_path": rel_vault,
            "rel_notes_path": rel_notes,
            "category": category,
            "tags": tags,
            "aliases": aliases,
            "links": links,
            "headings": headings,
            "summary": _plain_summary(body),
            "frontmatter": frontmatter,
            "is_index": path.name == "INDEX.md",
            "is_moc": path.name == "MOC.md",
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
        }),
        "is_index": path.name == "INDEX.md",
        "is_moc": path.name == "MOC.md",
        "outbound_count": len(links),
        "inbound_count": 0,
        "backlinks": [],
        "mtime": path.stat().st_mtime,
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
        "size": path.stat().st_size,
    }


def _target_key(value: str) -> str:
    return str(value or "").strip().removesuffix(".md").lower()


def _add_candidate_paths(base: Path, raw: str, out: list[Path]) -> None:
    raw_path = Path(raw)
    candidates = [base / raw_path]
    if raw_path.suffix == "":
        candidates.append(base / (raw + ".md"))
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in out:
            out.append(resolved)


def _link_candidates(source_path: Path, raw_target: str, vault_root: Path, notes_root: Path) -> list[Path]:
    raw = str(raw_target or "").strip().removesuffix(".md")
    out: list[Path] = []
    source_dir = source_path.parent
    is_path_like = raw.startswith("../") or raw.startswith("./") or raw.startswith("/") or "/" in raw or "\\" in raw
    raw = raw.replace("\\", "/")
    if raw.startswith("/"):
        _add_candidate_paths(vault_root, raw.lstrip("/"), out)
        _add_candidate_paths(notes_root, raw.lstrip("/"), out)
    elif is_path_like:
        _add_candidate_paths(source_dir, raw, out)
        _add_candidate_paths(notes_root, raw, out)
        _add_candidate_paths(vault_root, raw, out)
    else:
        _add_candidate_paths(source_dir, raw, out)
        _add_candidate_paths(notes_root, raw, out)
        for base in notes_root.rglob(raw + ".md"):
            if base.is_file():
                resolved = base.resolve()
                if resolved not in out:
                    out.append(resolved)
    return out


def _target_maps(records: list[dict[str, Any]]) -> tuple[set[str], dict[str, str], dict[str, dict[str, Any]]]:
    names: set[str] = set()
    key_to_rel: dict[str, str] = {}
    rel_to_record: dict[str, dict[str, Any]] = {}
    for row in records:
        rel = str(row.get("rel_path") or "")
        rel_notes = str(row.get("rel_notes_path") or "")
        rel_to_record[rel] = row
        values = [row.get("stem"), row.get("title"), rel_notes[:-3] if rel_notes.lower().endswith(".md") else rel_notes, rel[:-3] if rel.lower().endswith(".md") else rel]
        values.extend(row.get("aliases") or [])
        for value in values:
            key = _target_key(str(value or ""))
            if key:
                names.add(key)
                key_to_rel.setdefault(key, rel)
    return names, key_to_rel, rel_to_record


def _resolve_wikilink(source_path: Path, raw_target: str, records: list[dict[str, Any]], vault_root: Path, notes_root: Path) -> dict[str, Any]:
    target_names, key_to_rel, _ = _target_maps(records)
    normalized = _target_key(raw_target)
    if normalized in target_names:
        return {"ok": True, "kind": "note", "rel_path": key_to_rel.get(normalized), "method": "name"}
    for candidate in _link_candidates(source_path, raw_target, vault_root, notes_root):
        if candidate.exists() and candidate.is_file():
            try:
                candidate.relative_to(vault_root)
            except ValueError:
                continue
            if _should_skip_target(candidate):
                continue
            rel = candidate.relative_to(vault_root).as_posix()
            return {"ok": True, "kind": "file", "rel_path": rel, "path": str(candidate), "method": "path"}
    return {"ok": False, "kind": "missing", "target": raw_target}


def _annotate_graph(records: list[dict[str, Any]], vault_root: Path, notes_root: Path) -> None:
    _, _, rel_to_record = _target_maps(records)
    inbound: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in records:
        source_path = Path(str(row.get("path"))).resolve()
        for link in row.get("links") or []:
            resolved = _resolve_wikilink(source_path, str(link), records, vault_root, notes_root)
            target_rel = resolved.get("rel_path")
            if target_rel in rel_to_record:
                inbound[str(target_rel)].append({"source": str(row.get("rel_path")), "link": str(link)})
    for row in records:
        backlinks = inbound.get(str(row.get("rel_path")), [])
        row["inbound_count"] = len(backlinks)
        row["backlinks"] = backlinks[:50]


def _broken_links(records: list[dict[str, Any]], vault_root: Path, notes_root: Path) -> list[dict[str, Any]]:
    broken: list[dict[str, Any]] = []
    for row in records:
        source_path = Path(str(row.get("path"))).resolve()
        for link in row.get("links") or []:
            resolved = _resolve_wikilink(source_path, str(link), records, vault_root, notes_root)
            if not resolved.get("ok"):
                broken.append({"source": row.get("rel_path"), "link": link})
    return broken


def _orphan_notes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in records:
        rel = str(row.get("rel_path"))
        if rel.endswith("INDEX.md") or rel.endswith("MOC.md"):
            continue
        if int(row.get("inbound_count") or 0) == 0 and not row.get("links"):
            out.append({"title": row.get("title"), "rel_path": rel, "path": row.get("path")})
    return out


def _build_index(root: str | None = None, notes_root: str | None = None, *, include_archives: bool = False, max_notes: int | None = None) -> dict[str, Any]:
    vault = _resolve_vault_root(root)
    notes = _resolve_notes_root(vault, notes_root)
    md_files = sorted(p for p in notes.rglob("*.md") if p.is_file() and not _should_skip(p, include_archives=include_archives))
    if max_notes is not None and len(md_files) > max_notes:
        md_files = md_files[:max_notes]
    records = [_extract_note(path, notes, vault) for path in md_files]
    _annotate_graph(records, vault, notes)
    broken = _broken_links(records, vault, notes)
    payload = {
        "schema_version": INDEX_VERSION,
        "kind": "brainlace.index",
        "generated_at": _now_iso(),
        "vault_root": str(vault),
        "notes_root": str(notes),
        "include_archives": include_archives,
        "note_count": len(records),
        "records": records,
        "summary": {
            "tag_counts": Counter(tag for row in records for tag in row.get("tags", [])).most_common(50),
            "category_counts": Counter(row.get("category") or "root" for row in records).most_common(50),
            "broken_link_count": len(broken),
            "orphan_note_count": len(_orphan_notes(records)),
            "index_count": sum(1 for row in records if row.get("is_index")),
            "moc_count": sum(1 for row in records if row.get("is_moc")),
            "index_path": str(_index_path()),
        },
        "policy": {
            "editor_agnostic": True,
            "obsidian_is_current_editor_not_core_dependency": True,
            "filesystem_first": True,
        },
    }
    _index_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _load_index(root: str | None = None, notes_root: str | None = None, *, refresh: bool = False) -> dict[str, Any]:
    if refresh or not _index_path().exists():
        return _build_index(root, notes_root)
    payload = json.loads(_index_path().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Brainlace index must be a JSON object: {_index_path()}")
    if payload.get("schema_version") != INDEX_VERSION:
        return _build_index(root, notes_root)
    if root or notes_root:
        vault = str(_resolve_vault_root(root)) if root else payload.get("vault_root")
        notes = str(_resolve_notes_root(Path(vault), notes_root)) if notes_root and vault else payload.get("notes_root")
        if vault and payload.get("vault_root") != vault:
            return _build_index(root, notes_root)
        if notes and payload.get("notes_root") != notes:
            return _build_index(root, notes_root)
    return payload


def _tokens(text: str) -> set[str]:
    return {tok.lower() for tok in TOKEN_RE.findall(str(text or "")) if len(tok.strip()) >= 2}


def _record_haystack(row: dict[str, Any]) -> str:
    values: list[str] = [
        str(row.get("title") or ""),
        str(row.get("rel_path") or ""),
        str(row.get("rel_notes_path") or ""),
        str(row.get("category") or ""),
        str(row.get("summary") or ""),
    ]
    for key in ("tags", "aliases", "headings", "links"):
        values.extend(str(v) for v in row.get(key) or [])
    return "\n".join(values)


def _score_query(row: dict[str, Any], query: str) -> tuple[float, list[str]]:
    q = query.strip().lower()
    if not q:
        return 0.0, []
    haystack = _record_haystack(row).lower()
    q_tokens = _tokens(query)
    score = 0.0
    reasons: list[str] = []
    title = str(row.get("title") or "").lower()
    aliases = [str(v).lower() for v in row.get("aliases") or []]
    tags = [str(v).lower() for v in row.get("tags") or []]
    category = str(row.get("category") or "").lower()
    if q == title:
        score += 18.0
        reasons.append("exact-title")
    elif q in title:
        score += 10.0
        reasons.append("title")
    if any(q == alias for alias in aliases):
        score += 14.0
        reasons.append("exact-alias")
    elif any(q in alias for alias in aliases):
        score += 8.0
        reasons.append("alias")
    if any(q == tag for tag in tags):
        score += 7.0
        reasons.append("tag")
    if q and q in category:
        score += 3.0
        reasons.append("category")
    if q in haystack:
        score += 4.0
        reasons.append("phrase")
    h_tokens = _tokens(haystack)
    if q_tokens:
        overlap = q_tokens & h_tokens
        if overlap:
            score += len(overlap) / max(1, len(q_tokens)) * 5.0
            reasons.extend(sorted(overlap)[:8])
    inbound = min(int(row.get("inbound_count") or 0), 10)
    score += inbound * 0.05
    return score, reasons


def _result_row(row: dict[str, Any], score: float, reasons: list[str] | None = None) -> dict[str, Any]:
    return {
        "score": round(score, 3),
        "title": row.get("title"),
        "rel_path": row.get("rel_path"),
        "rel_notes_path": row.get("rel_notes_path"),
        "category": row.get("category"),
        "path": row.get("path"),
        "tags": row.get("tags") or [],
        "aliases": row.get("aliases") or [],
        "headings": (row.get("headings") or [])[:8],
        "summary": row.get("summary"),
        "inbound_count": row.get("inbound_count") or 0,
        "outbound_count": row.get("outbound_count") or 0,
        "updated_at": row.get("updated_at"),
        "match_reasons": reasons or [],
    }


def _catalog_search_row(row: dict[str, Any], score: float, reasons: list[str] | None = None) -> dict[str, Any]:
    card = dict(row.get("catalog") or _catalog_card(row))
    item = _result_row(row, score, reasons)
    item["catalog"] = card
    item["read_cost"] = card.get("read_cost") or "summary_only"
    item["recommended_action"] = card.get("recommended_action") or "describe"
    item["confidence"] = card.get("confidence") or 0
    return item


def _find_index_record_for_path(payload: dict[str, Any], note_path: Path, vault: Path) -> dict[str, Any] | None:
    rel = note_path.relative_to(vault).as_posix()
    for row in payload.get("records") or []:
        if isinstance(row, dict) and row.get("rel_path") == rel:
            return row
    return None


def _tool_describe_note(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    vault = _resolve_vault_root(params.get("root"))
    notes = _resolve_notes_root(vault, params.get("notes_root"))
    note_path = _resolve_note_path(vault, notes, str(params.get("path") or params.get("note") or ""))
    payload = _load_index(str(vault), str(notes), refresh=bool(params.get("refresh", False)))
    row = _find_index_record_for_path(payload, note_path, vault)
    if row is None:
        payload = _build_index(str(vault), str(notes))
        row = _find_index_record_for_path(payload, note_path, vault)
    if row is None:
        raise RuntimeError(f"note is inside vault but missing from Brainlace index: {note_path}")
    catalog = dict(row.get("catalog") or _catalog_card(row))
    raw_frontmatter = row.get("frontmatter")
    frontmatter: dict[str, Any] = raw_frontmatter if isinstance(raw_frontmatter, dict) else {}
    return _json({
        "ok": True,
        "index_generated_at": payload.get("generated_at"),
        "note": {
            "title": row.get("title"),
            "rel_path": row.get("rel_path"),
            "rel_notes_path": row.get("rel_notes_path"),
            "category": row.get("category"),
            "path": row.get("path"),
            "summary": row.get("summary"),
            "tags": row.get("tags") or [],
            "aliases": row.get("aliases") or [],
            "headings": row.get("headings") or [],
            "frontmatter": {
                "context_role": frontmatter.get("context_role"),
                "freshness": frontmatter.get("freshness"),
                "source_quality": frontmatter.get("source_quality"),
            },
            "inbound_count": row.get("inbound_count") or 0,
            "outbound_count": row.get("outbound_count") or 0,
            "updated_at": row.get("updated_at"),
        },
        "catalog": catalog,
        "related": {
            "links": (row.get("links") or [])[:20],
            "backlinks": (row.get("backlinks") or [])[:20],
        },
    })


def _tool_catalog_search(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    query = str(params.get("query") or params.get("text") or "").strip()
    if not query:
        raise RuntimeError("query or text is required")
    task_type = str(params.get("task_type") or "").strip().lower()
    limit = max(1, int(params.get("limit") or 8))
    payload = _load_index(params.get("root"), params.get("notes_root"), refresh=bool(params.get("refresh", False)))
    scored = []
    for row in payload.get("records") or []:
        if not isinstance(row, dict):
            continue
        score, reasons = _score_query(row, query)
        card = row.get("catalog") or _catalog_card(row)
        role = str(card.get("inferred_context_role") or "")
        uses = {str(item).lower() for item in card.get("when_to_use") or []}
        if task_type:
            if task_type in uses or (task_type in {"planning", "implementation", "design"} and role == "design"):
                score += 2.5
                reasons.append(f"task:{task_type}")
            if task_type in {"current", "operations"} and card.get("freshness_guess") in {"stale", "archived"}:
                score -= 3.0
                reasons.append("freshness-penalty")
        if score > 0:
            item = _catalog_search_row(row, score, sorted(set(reasons))[:16])
            scored.append(item)
    scored.sort(key=lambda item: (item["score"], item.get("confidence") or 0, item.get("inbound_count") or 0, item.get("updated_at") or ""), reverse=True)
    return _json({"ok": True, "query": query, "task_type": task_type or None, "index_generated_at": payload.get("generated_at"), "results": scored[:limit], "total_matches": len(scored)})



def _tool_status(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    vault = _resolve_vault_root(params.get("root"))
    notes = _resolve_notes_root(vault, params.get("notes_root"))
    index_exists = _index_path().exists()
    index_payload: dict[str, Any] = {}
    if index_exists:
        try:
            index_payload = json.loads(_index_path().read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - status should report corruption, not crash
            index_payload = {"error": str(exc)}
    md_count = sum(1 for p in notes.rglob("*.md") if p.is_file() and not _should_skip(p, include_archives=False))
    return _json({
        "ok": True,
        "plugin": PLUGIN_NAME,
        "vault_root": str(vault),
        "notes_root": str(notes),
        "index_path": str(_index_path()),
        "index_exists": index_exists,
        "indexed_note_count": index_payload.get("note_count"),
        "index_generated_at": index_payload.get("generated_at"),
        "index_schema_version": index_payload.get("schema_version"),
        "markdown_note_count": md_count,
        "policy": {
            "human_editor": "Obsidian or any filesystem editor",
            "lin_surface": "Hermes plugin tools",
            "gui_required": False,
            "obsidian_dependency": False,
        },
    })


def _tool_index(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    payload = _build_index(
        params.get("root"),
        params.get("notes_root"),
        include_archives=bool(params.get("include_archives", False)),
        max_notes=int(params["max_notes"]) if params.get("max_notes") else None,
    )
    return _json({"ok": True, "index_path": str(_index_path()), "note_count": payload.get("note_count"), "summary": payload.get("summary"), "generated_at": payload.get("generated_at")})


def _tool_search(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    query = str(params.get("query") or "").strip()
    if not query:
        raise RuntimeError("query is required")
    limit = max(1, int(params.get("limit") or 10))
    payload = _load_index(params.get("root"), params.get("notes_root"), refresh=bool(params.get("refresh", False)))
    scored = []
    for row in payload.get("records") or []:
        if not isinstance(row, dict):
            continue
        score, reasons = _score_query(row, query)
        if score > 0:
            scored.append(_result_row(row, score, reasons))
    scored.sort(key=lambda item: (item["score"], item.get("inbound_count") or 0, item.get("updated_at") or ""), reverse=True)
    return _json({"ok": True, "query": query, "index_generated_at": payload.get("generated_at"), "results": scored[:limit], "total_matches": len(scored)})


def _tool_related(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    text = str(params.get("text") or "").strip()
    if not text:
        raise RuntimeError("text is required")
    limit = max(1, int(params.get("limit") or 8))
    needle = _tokens(text)
    payload = _load_index(params.get("root"), params.get("notes_root"), refresh=bool(params.get("refresh", False)))
    results = []
    for row in payload.get("records") or []:
        if not isinstance(row, dict):
            continue
        score, reasons = _score_query(row, text)
        hay = _tokens(_record_haystack(row))
        overlap = needle & hay
        if overlap:
            score += len(overlap) / max(1, len(needle)) * 8
            reasons.extend(sorted(overlap)[:12])
        if score <= 0:
            continue
        item = _result_row(row, score, sorted(set(reasons))[:20])
        item["matched_terms"] = sorted(overlap)[:20]
        results.append(item)
    results.sort(key=lambda item: (item["score"], item.get("inbound_count") or 0, item.get("updated_at") or ""), reverse=True)
    return _json({"ok": True, "index_generated_at": payload.get("generated_at"), "results": results[:limit], "total_matches": len(results)})


def _short_note_summary(body: str) -> str:
    return _plain_summary(body, 120)


def _category_index_link_line(note_path: Path, category_dir: Path, title: str, body: str = "") -> str:
    rel = note_path.relative_to(category_dir).with_suffix("").as_posix()
    summary = _short_note_summary(body)
    suffix = f" — {summary}" if summary else ""
    return f"- [[{rel}|{title}]]{suffix}"


def _wire_category_index(category_dir: Path, category_name: str, note_path: Path, title: str, body: str) -> Path:
    index_path = category_dir / "INDEX.md"
    line = _category_index_link_line(note_path, category_dir, title, body)
    if not index_path.exists():
        content = f"# {category_name}\n\nこの階層の入口。Brainlace が作成・更新したノートへの導線を置く。\n\n## この階層のノート\n\n{line}\n"
        index_path.write_text(content, encoding="utf-8")
        return index_path
    current = index_path.read_text(encoding="utf-8", errors="replace")
    target = f"[[{note_path.relative_to(category_dir).with_suffix('').as_posix()}"
    if target in current or f"[[{note_path.stem}]]" in current or f"[[{note_path.stem}|" in current:
        return index_path
    if "## この階層のノート" not in current:
        sep = "" if current.endswith("\n") else "\n"
        current = current + sep + "\n## この階層のノート\n\n"
    if not current.endswith("\n"):
        current += "\n"
    index_path.write_text(current + line + "\n", encoding="utf-8")
    return index_path


def _tool_create_note(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    vault = _resolve_vault_root(params.get("root"))
    notes = _resolve_notes_root(vault, params.get("notes_root"))
    category = str(params.get("category") or "").strip().strip("/")
    title = str(params.get("title") or "").strip()
    body = str(params.get("body") or "").strip()
    if not category or not title or not body:
        raise RuntimeError("category, title, and body are required")
    category_dir = (notes / category).resolve()
    _assert_under(category_dir, vault, label="category")
    category_dir.mkdir(parents=True, exist_ok=True)
    path = (category_dir / _safe_filename(title)).resolve()
    _assert_under(path, vault, label="note path")
    if path.exists() and not bool(params.get("overwrite", False)):
        raise RuntimeError(f"note already exists: {path}")
    tags = _normalize_list(params.get("tags"))
    aliases = _normalize_list(params.get("aliases"))
    content = _frontmatter(title, tags, aliases) + "\n" + body.rstrip() + "\n"
    path.write_text(content, encoding="utf-8")
    index_path = None
    if bool(params.get("wire_index", True)):
        index_path = _wire_category_index(category_dir, category, path, title, body)
    _build_index(str(vault), str(notes))
    return _json({"ok": True, "path": str(path), "rel_path": path.relative_to(vault).as_posix(), "index_path": str(index_path) if index_path else None})


def _resolve_note_path(vault: Path, notes: Path, raw_path: str) -> Path:
    raw = str(raw_path or "").strip()
    if not raw:
        raise RuntimeError("path is required")
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        direct = (vault / candidate).resolve()
        under_notes = (notes / candidate).resolve()
        if direct.exists():
            candidate = direct
        elif under_notes.exists():
            candidate = under_notes
        else:
            candidate = direct if str(raw).startswith("notes/") else under_notes
    candidate = candidate.resolve()
    _assert_under(candidate, vault, label="note path")
    if not candidate.exists() or not candidate.is_file():
        raise RuntimeError(f"note not found: {candidate}")
    if candidate.suffix.lower() != ".md":
        raise RuntimeError(f"Brainlace only edits Markdown notes: {candidate}")
    return candidate


def _tool_append_note(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    vault = _resolve_vault_root(params.get("root"))
    notes = _resolve_notes_root(vault, params.get("notes_root"))
    path = _resolve_note_path(vault, notes, str(params.get("path") or ""))
    body = str(params.get("body") or "").strip()
    if not body:
        raise RuntimeError("body is required")
    heading = str(params.get("heading") or "").strip()
    current = path.read_text(encoding="utf-8", errors="replace")
    block_parts = [""]
    if heading:
        block_parts.append(f"## {heading}")
        block_parts.append("")
    block_parts.append(body.rstrip())
    block = "\n".join(block_parts).rstrip() + "\n"
    sep = "" if current.endswith("\n") else "\n"
    path.write_text(current + sep + block, encoding="utf-8")
    _build_index(str(vault), str(notes))
    return _json({"ok": True, "path": str(path), "rel_path": path.relative_to(vault).as_posix(), "appended_chars": len(block)})


def _unified_diff(path: Path, before: str, after: str) -> str:
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=str(path), tofile=str(path)))


def _tool_patch_note(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    vault = _resolve_vault_root(params.get("root"))
    notes = _resolve_notes_root(vault, params.get("notes_root"))
    path = _resolve_note_path(vault, notes, str(params.get("path") or ""))
    old = str(params.get("old_string") if params.get("old_string") is not None else "")
    new = str(params.get("new_string") if params.get("new_string") is not None else "")
    if old == "":
        raise RuntimeError("old_string is required")
    replace_all = bool(params.get("replace_all", False))
    dry_run = bool(params.get("dry_run", False))
    current = path.read_text(encoding="utf-8", errors="replace")
    count = current.count(old)
    if count == 0:
        raise RuntimeError("old_string not found in note")
    if count > 1 and not replace_all:
        raise RuntimeError(f"old_string matched {count} times; pass replace_all=true or provide more context")
    updated = current.replace(old, new) if replace_all else current.replace(old, new, 1)
    diff = _unified_diff(path, current, updated)
    if not dry_run:
        path.write_text(updated, encoding="utf-8")
        _build_index(str(vault), str(notes))
    return _json({"ok": True, "dry_run": dry_run, "path": str(path), "rel_path": path.relative_to(vault).as_posix(), "replacements": count if replace_all else 1, "diff": diff})


def _relative_link_target(source_path: Path, target_path: Path, notes_root: Path) -> str:
    if source_path.parent == target_path.parent:
        return target_path.stem
    rel = os.path.relpath(target_path.with_suffix(""), source_path.parent)
    return Path(rel).as_posix()


def _replace_wikilinks_to_path(text: str, source_path: Path, old_path: Path, new_path: Path, records: list[dict[str, Any]], vault: Path, notes: Path) -> tuple[str, int]:
    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        embed, raw, heading, alias = match.group(1), match.group(2), match.group(3) or "", match.group(4)
        resolved = _resolve_wikilink(source_path, raw, records, vault, notes)
        target_rel = resolved.get("rel_path")
        old_rel = old_path.relative_to(vault).as_posix()
        if target_rel != old_rel:
            return match.group(0)
        changed += 1
        new_raw = _relative_link_target(source_path, new_path, notes)
        alias_part = f"|{alias}" if alias else ""
        return f"{embed}[[{new_raw}{heading}{alias_part}]]"

    return WIKILINK_RE.sub(repl, text), changed


def _destination_note_path(vault: Path, notes: Path, params: dict[str, Any]) -> Path:
    dest_path = str(params.get("dest_path") or "").strip()
    if dest_path:
        candidate = Path(dest_path).expanduser()
        if not candidate.is_absolute():
            candidate = (vault / candidate if dest_path.startswith("notes/") else notes / candidate).resolve()
        if candidate.suffix.lower() != ".md":
            candidate = candidate.with_suffix(".md")
        return candidate.resolve()
    category = str(params.get("category") or "").strip().strip("/")
    title = str(params.get("title") or "").strip()
    if not category or not title:
        raise RuntimeError("dest_path or both category and title are required")
    return (notes / category / _safe_filename(title)).resolve()


def _tool_move_note(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    vault = _resolve_vault_root(params.get("root"))
    notes = _resolve_notes_root(vault, params.get("notes_root"))
    source = _resolve_note_path(vault, notes, str(params.get("source_path") or params.get("path") or ""))
    dest = _destination_note_path(vault, notes, params)
    _assert_under(dest, vault, label="destination")
    if dest.exists() and not bool(params.get("overwrite", False)):
        raise RuntimeError(f"destination already exists: {dest}")
    dry_run = bool(params.get("dry_run", False))
    update_links = bool(params.get("update_links", True))
    wire_index = bool(params.get("wire_index", True))
    payload = _build_index(str(vault), str(notes))
    records = [row for row in payload.get("records") or [] if isinstance(row, dict)]
    planned: list[dict[str, Any]] = []
    if update_links:
        for md in sorted(p for p in notes.rglob("*.md") if p.is_file() and not _should_skip(p, include_archives=False)):
            before = md.read_text(encoding="utf-8", errors="replace")
            after, count = _replace_wikilinks_to_path(before, md, source, dest, records, vault, notes)
            if count:
                planned.append({"path": str(md), "rel_path": md.relative_to(vault).as_posix(), "replacements": count, "diff": _unified_diff(md, before, after)})
                if not dry_run:
                    md.write_text(after, encoding="utf-8")
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        if wire_index:
            text = dest.read_text(encoding="utf-8", errors="replace")
            fm, body = _parse_frontmatter(text)
            title = str(fm.get("title") or dest.stem)
            _wire_category_index(dest.parent, dest.parent.relative_to(notes).as_posix(), dest, title, body)
        _build_index(str(vault), str(notes))
    return _json({"ok": True, "dry_run": dry_run, "source": source.relative_to(vault).as_posix(), "destination": dest.relative_to(vault).as_posix(), "updated_link_files": planned})


def _tool_plan_note_update(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    text = str(params.get("text") or params.get("query") or "").strip()
    if not text:
        raise RuntimeError("text or query is required")
    limit = max(1, int(params.get("limit") or 5))
    action_hint = str(params.get("action_hint") or "append").strip() or "append"
    payload = _load_index(params.get("root"), params.get("notes_root"), refresh=bool(params.get("refresh", False)))
    candidates = []
    for row in payload.get("records") or []:
        if not isinstance(row, dict) or row.get("is_index"):
            continue
        score, reasons = _score_query(row, text)
        hay = _tokens(_record_haystack(row))
        overlap = _tokens(text) & hay
        if overlap:
            score += len(overlap) * 1.5
            reasons.extend(sorted(overlap))
        if score > 0:
            candidates.append(_result_row(row, score, sorted(set(reasons))[:12]))
    candidates.sort(key=lambda item: item["score"], reverse=True)
    top = candidates[:limit]
    suggested_category = top[0].get("category") if top else "Inbox"
    recommendation = {
        "action": "append" if top and action_hint != "create" else "create",
        "target": top[0].get("rel_path") if top and action_hint != "create" else None,
        "category": suggested_category,
        "reason": "既存ノートの語彙・タイトル・リンクと近い" if top else "近い既存ノートが弱いので新規作成候補",
    }
    return _json({"ok": True, "query": text, "recommendation": recommendation, "candidates": top})


def _tool_check_links(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    limit = max(1, int(params.get("limit") or 50))
    payload = _load_index(params.get("root"), params.get("notes_root"), refresh=bool(params.get("refresh", False)))
    records = [row for row in payload.get("records") or [] if isinstance(row, dict)]
    vault = Path(str(payload.get("vault_root"))).resolve()
    notes = Path(str(payload.get("notes_root"))).resolve()
    broken = _broken_links(records, vault, notes)
    orphans = _orphan_notes(records)
    return _json({
        "ok": True,
        "index_generated_at": payload.get("generated_at"),
        "note_count": len(records),
        "broken_link_count": len(broken),
        "orphan_note_count": len(orphans),
        "broken_links": broken[:limit],
        "orphan_notes": orphans[:limit],
    })


def _tool_read(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    params = params or {}
    view = str(params.get("view") or "status").strip().lower()
    if view == "status":
        return _tool_status(params, **kwargs)
    if view == "search":
        return _tool_search(params, **kwargs)
    if view == "related":
        if not params.get("text") and params.get("query"):
            params = {**params, "text": params.get("query")}
        return _tool_related(params, **kwargs)
    if view == "catalog_search":
        return _tool_catalog_search(params, **kwargs)
    if view == "describe_note":
        return _tool_describe_note(params, **kwargs)
    if view == "plan_note_update":
        return _tool_plan_note_update(params, **kwargs)
    if view == "check_links":
        return _tool_check_links(params, **kwargs)

    raise RuntimeError(f"unknown Brainlace read view: {view}")


def _tool_control(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    params = params or {}
    action = str(params.get("action") or "index").strip().lower()
    if action == "index":
        return _tool_index(params, **kwargs)
    raise RuntimeError(f"unknown Brainlace control action: {action}")


def _tool_write(params: dict[str, Any] | None = None, **kwargs: Any) -> str:
    params = params or {}
    action = str(params.get("action") or "").strip().lower()
    if action == "create_note":
        return _tool_create_note(params, **kwargs)
    if action == "append_note":
        return _tool_append_note(params, **kwargs)
    if action == "patch_note":
        return _tool_patch_note(params, **kwargs)
    if action == "move_note":
        return _tool_move_note(params, **kwargs)
    raise RuntimeError(f"unknown Brainlace write action: {action}")


def _register_tool(ctx, *, name: str, schema: dict[str, Any], handler: Any, description: str) -> None:
    ctx.register_tool(name=name, toolset="brainlace", schema=schema, handler=handler, description=description, emoji="🪢")


def register(ctx) -> None:
    skill_path = PLUGIN_DIR / "skills" / "brainlace" / "SKILL.md"
    if skill_path.exists():
        ctx.register_skill("brainlace", skill_path, "Operate Brainlace, LIN's filesystem-first second-brain framework.")
    tools = [
        ("brainlace_read", schemas.BRAINLACE_READ, _tool_read, "Read notes and catalog data."),
        ("brainlace_control", schemas.BRAINLACE_CONTROL, _tool_control, "Run maintenance actions such as indexing."),
        ("brainlace_write", schemas.BRAINLACE_WRITE, _tool_write, "Create, append, patch, or move notes."),
    ]
    for name, schema, handler, description in tools:
        _register_tool(ctx, name=name, schema=schema, handler=handler, description=description)


if __name__ == "__main__":
    print(_tool_status({}))
