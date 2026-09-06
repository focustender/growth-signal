"""
Perspective texture-mapping visualizer prototype.

Answers the scoping question directly: this needs no paid image-generation
model or API. It's a classic homography (perspective-warp) compositing
technique -- the same category RoomVo/Cylindo use -- built with Pillow's
native PERSPECTIVE transform plus a small numpy linear solve for the
coefficients. Accurate to the real tile texture rather than an AI-imagined
approximation.

The room scene and tile texture here are procedurally drawn (not downloaded
product/stock photography) specifically to sidestep any rights ambiguity in
a job-application work sample. Swapping in a real Fireclay product photo
crop and a real room photo is a drop-in replacement -- see the README in
this directory for exactly what changes.
"""

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

OUT_DIR = Path(__file__).parent
ROOM_SIZE = (1200, 900)


def find_coeffs(source_coords, target_coords):
    """Solve for the 8 PIL PERSPECTIVE coefficients mapping target_coords
    (the quad in the destination canvas) back to source_coords (the tile
    texture's own corners), per the standard Pillow perspective recipe."""
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0] * t[0], -s[0] * t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1] * t[0], -s[1] * t[1]])
    A = np.array(matrix, dtype=float)
    B = np.array(source_coords, dtype=float).reshape(8)
    res = np.linalg.solve(A, B)
    return tuple(res)


