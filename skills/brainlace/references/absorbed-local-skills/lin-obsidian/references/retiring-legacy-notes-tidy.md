# Retiring legacy notes tidy cron

Use this reference when notes/Brainlace maintenance overlaps with the old `weekly-notes-tidy` / `organize-notes` lane.

## Durable lesson

Brainlace now owns the normal second-brain maintenance surface: indexing, path-aware wikilink checks, search/related, planned note placement, patch/move operations, and human-readable `INDEX.md` wiring.

The old `maintenance/organize-notes.py` cron was a legacy automation that:

- refreshed auto-generated blocks inside `INDEX.md`
- emitted `weekly-notes-tidy.md/json` monitor artifacts
- reported broken wikilink candidates

After Brainlace gained stronger resolver/check/index/wiring tools, this lane became redundant and risked fighting human-readable index curation.

## Preferred future handling

- Do not recreate `weekly-notes-tidy` or `organize-notes.py` by default.
- Use Brainlace tools for note health and link hygiene.
- If recurring reporting is needed again, implement it as a thin Brainlace health consumer rather than a separate notes mutator.
- Avoid daily automatic edits to `INDEX.md` unless the user explicitly wants generated blocks back.
- If removing similar legacy automation, delete all four surfaces together: cron job, script, monitor artifacts, and stale backup references that would resurrect it during restore.

## Removal checklist

1. List cron jobs and identify the exact job id; do not guess.
2. Remove the cron job through the cron tool.
3. Delete the script under `/opt/data/scripts/...`.
4. Delete monitor artifacts under `/opt/data/workspace/monitor/...`.
5. Search for remaining active references by job name, script path, and artifact basename.
6. Check stale cron backups if they contain the removed lane and would cause confusion during restore.
7. Commit the removal if the workspace source tree tracks those files.
