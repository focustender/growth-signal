# Fireclay Tile brand foundations — extraction and decisions

Real values pulled directly from fireclaytile.com's live CSS custom properties (curl + grep against the actual stylesheet and inline `:root` blocks, not estimated from screenshots or guessed).

## Colors (real, sourced)

| Token | Hex | Source CSS variable |
|---|---|---|
| Accent | `#6E2F1B` | `--accent` / `--button-background-primary` |
| Text | `#1A1A1A` | `--text-primary` |
| Background | `#FFFFFF` | `--background-primary` |
| Background (dark) | `#312A29` | dark-section `--background` variant |
| Button secondary | `#D5CDBB` | `--button-background-secondary` |
| Border | Text at 12% opacity | `--border-color: var(--text-primary) / 0.12` |

## Spacing (real, sourced)

Their own CSS comment says it directly: "a spacing inspired from frameworks like Tailwind CSS" — a rem-based scale from `--spacing-0-5` (2px) to `--spacing-96` (384px), including half-steps up through `--spacing-9-5` that go beyond stock Tailwind. The named, actually-referenced tokens (not just the raw scale) are more useful than the full list:

| Token | Value | Used for |
|---|---|---|
| `--input-gap` | `--spacing-2` (8px) | gap inside form inputs |
| `--container-gutter` / `--grid-gutter` | `--spacing-5` (20px) | side padding, grid gaps |
| `--section-stack-spacing-block` / `--product-list-row-gap` | `--spacing-8` (32px) | space between stacked sections |
| `--section-inner-max-spacing-block` | `--spacing-9` (36px) | internal section padding |
| `--section-outer-spacing-block` | `--spacing-10` (40px) | space around a full section |
| `--container-max-width` | 1640px (1390px narrow variant) | overall content width |

**Type scale correction**: the Figma file originally used invented sizes (48/28/16px) for the specimen text styles. Fireclay's real scale is `--text-h0: 44px`, `--text-h1: 32px`, `--text-h2: 28px`, `--text-h3: 22px`, `--text-h4/h5: 18px`, `--text-h6: 16px`, and — worth noting specifically — **base body text is 14px**, not the more common 16px default. The Figma file's text styles have been corrected to match (display 44px, heading 28px, body 14px).

## Fonts

The live site renders **"Playwright Display"** (headings) and **"MuseoSans 300/700"** (body) — both commercial fonts self-hosted through a paid Fontify app, not available on Google Fonts and not something I can license or verify on your behalf.

**Decision (confirmed with the user, 2026-09-04): use Playfair Display (headings) and Mulish (body) as the working substitutes** for the Figma design work and any prototype builds. These aren't an arbitrary guess — they're the theme's own declared *fallback* fonts, present in Fireclay's base CSS before the Fontify override, and a live screenshot comparison confirmed a close visual match (see the Figma file's own typography section for the side-by-side).

If pixel-accurate final production matters later, the real fonts (Museo Sans, Playwright Display) would need to be licensed separately — flagged here so the substitution is never mistaken for the genuine brand asset.

## Where this lives

`https://www.figma.com/design/2JqexYCjK4sWUCdPYJ06YS` ("Fireclay Tile — Brand Foundations") — color variables, text styles, a swatch/type specimen reference. Deliberately no page layouts; storefront screen design is a separate, user-driven task from here.
