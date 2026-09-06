# Visualizer no-follow-up nurture — email copy

**Trigger**: `visualizer_use` event with no `sample_request` event in the following 3 days.
**Send time**: Day 3, 10am recipient local time (avoids the immediate-bounce feel of a same-day send while staying close enough that the visitor still remembers the session).
**Personalization tokens**: `{{first_name}}`, `{{collection_viewed}}`, `{{visualizer_image_url}}` (the actual composited image from that visitor's session), `{{segment}}` (used only to select the subject line variant below, not shown to the recipient).

---

**Subject (homeowner/designer):** Still thinking about {{collection_viewed}}?

**Subject (trade/commercial):** Your {{collection_viewed}} mockup, saved

---

Hi {{first_name}},

You put {{collection_viewed}} up in a room a few days ago — here's what it looked like:

[{{visualizer_image_url}}]

A sample tells you more than a screen ever will: the exact glaze depth, the weight of it in your hand, how the light actually catches the surface. If {{collection_viewed}} is still in the running, your next step is a physical sample, not another photo.

**[Request your {{collection_viewed}} sample →]**

Most people who visualize a tile and then request a sample end up ordering something close to what they first pictured — so this isn't about starting over, just holding the real thing.

—The Fireclay Team

---

## Why this copy, specifically

- It doesn't ask "are you still interested" as an open question — it reintroduces the exact visual the person generated, which is the one thing a generic re-engagement email can't do without the visualizer data behind it.
- It makes an explicit, honest case for *why* the next step is a sample rather than just repeating a CTA — matches the JD's "without compromising judgment, data privacy, or the customer experience" standard: this isn't a pressure send, it's answering the real gap between a screen render and a physical material.
- Trade/commercial subject line is deliberately more utilitarian ("saved," not "thinking about") — the tone shift matches the segment's professional register in a way a single generic template can't.
- No fabricated urgency or scarcity language. The claim in the last line ("end up ordering something close to what they first pictured") should be validated against real visualizer-to-purchase-SKU-match data before shipping — flagged here explicitly rather than stated as fact, since this dataset doesn't yet track which SKU visitors ultimately purchase.
