from __future__ import annotations

"""Conservative final typography/alignment pass for Results slides only.

The deck stays fully editable. This script changes native text formatting and
paragraph alignment only; it never rasterizes charts, tables, shapes or text.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import re
import sys
import xml.etree.ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

RESULT_SLIDES = {54, 55, 56, 58, 59}
TITLE_STARTS = {
    54: ("Development Ablation",),
    55: ("Ablation Trend",),
    56: ("Ablation Study",),
    58: ("Development Accuracy",),
    59: ("Final Official Comparison",),
}
OFFICIAL_VALUES = {
    "19.718", "22.999", "28.418", "33.017", "32.716", "40.021",
    "1238", "994", "44.181", "37.686",
}


def q(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def shape_text(shape: ET.Element) -> str:
    return " ".join((n.text or "") for n in shape.findall(".//a:t", NS)).strip()


def is_title(text: str, slide_no: int) -> bool:
    return any(text.startswith(prefix) for prefix in TITLE_STARTS.get(slide_no, ()))


def is_short_label(text: str) -> bool:
    t = text.strip()
    if len(t) > 34:
        return False
    if re.fullmatch(r"[A-Za-z0-9 .+%/()_\-–—]+", t) is None:
        return False
    return bool(re.search(r"\d", t) or t.startswith(("A0", "A1", "A2", "A3", "MOTA", "IDF1", "FPS", "HOTA", "IDS")))


def target_size(text: str, slide_no: int, title: bool) -> int:
    # DrawingML font size is hundredths of a point.
    if title:
        return 2600
    if slide_no == 59 and any(v in text for v in OFFICIAL_VALUES):
        return 1500
    if is_short_label(text):
        return 1400
    n = len(text)
    if n <= 55:
        return 1450
    if n <= 110:
        return 1300
    return 1200


def ensure_autofit(shape: ET.Element, font_scale: str = "96000") -> None:
    tx_body = shape.find("a:txBody", NS)
    if tx_body is None:
        return
    body_pr = tx_body.find("a:bodyPr", NS)
    if body_pr is None:
        return
    body_pr.set("wrap", "square")
    # Small balanced internal margins: enough breathing room without wasting space.
    for attr in ("lIns", "rIns", "tIns", "bIns"):
        body_pr.set(attr, "60960")
    for name in ("noAutofit", "spAutoFit", "normAutofit"):
        node = body_pr.find(f"a:{name}", NS)
        if node is not None:
            body_pr.remove(node)
    fit = ET.SubElement(body_pr, q("a", "normAutofit"))
    fit.set("fontScale", font_scale)
    fit.set("lnSpcReduction", "3000")


def patch_shape(shape: ET.Element, slide_no: int) -> None:
    text = shape_text(shape)
    if not text:
        return
    title = is_title(text, slide_no)
    size = target_size(text, slide_no, title)

    # Keep titles stable; apply autofit to body/callout blocks only.
    if not title:
        ensure_autofit(shape, "97000" if len(text) < 110 else "94000")

    for rpr in (
        shape.findall(".//a:rPr", NS)
        + shape.findall(".//a:defRPr", NS)
        + shape.findall(".//a:endParaRPr", NS)
    ):
        current = rpr.get("sz")
        # Normalize Results typography without creating giant or microscopic runs.
        if current is None or not current.isdigit() or int(current) > 2200 or int(current) < 1100:
            rpr.set("sz", str(size))
        elif title:
            rpr.set("sz", str(size))
        elif slide_no == 59 and any(v in text for v in OFFICIAL_VALUES):
            rpr.set("sz", str(size))
            rpr.set("b", "1")

    # Numeric/chart-associated labels read more naturally when centered in their boxes.
    if is_short_label(text) or (slide_no == 59 and any(v in text for v in OFFICIAL_VALUES)):
        for ppr in shape.findall(".//a:pPr", NS):
            ppr.set("algn", "ctr")


def patch_slide(xml_bytes: bytes, slide_no: int) -> bytes:
    root = ET.fromstring(xml_bytes)
    for shape in root.findall(".//p:sp", NS):
        patch_shape(shape, slide_no)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def apply(pptx_path: Path) -> None:
    if not pptx_path.exists():
        raise FileNotFoundError(pptx_path)

    with ZipFile(pptx_path, "r") as src:
        with NamedTemporaryFile(
            prefix=pptx_path.stem + "_finalpolish_",
            suffix=".pptx",
            dir=pptx_path.parent,
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with ZipFile(tmp_path, "w", compression=ZIP_DEFLATED) as dst:
                for info in src.infolist():
                    payload = src.read(info.filename)
                    m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", info.filename)
                    if m and int(m.group(1)) in RESULT_SLIDES:
                        payload = patch_slide(payload, int(m.group(1)))
                    dst.writestr(info, payload)
            tmp_path.replace(pptx_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    print("Applied final Results-slide typography/alignment pass (slides 54,55,56,58,59).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/final_polish_xml.py <pptx>")
    apply(Path(sys.argv[1]).resolve())
