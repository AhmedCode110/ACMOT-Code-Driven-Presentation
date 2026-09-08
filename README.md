# AC-MOT — Code-Driven Presentation (V7)

Production-quality Master's defense deck for the AC-MOT paper.  
Branch: **acmot-paper-realtime-v7**

## Authoritative output

```
output/ACMOT_Final_Paper_Realtime_v7.pptx   (~57 MB, 67 slides)
```

## Architecture overview

```
config/
    __init__.py
    metrics.py      ← SINGLE SOURCE OF TRUTH for all research numbers
    typography.py   ← semantic text roles (TITLE, BODY, CARD_TITLE, …)
    paths.py        ← canonical file paths for build scripts

content/
    slides.py       ← slide metadata (titles, text, background image)
    overrides.py    ← text replacements applied over the source reference
    final_polish.py ← results-section polish overrides

theme/
    constants.py    ← layout tokens (margins, font sizes, color palette)
    components.py   ← reusable shape builders
    layouts.py      ← slide-level layout helpers

scripts/
    build_final_mac.sh      ← one-command Mac build entry point
    build_v7_from_source.py ← direct XML build (no Codex runtime required)
    validate.py             ← comprehensive A–J validation
    verify_final_pptx.py    ← quick final-PPTX check (size, video, metrics)
    embed_video_v7.py       ← embeds MP4 into the PPTX package
    v7_targeted_fixes.py    ← slide 55 A1 label; slide 59 frame; font pass
    xml_apply_overrides.py  ← typography/autofit/chart XML pass
    final_polish_xml.py     ← results-slides XML polish pass

reference/
    original_presentation.pptx   ← accepted V5 editable source (DO NOT MODIFY)

assets/
    images/     ← slide background PNGs
    videos/     ← evidence MP4 (uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4)
```

## Requirements

```
Python 3.9+
python-pptx   (pip install python-pptx)
```

No other non-standard packages are needed for the direct build or validation.

The full Codex pipeline (`python3 build.py`) additionally requires the Codex
Node.js runtime and `@oai/artifact-tool`.  If that runtime is unavailable use
`build_v7_from_source.py` instead.

---

## Build commands

### Mac — recommended one-command build

```bash
./scripts/build_final_mac.sh
```

This script:
1. Detects whether the Codex Node.js runtime is available and falls back to the direct build automatically.
2. Embeds the evidence video.
3. Applies V7 targeted XML fixes (A1/30.1 FPS label, font normalisation, slide 59 frame).
4. Runs comprehensive A–J validation.
5. Reports the final PPTX path and size.

**Keynote** round-trip is disabled by default (AppleScript has historically produced
`-1708 / -1700 / -1728 / -1712` errors).  Enable it with `KEYNOTE=1`:

```bash
KEYNOTE=1 ./scripts/build_final_mac.sh
```

### Direct build (no Codex runtime — Claude Code, CI, clean Mac)

```bash
python3 scripts/build_v7_from_source.py
```

Applies all patches directly to `reference/original_presentation.pptx` and
produces the final PPTX in one step.

### Full Codex pipeline (when Codex runtime is available)

```bash
python3 build.py
```

---

## Validation

```bash
python3 scripts/validate.py                            # auto-detects final PPTX
python3 scripts/validate.py output/ACMOT_Final_Paper_Realtime_v7.pptx
```

Checks A–J:

| Check | What it verifies |
|-------|-----------------|
| A | PPTX package is a valid ZIP with required members |
| B | Exactly 67 slides |
| C | Slide 59 contains all 10 official final metric values |
| D | Historical development-ablation values absent from Slide 59 |
| E | MP4 video file embedded in `ppt/media/` |
| F | Slide 59 has a valid video relationship in `_rels` |
| G | Slide 59 contains a `<p:pic>` / `<a:videoFile>` video object |
| H | Slide 55 contains the A1 system label and 30.1 FPS value |
| I | Source `content/slides.py` has exactly 67 non-duplicate entries |
| J | Slide IDs are contiguous (1–67) |

```bash
python3 scripts/verify_final_pptx.py output/ACMOT_Final_Paper_Realtime_v7.pptx
```

Quick check: size, slide count, Slide 59 metrics, embedded video.

---

## Where things live

| What | Where |
|------|-------|
| Official final metrics (MOTA, HOTA, IDF1, IDS, FPS) | `config/metrics.py → OFFICIAL_RESULTS` |
| Development ablation values (A0–A3) | `config/metrics.py → ABLATION` |
| Semantic typography roles | `config/typography.py` |
| Canonical file paths | `config/paths.py` |
| Layout margins / spacing tokens | `theme/constants.py` |
| Slide titles and text content | `content/slides.py` |
| Text replacements applied at build time | `content/overrides.py`, `content/final_polish.py` |
| Evidence video | `assets/videos/uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4` |
| Source reference deck | `reference/original_presentation.pptx` |

---

## How to edit individual slides

1. Open `content/slides.py` — find the slide entry (keyed by slide number).
2. Edit `title` or `text` fields.
3. If the edit is a **metric value**, change it in `config/metrics.py` first and update the slide text to reference the derived constant.
4. Rebuild: `python3 scripts/build_v7_from_source.py`
5. Validate: `python3 scripts/validate.py`

---

## How to change a metric value

1. Edit `config/metrics.py` — update `OFFICIAL_RESULTS["baseline"]["mota"]` (or whichever field).
2. Update any human-readable strings in `content/slides.py` that reference that metric.
3. Rebuild and validate as above.
4. The validator (check C) will confirm the new value is present on Slide 59.

---

## How to replace the evidence video

1. Copy the new MP4 to `assets/videos/`.
2. Update `EVIDENCE_VIDEO` in `config/paths.py` to point to the new file name.
3. Run `python3 scripts/build_v7_from_source.py` — the new video is embedded automatically.
4. Validate.

---

## How to modify a chart

Charts in the source reference deck are native PPTX chart objects.  To change
chart data:

1. Open `reference/original_presentation.pptx` in PowerPoint or Keynote.
2. Edit the chart.
3. Save as the same filename.
4. Rebuild with `python3 scripts/build_v7_from_source.py`.

Chart labels that appear as separate text shapes (e.g. the bar values on Slide 55)
are controlled by `scripts/v7_targeted_fixes.py`.

---

## How to add a new slide safely

1. Copy an existing `SLIDES[N]` entry in `content/slides.py` to `SLIDES[68]` (or next available number).
2. Provide a background image at `assets/images/slide_68.png`.
3. Add a text override in `content/overrides.py` if required.
4. Update `EXPECTED_SLIDE_COUNT` in `config/paths.py` from 67 to 68.
5. Rebuild and validate.

---

## Local Mac path

```
/Users/ahmedgouda/CLAUDECODEX/Master/macneo_wrk/09_Presentation/ACMOT-Code-Driven-Presentation
```

---

## Known limitations

- The full Codex pipeline (`python3 build.py`) requires the Codex Node.js runtime and is not available in Claude Code or a clean environment.  Use `build_v7_from_source.py` instead.
- Keynote AppleScript automation is fragile on macOS; it is optional and disabled by default.
- Font rendering differences between PowerPoint on Windows/Mac and Keynote may cause minor reflowing on slides with dense text.
- The direct build (`build_v7_from_source.py`) preserves all native chart objects from the source reference.  Complex chart data changes require editing the source reference in PowerPoint first.
