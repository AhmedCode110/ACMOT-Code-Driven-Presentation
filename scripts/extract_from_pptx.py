from __future__ import annotations

import ast
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reference" / "original_presentation.pptx"
SLIDES_OUT = ROOT / "content" / "slides.py"
INDEX_OUT = ROOT / "SLIDE_INDEX.md"
IMAGE_DIR = ROOT / "assets" / "images"

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def natural_slide_paths(zf: zipfile.ZipFile) -> list[str]:
    paths = [name for name in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name)]
    return sorted(paths, key=lambda p: int(re.search(r"slide(\d+)\.xml", p).group(1)))


def text_runs(xml: bytes) -> list[str]:
    root = ET.fromstring(xml)
    lines = []
    for shape in root.findall(".//p:sp", NS):
        pieces = []
        for text in shape.findall(".//a:t", NS):
            if text.text:
                pieces.append(text.text)
        line = " ".join(piece.strip() for piece in pieces if piece.strip())
        if line:
            lines.append(line)
    return lines


def slide_type(number: int, title: str, lines: list[str]) -> str:
    title_l = title.lower()
    joined = " ".join(lines).lower()
    if number == 1:
        return "title_slide"
    if "section" in title_l or re.fullmatch(r"\d+", title.strip() or ""):
        return "section_slide"
    if any(term in joined for term in ["mota", "idf1", "hota", "fps", "ids"]):
        return "results_slide"
    if any(term in title_l for term in ["comparison", "ablation", "baseline", "results"]):
        return "comparison_slide"
    return "image_backed"


def py_literal(value):
    return ast.literal_eval(repr(value))


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(IMAGE_DIR)

    slides = {}
    with zipfile.ZipFile(SOURCE) as zf:
        for number, slide_path in enumerate(natural_slide_paths(zf), start=1):
            lines = text_runs(zf.read(slide_path))
            title = lines[0] if lines else f"Slide {number}"
            image = f"assets/images/slide_{number:02d}.png"
            slides[number] = {
                "id": number,
                "type": slide_type(number, title, lines),
                "title": title,
                "text": lines[1:],
                "background_image": image,
                "source_slide_xml": slide_path,
            }

    SLIDES_OUT.write_text(
        "# Generated from reference/original_presentation.pptx.\n"
        "# Edit one slide entry at a time for low-token slide updates.\n\n"
        "SLIDES = "
        + repr(slides)
        + "\n",
        encoding="utf-8",
    )

    rows = ["slide number | slide type | short title | source file/key"]
    for number, slide in slides.items():
        title = slide["title"].replace("|", "/").strip()
        if len(title) > 72:
            title = title[:69].rstrip() + "..."
        rows.append(f"{number:02d} | {slide['type']} | {title} | content/slides.py:{number}")
    INDEX_OUT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Extracted {len(slides)} slides")


if __name__ == "__main__":
    main()
