# AC-MOT Code-Driven Presentation

This project builds the existing AC-MOT PowerPoint from the original editable source while keeping native PowerPoint objects editable.

The original deck stays unchanged at:

`reference/original_presentation.pptx`

The final generated deck is:

`output/ACMOT_Final_Paper_Realtime_v2.pptx`

The project metadata contains exactly 67 slides. The build keeps the original design/content structure, applies the focused paper/realtime text overrides, runs the presentation finalizer, then applies a conservative editable-PPTX typography/layout pass and validates the resulting package.

## Local macOS rebuild

Use branch:

`acmot-paper-realtime-v2`

From the repository root run:

```bash
python3 build.py
```

`build.py` automatically:

1. resolves the local Codex Node/runtime paths (environment overrides are supported),
2. backs up an existing generated PPTX under `.build/backups/`,
3. imports `reference/original_presentation.pptx`,
4. applies `content/overrides.py`,
5. exports/finalizes the editable PPTX,
6. runs `scripts/xml_apply_overrides.py` for conservative typography/autofit/chart-readability fixes,
7. runs `scripts/validate.py`.

You can rerun validation independently with:

```bash
python3 scripts/validate.py
```

Successful validation checks that the PPTX package is readable, contains exactly 67 slides, and that slide 59 contains the official comparison values `19.718`, `22.999`, `28.418`, and `33.017`.

## Optional presentation video

For a local demo video, place the compact H.264 MP4 at:

`assets/videos/uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4`

Keep it inside the repository if a later build step is asked to embed it into the PPTX. The current build does not automatically add or remove slides for the video.

## Structure

- `content/slides.py` contains stable slide metadata extracted from the source deck.
- `SLIDE_INDEX.md` maps slide number to slide type and source key.
- `theme/constants.py` contains shared visual settings.
- `theme/layouts.py` and `theme/components.py` contain reusable layout helpers.
- `content/overrides.py` contains focused text edits applied on top of the editable source deck.
- `assets/images/` contains visual reference images per original slide for comparison only.
- `scripts/build_deck.mjs` performs the editable Artifact Tool import/export/finalization.
- `scripts/xml_apply_overrides.py` performs conservative package-level formatting fixes without flattening slides.
- `scripts/validate.py` validates the final generated PPTX.
- `scripts/extract_from_pptx.py` regenerates slide content metadata from the archived source PPTX.

## Instructions for AI/Codex

- Read `SLIDE_INDEX.md` first.
- Preserve unrelated slides exactly.
- Do not flatten slides into images.
- Do not change research metrics or the Results sequence unless explicitly requested.
- Keep modifications minimal and editable.
- Regenerate and validate the presentation after source changes.
