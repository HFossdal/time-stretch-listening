#!/usr/bin/env python3
"""
Build a single self-contained index.html that lets people browse and compare
the rendered listening examples from the thesis.

Usage:
    python generate_site.py [AUDIO_DIR]

AUDIO_DIR defaults to "audio". It is the directory that *contains* the
per-example subfolders, e.g.

    audio/
        SPEECH_idx0_1.00x_controlled_inpainting/
            00_original_clip.wav
            01_interpolation_baseline_bigvgan.wav
            Full-skip_2D_U-Net.wav
            ...
        MUSIC_idx2_stretch_0.50x/
            ...

The script writes index.html in the current working directory, with audio
paths relative to AUDIO_DIR, so it works both locally and on GitHub Pages.
"""

import html
import re
import sys
from pathlib import Path

AUDIO_EXTS = {".wav", ".flac", ".mp3", ".ogg", ".m4a"}

# Preferred display order + friendly labels for known method filenames.
# Matching is done on the lowercased filename stem; first match wins.
METHOD_RULES = [
    (r"original",                       ("Original / reference", 0, "ref")),
    (r"interpolation|interp|baseline",  ("Linear interpolation + BigVGAN", 1, "ref")),
    (r"full.?skip|u.?net",              ("Full-skip 2D U-Net + BigVGAN", 2, "model")),
    (r"complex.?stft|crn",              ("Complex-STFT CRN + inverse STFT", 3, "model")),
    (r"alpha.?1[._]?0",                 ("Residual-mined adapter (\u03b1 = 1.0)", 4, "model")),
    (r"alpha.?1[._]?5",                 ("Residual-mined adapter (\u03b1 = 1.5)", 5, "model")),
    (r"alpha.?2[._]?0",                 ("Residual-mined adapter (\u03b1 = 2.0)", 6, "model")),
]

CASE_ORDER = ["controlled", "stretch075", "stretch050"]
CASE_LABELS = {
    "controlled": "Controlled 1\u00d7 inpainting",
    "stretch075": "Stretch 0.75\u00d7",
    "stretch050": "Stretch 0.50\u00d7",
}


def label_for(stem: str):
    """Return (label, sort_order, kind) for an audio file stem."""
    s = stem.lower()
    for pattern, (label, order, kind) in METHOD_RULES:
        if re.search(pattern, s):
            return label, order, kind
    pretty = re.sub(r"^[0-9]+[_\-\s]*", "", stem)      # drop leading "01_"
    pretty = pretty.replace("_", " ").replace("-", " ").strip()
    return (pretty or stem), 99, "model"


def parse_folder(name: str):
    """Parse a folder name like 'SPEECH_idx4_1.00x_controlled_inpainting'."""
    upper = name.upper()
    domain = "Speech" if upper.startswith("SPEECH") else "Music" if upper.startswith("MUSIC") else "Other"

    idx_match = re.search(r"idx(\d+)", name, re.IGNORECASE)
    idx = idx_match.group(1) if idx_match else None

    if re.search(r"controlled|inpaint|1\.?00x", name, re.IGNORECASE):
        case_key = "controlled"
    elif re.search(r"0\.?75", name):
        case_key = "stretch075"
    elif re.search(r"0\.?50|0\.?5x", name):
        case_key = "stretch050"
    else:
        case_key = "other"
    case_label = CASE_LABELS.get(case_key, name)
    return domain, idx, case_key, case_label


def collect(audio_dir: Path):
    examples = []
    for folder in sorted(p for p in audio_dir.iterdir() if p.is_dir()):
        clips = sorted(
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in AUDIO_EXTS
        )
        if not clips:
            continue
        domain, idx, case_key, case_label = parse_folder(folder.name)
        tracks = []
        for clip in clips:
            label, order, kind = label_for(clip.stem)
            rel = f"{audio_dir.name}/{folder.name}/{clip.name}"
            tracks.append((order, label, kind, rel))
        tracks.sort(key=lambda t: (t[0], t[1]))
        examples.append({
            "folder": folder.name, "domain": domain, "idx": idx,
            "case_key": case_key, "case_label": case_label, "tracks": tracks,
        })
    return examples


def render_example(ex):
    dom = ex["domain"].lower()
    idx_txt = f"idx{ex['idx']}" if ex["idx"] else ""
    eyebrow = " \u00b7 ".join(filter(None, [ex["domain"], idx_txt]))
    rows = []
    for _order, label, kind, rel in ex["tracks"]:
        rows.append(
            f'            <tr class="m m--{kind}">'
            f'<th scope="row">{html.escape(label)}</th>'
            f'<td><audio controls preload="none" src="{html.escape(rel)}"></audio></td></tr>'
        )
    rows_html = "\n".join(rows)
    return f"""        <div class="ex" data-domain="{dom}">
          <p class="ex__id">{html.escape(eyebrow)}</p>
          <table class="ex__tbl">
            <tbody>
{rows_html}
            </tbody>
          </table>
        </div>"""


