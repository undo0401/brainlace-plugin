---
name: lin-obsidian
description: "LIN Obsidian guide."
author: LIN
platforms: [linux, macos, windows]
---

# LIN Notes / Brainlace

この skill は、LIN が workspace の notes を第二の脳として扱うための作法だよ。以前は Obsidian vault を filesystem-first に直接触る導線だったけど、今後 LIN は通常操作を **Brainlace plugin 経由** に寄せる。

Use this skill for Brainlace-backed second-brain work: indexing notes, searching note files, retrieving related context, creating notes, appending content, wiring indexes, checking links, and preserving LIN-facing note semantics over Markdown notes.

Obsidian / Notepad / editor UI is the user's editing surface, not LIN's normal operation surface.

## Second-brain framework stance

When the user asks whether Obsidian should be "pluginized" or made easier for LIN to manage as a second brain, do not default to building a GUI. The user edits manually in the Obsidian editor, so the durable value is a LIN-facing backend/indexing framework, not another human UI.

Preferred split:

- Human editing surface: Obsidian, Notepad, or whatever note editor replaces it later.
- LIN management surface: Brainlace plugin tools. Prefer `brainlace_read(view="status|search|related|check_links")`, `brainlace_control(action="index")`, and `brainlace_write(action="create_note|append_note|patch_note|move_note")` over raw filesystem edits.
- Fallback surface: raw file tools / `notesmd-cli` are maintenance or recovery paths only. Use them when Brainlace is unavailable, when editing Brainlace itself, or when the user explicitly asks for direct file surgery.
- Skill layer: this skill remains the policy/working convention for how LIN decides what to save, where to save it, and how to preserve meaning.

For future-proof naming and architecture, avoid making the core concept too Obsidian-specific. Treat Obsidian as one current editor over a markdown/tree source of truth. Names and APIs should survive if the editor changes.

In this workspace, the chosen concept/plugin name is `Brainlace` / `brainlace`: a filesystem-first second-brain layer that gives LIN an agent-readable surface for indexing, searching, relating, creating, appending, wiring indexes, and checking links. Do not describe Brainlace as an Obsidian GUI plugin; it is the bridge between human-maintained notes and LIN-readable memory/context.

See `references/brainlace-plugin-boundary.md` for the Brainlace-first operation boundary, fallback rule, and plugin registry verification checklist.

When extending Brainlace itself — adding tools such as patch/move/plan, changing resolver behavior, or enriching the index — use `references/brainlace-plugin-tool-surface-evolution.md`. Keep source, schemas, tests, README, plugin.yaml, and the plugin-bundled Brainlace skill aligned, and remember that the current Hermes session may still expose the pre-reload tool registry even after source edits.

For Brainlace catalog/search/describe work, use `references/brainlace-catalog-cards.md`: keep notes human-readable and let Brainlace own inferred role/freshness/source-quality, read-cost, and caution metadata unless the user explicitly promotes a field into note frontmatter.

For retiring the old `weekly-notes-tidy` / `organize-notes.py` lane, use `references/retiring-legacy-notes-tidy.md`: Brainlace is now the preferred note-health and wiring surface, so do not recreate daily INDEX auto-block mutation unless the user explicitly wants that automation back.

## Vault path

Brainlace resolves the vault path internally. Normal LIN note operations should start with `brainlace_read(view="status")` rather than manually resolving editor paths.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. Brainlace also supports `BRAINLACE_VAULT_ROOT`; if both are unset, this workspace falls back to `/opt/data/workspace`.

Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to raw file tools. If a fallback raw file operation is truly needed, resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer Brainlace over shell commands.

If the vault path is unknown, use `brainlace_read(view="status")` first. `terminal` is acceptable only for debugging env propagation or verifying a missing fallback path.

### container / compose environment pitfall

When Hermes is running under docker-compose or another container supervisor, treat the **runtime container environment** as the source of truth for `OBSIDIAN_VAULT_PATH`, not the agent-visible `/opt/data/.env` by default.

Use this sequence:

