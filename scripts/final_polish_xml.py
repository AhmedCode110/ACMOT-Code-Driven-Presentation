from __future__ import annotations

"""Conservative final typography/alignment pass for Results slides only.

The deck stays fully editable. This script changes native text/chart formatting
only; it never rasterizes charts, tables, shapes or text. It also normalizes
chart typography on the Results slides so labels remain readable after import
into Keynote/PowerPoint.
"""

from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import re
import sys
import xml.etree.ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
for prefix in ("a", "p", "c", "r"):
    ET.register_namespace(prefix, NS[prefix])

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

# Consistent visual hierarchy for the Results section.
TITLE_PT100 = 2600
BODY_PT100 = 1300
CALLOUT_PT100 = 1400
OFFICIAL_PT100 = 1500
CHART_PT100 = 1300
FONT_FACE = "Helvetica Neue"


def q(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def shape_text(shape: ET.Element) -> str:
    return " ".join((n.text or "") for n in shape.findall(".//a:t", NS)).strip()


def is_title(text: str, slide_no: int) -> bool:
    return any(text.startswith(prefix) for prefix in TITLE_STARTS.get(slide_no, ()))


def is_short_label(text: str) -> bool:
    t = text.strip()
    if len(t) > 38:
        return False
    if re.fullmatch(r"[A-Za-z0-9 .+%/()_\-–—:]+", t) is None:
        return False
    return bool(re.search(r"\d", t) or t.startswith(("A0", "A1", "A2", "A3", "MOTA", "IDF1", "FPS", "HOTA", "IDS")))


def target_size(text: str, slide_no: int, title: bool) -> int:
    if title:
        return TITLE_PT100
    if slide_no == 59 and any(v in text for v in OFFICIAL_VALUES):
        return OFFICIAL_PT100
    if is_short_label(text):
        return CALLOUT_PT100
    return BODY_PT100


def set_typeface(rpr: ET.Element) -> None:
    latin = rpr.find("a:latin", NS)
    if latin is None:
        latin = ET.SubElement(rpr, q("a", "latin"))
    latin.set("typeface", FONT_FACE)


def ensure_autofit(shape: ET.Element, font_scale: str = "96000") -> None:
    tx_body = shape.find("a:txBody", NS)
    if tx_body is None:
        return
    body_pr = tx_body.find("a:bodyPr", NS)
    if body_pr is None:
        return
    body_pr.set("wrap", "square")
    # Balanced internal margins: text stays visibly inside its block.
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

    if not title:
        # Longer text gets slightly more room to shrink, but never becomes tiny.
        ensure_autofit(shape, "97000" if len(text) < 110 else "93000")

    # Force a consistent Results typography hierarchy rather than preserving
    # accidental mixed sizes from the source/reference deck.
    for rpr in (
        shape.findall(".//a:rPr", NS)
        + shape.findall(".//a:defRPr", NS)
        + shape.findall(".//a:endParaRPr", NS)
    ):
        rpr.set("sz", str(size))
        set_typeface(rpr)
        if title:
            rpr.set("b", "1")
        elif slide_no == 59 and any(v in text for v in OFFICIAL_VALUES):
            rpr.set("b", "1")

    # Numeric/chart-associated labels and official comparison rows belong to
    # their blocks visually, so center them. Long explanatory body stays left.
    if is_short_label(text) or (slide_no == 59 and any(v in text for v in OFFICIAL_VALUES)):
        for ppr in shape.findall(".//a:pPr", NS):
            ppr.set("algn", "ctr")


def patch_slide(xml_bytes: bytes, slide_no: int) -> bytes:
    root = ET.fromstring(xml_bytes)
    for shape in root.findall(".//p:sp", NS):
        patch_shape(shape, slide_no)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def chart_paths_for_slide(entries: dict[str, bytes], slide_no: int) -> set[str]:
    rel_name = f"ppt/slides/_rels/slide{slide_no}.xml.rels"
    payload = entries.get(rel_name)
    if payload is None:
        return set()
    root = ET.fromstring(payload)
    out: set[str] = set()
    base = PurePosixPath("ppt/slides")
    for rel in root.findall(f".//{{{NS['pr']}}}Relationship"):
        rel_type = rel.get("Type", "")
        target = rel.get("Target", "")
        if not rel_type.endswith("/chart") or not target:
            continue
        # Targets are normally ../charts/chartN.xml from ppt/slides.
        parts: list[str] = []
        for part in (base / target).parts:
            if part == "..":
                if parts:
                    parts.pop()
            elif part != ".":
                parts.append(part)
        out.add("/".join(parts))
    return out


def patch_chart(xml_bytes: bytes) -> bytes:
    root = ET.fromstring(xml_bytes)

    # Normalize every chart text run/default style to a readable 13 pt.
    for rpr in (
        root.findall(".//a:rPr", NS)
        + root.findall(".//a:defRPr", NS)
        + root.findall(".//a:endParaRPr", NS)
    ):
        rpr.set("sz", str(CHART_PT100))
        set_typeface(rpr)

    # Make chart titles a little stronger while keeping plot labels compact.
    for title in root.findall(".//c:title", NS):
        for rpr in (
            title.findall(".//a:rPr", NS)
            + title.findall(".//a:defRPr", NS)
            + title.findall(".//a:endParaRPr", NS)
        ):
            rpr.set("sz", "1500")
            rpr.set("b", "1")
            set_typeface(rpr)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def apply(pptx_path: Path) -> None:
    if not pptx_path.exists():
        raise FileNotFoundError(pptx_path)

    with ZipFile(pptx_path, "r") as src:
        infos = src.infolist()
        entries = {info.filename: src.read(info.filename) for info in infos}

    result_chart_paths: set[str] = set()
    for slide_no in RESULT_SLIDES:
        result_chart_paths |= chart_paths_for_slide(entries, slide_no)

    with NamedTemporaryFile(
        prefix=pptx_path.stem + "_finalpolish_",
        suffix=".pptx",
        dir=pptx_path.parent,
        delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with ZipFile(tmp_path, "w", compression=ZIP_DEFLATED) as dst:
            for info in infos:
                payload = entries[info.filename]
                m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", info.filename)
                if m and int(m.group(1)) in RESULT_SLIDES:
                    payload = patch_slide(payload, int(m.group(1)))
                elif info.filename in result_chart_paths:
                    payload = patch_chart(payload)
                dst.writestr(info, payload)
        tmp_path.replace(pptx_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    print(
        "Applied final Results typography/alignment pass "
        "(slides 54,55,56,58,59) plus chart-text normalization."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/final_polish_xml.py <pptx>")
    apply(Path(sys.argv[1]).resolve())
