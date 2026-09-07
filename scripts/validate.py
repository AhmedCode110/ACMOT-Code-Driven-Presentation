from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import sys



ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from content.slides import SLIDES

OUTPUT = ROOT / "output" / "presentation_editable.pptx"


def main() -> None:
    ids = list(SLIDES)
    problems = []
    if len(ids) != len(set(ids)):
        problems.append("Duplicate slide IDs")
    if sorted(ids) != list(range(1, len(ids) + 1)):
        problems.append("Slide IDs are not contiguous")
    for sid, slide in SLIDES.items():
        if not slide.get("title"):
            problems.append(f"Slide {sid} has no title")
    if not OUTPUT.exists():
        problems.append(f"Missing output: {OUTPUT}")
    else:
        with ZipFile(OUTPUT) as zf:
            ppt_slides = [n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        if len(ppt_slides) != len(SLIDES):
            problems.append(f"Output slide count {len(ppt_slides)} != expected {len(SLIDES)}")
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        raise SystemExit(1)
    print(f"OK: {len(SLIDES)} slides, assets present, output exists")


if __name__ == "__main__":
    main()
