"""Builds design/visualizer-demo.html by embedding the generated room/tile
images as base64 JPEGs into a hand-authored template. Keeps the large
base64 payloads out of manually-edited files."""

import base64
import io
from pathlib import Path

from PIL import Image

VIS_DIR = Path(__file__).parent
OUT_PATH = VIS_DIR.parent / "design" / "visualizer-demo.html"

FILES = {
    "before": "assets/room_before.png",
    "seaglass": "assets/visualizer_after_seaglass.png",
    "sable": "assets/visualizer_after_sable.png",
    "champagne": "assets/visualizer_after_champagne.png",
}

images = {}
for key, path in FILES.items():
    img = Image.open(VIS_DIR / path).convert("RGB").resize((760, 570))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    images[key] = base64.b64encode(buf.getvalue()).decode()

TEMPLATE = """<title>Tile Room Visualizer</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Newsreader:ital,wght@1,500&display=swap">
<style>
  :root{{
    --ink:#211d1a; --paper:#edeee8; --paper-raised:#f6f6f1;
    --seaglass:#3f6f66; --seaglass-soft:#e2ebe8;
    --clay:#a15c3e; --clay-soft:#f3e4dc;
    --slate:#6b6862; --slate-soft:#dcdbd3;
    --moss:#5b7f3a; --moss-soft:#e6ecdc; --line:#c9c7bd;
  }}
  @media (prefers-color-scheme: dark){{
    :root:not([data-theme="light"]){{
      --ink:#ece9e2; --paper:#1a1815; --paper-raised:#242220;
      --seaglass:#7fada2; --seaglass-soft:#25332f;
      --clay:#d08e6d; --clay-soft:#3a2a22;
      --slate:#a5a196; --slate-soft:#332f29;
      --moss:#93b76e; --moss-soft:#2b3221; --line:#3a372f;
    }}
  }}
  :root[data-theme="dark"]{{
    --ink:#ece9e2; --paper:#1a1815; --paper-raised:#242220;
    --seaglass:#7fada2; --seaglass-soft:#25332f;
    --clay:#d08e6d; --clay-soft:#3a2a22;
    --slate:#a5a196; --slate-soft:#332f29;
    --moss:#93b76e; --moss-soft:#2b3221; --line:#3a372f;
  }}
  *{{box-sizing:border-box;}}
  body{{background:var(--paper); color:var(--ink); font-family:"IBM Plex Sans",system-ui,sans-serif; line-height:1.5; padding:0 0 4rem;}}
  .wrap{{max-width:900px; margin:0 auto; padding:0 1.5rem;}}
  header.top{{padding:2.75rem 0 2rem; border-bottom:1px solid var(--line);}}
  .eyebrow{{font-family:"IBM Plex Mono",monospace; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--slate);}}
  h1{{font-size:1.65rem; font-weight:600; margin:.5rem 0 0; text-wrap:balance;}}
  .subhead{{color:var(--slate); font-size:.95rem; margin-top:.6rem; max-width:62ch;}}
  .stage{{margin-top:2rem;}}
  .frame{{position:relative; border:1px solid var(--line); background:var(--paper-raised); overflow:hidden;}}
  .frame img{{display:block; width:100%; height:auto;}}
  .controls{{display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-top:1rem; flex-wrap:wrap;}}
  .toggle{{display:flex; gap:.4rem;}}
  .toggle button{{
    font-family:"IBM Plex Mono",monospace; font-size:.72rem; letter-spacing:.04em;
    padding:.5rem .9rem; background:var(--paper-raised); color:var(--ink);
    border:1px solid var(--line); cursor:pointer;
  }}
  .toggle button.active{{background:var(--seaglass); color:var(--paper-raised); border-color:var(--seaglass);}}
  .swatches{{display:flex; gap:.5rem;}}
  .swatches button{{
    width:1.8rem; height:1.8rem; border:2px solid transparent; cursor:pointer; padding:0;
  }}
  .swatches button.active{{border-color:var(--ink);}}
  .sw-seaglass{{background:linear-gradient(135deg,#7ea9a0,#4f7b72);}}
  .sw-sable{{background:linear-gradient(135deg,#8b7a68,#5c4c3d);}}
  .sw-champagne{{background:linear-gradient(135deg,#e4d3ab,#c7ab72);}}
  .caption{{font-family:"IBM Plex Mono",monospace; font-size:.72rem; color:var(--slate); margin-top:.75rem;}}
  .mechanism{{margin-top:2.5rem; padding-top:1.75rem; border-top:1px solid var(--line);}}
  .mechanism h2{{font-size:1rem; font-weight:600; margin-bottom:.75rem;}}
  .mechanism p{{font-size:.9rem; max-width:68ch; margin-bottom:.9rem;}}
  .mechanism code{{font-family:"IBM Plex Mono",monospace; background:var(--slate-soft); padding:.1rem .3rem; font-size:.85em;}}
  .callout{{
    margin-top:1rem; padding:1rem 1.1rem; background:var(--moss-soft);
    border-left:3px solid var(--moss); font-size:.85rem;
  }}
  footer.meta{{margin-top:2.5rem; padding-top:1.25rem; border-top:1px solid var(--line);
    font-family:"IBM Plex Mono",monospace; font-size:.7rem; color:var(--slate);}}
  figure{{margin:0;}}
  figcaption{{font-size:.78rem; color:var(--slate); margin-top:.5rem;}}
</style>

<div class="wrap">
  <header class="top">
    <div class="eyebrow">Trade Signal — Design Concept 02</div>
    <h1>Room visualizer: perspective texture-mapping, not generative AI</h1>
    <p class="subhead">Real tile texture warped onto the actual wall plane in a photo, accurate to the SKU — the same category of technique RoomVo and Cylindo use, built with no paid model.</p>
  </header>

  <div class="stage">
    <figure class="frame">
      <img id="stage-img" src="data:image/jpeg;base64,{before}" alt="Kitchen backsplash visualizer">
      <figcaption class="caption" id="stage-caption">Before — plain wall</figcaption>
    </figure>

    <div class="controls">
      <div class="toggle">
        <button data-state="before" class="active">Before</button>
        <button data-state="after">After</button>
      </div>
      <div class="swatches">
        <button class="sw-seaglass active" data-color="seaglass" title="Glass — Seaglass"></button>
        <button class="sw-sable" data-color="sable" title="Natural Press — Sable"></button>
        <button class="sw-champagne" data-color="champagne" title="Glass — Champagne"></button>
      </div>
    </div>
  </div>

  <div class="mechanism">
    <h2>How it works</h2>
    <p>Four corner points define the backsplash quad in the photo. <code>find_coeffs()</code> solves an 8-variable linear system (via a small numpy solve) for the perspective coefficients that map those four points back to the tile texture's own rectangular corners. Pillow's native <code>Image.transform(size, Image.PERSPECTIVE, coeffs)</code> then warps the full texture in one pass, a polygon mask constrains it to the quad, and the wall's own local shading is multiplied back in so the result doesn't look pasted on.</p>
    <p>Swapping in a real Fireclay product photo and a real customer-uploaded room photo changes exactly two inputs — the warp math is unchanged. See <code>visualizer/README.md</code> for the specific swap-in path, and <code>visualizer/texture_map.py</code> for the full implementation (about 130 lines, no OpenCV, no GPU).</p>
    <div class="callout">Feeds back into the lifecycle side: a visualizer session with no sample request in the next 3 days triggers an AI-personalized nurture email using the exact composited image the visitor generated — see <code>docs/visualizer-nurture-email.md</code>.</div>
  </div>

  <footer class="meta">
    Fireclay Tile — AI-First UI/UX Designer application · concept prototype, not affiliated with or endorsed by Fireclay Tile · procedurally generated room/tile assets, no product or stock photography used
  </footer>
</div>

<script>
  const IMAGES = {{
    before: "{before}",
    seaglass: "{seaglass}",
    sable: "{sable}",
    champagne: "{champagne}"
  }};
  let state = "before";
  let color = "seaglass";
  const img = document.getElementById("stage-img");
  const caption = document.getElementById("stage-caption");
  const names = {{
    seaglass: "Glass — Seaglass",
    sable: "Natural Press — Sable",
    champagne: "Glass — Champagne"
  }};

  function render() {{
    if (state === "before") {{
      img.src = "data:image/jpeg;base64," + IMAGES.before;
      caption.textContent = "Before — plain wall";
    }} else {{
      img.src = "data:image/jpeg;base64," + IMAGES[color];
      caption.textContent = "After — " + names[color] + ", perspective-mapped to the wall plane";
    }}
  }}

  document.querySelectorAll(".toggle button").forEach(btn => {{
    btn.addEventListener("click", () => {{
      state = btn.dataset.state;
      document.querySelectorAll(".toggle button").forEach(b => b.classList.toggle("active", b === btn));
      render();
    }});
  }});

  document.querySelectorAll(".swatches button").forEach(btn => {{
    btn.addEventListener("click", () => {{
      color = btn.dataset.color;
      document.querySelectorAll(".swatches button").forEach(b => b.classList.toggle("active", b === btn));
      if (state === "after") render();
    }});
  }});
</script>
"""

OUT_PATH.write_text(TEMPLATE.format(**images))
print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")
