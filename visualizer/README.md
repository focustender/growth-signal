# AI Room Visualizer — perspective texture-mapping prototype

## What this is and isn't

This demonstrates the actual mechanism a tile-in-room visualizer needs: **perspective texture-mapping (homography)**, not generative image synthesis. Run `python3 texture_map.py` to regenerate `assets/room_before.png` and three `assets/visualizer_after_*.png` colorway variants.

No paid image-generation model or API is used, and none is needed. The whole thing is Pillow's native `Image.transform(..., Image.PERSPECTIVE, ...)` plus an 8-coefficient linear solve (`find_coeffs` in `texture_map.py`) computed with numpy — the same category of technique RoomVo and Cylindo use in production. Given a tile texture and the four corners of a target wall/floor region in a photo, it warps the texture to match that region's perspective exactly, rather than asking a diffusion model to *imagine* a plausible tile.

The room scene and tile texture here are drawn procedurally in code, not downloaded product or stock photography — a deliberate choice to keep this work sample free of any rights ambiguity. The result is intentionally illustrative rather than photorealistic; it's built to prove the mechanism, not to ship as a finished consumer feature.

## What swapping in real photography looks like

Two lines change, nothing else:

1. Replace `make_room_scene()`'s output with a real room photo, and replace the four hardcoded `quad` corner coordinates with the actual pixel coordinates of the wall/floor region in that photo (found manually by eye, or automatically via a segmentation model if this became a real product feature — Adobe's Firefly-based `image_select_subject` tool, already available in this environment, could locate that region for you rather than needing manual coordinates for every new room photo).
2. Replace `make_tile_texture()`'s procedural pattern with a cropped, de-perspectived photo of the actual SKU (a straight-on product shot, which Fireclay already has for every collection).

The warp math (`find_coeffs` + `composite()`) doesn't change at all — it works identically on any input image.

## How this connects to the lifecycle side

Every visualizer session is a funnel event (`visualizer_use` in the Trade Signal dataset — see `../data/generate_dataset.py`). The measurement foundation (`../docs/measurement-foundation.md`) shows 32–64% of visualizer users across segments don't request a sample within 14 days. The intended trigger: a visualizer session with no follow-up sample request within 3 days fires an AI-personalized nurture email referencing the specific tile/room the visitor viewed — built once a HubSpot connection exists, using the same session data this script already produces (colorway + a saved copy of the composited image as the email's hero visual).
