---
name: operational-wiki-notes
description: Capture durable operational findings in the Obsidian vault as discoverable runbook notes, especially after config audits, dashboard investigations, and source-vs-UI mismatch debugging.
---

# Operational Wiki Notes

## When to use

Use this when work produces operational knowledge that should survive the session, especially:

- dashboard or config review findings
- security / exposure checklists
- settings recommendations the user will revisit later
- debugging where the UI disagrees with the code, docs, or effective runtime behavior
- capability/readiness checks, where the answer is "feature exists in theory, but this environment is or is not actually ready"
- cases where a quick chat answer is not enough and the user asked to "write it to the wiki"

## Goal

Turn a one-off answer into a reusable vault note that future sessions can find quickly.

## Steps

1. Decide whether the finding belongs in an existing overview note or deserves its own focused note.
   - Use a focused standalone note when the content is a checklist, runbook, audit memo, or bug-shaped investigation.
   - Use the overview note for broad context and navigation.

2. If creating a focused note, place it under the relevant topic folder.
   - Example pattern: `notes/AI/<topic>.md`
   - Prefer names that read like future lookup queries, not session-specific titles.

2.5. If the topic is likely to recur and no suitable folder exists yet, create a new category folder under `notes/` with its own `INDEX.md`.
   - Use this for durable operational domains such as git / GitHub / branch rules, not for one-off incidents.
   - Keep the new category lightweight: one `INDEX.md`, the requested note, and a link from `notes/INDEX.md` in the same turn so future sessions can discover it.
   - Prefer this over hiding the note in an unrelated folder when the user is really establishing a new area of ongoing reference.

3. Write the note for re-use, not for storytelling.
   - Lead with the practical purpose.
   - If the task was a capability/readiness audit, explicitly separate:
     - what the upstream docs or source of truth say is supported
     - what the current environment actually has installed/configured
     - the final operational verdict for this machine/profile
   - Include the priority order or decision rubric if one emerged.
   - Separate "what to check", "why it matters", and "recommended action".

3.5. Choose the living note, not just the nearest note.
   - If the topic is about Hermes itself, prefer an active Hermes note such as `notes/AI/Hermes-Agent.md` or another current Hermes-focused page.
   - Do not keep appending fresh Hermes operational guidance into migration/comparison notes that were only used during evaluation or cutover.
   - If the user says a note is effectively frozen (for example, a pre-migration comparison page), treat that as a workflow rule: move or rewrite the new content into the active note and leave the frozen note untouched unless the user explicitly asks to revise history.

4. When the task uncovered a source-of-truth mismatch, record both layers.
   - State the user-visible symptom.
   - State the authoritative source of truth.
   - Cite the exact code/docs/config locations that proved it.
   - Add the safe workaround until the mismatch is fixed.

5. Add discoverability links.
   - If there is a broader umbrella note, add a backlink from it to the focused note.
   - Keep the umbrella note light; use it as an index, not a dump.
   - For note-heavy topics, add a parent `MOC.md` before the note tree gets too deep, and link it from the category `INDEX.md`.
   - When the user says things like 「notesにまとめといて」 after you already explained a Hermes/OpenClaw operational topic in chat, prefer creating a **focused reusable note** under the living topic folder (for Hermes topics, usually `notes/Hermes-Agent/`) rather than stuffing the answer into a giant parent page. Then update that folder's `INDEX.md` so the note is discoverable from the vault entrance.
   - Apply the same pattern to broader technical synthesis, not just Hermes ops. If the chat answer was a reusable comparison or recommendation memo (for example LLM/model rankings, local-vs-hosted tradeoffs, provider selection, benchmark interpretation), create a focused note in the domain folder such as `notes/AI/`, and link it from that folder's `INDEX.md`.
   - For model / benchmark comparison notes, explicitly separate **public leaderboard or vendor-facing claims** from **local measurements / in-house benchmarks**. Future readers need to see whether “strongest” means public snapshot, local workload fit, or both.
   - When the topic is repo / git / GitHub / branch rules and there is no existing category yet, create a dedicated `notes/構成管理/` folder with its own `INDEX.md`, put the focused note there (for example `github.md`), and add a backlink from root `notes/INDEX.md`. Treat this as durable operational guidance, not as a diary-only memo.

5.5. When the change is an operational behavior change the user will likely want to remember later, mirror it in the same-day diary as well as the living note.
   - Use the living note for reusable guidance and proof.
   - Use the diary for a short chronological record that the change happened.
   - This is especially useful for Hermes/OpenClaw runtime changes, cron jobs, notification wiring, and dashboard behavior adjustments.
   - Apply the same pattern to hardware/network planning decisions that the user says to "write down" for later execution, such as AI PC / NAS topology, NIC selection, and migration staging.

