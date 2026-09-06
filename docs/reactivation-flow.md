# Reactivation flow — Hypothesis 2, tested against the live system

The JD names "activation, education, nurture, reactivation" as the lifecycle side of the Trade Program — its own owned surface. `docs/measurement-foundation.md`'s experimentation backlog maps a real hypothesis onto reactivation specifically:

> **Trade Portal single-sample re-entry flow.** Hypothesis: a portal prompt shown when a trade account has exactly one sample on file and no activity in 21 days (the Sample Kit Builder) recovers a meaningful share of stalled leads without added sales-rep effort. Decision threshold: ≥5% of prompted accounts request a second sample within 30 days to justify keeping it live.

`analysis/experimentation/decision_memo.md` deliberately left this hypothesis unevaluated, since the prototype wasn't receiving real customer traffic — there was no usage data to check a threshold against. This doc is that follow-up, not a fabricated completion rate: rather than invent a conversion number no real customer produced, this round tested whether the mechanism *itself* actually works, end to end, in the live system it depends on. It didn't, until today.

## What already existed

`shopify-theme/sections/sample-kit-builder.liquid` reads the live `custom.companion_samples` metafield (`docs/shopify-setup.md`) and renders the companion-sample recommendation — the merchandising half of the reactivation prompt. Its "Add companion samples to kit" button was a deliberate, documented stub: a `console.log` of the companion product IDs, with a comment explaining a real implementation would need to resolve variant IDs and call the Cart API.

## What live testing against the real store found

Querying the three companion products' real inventory state (`OC-AEGEAN-SAMPLE`, `NP-OATMEAL-SAMPLE`, `GROUT-ALABASTER-SAMPLE`) turned up a genuine data-quality gap that no design review would have caught by reading the Liquid file:

| Product | `inventoryPolicy` | Available (Shop location) |
|---|---|---|
| Original Ceramic — Aegean | DENY | 0 |
| Natural Press Ceramic — Oatmeal | DENY | 0 |
| Grout — Alabaster | DENY | 0 |

`DENY` plus zero stock means Shopify's real `/cart/add.js` rejects the add outright. **Had the cart-add button already been wired up as originally stubbed, the reactivation mechanism would have failed silently the exact moment a real trade lead tried to use it** — no error surfaced anywhere a merchandising or lifecycle owner would see it, because nothing was ever added to a cart to notice was missing. This is precisely the kind of systems-level gap between "the design looks right" and "the system actually works" that the JD's Technology-partnership language points at, just surfaced here in Shopify's own inventory model instead of the HubSpot↔Salesforce boundary.

## The fix — live

Restocked all three companion SKUs at the store's Shop location via the Shopify inventory API, confirmed by each call's response payload (not assumed from a success code):

| Product | Before | After | Verified via |
|---|---|---|---|
| Original Ceramic — Aegean | 0 | **25** | `quantityAfterChange: 25` |
| Natural Press Ceramic — Oatmeal | 0 | **25** | `quantityAfterChange: 25` |
| Grout — Alabaster | 0 | **25** | `quantityAfterChange: 25` |

25 units is a deliberate, small restock appropriate to a low-cost consumable sample SKU, not an attempt to make the numbers look bigger than the fix warrants.

## The fix — in code

`sample-kit-builder.liquid`'s button no longer just logs. It now:

- Resolves each companion's `selected_or_first_available_variant.id` **server-side, in Liquid** — the metafield's `product_reference` values already return full Product objects, so there's no client-side lookup or guessed ID.
- POSTs a real `items` array to `/cart/add.js`.
- Renders an honest result: success updates the button label and a status line with the real count added and dispatches a `cart:refresh` event; failure re-enables the button, shows the actual error text Shopify returned, and logs it to the console instead of failing silently.

## Status — real, written, and pending, stated plainly

- **Real and live:** the store connection, the inventory bug, and its fix — all confirmed against the actual Shopify dev store, not assumed.
- **Written and ready, not yet deployed:** the updated `sample-kit-builder.liquid` lives in this repo with the real Cart API integration, but pushing it to the live unpublished theme (`Trade Signal — Sample Kit Builder (dev)`, id `148365705269`) was blocked mid-session by this environment's own write-permission gate on theme-file mutations — not a Shopify-side limitation. Deploying it is a single `themeFilesUpsert` call against a file already committed here.
- **Still not measurable, on purpose:** Hypothesis 2's actual ≥5% threshold needs real trade accounts hitting a live, published section over a real 30-day window. Nothing in this project claims that number, because nothing here produced it yet.

## Why this, not a cleaner-sounding story

The easier write-up would have been "walked through the reactivation flow end to end, confirmed it works." That would have been true of the *design* and false of the *system* — the button would have failed on first real use. Finding that gap by actually querying live inventory state, instead of reading the Liquid file and calling it done, is the same discipline `analysis/experimentation/decision_memo.md` applied to Hypothesis 1: a real, checkable fact changing the plan is worth more than a deliverable that merely looks finished.
