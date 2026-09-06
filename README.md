# Trade Signal

A work-sample system built for a real application to Fireclay Tile's Lifecycle Growth & Analytics Manager role, reporting to Samantha Grow. It's meant to demonstrate the actual competencies the job description asks for against real (free-tier) tooling, not describe them.

Read the full write-up at [`site/case-study.html`](site/case-study.html) (open with `python3 -m http.server` from the repo root, then visit `localhost:8000/site/case-study.html`).

## What's real, what's synthetic, what's simulated

Every doc and page in this repo labels itself against three categories, consistently:

- **Real / live** — an actual account (HubSpot, Salesforce, a Shopify Partner dev store) with real API calls against it, verified by reading data back through the connector rather than assumed from a write summary.
- **Synthetic** — the underlying 3,200-customer dataset is generated, not real Fireclay customer data. Every email uses the `@example.com` domain (RFC 2606, guaranteed never to reach a real inbox).
- **Simulated** — a small number of things are deliberately faked for demonstration purposes even though the underlying mechanism is real (e.g. backdated weekly snapshots used to prove trend-detection logic without waiting real weeks). Always called out explicitly where it happens.

Nothing here is affiliated with or endorsed by Fireclay Tile.

## Layout

```
data/            synthetic dataset generation, single- and cross-CRM reconciliation exercises
docs/            setup logs and the measurement-foundation write-up
design/          mockups
shopify-theme/   real Liquid theme section on a live Shopify Partner dev store
visualizer/      perspective texture-mapping room visualizer (not generative AI)
analysis/
  crm-reconciliation/   HubSpot <-> Salesforce lifecycle data-quality reconciliation
.claude/
  skills/lifecycle-pulse/   a real, runnable Claude Code skill: recurring lifecycle/funnel digest
site/            the case-study write-up
```

## Running things

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Scripts that touch a live account read credentials from `.env` (copy `.env.example` first). Nothing in this repo will run against a live account without those set.

## Build status

See `site/case-study.html` for the full list. In short: the core dataset, measurement foundation, HubSpot integration, Sample Kit Builder, and Room Visualizer are done. The HubSpot↔Salesforce reconciliation and the Lifecycle Pulse skill are the newest pieces — check `analysis/crm-reconciliation/README.md` and `.claude/skills/lifecycle-pulse/README.md` for their own status.
