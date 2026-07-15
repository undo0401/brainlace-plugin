# Archive exclusion in Obsidian

## When to use

Use this when the user wants a legacy subtree such as `Archive/` to stop appearing in normal Obsidian workflows, especially in:

- search results
- graph view
- general indexing / note discovery

## Safer default

Prefer Obsidian core **Excluded files** over a community plugin when the goal is "hide from search/graph without changing filenames".

The setting lives in `.obsidian/app.json` as `userIgnoreFilters`.

### Workspace-root vault example

If the vault root is `/opt/data/workspace` and archived notes live under `notes/Archive/`, use:

```json
{
  "userIgnoreFilters": [
    "notes/Archive/"
  ]
}
```

### Notes-root vault example

If the user sometimes opens `/opt/data/workspace/notes` directly as the vault, mirror the setting there as:

```json
{
  "userIgnoreFilters": [
    "Archive/"
  ]
}
```

## Why not "File Ignore"-style plugins by default?

Some ignore/hide plugins achieve exclusion by renaming files/folders with a leading dot.

Example risk:

- `Archive/` becomes `.Archive/`
- existing wikilinks, backlinks, bookmarks, or external references may drift or break
- the vault history becomes noisier because many paths changed for a display/indexing concern

That makes them a poor default for mature vaults with lots of existing links.

## Decision rule

- If the user only wants the explorer to look cleaner, explorer-only plugins are fine.
- If the user wants search/graph/indexing exclusion without path churn, use core `userIgnoreFilters` first.
- If the user explicitly wants filesystem-level hiding and accepts path mutation, then a rename-based plugin can be considered.