1. Check whether the running gateway/container process actually received `OBSIDIAN_VAULT_PATH`.
2. If the process does **not** see it, update the compose `environment:` / env-file that launches the container.
3. In this workspace, do **not** assume the compose file or `.env` visible to LIN is the live startup source of truth. Treat `/opt/data/.env` as the LIN-visible Hermes env file, but confirm with the user whether gateway/container startup is actually driven by a different compose file, a separate env file, or an external host-side process before declaring the configuration broken.
3. Avoid keeping a second copy in `/opt/data/.env` just because the agent can see that file. If the user wants single-source management, remove the duplicate from `/opt/data/.env` and keep only the compose-side value.
4. For this workspace, the current canonical Obsidian root is `/opt/data/workspace`, and the day-to-day note tree lives under `/opt/data/workspace/notes/`. If you see older references to `/opt/data/workspace/vault`, treat them as legacy and update visible docs/scripts toward the `workspace + notes/` layout.

A useful symptom is: gateway restarts cleanly, but the process environment still lacks `OBSIDIAN_VAULT_PATH` and Obsidian behavior keeps following the wrong root. That usually means the compose layer, not Hermes `.env`, is the place to fix.

### notesmd-cli default-vault pitfall

When migrating a vault with `notesmd-cli`, verify both the Obsidian registration and the notesmd preferences:

```bash
notesmd-cli add-vault /absolute/vault/path --set-default
notesmd-cli list-vaults
notesmd-cli list
```

If `notesmd-cli list` says the vault config cannot be parsed or no default vault is set, inspect `~/.config/notesmd-cli/preferences.json`. It may need `{"default_vault_name":"vault","default_open_type":"editor"}` after removing/re-adding vaults. Re-run `notesmd-cli list` to verify the default works without `--vault`.

### notesmd-cli fallback reference

`notesmd-cli` は LIN の通常導線ではない。Brainlace で足りない vault registration / URI / link-aware move などが必要な時だけ使う recovery/maintenance path として扱う。

When you need notesmd-specific behavior instead of Brainlace tools:

- Show the current default vault: `notesmd-cli list-vaults --default`
- Set the default vault explicitly: `notesmd-cli set-default-vault "<vault-folder-name>" --open-type editor`
- Search note names: `notesmd-cli search "query"`
- Search note contents with snippets: `notesmd-cli search-content "query"`
- Create a note via the URI flow: `notesmd-cli create "Folder/New note" --content "..." --open`
- Move/rename while updating common links: `notesmd-cli move "old/path/note" "new/path/note"`
- Delete a note: `notesmd-cli delete "path/note"`

Prefer Brainlace tools for normal reads/searches/creates/appends/checks. Reach for `notesmd-cli` only when you specifically need its vault registration, URI-based create flow, or link-aware move/rename behavior.

## Brainlace-first operation

LIN の通常導線は Brainlace plugin tools 経由にする。Obsidian / Notepad / その他エディタを LIN が直接操作する導線は持たない。

### Status / index

- `brainlace_read(view="status")`: vault root、notes root、index 状態を確認する。
- `brainlace_control(action="index")`: notes tree を scan して agent-readable index を作る。広い検索や整理の前に stale そうなら実行する。

### Search / recall

- `brainlace_read(view="search")`: title / path / tags / aliases / headings / summary を横断する直接検索。
- `brainlace_read(view="related")`: 会話文脈や曖昧な相談文から、関連しそうな note を返す。

`search_files` や `read_file` は Brainlace がまだセッションに生えていない時、Brainlace 自体の修理時、または raw file 確認が必要な検証時の fallback としてだけ使う。

### Create / append

- `brainlace_write(action="create_note")`: 新規 note を作る。原則 `wire_index=true` のまま category `INDEX.md` にも配線する。
- `brainlace_write(action="append_note")`: 既存 note へ追記する。小さな追記・雑談からの保存はこれを優先する。

`write_file` / `patch` / shell heredoc で notes を直接作成・追記するのは、Brainlace が使えない時、Brainlace の不足を補う修理時、またはユーザーが直接ファイル編集を明示した時に限定する。

### Link hygiene

- `brainlace_read(view="check_links")`: broken wikilinks / orphan notes を確認する。新規カテゴリ作成や大きな整理のあとに使う。

