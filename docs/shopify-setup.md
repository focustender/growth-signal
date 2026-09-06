# Shopify Development Store — configuration log

Store: `fireclaytile-project.myshopify.com` (Shopify Plus App Development plan — a dev store, not a live storefront). Connected via Claude's Shopify connector, configured through GraphQL and the built-in product/collection/discount tools.

## Products (7)

All draft status, tagged by material line, priced as illustrative sample pricing:

| Product | Type | Price | SKU | Tags |
|---|---|---|---|---|
| Original Ceramic — Aegean | Tile Sample | $4.00 | OC-AEGEAN-SAMPLE | original-ceramic, sample, aegean |
| Natural Press Ceramic — Oatmeal | Tile Sample | $4.00 | NP-OATMEAL-SAMPLE | natural-press, sample, oatmeal, companion |
| Grout — Alabaster | Grout Sample | $2.00 | GROUT-ALABASTER-SAMPLE | grout, sample, alabaster, companion |
| Glass — Seaglass | Tile Sample | $5.00 | GL-SEAGLASS-SAMPLE | glass, sample, seaglass |
| Natural Press Ceramic — Sable | Tile Sample | $4.00 | NP-SABLE-SAMPLE | natural-press, sample, sable |
| Glass — Champagne | Tile Sample | $5.00 | GL-CHAMPAGNE-SAMPLE | glass, sample, champagne |
| Thin Brick — Weathered White | Tile Sample | $4.00 | TB-WEATHEREDWHITE-SAMPLE | thin-brick, sample, weathered-white |

No product images — deliberately, since Shopify's create-product tool requires publicly hosted HTTPS image URLs and this project avoided downloading Fireclay's real product photography for rights reasons (see `visualizer/README.md` for the same reasoning applied there). Swapping in real photography before any actual submission/demo is a drop-in change, not a rework.

## Collections (5)

- **All Tile Samples** (manual) — all 7 products, mirroring the real site's `/collections/all-tile-samples` naming found during research.
- **Original Ceramic**, **Natural Press Ceramic**, **Glass**, **Thin Brick** (smart, filtered by tag) — mirrors the real site's material-based navigation.

## Metafield: the actual Sample Kit Builder mechanism

- Definition: `custom.companion_samples` (`list.product_reference`, owner type PRODUCT) — "Samples most often specified alongside this one, used to power the Sample Kit Builder recommendation."
- Value set on **Original Ceramic — Aegean**: `[Natural Press Ceramic — Oatmeal, Grout — Alabaster]`.

This is the real backend mechanism the Sample Kit Builder design (`design/sample-kit-builder.html`) depicts — a theme section on the product or account page reading this metafield to render the companion suggestion, rather than a hardcoded recommendation.

## Discount: TRADE-SAMPLES

15% off the entire "All Tile Samples" collection, no minimum. Scoped to all customers for now — this dev store has no synced trade customer segment yet (trade accounts currently exist only in the HubSpot side of this project, not as tagged Shopify customers). In production this would scope to a "Trade" customer segment/tag synced from HubSpot rather than all customers; noted here rather than left unstated.

## Theme port: Sample Kit Builder as a real section

The store's only theme was Shopify's newer "Horizon" theme (a flexible block-based architecture, distinct from classic Online Store 2.0 sections) and was the published/MAIN theme — live theme file writes are blocked by the connector on the MAIN theme by design. Duplicated it to an unpublished theme (`Trade Signal — Sample Kit Builder (dev)`, id `148365705269`) to get a safe target for writes.

Built `sections/sample-kit-builder.liquid` as a standalone classic section rather than adopting Horizon's full proprietary block system — a scoping decision made deliberately given the time available, not an oversight. It:

- Reads `product.metafields.custom.companion_samples` (the real metafield configured above) and renders each companion as a swatch + name + link, with a graceful fallback when a companion has no product image yet.
- Ships its own scoped `{% stylesheet %}` matching the established Trade Signal visual language (same CSS custom properties as the HTML mockups), so it reads as a coherent part of the same system rather than a bolted-on component.
- Exposes real theme-editor settings (eyebrow text, button labels, skip link) via `{% schema %}`, so a merchant can adjust copy without touching code.
- Includes a click handler for the "Add companion samples to kit" button with an explicit, honest stub: it logs the companion product IDs rather than fabricating a working Cart API call against variant IDs the template doesn't have resolved — a real implementation would resolve each companion's first available variant and POST to `/cart/add.js`.

Added to `templates/product.json` as a new top-level section (`sample_kit_builder`, positioned directly after `main`), not nested inside Horizon's block tree — sections and the product template's `order` array are the stable, well-documented surface; Horizon's internal block schema for its own sections is not.

**Live preview** (unpublished theme, requires an authenticated Shopify admin session in the browser to bypass the dev store's default storefront password):
`https://fireclaytile-project.myshopify.com/products/original-ceramic-aegean?preview_theme_id=148365705269`

## Not yet done

Navigation menu structure wasn't touched. The cart-add click handler is a stub, not a working add-to-cart call, for the reason stated above.