def make_room_scene():
    """A simple stylized kitchen scene: wall, countertop, and a backsplash
    quad drawn with a slight perspective skew, so the warp has to do real
    work rather than mapping onto an already-rectangular region."""
    img = Image.new("RGB", ROOM_SIZE, "#e7e3d8")
    draw = ImageDraw.Draw(img)

    # wall gradient
    for y in range(ROOM_SIZE[1]):
        shade = 235 - int(18 * (y / ROOM_SIZE[1]))
        draw.line([(0, y), (ROOM_SIZE[0], y)], fill=(shade, shade - 4, shade - 12))

    # a pair of upper cabinet doors with visible seam, panel line, and pulls
    cab_y0, cab_y1 = 30, 262
    cab_x0, cab_x1 = 30, ROOM_SIZE[0] - 320
    draw.rectangle([cab_x0, cab_y0, cab_x1, cab_y1], fill="#f2efe6", outline="#b9b3a0", width=3)
    mid_x = (cab_x0 + cab_x1) // 2
    for lx, rx in [(cab_x0 + 14, mid_x - 8), (mid_x + 8, cab_x1 - 14)]:
        draw.rectangle([lx, cab_y0 + 14, rx, cab_y1 - 14], outline="#b9b3a0", width=2)
        draw.rectangle([lx + 18, cab_y0 + 24, rx - 18, cab_y1 - 24], outline="#cfc9b8", width=1)
        draw.rectangle([rx - 10, (cab_y0 + cab_y1) // 2 - 22, rx - 6, (cab_y0 + cab_y1) // 2 + 22],
                        fill="#8a8371")

    # a simple window to the right, breaking up the wall
    win_x0, win_y0, win_x1, win_y1 = ROOM_SIZE[0] - 280, 30, ROOM_SIZE[0] - 30, 262
    draw.rectangle([win_x0, win_y0, win_x1, win_y1], fill="#bcd4d8", outline="#8a8371", width=6)
    draw.line([(win_x0, (win_y0 + win_y1) // 2), (win_x1, (win_y0 + win_y1) // 2)], fill="#8a8371", width=4)
    draw.line([((win_x0 + win_x1) // 2, win_y0), ((win_x0 + win_x1) // 2, win_y1)], fill="#8a8371", width=4)

    # countertop (bottom), drawn with a slight perspective tilt and a
    # faint stone-like mottling rather than flat black
    counter_top_left = (0, 650)
    counter_top_right = (ROOM_SIZE[0], 600)
    counter = Image.new("RGB", ROOM_SIZE, "#2f2b28")
    counter_noise = Image.effect_noise(ROOM_SIZE, 10).convert("L").point(lambda p: 235 + p // 6)
    counter = ImageChops.multiply(counter, Image.merge("RGB", [counter_noise] * 3))
    counter_mask = Image.new("L", ROOM_SIZE, 0)
    ImageDraw.Draw(counter_mask).polygon(
        [counter_top_left, counter_top_right, (ROOM_SIZE[0], ROOM_SIZE[1]), (0, ROOM_SIZE[1])],
        fill=255,
    )
    img.paste(counter, (0, 0), counter_mask)
    draw.line([counter_top_left, counter_top_right], fill="#e8e3d5", width=3)
    draw.line([(counter_top_left[0], counter_top_left[1] + 4), (counter_top_right[0], counter_top_right[1] + 4)],
               fill="#1c1a18", width=4)

    # backsplash quad: between cabinet bottom (y=260) and countertop line,
    # narrower at the top than the bottom to imply camera angle
    quad = [
        (110, 262),                # top-left
        (ROOM_SIZE[0] - 90, 262),  # top-right
        (ROOM_SIZE[0], 598),       # bottom-right (follows countertop tilt)
        (0, 648),                  # bottom-left
    ]
    img.save(OUT_DIR / "assets" / "room_before.png")
    return img, quad


def make_tile_texture(name="seaglass", size=1400, brick=(220, 74), grout=6):
    """A tileable subway-brick pattern in a Fireclay-style glaze colorway.
    Large enough to cover the backsplash quad after warping."""
    palette = {
        "seaglass": ("#4f7b72", "#dfe7e2"),
        "sable": ("#5c4c3d", "#e6ded3"),
        "champagne": ("#c7ab72", "#efe6d2"),
    }
    tile_color, grout_color = palette.get(name, palette["seaglass"])

    img = Image.new("RGB", (size, size), grout_color)
    draw = ImageDraw.Draw(img)
    bw, bh = brick
    row = 0
    y = 0
    while y < size:
        offset = (bw // 2) if row % 2 else 0
        x = -offset
        while x < size:
            draw.rectangle(
                [x + grout, y + grout, x + bw - grout, y + bh - grout],
                fill=tile_color,
            )
            x += bw
        y += bh
        row += 1

    # subtle per-brick shading for a hand-glazed look
    noise = Image.effect_noise((size, size), 18).convert("L")
    tinted = Image.merge("RGB", [
        ImageChops.multiply(img.split()[i], noise.point(lambda p: 200 + p // 4))
        for i in range(3)
    ])
    tinted.save(OUT_DIR / "assets" / f"tile_texture_{name}.png")
    return tinted


def composite(room_img, quad, tile_img):
    tw, th = tile_img.size
    source_corners = [(0, 0), (tw, 0), (tw, th), (0, th)]
    coeffs = find_coeffs(source_corners, quad)

    warped = tile_img.transform(ROOM_SIZE, Image.PERSPECTIVE, coeffs, resample=Image.BICUBIC)

    mask = Image.new("L", ROOM_SIZE, 0)
    ImageDraw.Draw(mask).polygon(quad, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1))

    # borrow the original wall's local shading so the composited tile
    # picks up the same soft light gradient instead of looking pasted-on
    shading = room_img.convert("L").filter(ImageFilter.GaussianBlur(30))
    shading = shading.point(lambda p: 160 + p // 3)
    shaded_tile = ImageChops.multiply(warped, Image.merge("RGB", [shading] * 3))

    result = room_img.copy()
    result.paste(shaded_tile, (0, 0), mask)
    return result


def main():
    (OUT_DIR / "assets").mkdir(exist_ok=True)
    room, quad = make_room_scene()
    for colorway in ("seaglass", "sable", "champagne"):
        tile = make_tile_texture(colorway)
        result = composite(room, quad, tile)
        result.save(OUT_DIR / "assets" / f"visualizer_after_{colorway}.png")
        print(f"Saved assets/visualizer_after_{colorway}.png")
    print("Saved assets/room_before.png")


if __name__ == "__main__":
    main()
