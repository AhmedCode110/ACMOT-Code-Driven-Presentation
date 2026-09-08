from __future__ import annotations

"""AC-MOT v3 Results-section cleanup.

Goals:
- consistent Helvetica Neue hierarchy on slides 54-59;
- keep body text safely inside its native text boxes;
- make chart titles/axes/data labels visible after PowerPoint/Keynote import;
- keep everything editable (native OOXML only; no rasterization).
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
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
for prefix in ("a", "p", "c"):
    ET.register_namespace(prefix, NS[prefix])

TARGET_SLIDES = {54, 55, 56, 57, 58, 59}
TITLE_PREFIXES = {
    54: ("Development Ablation",),
    55: ("Ablation Trend",),
    56: ("Ablation Study",),
    57: ("Tracker", "ByteTrack"),
    58: ("Development Accuracy",),
    59: ("Final Official Comparison",),
}
OFFICIAL_VALUES = {
    "19.718", "22.999", "28.418", "33.017", "32.716", "40.021",
    "1238", "994", "44.181", "37.686",
}

FONT = "Helvetica Neue"
TEXT_HEX = "111827"
ACCENT_HEX = "2563EB"
TITLE_SZ = 2600
HEADER_SZ = 1500
BODY_SZ = 1300
OFFICIAL_SZ = 1550
CHART_TITLE_SZ = 1500
CHART_LABEL_SZ = 1300


def q(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def shape_text(shape: ET.Element) -> str:
    return " ".join((n.text or "") for n in shape.findall(".//a:t", NS)).strip()


def is_title(slide_no: int, text: str) -> bool:
    return any(text.startswith(p) for p in TITLE_PREFIXES.get(slide_no, ()))


def looks_like_header(text: str) -> bool:
    t = " ".join(text.split()).strip()
    if not t or len(t) > 70:
        return False
    upper = sum(ch.isupper() for ch in t if ch.isalpha())
    alpha = sum(ch.isalpha() for ch in t)
    if alpha and upper / alpha > 0.72:
        return True
    return bool(re.match(r"^(A[0-4]|MOTA|IDF1|HOTA\*?|IDS|FPS|BASELINE|AC-MOT)\b", t, re.I))


def set_font_and_fill(rpr: ET.Element, size: int, bold: bool = False, accent: bool = False) -> None:
    rpr.set("sz", str(size))
    rpr.set("b", "1" if bold else "0")
    latin = rpr.find("a:latin", NS)
    if latin is None:
        latin = ET.SubElement(rpr, q("a", "latin"))
    latin.set("typeface", FONT)

    for old in list(rpr):
        if old.tag in {q("a", "solidFill"), q("a", "gradFill"), q("a", "noFill")}:
            rpr.remove(old)
    fill = ET.SubElement(rpr, q("a", "solidFill"))
    color = ET.SubElement(fill, q("a", "srgbClr"))
    color.set("val", ACCENT_HEX if accent else TEXT_HEX)


def ensure_body_pr(shape: ET.Element, long_text: bool) -> None:
    tx_body = shape.find("a:txBody", NS)
    if tx_body is None:
        return
    body_pr = tx_body.find("a:bodyPr", NS)
    if body_pr is None:
        return
    body_pr.set("wrap", "square")
    # Keep text visibly inside the card/block.
    body_pr.set("lIns", "76200")
    body_pr.set("rIns", "76200")
    body_pr.set("tIns", "57150")
    body_pr.set("bIns", "57150")
    for name in ("noAutofit", "spAutoFit", "normAutofit"):
        node = body_pr.find(f"a:{name}", NS)
        if node is not None:
            body_pr.remove(node)
    fit = ET.SubElement(body_pr, q("a", "normAutofit"))
    fit.set("fontScale", "90000" if long_text else "96000")
    fit.set("lnSpcReduction", "5000" if long_text else "2500")


def patch_shape(shape: ET.Element, slide_no: int) -> None:
    text = shape_text(shape)
    if not text:
        return

    title = is_title(slide_no, text)
    official = slide_no == 59 and any(v in text for v in OFFICIAL_VALUES)
    header = looks_like_header(text)

    if title:
        size, bold, accent = TITLE_SZ, True, True
    elif official:
        size, bold, accent = OFFICIAL_SZ, True, False
    elif header:
        size, bold, accent = HEADER_SZ, True, False
    else:
        size, bold, accent = BODY_SZ, False, False

    if not title:
        ensure_body_pr(shape, len(text) > 115)

    run_nodes = (
        shape.findall(".//a:rPr", NS)
        + shape.findall(".//a:defRPr", NS)
        + shape.findall(".//a:endParaRPr", NS)
    )
    for rpr in run_nodes:
        set_font_and_fill(rpr, size=size, bold=bold, accent=accent)

    # Center short numeric callouts and the official comparison rows.
    if official or (header and len(text) < 45):
        for ppr in shape.findall(".//a:pPr", NS):
            ppr.set("algn", "ctr")


def patch_slide(payload: bytes, slide_no: int) -> bytes:
    root = ET.fromstring(payload)
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


def patch_chart(payload: bytes) -> bytes:
    root = ET.fromstring(payload)

    # PowerPoint/Keynote sometimes imports inherited chart text with an
    # invisible/incorrect theme color. Explicit dark text fixes missing labels.
    all_text = (
        root.findall(".//a:rPr", NS)
        + root.findall(".//a:defRPr", NS)
        + root.findall(".//a:endParaRPr", NS)
    )
    for rpr in all_text:
        set_font_and_fill(rpr, CHART_LABEL_SZ, bold=False, accent=False)

    for title in root.findall(".//c:title", NS):
        for rpr in (
            title.findall(".//a:rPr", NS)
            + title.findall(".//a:defRPr", NS)
            + title.findall(".//a:endParaRPr", NS)
        ):
            set_font_and_fill(rpr, CHART_TITLE_SZ, bold=True, accent=False)

    # Ensure axis text properties exist and are readable even when inherited
    # formatting is lost during Keynote import.
    for axis in root.findall(".//c:catAx", NS) + root.findall(".//c:valAx", NS):
        tx_pr = axis.find("c:txPr", NS)
        if tx_pr is None:
            tx_pr = ET.SubElement(axis, q("c", "txPr"))
            ET.SubElement(tx_pr, q("a", "bodyPr"))
            ET.SubElement(tx_pr, q("a", "lstStyle"))
            p = ET.SubElement(tx_pr, q("a", "p"))
            ppr = ET.SubElement(p, q("a", "pPr"))
            defr = ET.SubElement(ppr, q("a", "defRPr"))
            ET.SubElement(p, q("a", "endParaRPr"))
            set_font_and_fill(defr, CHART_LABEL_SZ)
        else:
            for rpr in tx_pr.findall(".//a:defRPr", NS) + tx_pr.findall(".//a:endParaRPr", NS):
                set_font_and_fill(rpr, CHART_LABEL_SZ)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def apply(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)

    with ZipFile(path, "r") as src:
        infos = src.infolist()
        entries = {i.filename: src.read(i.filename) for i in infos}

    chart_paths: set[str] = set()
    for slide_no in TARGET_SLIDES:
        chart_paths |= chart_paths_for_slide(entries, slide_no)

    with NamedTemporaryFile(prefix=path.stem + "_v3_", suffix=".pptx", dir=path.parent, delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with ZipFile(tmp_path, "w", compression=ZIP_DEFLATED) as dst:
            for info in infos:
                payload = entries[info.filename]
                m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", info.filename)
                if m and int(m.group(1)) in TARGET_SLIDES:
                    payload = patch_slide(payload, int(m.group(1)))
                elif info.filename in chart_paths:
                    payload = patch_chart(payload)
                dst.writestr(info, payload)
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    print("v3 Results polish applied: consistent headers/body, in-block autofit, and visible chart text on slides 54-59.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/v3_results_polish.py <pptx>")
    apply(Path(sys.argv[1]).resolve())
