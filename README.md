# AC-MOT Code-Driven Presentation

This project converts the existing AC-MOT PowerPoint into a compact, token-efficient source tree.

The original deck stays unchanged at:

`reference/original_presentation.pptx`

The generated editable deck is:

`output/presentation_editable.pptx`

Validation on 2026-09-07 found 67 slides with native editable content:
700 text boxes, 732 shapes, 13 tables, and 48 images. Render check produced
67 non-blank slide previews.

## Rebuild

Run:

```bash
python build.py
```

Then validate:

```bash
python scripts/validate.py
```

## Structure

- `content/slides.py` contains stable slide entries.
- `SLIDE_INDEX.md` maps slide number to slide type and source key.
- `theme/constants.py` contains shared visual settings.
- `theme/layouts.py` and `theme/components.py` contain reusable layout helpers.
- `content/overrides.py` contains optional small code edits applied on top of the editable source deck.
- `assets/images/` contains visual reference images per original slide for comparison only.
- `scripts/extract_from_pptx.py` regenerates slide content metadata from the archived source PPTX.

## Instructions for AI/Codex

- Read `SLIDE_INDEX.md` first.
- Do not inspect the whole repository for a slide-specific edit.
- Open only the target slide entry and the required layout/component.
- Preserve unrelated slides exactly.
- Do not refactor unrelated code during small edits.
- Regenerate the presentation after changes.
- Validate that the generated PPTX opens successfully.
- Keep modifications minimal.

## First-Pass Limitation

This project now builds from the original editable PPTX instead of flattening slides to images. Existing text boxes, shapes, tables, images, masters, and themes remain editable in the generated deck where the original PPTX exposed them as editable objects.

For a future slide edit, add a focused override in `content/overrides.py` or edit the relevant source content file. This keeps small changes cheap while preserving the full editable deck.
