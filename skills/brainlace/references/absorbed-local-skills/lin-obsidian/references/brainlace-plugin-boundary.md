# Brainlace plugin boundary

Use this reference when LIN is operating the user's second-brain notes after the Brainlace migration.

## Durable split

- Human editor: Obsidian, Notepad, or any future Markdown editor the user chooses.
- LIN operation surface: Brainlace plugin tools.
- Durable substrate: the filesystem Markdown note tree under the workspace notes root.

Do not describe Brainlace as an Obsidian GUI plugin. It is the LIN/Hermes tool surface for indexing, recalling, creating, appending, and checking Markdown notes without depending on a specific editor UI.

## Default workflow

1. Start with `brainlace_status` to confirm roots and index state.
2. Refresh with `brainlace_index` when the index is stale or a broad recall task starts.
3. Use `brainlace_search` for direct known terms and `brainlace_related` for fuzzy conversation context.
4. Use `brainlace_create_note` for new notes, keeping index wiring on unless there is a specific reason not to.
5. Use `brainlace_append_note` for small additions from casual chat.
6. Use `brainlace_check_links` after category creation, large reorganization, or suspected broken wikilinks.

## Fallback rule

Raw `read_file`, `search_files`, `write_file`, `patch`, shell text editing, and `notesmd-cli` are fallback/maintenance paths only:

- Brainlace tools are unavailable in the current session.
- Brainlace itself is being repaired or extended.
- The user explicitly asks for direct file surgery.
- A structured note edit is not yet expressible through Brainlace, and the fallback scope is stated clearly.

## Implementation lesson

When creating a Hermes plugin as a LIN-facing operation surface, verify three layers before declaring it usable:

- Plugin files and local tests pass.
- `hermes plugins enable <plugin>` succeeds and reports that changes take effect next session.
- The plugin's `ctx.register_tool(...)` calls actually flow into `tools.registry.registry.register(...)`, with expected tool names and toolset.

If the plugin is enabled during an active session, expect the new registry tools to appear only after a new session, gateway restart, or session reset.