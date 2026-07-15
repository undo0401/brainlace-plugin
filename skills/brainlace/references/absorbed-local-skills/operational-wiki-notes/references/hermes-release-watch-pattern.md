# Hermes release watch pattern

Use this pattern when the user wants update notifications for an external project repo (for example `NousResearch/hermes-agent`) but does not control that repo's webhook settings.

## Decision rule

- If you need notifications from **your own repo/service** and can configure the producer, webhook subscriptions may fit.
- If you only need to **observe an external repo's releases**, prefer **cron + script polling**.
- For Hermes release tracking specifically, poll the GitHub Releases API instead of trying to attach a webhook to the upstream repo.

## Durable implementation pattern

1. Write a deterministic script that fetches the latest release metadata from GitHub.
2. Store the last seen release in a state file under the workspace runtime area, e.g. `workspace/state/<name>.json`.
3. On first run, seed the state file without notifying so existing releases do not create a false alert storm.
4. On later runs, print a message only when the tag/version changed.
5. Exit silently when nothing changed.
6. Schedule the script with a Hermes cron job using `no_agent: true` so stdout becomes the delivered notification text.

## Why this pattern worked

- It avoids requiring admin access to the upstream repository.
- It keeps routine checks silent and only emits human-facing output on change.
- It matches a config/state split where long-lived configuration lives under `config/` and mutable runtime markers live under `state/`.

## Notes to record in the vault

When documenting this kind of automation change for this user, update both:

- the living Hermes operational note (for example `notes/AI/Hermes-Agent.md`)
- the same-day diary with a short summary of what changed and why

If you briefly tested a webhook route or other alternate path first, do not leave the notes frozen in that intermediate state. Rewrite them to say the cron+script watch is the final source of truth, and note the cleanup of the abandoned artifact (for example removing `webhook_subscriptions.json`).
