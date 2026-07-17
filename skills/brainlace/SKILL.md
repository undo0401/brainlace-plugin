---
name: brainlace
description: "Brainlace plugin registry: Markdown vault indexing, retrieval, mutation, and link-integrity tool surface."
author: LIN
---

# Brainlace registry

## Public tools

- `brainlace_status` — vault root、notes root、index 状態
- `brainlace_read` — catalog、search、related、note description、link check
- `brainlace_write` — note create、append、patch、move
- `brainlace_control` — index / maintenance action

## Data model

- human editing surface: Markdown filesystem（Obsidian は現在の editor）
- agent operation surface: Brainlace plugin tools
- source of truth: configured vault 内の Markdown
- catalog metadata: Brainlace が index 側で保持する派生情報。人間向け frontmatter へ自動で書き戻さない

## Operation invariants

1. broad retrieval の前に vault status と index freshness を確認する
2. note mutation は raw file tool より Brainlace write tool を優先する
3. move / rename は inbound wikilink と category `INDEX.md` を同じ操作単位で扱う
4. structure mutation の後は link check を行う
5. index は human-readable な category `INDEX.md` を維持し、単なる link dump にしない

## Boundaries

- Brainlace は Obsidian GUI plugin ではない
- task / calendar の正本は Living Roots
- raw `patch` / `write_file` は Brainlace 自体の修復、tool unavailable、明示された direct edit の recovery path
- active-memory context packet は Brainlace の retrieval responsibility。prompt injection は別 layer が public tool 経由で扱う

## Historical references

- `references/absorbed-local-skills/lin-obsidian/`
- `references/absorbed-local-skills/operational-wiki-notes/`