5.6. If the session tried an approach and later removed or replaced it, record the **final authoritative state**, not just the experiment.
   - Rewrite any note text that still reads like the discarded path is current.
   - Mention the cleanup explicitly when it matters operationally, such as deleting a temporary config file, route, proxy, or subscription.
   - For notifications/automation work, state which artifact is now the source of truth and which artifact was intentionally removed.

6. Verify that the note is useful on its own.
   - A future agent should be able to open only the new note and understand the recommendation, the pitfall, and the workaround.

## Recommended structure

- Title
- Short purpose statement
- Priority / checklist section
- Known pitfall or mismatch section
- Safe workaround
- References / proof locations

## Pitfalls

- Do not bury an actionable audit checklist inside a giant general note.
- Do not create an orphan standalone note with no backlink from the relevant overview page.
- Do not record only the symptom when the important learning was the mismatch between UI and implementation.
- Do not keep updating a legacy migration/comparison note just because it already contains related text; once a page is no longer the active source for that domain, new operational guidance belongs in the living domain note.
- If the user explicitly says a note is frozen or only for pre-migration evaluation, treat edits to that page as a mistake to unwind: move the new material into the living note and restore the frozen note's metadata when practical.
- When the UI exposes config choices, verify whether those labels still match the current implementation semantics. A stale dropdown can be worse than a missing option if it writes outdated values.
- If a settings UI appears wrong, document not only the missing choice but also whether selecting the visible legacy values could save an invalid or behaviorally wrong config.
- Do not mirror large upstream docs; condense only the parts that mattered to the task.
- When the user asks to "organize notes", prefer a light structural cleanup first: add or refresh `INDEX.md` entry points, move obviously misplaced notes into the right folder, and avoid rewriting note bodies unless asked.
- After moving a note, update the relevant indexes and verify the old stray path is gone so the vault doesn't end up with split entry points.
- For Hermes-specific operational findings, prefer the established Hermes note of record over older comparison pages; if the user has named the living note, follow that naming consistently instead of improvising a nearby page.

## Reference patterns

- `references/hermes-dashboard-approval-mode-mismatch.md` — example of documenting a source-vs-UI mismatch where the dashboard dropdown lagged behind the backend config semantics.
- `references/hermes-release-watch-pattern.md` — when upstream notifications should be implemented as cron + `no_agent` polling with a state file, and how to record that change in the living Hermes note plus the same-day diary.
- `references/hermes-webui-runtime-vs-compose-check.md` — checklist for cases where notes or intended compose changes mention Open WebUI / API Server, but the live system is actually running built-in Dashboard or community Hermes WebUI on different ports.

## Additional pitfall: intended architecture vs live runtime

When debugging Hermes web surfaces, do not assume the current browser target matches the most recent design note or intended compose plan.

- Separate these four surfaces explicitly before writing conclusions:
  - built-in Hermes Dashboard
  - community `hermes-webui`
  - Open WebUI
  - Hermes API Server
- Verify each with the actual listener/HTTP response first, because the user may remember "webui" while the live system has drifted to a different implementation.
- If a note says Open WebUI should be on `3000` and Hermes API Server on `8642`, but live probes show Dashboard on `9119` and `hermes-webui` on `8787`, record that as a **runtime-vs-plan mismatch**, not as a generic outage.
- Prefer notes that state both the intended architecture and the observed live endpoints so future sessions do not keep chasing the wrong port.

## Archive shelf refactors and index hygiene

When the user wants to retire a subdirectory like `benchmark/old` and fold it into archive storage, treat that as a **navigation refactor**, not just a file move.

- Prefer moving the whole shelf into `notes/Archive/<topic>/` rather than leaving an `old/` directory under an active category.
- After the move, update both kinds of references:
  - literal path mentions like ``notes/benchmark/old/...``
  - wikilinks like ``[[../benchmark/old/foo|...]]``
- Refresh the archive entrypoints too:
  - add or update `notes/Archive/INDEX.md`
  - ensure `notes/Archive/<topic>/INDEX.md` reads like an archive shelf, not like a leftover `old` index
- Refresh the active side entrypoints:
  - `notes/<topic>/INDEX.md` should explain that current artifacts live here and historical artifacts moved to `Archive/<topic>/`
  - if the category is important from root navigation, also patch `notes/INDEX.md` and any domain index like `notes/AI/INDEX.md` so both current and archive shelves are discoverable
- Re-run the note index organizer after the move so auto-generated blocks stop advertising the removed subdirectory.

## Good outcomes

- The user can revisit the note later and immediately act.
- Future sessions can find the note from either the focused filename or the umbrella page.
- Debugging notes include enough proof locations to support a code fix later.
- Archive migrations leave clean navigation on both the active shelf and the archive shelf, with no stale `old/` doorway left behind.
