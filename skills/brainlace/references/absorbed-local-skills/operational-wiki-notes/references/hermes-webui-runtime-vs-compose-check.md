# Hermes web surfaces: runtime-vs-compose check

Use this when a user says "Hermes WebUI is broken" or refers loosely to "the web UI" and the stack may contain more than one frontend.

## Why this matters

Hermes-related web access can mean different things:

- built-in Hermes Dashboard
- community `ghcr.io/nesquena/hermes-webui`
- Open WebUI
- Hermes API Server backing Open WebUI

A lot of wasted debugging comes from treating these as one thing.

## Fast classification checklist

1. Identify the compose source of truth actually mounted in the workspace.
   - In this workspace, the live compose path was `/opt/data/overrides/docker-compose.yaml`.
   - A remembered or older path can be wrong even if the note around it is mostly right.

2. Read the live service list, not just the design note.
   - Look for service names like `hermes`, `hermes-webui`, `open-webui`.
   - Presence of `HERMES_DASHBOARD=1` strongly suggests the built-in Dashboard is expected.
   - Presence of `API_SERVER_ENABLED` / `API_SERVER_KEY` is a strong signal that Open WebUI + Hermes API Server was intended.

3. Probe the actual listeners and classify by response shape.
   - `9119` returning `Sign in — Hermes Agent` or `/api/health -> 401` suggests built-in Dashboard.
   - `8787` returning `Hermes — Sign in` or `/health -> 200` suggests community `hermes-webui`.
   - `3000` often corresponds to Open WebUI, but do not assume it exists unless it answers.
   - `8642/v1/models` refusing connections means Hermes API Server is not currently serving.

4. Write the conclusion in mismatch language when appropriate.
   - Good: "The runtime is on Dashboard 9119 + community Hermes WebUI 8787; Open WebUI/API Server are not currently live."
   - Bad: "Hermes WebUI is down" when only the wrong port was checked.

## Example mismatch pattern

Observed in this workspace:

- built-in Dashboard live on `127.0.0.1:9119`
- community `hermes-webui` live on `127.0.0.1:8787`
- `127.0.0.1:3000` refused
- `127.0.0.1:8642` refused
- live compose contained `hermes-webui`, not `open-webui`
- note history still discussed an intended Open WebUI + API Server design

Operational verdict:

- This is not primarily a frontend crash.
- It is a source-of-truth mismatch between the remembered/intended architecture and the actual running stack.

## What to record in notes

- exact compose path used as source of truth
- exact live endpoints and what each one served
- whether the issue was a dead service, wrong port, wrong product, or missing API Server
- whether a prior design note described a future state rather than current runtime
