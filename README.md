# Brainlace

Brainlace is a filesystem-first second-brain bridge for LIN/Hermes.

Humans can keep editing Markdown notes in Obsidian or any future editor. Brainlace gives agents a stable tool surface for indexing, searching, relating, creating, appending, and checking links without depending on an Obsidian GUI.

## Runtime defaults

- Vault root: `BRAINLACE_VAULT_ROOT`, then `OBSIDIAN_VAULT_PATH`, then `/opt/data/workspace`
- Notes root: `BRAINLACE_NOTES_ROOT`, then `notes`
- Index path: `plugins/brainlace/data/index.json`

## Tool surface

- `brainlace_status`
- `brainlace_index`
- `brainlace_search`
- `brainlace_related`
- `brainlace_create_note`
- `brainlace_append_note`
- `brainlace_check_links`

## Boundary

Brainlace treats Obsidian as the current human editor, not as the core dependency. The source of truth is the filesystem note tree.
