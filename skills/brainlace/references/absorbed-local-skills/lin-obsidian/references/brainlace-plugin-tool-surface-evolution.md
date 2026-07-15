# Brainlace plugin tool-surface evolution

Use this reference when extending Brainlace itself, not just operating notes through it.

## Durable lessons

- Keep Brainlace as the LIN/Hermes backend for filesystem-first notes; do not drift into building an Obsidian GUI replacement.
- When adding note-mutation capability, update the full plugin surface together: `__init__.py`, `schemas.py`, `test_plugin.py`, `README.md`, `plugin.yaml`, and the plugin-bundled `skills/brainlace/SKILL.md`.
- Prefer class-level Brainlace tools over raw file fallback for recurring note operations. Good tool boundaries are:
  - `brainlace_patch_note` for targeted old/new replacements with diff output.
  - `brainlace_move_note` for move/rename plus inbound wikilink updates and destination `INDEX.md` wiring.
  - `brainlace_plan_note_update` for deciding append vs create and candidate target notes.
- Link resolution should match real vault behavior, not only note stems. Resolve wikilinks by title/stem/alias, source-relative path, notes-root path, and vault-root path. Allow `.md` omission. Let Archive/design/workspace targets satisfy links even if Archive is excluded from normal source indexing.
- Index records are more useful when they include category, first heading, frontmatter, index/MOC flags, inbound/outbound counts, backlinks, embedded links, summaries, update timestamps, and Brainlace-owned catalog cards for inferred role/freshness/source quality.
- Keep machine-derived catalog metadata in Brainlace index/cache rather than writing it into Markdown. Only promote explicit, human-meaningful decisions like `context_role` or `freshness` into note frontmatter when the user chooses that.
- Human-facing `INDEX.md` wiring should not be a bare link dump. Prefer a stable section such as `## この階層のノート` with `[[target|title]] — short summary` rows.

## Verification pattern

- Compile plugin Python: `python3 -m py_compile __init__.py schemas.py test_plugin.py`.
- If `pytest` is unavailable, directly import `test_plugin` and run every `test_*` function; do not record missing pytest as a durable tool failure.
- Test plugin registration with a fake ctx and confirm all expected tools are registered.
- For live-vault behavior, direct-import the modified plugin source and call internal tool handlers before relying on current-session Hermes tool calls.
- Important: Hermes tool registry may keep the old plugin implementation for the current session. If `functions.brainlace_*` still returns old behavior after source edits, verify via direct import, then tell the user gateway/plugin reload is needed for the new public tool surface.

## Skill/script absorption guidance

- Put operating policy and preferred flows in `lin-obsidian` and the plugin-bundled `brainlace` skill.
- Move reusable deterministic checks toward Brainlace source or a thin script that calls Brainlace, rather than duplicating link resolvers in multiple places.
- システムステータス should ideally consume Brainlace health output instead of owning a divergent Obsidian resolver.
