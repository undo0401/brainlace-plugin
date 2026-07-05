"""Brainlace Hermes plugin.

Brainlace is a filesystem-first second-brain bridge: humans can keep editing
Markdown notes in Obsidian or any future editor, while LIN/Hermes gets stable
agent-readable tools for indexing, searching, linking, and writing notes.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from collections import Counter
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
INDEX_VERSION = 1
WIKILINK_RE = re.compile(r"!??\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]{2,}|[\u3040-\u30ff\u3400-\u9fff]{2,}")


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


def _extract_note(path: Path, notes_root: Path, vault_root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = _parse_frontmatter(text)
    rel_notes = path.relative_to(notes_root).as_posix()
    rel_vault = path.relative_to(vault_root).as_posix()
    title = str(frontmatter.get("title") or path.stem).strip()
    tags = _normalize_list(frontmatter.get("tags"))
    aliases = _normalize_list(frontmatter.get("aliases"))
    links = []
    seen_links: set[str] = set()
    for match in WIKILINK_RE.finditer(text):
        link = match.group(1).strip()
        if link and link not in seen_links:
            seen_links.add(link)
            links.append(link)
    headings = [m.group(2).strip() for m in HEADING_RE.finditer(body)][:30]
    plain = re.sub(r"```.*?```", " ", body, flags=re.S)
    plain = re.sub(r"[#>*_`\[\](){}]", " ", plain)
    plain = re.sub(r"\s+", " ", plain).strip()
    summary = plain[:420]
    return {
        "title": title,
        "path": str(path),
        "rel_path": rel_vault,
        "rel_notes_path": rel_notes,
        "stem": path.stem,
        "tags": tags,
        "aliases": aliases,
        "links": links,
        "headings": headings,
        "summary": summary,
        "mtime": path.stat().st_mtime,
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).astimezone().isoformat(timespec="seconds"),
        "size": path.stat().st_size,
    }


def _should_skip(path: Path, *, include_archives: bool) -> bool:
    parts = {part.lower() for part in path.parts}
    if ".obsidian" in parts or ".git" in parts:
        return True
    if include_archives:
        return False
    return any(part in {"archive", "archives", ".archive", "legacy"} for part in parts)


def _build_index(root: str | None = None, notes_root: str | None = None, *, include_archives: bool = False, max_notes: int | None = None) -> dict[str, Any]:
    vault = _resolve_vault_root(root)
    notes = _resolve_notes_root(vault, notes_root)
    md_files = sorted(p for p in notes.rglob("*.md") if p.is_file() and not _should_skip(p, include_archives=include_archives))
    if max_notes is not None and len(md_files) > max_notes:
        md_files = md_files[:max_notes]
    records = [_extract_note(path, notes, vault) for path in md_files]
    link_targets = _target_names(records)
    broken = _broken_links(records, link_targets)
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
            "broken_link_count": len(broken),
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
        str(row.get("summary") or ""),
    ]
    for key in ("tags", "aliases", "headings", "links"):
        values.extend(str(v) for v in row.get(key) or [])
    return "\n".join(values)


def _score_query(row: dict[str, Any], query: str) -> float:
    q = query.strip().lower()
    if not q:
        return 0.0
    haystack = _record_haystack(row).lower()
    score = 0.0
    if q in haystack:
        score += 5.0
    q_tokens = _tokens(query)
    h_tokens = _tokens(haystack)
    if q_tokens:
        overlap = q_tokens & h_tokens
        score += len(overlap) / max(1, len(q_tokens)) * 4.0
    title = str(row.get("title") or "").lower()
    if q in title:
        score += 3.0
    return score


def _result_row(row: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "score": round(score, 3),
        "title": row.get("title"),
        "rel_path": row.get("rel_path"),
        "rel_notes_path": row.get("rel_notes_path"),
        "path": row.get("path"),
        "tags": row.get("tags") or [],
        "aliases": row.get("aliases") or [],
        "headings": (row.get("headings") or [])[:8],
        "summary": row.get("summary"),
        "updated_at": row.get("updated_at"),
    }


def _target_names(records: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for row in records:
        names.add(str(row.get("stem") or "").lower())
        names.add(str(row.get("title") or "").lower())
        for alias in row.get("aliases") or []:
            names.add(str(alias).lower())
        rel = str(row.get("rel_notes_path") or "")
        if rel.lower().endswith(".md"):
            names.add(rel[:-3].lower())
    return {name for name in names if name}


def _broken_links(records: list[dict[str, Any]], targets: set[str]) -> list[dict[str, Any]]:
    broken: list[dict[str, Any]] = []
    for row in records:
        for link in row.get("links") or []:
            normalized = str(link).strip().removesuffix(".md").lower()
            if normalized not in targets:
                broken.append({"source": row.get("rel_path"), "link": link})
    return broken


def _orphan_notes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inbound: Counter[str] = Counter()
    by_name: dict[str, dict[str, Any]] = {}
    for row in records:
        names = {str(row.get("stem") or "").lower(), str(row.get("title") or "").lower()}
        names.update(str(alias).lower() for alias in row.get("aliases") or [])
        for name in names:
            if name:
                by_name[name] = row
    for row in records:
        for link in row.get("links") or []:
            normalized = str(link).strip().removesuffix(".md").lower()
            if normalized in by_name:
                inbound[str(by_name[normalized].get("rel_path"))] += 1
    out = []
    for row in records:
        rel = str(row.get("rel_path"))
        if rel.endswith("INDEX.md") or rel.endswith("MOC.md"):
            continue
        if inbound[rel] == 0 and not row.get("links"):
            out.append({"title": row.get("title"), "rel_path": rel, "path": row.get("path")})
    return out


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
        score = _score_query(row, query)
        if score > 0:
            scored.append(_result_row(row, score))
    scored.sort(key=lambda item: item["score"], reverse=True)
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
        hay = _tokens(_record_haystack(row))
        overlap = needle & hay
        if not overlap:
            continue
        score = len(overlap) / max(1, len(needle))
        item = _result_row(row, score * 10)
        item["matched_terms"] = sorted(overlap)[:20]
        results.append(item)
    results.sort(key=lambda item: item["score"], reverse=True)
    return _json({"ok": True, "index_generated_at": payload.get("generated_at"), "results": results[:limit], "total_matches": len(results)})


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
        index_path = category_dir / "INDEX.md"
        link = f"- [[{path.stem}]]"
        if index_path.exists():
            current = index_path.read_text(encoding="utf-8", errors="replace")
            if link not in current:
                sep = "" if current.endswith("\n") else "\n"
                index_path.write_text(current + sep + link + "\n", encoding="utf-8")
        else:
            index_path.write_text(f"# {category}\n\n{link}\n", encoding="utf-8")
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
        candidate = direct if direct.exists() else under_notes
    candidate = candidate.resolve()
    _assert_under(candidate, vault, label="note path")
    if not candidate.exists() or not candidate.is_file():
        raise RuntimeError(f"note not found: {candidate}")
    if candidate.suffix.lower() != ".md":
        raise RuntimeError(f"Brainlace only appends to Markdown notes: {candidate}")
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


def _tool_check_links(params: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    params = params or {}
    limit = max(1, int(params.get("limit") or 50))
    payload = _load_index(params.get("root"), params.get("notes_root"), refresh=bool(params.get("refresh", False)))
    records = [row for row in payload.get("records") or [] if isinstance(row, dict)]
    targets = _target_names(records)
    broken = _broken_links(records, targets)
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


def _register_tool(ctx, *, name: str, schema: dict[str, Any], handler: Any, description: str) -> None:
    ctx.register_tool(name=name, toolset="brainlace", schema=schema, handler=handler, description=description)


def register(ctx) -> None:
    skill_path = PLUGIN_DIR / "skills" / "brainlace" / "SKILL.md"
    if skill_path.exists():
        ctx.register_skill("brainlace", skill_path, "Operate Brainlace, LIN's filesystem-first second-brain framework.")
    tools = [
        ("brainlace_status", schemas.BRAINLACE_STATUS, _tool_status, "Inspect Brainlace vault/index status."),
        ("brainlace_index", schemas.BRAINLACE_INDEX, _tool_index, "Build the Brainlace Markdown note index."),
        ("brainlace_search", schemas.BRAINLACE_SEARCH, _tool_search, "Search Brainlace-indexed notes."),
        ("brainlace_related", schemas.BRAINLACE_RELATED, _tool_related, "Find notes related to provided text."),
        ("brainlace_create_note", schemas.BRAINLACE_CREATE_NOTE, _tool_create_note, "Create a Markdown note and wire category index."),
        ("brainlace_append_note", schemas.BRAINLACE_APPEND_NOTE, _tool_append_note, "Append Markdown to an existing Brainlace note."),
        ("brainlace_check_links", schemas.BRAINLACE_CHECK_LINKS, _tool_check_links, "Check broken wikilinks and orphan notes."),
    ]
    for name, schema, handler, description in tools:
        _register_tool(ctx, name=name, schema=schema, handler=handler, description=description)


if __name__ == "__main__":
    print(_tool_status({}))
