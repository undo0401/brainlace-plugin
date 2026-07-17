# Brainlace

Brainlace is a filesystem-first second-brain bridge for LIN/Hermes.

Humans can keep editing Markdown notes in Obsidian or any future editor. Brainlace gives agents a stable tool surface for indexing, searching, catalog-describing, relating, planning, creating, appending, patching, moving, and checking links without depending on an Obsidian GUI.

## Runtime defaults

- Vault root: `BRAINLACE_VAULT_ROOT`, then `OBSIDIAN_VAULT_PATH`, then `/opt/data/workspace`
- Notes root: `BRAINLACE_NOTES_ROOT`, then `notes`
- Index path: `plugins/brainlace/data/index.json`

## Tool surface

Brainlace exposes grouped router tools instead of many one-action tools:

- `brainlace_status()` — vault root、notes root、index 状態を読む
- `brainlace_read(view="search|related|catalog_search|describe_note|plan_note_update|check_links")`
- `brainlace_control(action="index")`
- `brainlace_write(action="create_note|append_note|patch_note|move_note")`

## Current capabilities

- Path-aware wikilink resolution across source-relative paths, `notes/`, and the vault root.
- Archive/design/workspace targets can satisfy links without making Archive a normal source scan target.
- Index records include category, headings, frontmatter, inbound/outbound counts, backlinks, index/MOC flags, summaries, and catalog cards.
- `brainlace_catalog_search` and `brainlace_describe_note` expose role/freshness/source-quality inference without writing those machine hints back into Markdown notes.

- Search and related retrieval weight title, aliases, tags, category/path, phrase matches, token overlap, and backlinks.
- Note creation and moves wire category `INDEX.md` pages with a human-readable `## この階層のノート` section.
- Patch/move tools return diffs or impacted link files, so LIN can repair notes without falling back to raw filesystem edits for ordinary note work.

## Boundary

Brainlace treats Obsidian as the current human editor, not as the core dependency. The source of truth is the filesystem note tree.
