# Hermes dashboard approval-mode mismatch

Use this as a model when documenting UI-vs-source-of-truth drift in the wiki.

## Symptom

The dashboard settings page did not offer `approvals.mode: smart`. It showed legacy-looking choices instead.

## Source of truth to verify

Check all three layers, not just docs:

1. Effective config defaults / comments
2. Runtime implementation
3. Dashboard field metadata

## Example proof locations

- `hermes_cli/config.py`
  - `approvals.mode` default/comment indicate: `manual`, `smart`, `off`
- `tools/approval.py`
  - `_get_approval_mode()` and smart-approval branches also expect: `manual`, `smart`, `off`
- `hermes_cli/web_server.py`
  - dashboard field metadata exposed `approvals.mode.options = ["ask", "yolo", "deny"]`

## Why this matters

A stale dashboard dropdown is not just a cosmetic bug.

If the visible values differ from runtime semantics, the UI may:
- hide a valid mode the user actually wants
- encourage saving legacy values
- leave the user with config that does not map cleanly to current behavior

## What to record in the wiki note

- the user-visible symptom
- the authoritative values
- the exact files that proved it
- whether legacy UI values are normalized safely or not
- the safe workaround until the UI is fixed

## Safe workaround pattern

When a config UI is stale, prefer direct config or CLI writes over the dashboard.

For this example, the safe guidance was:
- set `approvals.mode` directly in `config.yaml`, or
- use `hermes config set approvals.mode smart`

## Reusable lesson

When documenting dashboard/config issues, always distinguish:
- missing feature
- stale docs
- stale UI metadata
- stale runtime behavior

Only the last one proves the feature is truly absent.
