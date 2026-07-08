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
4. Use `brainlace_catalog_search` when deciding which notes are safe/useful before reading full bodies; it returns role, freshness, source-quality, read-cost, and cautions as Brainlace-owned catalog metadata.
5. Use `brainlace_describe_note` on a candidate before treating it as context, especially when the note may be design/history/lore rather than current source of truth.
6. Use `brainlace_active_memory_preview` to inspect which catalog cards would be safe soft context before any memory/prompt layer injects them. This tool previews only; it does not modify notes, memory, or prompts.
7. Use `brainlace_active_memory_context` when a separate memory/prompt layer needs a compact `inject_text` packet. Brainlace still only retrieves and formats; it never writes to memory or injects prompts by itself.
8. Use `brainlace_related` when the user gives a loose idea and LIN needs likely context.
9. Use `brainlace_plan_note_update` when deciding whether a thought belongs in an existing note or a new note.
10. Use `brainlace_create_note` for new durable notes; keep `wire_index=true` unless intentionally creating an unlinked scratch note.
11. Use `brainlace_append_note` for small additions to existing notes.
12. Use `brainlace_patch_note` for targeted replacements and link repairs; inspect the returned diff.
13. Use `brainlace_move_note` for note moves/renames so inbound wikilinks and destination `INDEX.md` wiring can be handled together.
14. Use `brainlace_check_links` after structural changes or when notes feel messy.

## Link / index expectations

- Brainlace resolves wikilinks by note title/stem/alias, source-relative path, notes-root path, and vault-root path.
- Archive/design/workspace files can satisfy links even when Archive is excluded from normal source indexing.
- Index rows carry category, heading, frontmatter, inbound/outbound counts, backlinks, index/MOC flags, summaries, update timestamps, and Brainlace-owned catalog cards.
- Catalog cards may infer role/freshness/source quality, but those machine hints should not be written back into Markdown unless the user explicitly chooses to promote them to human-readable frontmatter.
- Active-memory preview/context belongs to Brainlace because it is second-brain retrieval and context-packet formatting. Prompt injection belongs to a separate memory/prompt layer that may call the public Brainlace tool, not import Brainlace internals.
- Category `INDEX.md` wiring should remain human-readable, using `## この階層のノート` and short summaries rather than a bare link dump when Brainlace creates the entry.

## Boundaries

- Do not treat Brainlace as an Obsidian GUI plugin.
- Do not bypass Living Roots/other canonical ledgers; Brainlace is for notes and knowledge, not task/calendar truth.
- Prefer Brainlace mutation tools over raw `patch`/`write_file` for ordinary note edits. Raw file tools remain appropriate when repairing Brainlace itself or when a requested edit is outside the tool surface.
- For sensitive or relationship notes, preserve the user's meaning and uncertainty layers according to `lin-obsidian` conventions.
