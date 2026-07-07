# Brainlace

Brainlace is a filesystem-first second-brain bridge for LIN/Hermes.

Humans can keep editing Markdown notes in Obsidian or any future editor. Brainlace gives agents a stable tool surface for indexing, searching, catalog-describing, relating, planning, creating, appending, patching, moving, and checking links without depending on an Obsidian GUI.

## Runtime defaults

- Vault root: `BRAINLACE_VAULT_ROOT`, then `OBSIDIAN_VAULT_PATH`, then `/opt/data/workspace`
- Notes root: `BRAINLACE_NOTES_ROOT`, then `notes`
- Index path: `plugins/brainlace/data/index.json`

## Tool surface

- `brainlace_status`
- `brainlace_index`
- `brainlace_search`
- `brainlace_related`
- `brainlace_catalog_search`
- `brainlace_describe_note`
- `brainlace_create_note`
- `brainlace_append_note`
- `brainlace_patch_note`
- `brainlace_move_note`
- `brainlace_plan_note_update`
- `brainlace_check_links`

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
