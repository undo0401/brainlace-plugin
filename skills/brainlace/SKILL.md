---
name: brainlace
description: Use Brainlace, LIN's filesystem-first second-brain bridge for Markdown notes, when searching, indexing, relating, creating, appending, or checking notes through plugin tools rather than raw file operations.
author: LIN
---

# Brainlace

Use this skill when operating Brainlace, the editor-agnostic second-brain framework for LIN/Hermes.

## Core stance

- Human editing surface: Obsidian now, any Markdown/filesystem editor later.
- LIN surface: Brainlace plugin tools.
- Source of truth: filesystem-first Markdown notes under the configured vault.
- GUI is not required. The point is agent-readable structure, retrieval, and safe note operations.

## Preferred flow

1. Call `brainlace_status` to confirm the vault and notes root.
2. Call `brainlace_index` when the index may be stale or before broad retrieval.
3. Use `brainlace_search` for direct keyword/title/tag lookup.
4. Use `brainlace_related` when the user gives a loose idea and LIN needs likely context.
5. Use `brainlace_create_note` for new durable notes; keep `wire_index=true` unless intentionally creating an unlinked scratch note.
6. Use `brainlace_append_note` for small additions to existing notes.
7. Use `brainlace_check_links` after structural changes or when notes feel messy.

## Boundaries

- Do not treat Brainlace as an Obsidian GUI plugin.
- Do not bypass Lifeleaf/other canonical ledgers; Brainlace is for notes and knowledge, not task/calendar truth.
- For sensitive or relationship notes, preserve the user's meaning and uncertainty layers according to `lin-obsidian` conventions.