def render_section(case_key, case_label, examples):
    blocks = "\n".join(render_example(e) for e in examples)
    return f"""      <section class="case" id="{case_key}" data-case="{case_key}">
        <h2>{html.escape(case_label)}</h2>
        <div class="examples">
{blocks}
        </div>
      </section>"""


def build_html(examples, audio_dir_name):
    n = len(examples)
    n_speech = sum(1 for e in examples if e["domain"] == "Speech")
    n_music = sum(1 for e in examples if e["domain"] == "Music")

    present = [c for c in CASE_ORDER if any(e["case_key"] == c for e in examples)]
    present += sorted({e["case_key"] for e in examples} - set(CASE_ORDER))

    sections = []
    nav_links = []
    for ck in present:
        label = CASE_LABELS.get(ck, ck)
        group = [e for e in examples if e["case_key"] == ck]
        group.sort(key=lambda e: (e["domain"], int(e["idx"]) if e["idx"] else 0))
        sections.append(render_section(ck, label, group))
        nav_links.append(f'<a href="#{ck}">{html.escape(label)}</a>')
    sections_html = "\n".join(sections)
    nav_html = "\n        ".join(nav_links)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Listening examples \u2014 Neural Refinement of Time-Frequency Representations for Audio Time-Stretching</title>
<style>
  :root {{
    --paper: #fcfcf9;
    --ink: #1c1b19;
    --muted: #67635c;
    --faint: #908b82;
    --rule: #e6e3db;
    --rule-strong: #d2cec3;
    --accent: #00509e;
    --accent-ink: #003a73;
    --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    margin: 0; background: var(--paper); color: var(--ink);
    font-family: var(--serif); line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 28px; }}

  header.site {{ padding: 72px 0 26px; border-bottom: 1px solid var(--rule-strong); }}
  .kicker {{
    font-family: var(--mono); font-size: 11.5px; letter-spacing: 0.15em;
    text-transform: uppercase; color: var(--accent-ink); margin: 0 0 18px;
  }}
  h1 {{
    font-family: var(--serif); font-weight: 600;
    font-size: clamp(25px, 3.6vw, 37px); line-height: 1.16;
    letter-spacing: 0.002em; margin: 0 0 18px; max-width: 24ch;
  }}
  .affil {{ font-family: var(--sans); font-size: 14px; color: var(--muted); margin: 0 0 4px; }}
  .affil b {{ color: var(--ink); font-weight: 600; }}
  .count {{ font-family: var(--mono); font-size: 12px; color: var(--faint); margin: 14px 0 0; }}
  .caption {{ font-style: italic; color: var(--muted); font-size: 15.5px; margin: 22px 0 0; max-width: 68ch; }}

  .toolbar {{
    position: sticky; top: 0; z-index: 5;
    background: var(--paper); border-bottom: 1px solid var(--rule);
    padding: 12px 0;
  }}
  .toolbar .wrap {{ display: flex; flex-wrap: wrap; gap: 14px 28px; align-items: center; }}
  .jump {{ font-family: var(--sans); font-size: 13px; color: var(--muted); display: flex; gap: 16px; flex-wrap: wrap; align-items: baseline; }}
  .jump a {{ color: var(--accent-ink); text-decoration: none; border-bottom: 1px solid transparent; }}
  .jump a:hover {{ border-bottom-color: var(--accent-ink); }}
  .seg {{ display: flex; align-items: center; gap: 8px; margin-left: auto; }}
  .seg .seg__label {{ font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--faint); }}
  .seg button {{
    font-family: var(--sans); font-size: 13px; color: var(--muted);
    background: none; border: 1px solid var(--rule-strong); border-radius: 3px;
    padding: 4px 12px; cursor: pointer; transition: all .12s ease;
  }}
  .seg button:hover {{ color: var(--ink); border-color: var(--faint); }}
  .seg button[aria-pressed="true"] {{ color: #fff; background: var(--accent); border-color: var(--accent); }}
  :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}

  main {{ padding: 8px 0 40px; }}
  section.case {{ padding-top: 44px; }}
  section.case > h2 {{
    font-family: var(--serif); font-weight: 600; font-size: 22px;
    margin: 0 0 4px; padding-bottom: 9px; border-bottom: 1px solid var(--rule-strong);
  }}
  .examples {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
    gap: 30px 44px; margin-top: 26px;
  }}
  .ex__id {{
    font-family: var(--mono); font-size: 11px; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--faint); margin: 0 0 10px;
  }}
  table.ex__tbl {{ width: 100%; border-collapse: collapse; }}
  .ex__tbl th {{
    font-family: var(--sans); font-weight: 400; font-size: 13.5px;
    text-align: left; color: var(--ink); vertical-align: middle;
    padding: 9px 16px 9px 0; white-space: nowrap; width: 1%;
  }}
  .ex__tbl td {{ padding: 9px 0; vertical-align: middle; }}
  .ex__tbl tr + tr th, .ex__tbl tr + tr td {{ border-top: 1px solid var(--rule); }}
  .m--ref th {{ color: var(--muted); font-style: italic; }}
  audio {{ width: 100%; min-width: 230px; height: 32px; }}

  .empty {{ font-family: var(--mono); font-size: 13px; color: var(--faint); padding: 50px 0; }}

  footer.site {{
    border-top: 1px solid var(--rule-strong); margin-top: 56px;
    padding: 28px 0 72px; font-family: var(--sans); font-size: 13px; color: var(--muted);
  }}
  .foot-cite {{ font-family: var(--serif); color: var(--ink); font-size: 14.5px; margin: 0 0 10px; max-width: 80ch; line-height: 1.5; }}
  .foot-src {{ margin: 0; max-width: 80ch; line-height: 1.6; }}

  @media (max-width: 540px) {{
    .ex__tbl th {{ display: block; white-space: normal; width: auto; padding: 10px 0 4px; }}
    .ex__tbl td {{ display: block; padding: 0 0 4px; }}
    .ex__tbl tr + tr th {{ border-top: 1px solid var(--rule); margin-top: 4px; }}
    .ex__tbl tr + tr td {{ border-top: 0; }}
    .seg {{ margin-left: 0; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    html {{ scroll-behavior: auto; }}
    * {{ transition: none !important; }}
  }}
</style>
</head>
<body>
<header class="site">
  <div class="wrap">
    <p class="kicker">Supplementary listening material</p>
    <h1>Neural Refinement of Time-Frequency Representations for Audio Time-Stretching</h1>
    <p class="affil"><b>H&aring;vard Fossdal</b> &nbsp;\u00b7&nbsp; Supervisor: Erlend Aune &nbsp;\u00b7&nbsp; Co-supervisor: Daesoo Lee</p>
    <p class="affil">TMA4900 Master Thesis &nbsp;\u00b7&nbsp; Department of Mathematical Sciences, NTNU &nbsp;\u00b7&nbsp; June 2026</p>
    <p class="count">{n} examples &nbsp;\u00b7&nbsp; {n_speech} speech &nbsp;\u00b7&nbsp; {n_music} music</p>
    <p class="caption">Diagnostic, side-by-side listening evidence. A formal listener study is left
      as future work.</p>
  </div>
</header>

<nav class="toolbar">
  <div class="wrap">
    <div class="jump">
      <span>Jump to</span>
        {nav_html}
    </div>
    <div class="seg" id="domain-filter">
      <span class="seg__label">Domain</span>
      <button data-value="all" aria-pressed="true">All</button>
      <button data-value="speech" aria-pressed="false">Speech</button>
      <button data-value="music" aria-pressed="false">Music</button>
    </div>
  </div>
</nav>

<main>
  <div class="wrap">
{sections_html}
    <p class="empty" id="empty" hidden>No examples match this filter.</p>
  </div>
</main>

<footer class="site">
  <div class="wrap">
    <p class="foot-cite">Fossdal, H. (2026). <em>Neural Refinement of Time-Frequency Representations
      for Audio Time-Stretching</em>. Master thesis, TMA4900, Department of Mathematical Sciences,
      Norwegian University of Science and Technology (NTNU).</p>
    <p class="foot-src">Speech material from EARS, LibriTTS, and VCTK. Music material from
      MUSDB18-HQ. Waveforms reconstructed with BigVGAN for the mel-domain routes and with inverse
      STFT for the complex-STFT route.</p>
  </div>
</footer>

<script>
  let domain = "all";
  const examples = Array.from(document.querySelectorAll(".ex"));
  const sections = Array.from(document.querySelectorAll("section.case"));
  const empty = document.getElementById("empty");

  function apply() {{
    let shown = 0;
    examples.forEach(ex => {{
      const ok = domain === "all" || ex.dataset.domain === domain;
      ex.style.display = ok ? "" : "none";
      if (ok) shown++;
    }});
    sections.forEach(sec => {{
      const any = sec.querySelectorAll('.ex:not([style*="display: none"])').length > 0;
      sec.style.display = any ? "" : "none";
    }});
    empty.hidden = shown !== 0;
  }}

  document.querySelectorAll("#domain-filter button").forEach(btn => {{
    btn.addEventListener("click", () => {{
      domain = btn.dataset.value;
      document.querySelectorAll("#domain-filter button")
        .forEach(b => b.setAttribute("aria-pressed", b === btn ? "true" : "false"));
      apply();
    }});
  }});

  document.querySelectorAll("audio").forEach(a => {{
    a.addEventListener("play", () => {{
      document.querySelectorAll("audio").forEach(o => {{ if (o !== a) o.pause(); }});
    }});
  }});
</script>
</body>
</html>
"""


def main():
    audio_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "audio")
    if not audio_dir.is_dir():
        sys.exit(f"Audio directory not found: {audio_dir}\n"
                 f"Run: python generate_site.py <folder-containing-the-subfolders>")
    examples = collect(audio_dir)
    if not examples:
        sys.exit(f"No audio files found under {audio_dir}/*/")
    Path("index.html").write_text(build_html(examples, audio_dir.name), encoding="utf-8")
    print(f"Wrote index.html with {len(examples)} examples "
          f"({sum(len(e['tracks']) for e in examples)} clips).")


if __name__ == "__main__":
    main()
