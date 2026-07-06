---
name: brainlace
description: Use Brainlace, LIN's filesystem-first second-brain bridge for Markdown notes, when searching, indexing, relating, planning, creating, appending, patching, moving, or checking notes through plugin tools rather than raw file operations.
author: LIN
---

# Brainlace

Use this skill when operating Brainlace, the editor-agnostic second-brain framework for LIN/Hermes.

## Core stance

- Human editing surface: Obsidian now, any Markdown/filesystem editor later.
- LIN surface: Brainlace plugin tools.
- Source of truth: filesystem-first Markdown notes under the configured vault.
- GUI is not required. The point is agent-readable structure, retrieval, safe note operations, and link hygiene.

## Preferred flow

1. Call `brainlace_status` to confirm the vault, notes root, and index freshness.
2. Call `brainlace_index` when the index may be stale or before broad retrieval.
3. Use `brainlace_search` for direct keyword/title/tag/category lookup.
4. Use `brainlace_related` when the user gives a loose idea and LIN needs likely context.
5. Use `brainlace_plan_note_update` when deciding whether a thought belongs in an existing note or a new note.
6. Use `brainlace_create_note` for new durable notes; keep `wire_index=true` unless intentionally creating an unlinked scratch note.
7. Use `brainlace_append_note` for small additions to existing notes.
8. Use `brainlace_patch_note` for targeted replacements and link repairs; inspect the returned diff.
9. Use `brainlace_move_note` for note moves/renames so inbound wikilinks and destination `INDEX.md` wiring can be handled together.
10. Use `brainlace_check_links` after structural changes or when notes feel messy.

## Link / index expectations

- Brainlace resolves wikilinks by note title/stem/alias, source-relative path, notes-root path, and vault-root path.
- Archive/design/workspace files can satisfy links even when Archive is excluded from normal source indexing.
- Index rows carry category, heading, frontmatter, inbound/outbound counts, backlinks, index/MOC flags, summaries, and update timestamps.
- Category `INDEX.md` wiring should remain human-readable, using `## この階層のノート` and short summaries rather than a bare link dump when Brainlace creates the entry.

## Boundaries

- Do not treat Brainlace as an Obsidian GUI plugin.
- Do not bypass Living Roots/other canonical ledgers; Brainlace is for notes and knowledge, not task/calendar truth.
- Prefer Brainlace mutation tools over raw `patch`/`write_file` for ordinary note edits. Raw file tools remain appropriate when repairing Brainlace itself or when a requested edit is outside the tool surface.
- For sensitive or relationship notes, preserve the user's meaning and uncertainty layers according to `lin-obsidian` conventions.
