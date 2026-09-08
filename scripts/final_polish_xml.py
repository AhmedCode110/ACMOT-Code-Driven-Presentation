from __future__ import annotations

"""V3 typography/layout cleanup.

Goals:
- keep the existing visual direction and native editability;
- normalize the font family across the whole deck;
- enforce a clear title/body hierarchy on Results slides;
- keep Results text inside its blocks with native autofit;
- make chart text readable and show numeric data labels on slides 55, 56 and 58.
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
DATA_LABEL_SLIDES = {55, 56, 58}
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

FONT_FACE = "Helvetica Neue"
TITLE_PT100 = 2600
BODY_PT100 = 1300
CALLOUT_PT100 = 1400
OFFICIAL_PT100 = 1500
CHART_PT100 = 1200
CHART_TITLE_PT100 = 1500


def q(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def shape_text(shape: ET.Element) -> str:
    return " ".join((n.text or "") for n in shape.findall(".//a:t", NS)).strip()


def set_typeface(rpr: ET.Element) -> None:
    latin = rpr.find("a:latin", NS)
    if latin is None:
        latin = ET.SubElement(rpr, q("a", "latin"))
    latin.set("typeface", FONT_FACE)


def normalize_font_family(root: ET.Element) -> None:
    for rpr in (
        root.findall(".//a:rPr", NS)
        + root.findall(".//a:defRPr", NS)
        + root.findall(".//a:endParaRPr", NS)
    ):
        set_typeface(rpr)


def is_title(text: str, slide_no: int) -> bool:
    return any(text.startswith(prefix) for prefix in TITLE_STARTS.get(slide_no, ()))


def is_short_label(text: str) -> bool:
    t = text.strip()
    if len(t) > 42:
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


def ensure_autofit(shape: ET.Element, font_scale: str) -> None:
    tx_body = shape.find("a:txBody", NS)
    if tx_body is None:
        return
    body_pr = tx_body.find("a:bodyPr", NS)
    if body_pr is None:
        return
    body_pr.set("wrap", "square")
    # Safe insets keep text visually inside cards/blocks.
    body_pr.set("lIns", "76200")
    body_pr.set("rIns", "76200")
    body_pr.set("tIns", "50800")
    body_pr.set("bIns", "50800")
    for name in ("noAutofit", "spAutoFit", "normAutofit"):
        node = body_pr.find(f"a:{name}", NS)
        if node is not None:
            body_pr.remove(node)
    fit = ET.SubElement(body_pr, q("a", "normAutofit"))
    fit.set("fontScale", font_scale)
    fit.set("lnSpcReduction", "5000")


def patch_result_shape(shape: ET.Element, slide_no: int) -> None:
    text = shape_text(shape)
    if not text:
        return

    title = is_title(text, slide_no)
    size = target_size(text, slide_no, title)

    if not title:
        if len(text) > 180:
            scale = "86000"
        elif len(text) > 110:
            scale = "90000"
        else:
            scale = "95000"
        ensure_autofit(shape, scale)

    for rpr in (
        shape.findall(".//a:rPr", NS)
        + shape.findall(".//a:defRPr", NS)
        + shape.findall(".//a:endParaRPr", NS)
    ):
        rpr.set("sz", str(size))
        set_typeface(rpr)
        if title or (slide_no == 59 and any(v in text for v in OFFICIAL_VALUES)):
            rpr.set("b", "1")

    if is_short_label(text) or (slide_no == 59 and any(v in text for v in OFFICIAL_VALUES)):
        for ppr in shape.findall(".//a:pPr", NS):
            ppr.set("algn", "ctr")


def patch_slide(xml_bytes: bytes, slide_no: int) -> bytes:
    root = ET.fromstring(xml_bytes)
    normalize_font_family(root)
    if slide_no in RESULT_SLIDES:
        for shape in root.findall(".//p:sp", NS):
            patch_result_shape(shape, slide_no)
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
        if not rel.get("Type", "").endswith("/chart"):
            continue
        target = rel.get("Target", "")
        if not target:
            continue
        parts: list[str] = []
        for part in (base / target).parts:
            if part == "..":
                if parts:
                    parts.pop()
            elif part != ".":
                parts.append(part)
        out.add("/".join(parts))
    return out


def bool_node(parent: ET.Element, name: str, value: str) -> ET.Element:
    node = parent.find(f"c:{name}", NS)
    if node is None:
        node = ET.SubElement(parent, q("c", name))
    node.set("val", value)
    return node


def ensure_series_data_labels(root: ET.Element) -> None:
    # Explicit numeric values on the plot solve the "chart exists but its text is missing" issue.
    for ser in root.findall(".//c:ser", NS):
        d_lbls = ser.find("c:dLbls", NS)
        if d_lbls is None:
            d_lbls = ET.Element(q("c", "dLbls"))
            children = list(ser)
            insert_at = len(children)
            for i, child in enumerate(children):
                if child.tag in {q("c", "trendline"), q("c", "errBars"), q("c", "cat"), q("c", "val"), q("c", "xVal"), q("c", "yVal")}:
                    insert_at = i
                    break
            ser.insert(insert_at, d_lbls)
        bool_node(d_lbls, "showLegendKey", "0")
        bool_node(d_lbls, "showVal", "1")
        bool_node(d_lbls, "showCatName", "0")
        bool_node(d_lbls, "showSerName", "0")
        bool_node(d_lbls, "showPercent", "0")
        bool_node(d_lbls, "showLeaderLines", "0")


def patch_chart(xml_bytes: bytes, show_values: bool) -> bytes:
    root = ET.fromstring(xml_bytes)
    normalize_font_family(root)

    for rpr in (
        root.findall(".//a:rPr", NS)
        + root.findall(".//a:defRPr", NS)
        + root.findall(".//a:endParaRPr", NS)
    ):
        rpr.set("sz", str(CHART_PT100))
        set_typeface(rpr)

    for title in root.findall(".//c:title", NS):
        for rpr in (
            title.findall(".//a:rPr", NS)
            + title.findall(".//a:defRPr", NS)
            + title.findall(".//a:endParaRPr", NS)
        ):
            rpr.set("sz", str(CHART_TITLE_PT100))
            rpr.set("b", "1")
            set_typeface(rpr)

    if show_values:
        ensure_series_data_labels(root)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def apply(pptx_path: Path) -> None:
    if not pptx_path.exists():
        raise FileNotFoundError(pptx_path)

    with ZipFile(pptx_path, "r") as src:
        infos = src.infolist()
        entries = {info.filename: src.read(info.filename) for info in infos}

    chart_to_slide: dict[str, int] = {}
    for slide_no in RESULT_SLIDES:
        for path in chart_paths_for_slide(entries, slide_no):
            chart_to_slide[path] = slide_no

    with NamedTemporaryFile(
        prefix=pptx_path.stem + "_v3polish_",
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
                if m:
                    payload = patch_slide(payload, int(m.group(1)))
                elif info.filename in chart_to_slide:
                    slide_no = chart_to_slide[info.filename]
                    payload = patch_chart(payload, slide_no in DATA_LABEL_SLIDES)
                dst.writestr(info, payload)
        tmp_path.replace(pptx_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    print(
        "Applied V3 polish: deck-wide Helvetica Neue, consistent Results hierarchy/autofit, "
        "and numeric chart labels on slides 55, 56 and 58."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/final_polish_xml.py <pptx>")
    apply(Path(sys.argv[1]).resolve())
