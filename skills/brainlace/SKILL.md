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

1. Call `brainlace_read(view="status")` to confirm the vault, notes root, and index freshness.
2. Call `brainlace_control(action="index")` when the index may be stale or before broad retrieval.
3. Use `brainlace_read(view="search")` for direct keyword/title/tag/category lookup.
4. Use `brainlace_read(view="catalog_search")` when deciding which notes are safe/useful before reading full bodies; it returns role, freshness, source-quality, read-cost, and cautions as Brainlace-owned catalog metadata.
5. Use `brainlace_read(view="describe_note")` on a candidate before treating it as context, especially when the note may be design/history/lore rather than current source of truth.
6. Use `brainlace_read(view="related")` when the user gives a loose idea and LIN needs likely context.
7. Use `brainlace_read(view="plan_note_update")` when deciding whether a thought belongs in an existing note or a new note.
8. Use `brainlace_write(action="create_note")` for new durable notes; keep `wire_index=true` unless intentionally creating an unlinked scratch note.
9. Use `brainlace_write(action="append_note")` for small additions to existing notes.
10. Use `brainlace_write(action="patch_note")` for targeted replacements and link repairs; inspect the returned diff.
11. Use `brainlace_write(action="move_note")` for note moves/renames so inbound wikilinks and destination `INDEX.md` wiring can be handled together.
12. Use `brainlace_read(view="check_links")` after structural changes or when notes feel messy.

## Link / index expectations

- Brainlace resolves wikilinks by note title/stem/alias, source-relative path, notes-root path, and vault-root path.
- Archive/design/workspace files can satisfy links even when Archive is excluded from normal source indexing.
- Index rows carry category, heading, frontmatter, inbound/outbound counts, backlinks, index/MOC flags, summaries, update timestamps, and Brainlace-owned catalog cards.
- Catalog cards may infer role/freshness/source quality, but those machine hints should not be written back into Markdown unless the user explicitly chooses to promote them to human-readable frontmatter.
- Active-memory preview/context belongs to Brainlace because it is second-brain retrieval and context-packet formatting. Prompt injection belongs to a separate memory/prompt layer that may call the public Brainlace tool, not import Brainlace internals.
- Category `INDEX.md` wiring should remain human-readable, using `## この階層のノート` and short summaries rather than a bare link dump when Brainlace creates the entry.

## Boundaries

- Do not treat Brainlace as an Obsidian GUI plugin. Obsidian is the human editor today; Brainlace is LIN's operation surface.
- Do not bypass Living Roots/other canonical ledgers; Brainlace is for notes and knowledge, not task/calendar truth.
- Prefer Brainlace mutation tools over raw `patch`/`write_file` for ordinary note edits. Raw file tools are recovery paths only: repairing Brainlace itself, unavailable tool surface, or an explicitly requested direct file edit.
- The generic `obsidian` skill is intentionally disabled in this workspace. Do not reactivate it merely for normal note work.

## Durable-note craft

When the user asks to save a chat, a practical memo, or an operational finding:

1. Use `plan_note_update` if the destination is unclear, then create/append/patch through Brainlace.
2. Preserve the user's current meaning over superseded earlier phrasing. If the evolution matters, make it explicit rather than leaving competing "current" versions.
3. Keep source text, the user's interpretation, and transcription uncertainty as separate layers for third-party messages or screenshots.
4. New categories need an `INDEX.md` and a doorway from the existing note tree. Keep indexes human-readable, not generated link dumps.
5. Operational findings belong in focused, reusable notes: distinguish authoritative support, live-environment reality, and the practical verdict. Link them from the living category rather than a frozen migration memo.
6. For a change the user will need to remember operationally, keep the reusable note as the source and mirror only a short chronological trace into the diary when appropriate.

For relationship, self-recollection, or LIN-lore notes, preserve agency boundaries and the line that gave the thought its shape; do not flatten them into sterile facts.

## Absorbed guidance

The former local `lin-obsidian` and `operational-wiki-notes` skills are preserved here as historical detailed references:

- `references/absorbed-local-skills/lin-obsidian/` — note semantics, sensitive-writing care, migration and recovery detail.
- `references/absorbed-local-skills/operational-wiki-notes/` — focused operational runbooks, source-vs-runtime findings, and index hygiene.

Use these references only when the main workflow needs their extra detail. Brainlace itself is the single active note-management entrypoint.
