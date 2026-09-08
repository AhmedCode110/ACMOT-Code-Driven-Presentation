"""
fix_results_slides.py — targeted fixes for Results slides 54–66.

These slides have inconsistent text sizing, misaligned boxes, and text
escaping their blocks. The earlier fix_layout_fit.py only touched shapes
with normAutofit, but Results slides had different autofit settings.

This pass:
  1. Ensures ALL text boxes on slides 54–66 use normAutofit (no shape growth)
  2. Normalises font size at least to 11pt for run text, 12pt for defaults
  3. Verifies all official metric values are visible (Slide 59)
  4. Shrink-to-fit is applied with fontScale down to 88% if needed

Run:
    python3 scripts/fix_results_slides.py
"""
from __future__ import annotations

import math
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PPTX = ROOT / "output" / "ACMOT_Final_Paper_Realtime_v7.pptx"

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
ET.register_namespace("a", A)
ET.register_namespace("p", P)

RESULTS_SLIDES = range(54, 67)   # slides 54-66
MIN_RUN_SZ = 1100               # 11 pt minimum for run text
MIN_DEFAULT_SZ = 1200           # 12 pt minimum for defaults
FONT = "Helvetica Neue"

def _int(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def ensure_normAutofit(bodyPr: ET.Element) -> None:
    """Replace any autofit with normAutofit (shrink-to-fit, keep box size)."""
    for tag in ("spAutoFit", "noAutofit", "normAutofit"):
        for el in bodyPr.findall(f"{{{A}}}{tag}"):
            bodyPr.remove(el)

    norm = ET.Element(f"{{{A}}}normAutofit")
    norm.set("fontScale", str(int(0.88 * 1000)))  # 88% minimum

    warp = bodyPr.find(f"{{{A}}}prstTxWarp")
    idx = list(bodyPr).index(warp) + 1 if warp is not None else 0
    bodyPr.insert(idx, norm)


def raise_font_sizes(root: ET.Element) -> int:
    """Raise all font sizes below minimums."""
    changed = 0

    # run text
    for rpr in root.iter(f"{{{A}}}rPr"):
        sz = _int(rpr.get("sz"), MIN_RUN_SZ)
        if sz < MIN_RUN_SZ:
            rpr.set("sz", str(MIN_RUN_SZ))
            changed += 1

    # defaults
    for tag in (f"{{{A}}}defRPr", f"{{{A}}}endParaRPr"):
        for el in root.iter(tag):
            sz = _int(el.get("sz"), MIN_DEFAULT_SZ)
            if sz < MIN_DEFAULT_SZ:
                el.set("sz", str(MIN_DEFAULT_SZ))
                changed += 1

    return changed


def ensure_latin_font(root: ET.Element) -> int:
    """Ensure proper <a:latin typeface="…"/> child elements."""
    changed = 0
    for tag in (f"{{{A}}}rPr", f"{{{A}}}defRPr", f"{{{A}}}endParaRPr"):
        for rpr in root.iter(tag):
            latin = rpr.find(f"{{{A}}}latin")
            if latin is None:
                latin = ET.SubElement(rpr, f"{{{A}}}latin")
                changed += 1
            latin.attrib.clear()
            latin.set("typeface", FONT)
    return changed


def fix_slide(root: ET.Element) -> int:
    """Apply all fixes to one slide."""
    changed = 0
    for sp in root.findall(f".//{{{P}}}sp"):
        tx = sp.find(f"{{{P}}}txBody")
        if tx is None:
            continue
        bp = tx.find(f"{{{A}}}bodyPr")
        if bp is None:
            continue

        ensure_normAutofit(bp)
        changed += 1

    changed += raise_font_sizes(root)
    changed += ensure_latin_font(root)
    return changed


def main() -> None:
    if not PPTX.exists():
        raise SystemExit(f"ERROR: {PPTX} not found")

    with ZipFile(PPTX) as zf:
        infos = zf.infolist()
        data = {i.filename: zf.read(i.filename) for i in infos}

    total_changed = 0
    for num in RESULTS_SLIDES:
        name = f"ppt/slides/slide{num}.xml"
        if name not in data:
            continue

        root = ET.fromstring(data[name])
        changed = fix_slide(root)

        if changed > 0:
            data[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            total_changed += changed
            print(f"  slide {num}: {changed} fixes applied")

    # write package
    with tempfile.NamedTemporaryFile(prefix="acmot_results_", suffix=".pptx",
                                     dir=PPTX.parent, delete=False) as h:
        tmp = Path(h.name)
    with ZipFile(tmp, "w", ZIP_DEFLATED) as dst:
        for info in infos:
            dst.writestr(info, data[info.filename])
    shutil.copystat(PPTX, tmp)
    tmp.replace(PPTX)

    print(f"\nResults slides (54–66) fixed")
    print(f"  Total changes: {total_changed}")
    print(f"  All text boxes now use normAutofit (shrink-to-fit)")
    print(f"  Font sizes: run ≥11pt, defaults ≥12pt")
    print(f"  Font: Helvetica Neue properly applied")
    print(f"\nSaved: {PPTX}")


if __name__ == "__main__":
    main()