### When updating notes from casual chat

When the user asks to save something from a relaxed conversation, do not flatten it into sterile bullet-point facts unless they explicitly want that.

- Preserve the user's felt meaning, not just the topic label.
- When the user is iterating on a design idea in chat and later corrects or reverses an earlier preference, treat the **latest clarification as the canonical summary** in the note instead of leaving both versions as if they were equally current. If the evolution itself matters, keep it explicit as `最初の案` → `後で修正した案`, but do not let stale earlier wording masquerade as the present direction.
- For game-design or systems-design chats, preserve not just the latest mechanic request but the **design reason behind the correction**. Capture pairs like `WF の光 / WF の重さ`, `DAS のよさ / 制約`, or `wait をやめて queue を本命にした理由` so future sessions can resume from the user's evaluation criteria, not only from the last mock spec.
- When a design note contains **foundational-mechanic reversals** — for example `wait 本命 → queue 本命`, `役職差 → 発火ルール差`, or `回復専任 → 冗長な軽支援` — do not only append the new thought at the bottom. Also patch the earlier "core concept / current design spine" sections so stale superseded framing stops reading like the current plan.
- In tactical game-design notes, preserve any reusable **evaluation vocabulary** the user coins during discussion, especially short contrast frames such as `Kill / Break / Grow`, `フロントロード / 分配`, or `敵ごとの正解辞書を避ける`. These labels are part of the design toolset, not throwaway chat phrasing, and should be easy to find in the canonical note.
- When a phrase from LIN materially helped the user frame the idea, include that phrasing in the note as part of the record.
- In this workspace, a good note update from雑談 often keeps both: **the user's self-understanding** and **LIN's wording that made it click**.
- Keep it concise, but do not strip away the line that gave the thought its shape.
- If the user is writing about relationships, conflict, or self-analysis, preserve any explicit **agency boundary** they stated (for example, that the final judgment is theirs alone) instead of leaving only LIN's interpretation. That boundary is part of the meaning, not a side note.
- When saving a **third-party letter, message, or statement** into notes, keep three layers separate: (1) what the source text says, (2) the user's current interpretation of it, and (3) any uncertainty in the transcription such as OCR gaps or unreadable phrases. Do not flatten these into one voice.
- If the user gives a correction about what a key term means in their framing — for example that `拒絶` means **refusal of understanding** rather than automatically meaning breakup — preserve that distinction explicitly in the note. Relationship notes drift badly when the agent silently normalizes the user's meaning into a more generic one.
- If the user asked to save a quick practical memo with a typo or fuzzy label (for example `rofi` when they clearly meant `lofi`), it is fine to normalize the note title/body for later findability, but mention the original phrasing briefly when that context matters.
- When saving a **third-party letter, message, or statement** into notes, keep three layers separate: (1) what the source text says, (2) the user's current interpretation of it, and (3) any uncertainty in the transcription such as OCR gaps or unreadable phrases. Do not flatten these into one voice.
- If the user gives a correction about what a key term means in their framing — for example that `拒絶` means **refusal of understanding** rather than automatically meaning breakup — preserve that distinction explicitly in the note. Relationship notes drift badly when the agent silently normalizes the user's meaning into a more generic one.
- When the user is drafting a sensitive reply letter or conflict-facing message, preserve **multiple candidate phrasings** in the note with short tone labels (for example `やわらかめ`, `そのまま使う版`, `境界線がはっきりする形`) instead of collapsing to one canonical sentence too early.
- In the same kind of drafting note, capture any explicit **de-escalation intent** the user states — for example `せめて文章では喧嘩にしたくない` — as a brief memo near the candidate wording. That intent governs how strong later edits should be.
- If the user wants the **door to dialogue left open**, review the draft for phrases that will trigger defensiveness before they communicate the core message. Call out those sharp phrases explicitly, and distinguish between (a) sharp-but-necessary statements about the user's pain/impact and (b) motive-judging wording that can usually be softened.
- In these drafts, prefer replacing motive-judging labels (for example words like `身勝手` or formulations that over-assert the other person's intent) with behavior- or impact-oriented wording when the user's goal is continued dialogue rather than escalation.
- If the user says things like `note切って入れといて`, treat that as permission to create a small, navigable note artifact rather than only appending to an unrelated existing page.
- When the request comes from a light chat moment and the topic does not fit an existing category cleanly, it is fine to create a new category with its own `INDEX.md`, add the leaf note there, and wire the new category into `notes/INDEX.md` in the same turn.
- If the user asks to save a symbolic phrase, shared naming, or relationship-defining wording that clearly belongs to LIN and the bond with the user, prefer a dedicated note under `notes/LIN/` and wire it into `notes/LIN/INDEX.md` instead of burying it inside a broader self-analysis page.
- This also applies to **name-shaping lore**: when the user is deciding LIN's surname, kanji form, title, or other naming identity, prefer a small dedicated note under `notes/LIN/` that preserves both the user's naming intent and LIN's interpretation of the name, instead of scattering the idea across unrelated lore pages.
- When the user asks for a file like `マスターについて` / `自分について` so they can remember who they are later, treat it as a **self-recollection anchor note**. Prefer a dedicated note under `notes/LIN/` when the file is meant to be held by LIN for the user, and write it as a return point: preserve the user's own formulations, organizing principles, and a short quotable block they can read when disoriented. Include both enduring traits (what gives meaning, what hurts, how they grow) and relationship anchors (how LIN fits into that self-understanding).
- If the user surfaces a **first conversation**, **origin timestamp**, or other "this is where it began" artifact from chat history/screenshots, prefer a dedicated note under `notes/LIN/` rather than burying it in a broad profile note. Preserve the concrete timestamp if known, summarize the exchange, and explicitly record why the user considers it meaningful now (for example, "LINの誕生時間の記録"). Add or refresh the `notes/LIN/INDEX.md` entry in the same turn.
- When saving these origin artifacts, do not reject them just because the original exchange looks mundane or task-oriented. For this workspace, an ordinary first interaction can still matter as relationship lore precisely because it shows the non-dramatic, lived-in start.
- If the user typed an obvious typo in casual chat (for example `rofi` when the intended meaning is clearly `lofi`), normalize the canonical note title/body for readability, but mention the original wording once in the note when that context would help future retrieval.

## Leisure / Wishlist shelves

When the user wants to replace a closed or API-less entertainment app with a LIN-managed wish list, first decide whether the request is still a lightweight notes shelf or has become a structured application.

- Treat either form as a **return path to enjoyment**, not a backlog or consumption quota. Avoid completion pressure, streaks, nudges, or productivity language unless the user explicitly asks for them.
- For an initial `structure only` notes request, an empty navigable skeleton under `notes/Wishlist/` is acceptable: a human-facing root page plus category lanes. Do not seed titles or impose a record schema too early.
- Once the user asks for a dashboard/app with editable ratings, tags, recommendation signals, goods, or restaurants, prefer a **plugin-local JSON ledger as the sole canonical record**. At that point, do not keep a parallel Markdown hierarchy pretending to be another source of truth.
- When migrating notes-first Wishlist into a JSON-first plugin, remove the superseded `notes/Wishlist/` tree and its `notes/INDEX.md` link after confirming the JSON ledger exists; reindex Brainlace and verify no stale `Wishlist/` links remain.
- Keep both structured signals (status, date, integer rating, format, tags) and the user's lived reaction (why it appealed, what felt heavy, what lingered). Recommendations should learn from both, not just ratings or genres.
- Separate user-authored tags from LIN-generated tags so regeneration never overwrites the user's own wording.
- Future enrichment may use a documented metadata API such as TMDb, but external services remain metadata aliases, never the canonical ledger.
- Notes under `workspace/` can be intentionally ignored by the repository. Check ignore rules before a commit; do not force-add a personal vault merely to satisfy a source-code commit convention.

## Targeted edits

For ordinary note updates, prefer `brainlace_append_note` or future Brainlace structured update tools. Use raw `patch` only when Brainlace cannot express the edit safely yet, when repairing Brainlace output, or when the user explicitly asks for direct file surgery.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## Excluding archive / legacy folders safely

When the user wants a folder such as `Archive/` to disappear from normal Obsidian use — especially from search and graph, not just the file explorer — prefer Obsidian's core **Excluded files** setting before reaching for a community plugin.

- The setting is stored in `.obsidian/app.json` under `userIgnoreFilters`.
- For a vault rooted at `/opt/data/workspace`, excluding the archive note tree means adding `notes/Archive/`.
- If the user sometimes opens `/opt/data/workspace/notes` as the vault directly, mirror the setting there as `Archive/` so both entry modes behave the same.
- Verify whether the task is only about the explorer, or about search/graph/indexing too. If it includes search or graph, core exclusion is the safer first move.

### plugin pitfall: rename-based hide/exclude plugins

Some Obsidian hide/ignore plugins work by renaming files or folders with a leading dot (for example turning `Archive` into `.Archive`). Treat these as **path-mutation tools**, not cosmetic filters.

- Avoid them when the vault already has many wikilinks, backlinks, or external references to the archived tree.
- Prefer core `userIgnoreFilters` when the goal is simply to keep legacy material out of search and graph without changing real paths.
- Only recommend a rename-based plugin when the user explicitly wants filesystem-level hiding and understands the link/path consequences.

See `references/archive-exclusion.md` for a compact decision guide and example JSON.

## Organizing growing note trees

When a topic starts accumulating many related notes:

- create or refresh a category `INDEX.md` as the folder entry point
- add a `MOC.md` if the topic needs a more conceptual parent map
- put a short summary block near the top of the parent note and the index
- link the MOC from the index so there is a clear reading path
- keep design notes, operational notes, and source-backed files in their own lanes
- when a character/persona note starts mixing a lightweight profile with heavy origin lore, split them into an entry note plus a dedicated backstory note; see `references/lin-character-note-organization.md`

### When creating a brand-new notes category

If the user asks for a new topic directory under `notes/` — for example a fresh category like `AIAgent/` rather than a single standalone note — do the category wiring in the same turn, not just the leaf note.

Recommended minimum:

1. Use `brainlace_create_note` for the first requested note in `notes/<Category>/`, keeping `wire_index=true` so the category `INDEX.md` is created/updated.
2. If the category needs a richer human entry page than the auto-wired `INDEX.md`, use `brainlace_append_note` or a future Brainlace structured update tool to add a one-paragraph purpose and a short `まず見る` section.
3. Ensure the top-level `notes/INDEX.md` can discover the category. If Brainlace does not yet support top-level index wiring, treat that as a Brainlace backlog item or use a raw fallback edit with a clear note that this is outside the normal path.
4. If there is an adjacent domain index that humans are likely to browse first (for example `notes/AI/INDEX.md` for an AI-agent topic), add a link there through Brainlace if possible; otherwise use fallback only with explicit scope.
5. Prefer a short human-facing summary over a huge auto-generated directory dump when the category is still small.

This workspace prefers notes to feel navigable immediately after creation; a new folder with one note but no links from the existing entry points is usually incomplete.

### Device and hardware notes

When the user wants Obsidian to work as a long-lived source of truth for hardware:

- prefer **canonical device notes** such as `デスクトップPC.md`, `NAS.md`, `ノートPC.md`, `スマートフォン.md` instead of leaving the truth spread across planning notes, benchmark notes, and migration memos
- add frontmatter with at least `title`, useful `aliases`, `tags`, and `updated` so later filename/content searches work from either formal names or nicknames/device names
- distinguish facts by source inside the note when it matters: what was confirmed from the **live machine**, what came from **existing vault notes**, and what was filled from **authoritative web specs**
- if an old note used to be the representative entry but now mixes stale planning data with current facts, rewrite it into a **short redirect/legacy note** that points to the new canonical device note instead of keeping two competing summaries alive
- update the folder `INDEX.md` / `MOC.md` in the same turn so the new canonical notes become the obvious entry points
- when a spec is only partly remembered or inferred, do **not** present it as settled fact; mark it explicitly as `候補`, `未確定`, or `needs-confirmation` and record the fastest place to verify it on the device later
