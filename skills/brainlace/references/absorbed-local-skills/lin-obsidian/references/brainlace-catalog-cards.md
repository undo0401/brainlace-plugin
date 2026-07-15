# Brainlace catalog cards: note-clean second-brain metadata

Use this reference when extending Brainlace or operating notes with catalog/search/describe semantics.

## User preference

- The user's preferred boundary is: Markdown notes remain human-readable source of truth; Brainlace bears growing machine metadata load.
- Do not write inferred scores, query matches, retrieval counters, or role guesses into notes.
- Only promote explicit, human-meaningful decisions to note frontmatter when the user asks or approves it, e.g. `context_role`, `freshness`, `source_quality`, `use_for`, `do_not_use_for`.

## Implementation pattern

- Build a deterministic `catalog` card in the Brainlace index/cache from existing note data: path, category, tags, aliases, headings, summary, links, backlinks, mtime, and frontmatter.
- Keep explicit frontmatter separate from inferred fields:
  - `context_role` vs `inferred_context_role`
  - `freshness` vs `freshness_guess`
  - `source_quality` vs `source_quality_guess`
- Add `when_to_use`, `when_not_to_use`, `read_cost`, `recommended_action`, and `confidence` as Brainlace-owned metadata.
- `brainlace_catalog_search` should answer "which note is useful/safe for this task before reading full body?"
- `brainlace_describe_note` should answer "what is this note, what is it safe for, and what cautions apply?"

## Verification

- Add tests for both direct handlers and public registration so the tool surface does not silently omit the new tools.
- Use direct import smoke tests after source edits because the active Hermes tool registry may still have the old plugin implementation until reload.
- Confirm a real vault query returns a sensible catalog candidate and `describe` separates explicit note fields from inferred catalog fields.
