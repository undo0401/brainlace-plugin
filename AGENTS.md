# AGENTS

Brainlace is the live plugin surface for LIN's filesystem-first second-brain framework.

## Scope

Safe to edit:

- `README.md`
- `AGENTS.md`
- `plugin.yaml`
- `__init__.py`
- `schemas.py`
- `test_plugin.py`
- `skills/`

Runtime/generated state lives under `data/` and should not be treated as source.

## Product boundary

- Brainlace is not an Obsidian GUI plugin.
- Obsidian is the current human editor; Markdown/filesystem notes are the durable substrate.
- Brainlace exists so LIN/Hermes can index, search, relate, write, and check notes safely through plugin tools.
