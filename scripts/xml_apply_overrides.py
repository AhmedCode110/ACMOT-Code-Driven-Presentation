from __future__ import annotations

"""Small, package-level formatting pass for the generated editable PPTX.

The presentation is still built from the original editable source.  This script
only normalizes typography and applies conservative autofit/readability fixes to
known Results slides.  It does not rasterize slides, alter metrics, or replace
charts/tables/images.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import re
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from content.slides import SLIDES
from theme.constants import ACCENT_COLOR, BODY_FONT, TEXT_COLOR, TITLE_FONT, OUTPUT_FILE


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

OUTPUT = ROOT / OUTPUT_FILE
RESULT_SLIDES = {54, 55, 56, 58, 59}
AUTOFIT_SCALE = {54: 90000, 55: 93000, 56: 88000, 58: 93000, 59: 90000}
OFFICIAL_VALUES = ("19.718", "22.999", "28.418", "33.017")

# Preserve specialist/symbol fonts.  Only ordinary UI/document families are normalized.
NORMALIZABLE_FONTS = {
    "",
    "+mn-lt",
    "+mj-lt",
    "aptos",
    "aptos display",
    "arial",
    "calibri",
    "calibri light",
    "helvetica",
    "helvetica neue",
}
DARK_COLORS = {
    "000000",
    "111111",
    "111827",
    "1F1F1F",
    "222222",
    "333333",
    "404040",
    "595959",
    "666666",
}


def q(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


def _shape_text(shape: ET.Element) -> str:
    return " ".join((node.text or "") for node in shape.findall(".//a:t", NS)).strip()


def _is_title_shape(shape: ET.Element, slide_no: int) -> bool:
    ph = shape.find("./p:nvSpPr/p:nvPr/p:ph", NS)
    if ph is not None and ph.get("type") in {"title", "ctrTitle"}:
        return True
    title = str(SLIDES.get(slide_no, {}).get("title", "")).strip()
    text = _shape_text(shape)
    return bool(title and text and (text == title or text.startswith(title)))


def _ensure_font(rpr: ET.Element, family: str) -> None:
    for tag in ("latin", "ea", "cs"):
        node = rpr.find(f"a:{tag}", NS)
        if node is None:
            node = ET.SubElement(rpr, q("a", tag))
            node.set("typeface", family)
            continue
        current = (node.get("typeface") or "").strip()
        if current.lower() in NORMALIZABLE_FONTS:
            node.set("typeface", family)


def _set_fill(rpr: ET.Element, rgb: str, force: bool = False) -> None:
    solid = rpr.find("a:solidFill", NS)
    if solid is None:
        if not force:
            return
        solid = ET.SubElement(rpr, q("a", "solidFill"))
        srgb = ET.SubElement(solid, q("a", "srgbClr"))
        srgb.set("val", rgb.replace("#", "").upper())
        return

    srgb = solid.find("a:srgbClr", NS)
    if srgb is None:
        return
    current = (srgb.get("val") or "").upper()
    if force or current in DARK_COLORS:
        srgb.set("val", rgb.replace("#", "").upper())


def _normalize_text_shape(shape: ET.Element, slide_no: int) -> None:
    is_title = _is_title_shape(shape, slide_no)
    family = TITLE_FONT if is_title else BODY_FONT

    for rpr in shape.findall(".//a:rPr", NS) + shape.findall(".//a:defRPr", NS) + shape.findall(".//a:endParaRPr", NS):
        _ensure_font(rpr, family)
        if is_title:
            _set_fill(rpr, ACCENT_COLOR, force=True)
        else:
            _set_fill(rpr, TEXT_COLOR, force=False)

    if slide_no == 59:
        for run in shape.findall(".//a:r", NS):
            text = "".join((t.text or "") for t in run.findall(".//a:t", NS))
            if any(value in text for value in OFFICIAL_VALUES):
                rpr = run.find("a:rPr", NS)
                if rpr is None:
                    rpr = ET.Element(q("a", "rPr"))
                    run.insert(0, rpr)
                rpr.set("b", "1")
                _ensure_font(rpr, BODY_FONT)

    # Conservative overflow protection only on long Results callouts.
    if slide_no in RESULT_SLIDES and not is_title:
        text_len = len(_shape_text(shape))
        threshold = 80 if slide_no in {54, 56, 59} else 120
        if text_len >= threshold:
            tx_body = shape.find("a:txBody", NS)
            if tx_body is None:
                return
            body_pr = tx_body.find("a:bodyPr", NS)
            if body_pr is None:
                return
            body_pr.set("wrap", "square")
            for child_name in ("noAutofit", "spAutoFit", "normAutofit"):
                child = body_pr.find(f"a:{child_name}", NS)
                if child is not None:
                    body_pr.remove(child)
            autofit = ET.SubElement(body_pr, q("a", "normAutofit"))
            autofit.set("fontScale", str(AUTOFIT_SCALE[slide_no]))
            autofit.set("lnSpcReduction", "5000")


def _patch_slide_xml(xml_bytes: bytes, slide_no: int) -> bytes:
    root = ET.fromstring(xml_bytes)
    for shape in root.findall(".//p:sp", NS):
        _normalize_text_shape(shape, slide_no)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _slide_chart_targets(zf: ZipFile, slide_no: int) -> set[str]:
    rel_name = f"ppt/slides/_rels/slide{slide_no}.xml.rels"
    if rel_name not in zf.namelist():
        return set()
    rel_root = ET.fromstring(zf.read(rel_name))
    out: set[str] = set()
    for rel in rel_root.findall("pr:Relationship", NS):
        target = rel.get("Target") or ""
        if "charts/chart" in target and target.endswith(".xml"):
            chart_name = "ppt/charts/" + Path(target).name
            out.add(chart_name)
    return out


def _chart_rprs(root: ET.Element) -> list[ET.Element]:
    return (
        root.findall(".//a:rPr", NS)
        + root.findall(".//a:defRPr", NS)
        + root.findall(".//a:endParaRPr", NS)
    )


def _patch_chart_xml(xml_bytes: bytes) -> bytes:
    root = ET.fromstring(xml_bytes)

    for rpr in _chart_rprs(root):
        _ensure_font(rpr, BODY_FONT)
        _set_fill(rpr, TEXT_COLOR, force=False)
        size = rpr.get("sz")
        if size and size.isdigit() and int(size) < 900:
            rpr.set("sz", "900")

    # Chart titles should remain visibly above data labels/axes.
    for title in root.findall(".//c:title", NS):
        for rpr in _chart_rprs(title):
            _ensure_font(rpr, TITLE_FONT)
            size = rpr.get("sz")
            if size is None or (size.isdigit() and int(size) < 1200):
                rpr.set("sz", "1200")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def apply(pptx_path: Path = OUTPUT) -> None:
    if not pptx_path.exists():
        raise FileNotFoundError(f"Generated PPTX not found: {pptx_path}")

    with ZipFile(pptx_path, "r") as src:
        chart_targets: set[str] = set()
        for slide_no in RESULT_SLIDES:
            chart_targets.update(_slide_chart_targets(src, slide_no))

        with NamedTemporaryFile(
            prefix=pptx_path.stem + "_",
            suffix=".pptx",
            dir=pptx_path.parent,
            delete=False,
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            with ZipFile(tmp_path, "w", compression=ZIP_DEFLATED) as dst:
                for info in src.infolist():
                    payload = src.read(info.filename)
                    slide_match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", info.filename)
                    if slide_match:
                        payload = _patch_slide_xml(payload, int(slide_match.group(1)))
                    elif info.filename in chart_targets:
                        payload = _patch_chart_xml(payload)
                    dst.writestr(info, payload)
            tmp_path.replace(pptx_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    print(
        "Applied editable XML formatting pass: Helvetica Neue typography, "
        "accent titles, conservative Results-slide autofit, and chart text readability."
    )


if __name__ == "__main__":
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else OUTPUT
    apply(path)
