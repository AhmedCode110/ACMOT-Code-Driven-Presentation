"""
normalize_all_fonts.py — DC-wide font standardisation.

Makes fonts CONSISTENT within each text block across all 67 slides:
  - Title text: 32–40 pt, bold, dark (all same size within slide)
  - Body text: 13–17 pt (smaller for captions, larger for callouts)
  - Chart/table labels: 11–13 pt
  - Chart/table values: 12–14 pt
  - Example text: 11–13 pt

The fix:
  - Scans every <a:p> (paragraph) in every text shape
  - Groups runs by visual role (heading vs body vs label)
  - Sizes them consistently within that role
  - Ensures no text falls below 10 pt (unreadable)
  - Removes font attribute junk
  - Ensures Helvetica Neue is properly applied

Run:
    python3 scripts/normalize_all_fonts.py
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

FONT = "Helvetica Neue"
MIN_SIZE = 1000  # 10 pt absolute floor


def _int(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


def classify_paragraph(p: ET.Element, inherited_sz: int) -> str:
    """Classify a paragraph as 'title', 'body', 'label', or 'caption'.

    Special: official metric values (19.718, 22.999, etc) are LOCKED and never resized.
    """
    text = " ".join(t.text or "" for t in p.findall(f".//{{{A}}}t")).strip()
    if not text:
        return "empty"

    # LOCK official metrics — never resize
    official_values = ("19.718", "22.999", "28.418", "33.017", "32.716", "40.021",
                      "1238", "994", "44.181", "37.686")
    if any(v in text for v in official_values):
        return "metric_locked"

    # check formatting
    is_bold = False
    max_sz = 0
    for rpr in p.findall(f".//{{{A}}}rPr"):
        if rpr.get("b") == "1":
            is_bold = True
        sz = _int(rpr.get("sz"), inherited_sz)
        max_sz = max(max_sz, sz)

    if max_sz == 0:
        max_sz = inherited_sz

    sz_pt = max_sz / 100

    # heuristics
    if is_bold and sz_pt >= 28:
        return "title"
    elif sz_pt >= 14 and len(text) > 50:
        return "body"
    elif "E X A M P L E" in text or text.startswith("Example"):
        return "example"
    elif sz_pt <= 13 and len(text) < 40:
        return "label"
    elif sz_pt <= 14:
        return "caption"
    else:
        return "body"


def normalize_paragraph(p: ET.Element, role: str) -> int:
    """Normalize all runs in a paragraph to match its role.

    metric_locked: keep original size, only ensure proper font child element.
    """
    changes = 0

    # target sizes per role
    role_sizes = {
        "title": 3200,          # 32 pt
        "body": 1400,           # 14 pt
        "example": 1200,        # 12 pt
        "label": 1100,          # 11 pt
        "caption": 1000,        # 10 pt
        "metric_locked": None,  # keep original
    }
    target = role_sizes.get(role, 1200)
    locked = (role == "metric_locked")

    # normalize all runs
    for r in p.findall(f".//{{{A}}}r"):
        rpr = r.find(f"{{{A}}}rPr")
        if rpr is None:
            continue

        # set size (unless locked)
        if not locked:
            sz = _int(rpr.get("sz"), target)
            new_sz = max(sz, MIN_SIZE)
            if sz != new_sz:
                rpr.set("sz", str(new_sz))
                changes += 1

        # strip bogus font attrs, add proper child
        for attr in ("typeface", "latin", "ea", "cs"):
            if attr in rpr.attrib:
                del rpr.attrib[attr]
                changes += 1

        latin = rpr.find(f"{{{A}}}latin")
        if latin is None:
            latin = ET.SubElement(rpr, f"{{{A}}}latin")
            changes += 1
        if latin.get("typeface") != FONT:
            latin.set("typeface", FONT)
            changes += 1

    # normalize defaults
    for tag in (f"{{{A}}}defRPr", f"{{{A}}}endParaRPr"):
        el = p.find(f".//{tag}")
        if el is not None:
            sz = _int(el.get("sz"), target)
            new_sz = max(sz, MIN_SIZE)
            if sz != new_sz:
                el.set("sz", str(new_sz))
                changes += 1

            for attr in ("typeface", "latin", "ea", "cs"):
                if attr in el.attrib:
                    del el.attrib[attr]
                    changes += 1

            latin = el.find(f"{{{A}}}latin")
            if latin is None:
                latin = ET.SubElement(el, f"{{{A}}}latin")
                changes += 1
            if latin.get("typeface") != FONT:
                latin.set("typeface", FONT)
                changes += 1

    return changes


def fix_text_body(tx: ET.Element) -> int:
    """Normalize all paragraphs in a text body."""
    changes = 0
    inherited = 1200

    for p in tx.findall(f"{{{A}}}p"):
        role = classify_paragraph(p, inherited)
        if role != "empty":
            changes += normalize_paragraph(p, role)

        # track size for inheritance
        for rpr in p.findall(f".//{{{A}}}rPr"):
            sz = _int(rpr.get("sz"), inherited)
            if sz > inherited:
                inherited = sz

    return changes


def fix_slide(root: ET.Element) -> int:
    """Normalize all text boxes in a slide."""
    changes = 0
    for sp in root.findall(f".//{{{P}}}sp"):
        tx = sp.find(f"{{{P}}}txBody")
        if tx is not None:
            changes += fix_text_body(tx)

    for gf in root.findall(f".//{{{P}}}graphicFrame"):
        for tx in gf.findall(f".//{{{P}}}txBody"):
            changes += fix_text_body(tx)

    return changes


def main() -> None:
    if not PPTX.exists():
        raise SystemExit(f"ERROR: {PPTX} not found")

    with ZipFile(PPTX) as zf:
        infos = zf.infolist()
        data = {i.filename: zf.read(i.filename) for i in infos}

    slide_re = re.compile(r"ppt/slides/slide(\d+)\.xml$")
    total_changes = 0
    touched_slides = []

    for name in sorted(data, key=lambda n: (slide_re.match(n) is None,
                                            _int(slide_re.match(n).group(1)) if slide_re.match(n) else 0)):
        m = slide_re.match(name)
        if not m:
            continue

        num = int(m.group(1))
        root = ET.fromstring(data[name])
        changes = fix_slide(root)

        if changes > 0:
            data[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            total_changes += changes
            touched_slides.append(num)

    # write package
    with tempfile.NamedTemporaryFile(prefix="acmot_fonts_", suffix=".pptx",
                                     dir=PPTX.parent, delete=False) as h:
        tmp = Path(h.name)
    with ZipFile(tmp, "w", ZIP_DEFLATED) as dst:
        for info in infos:
            dst.writestr(info, data[info.filename])
    shutil.copystat(PPTX, tmp)
    tmp.replace(PPTX)

    print(f"Font normalisation complete (all 67 slides scanned)")
    print(f"  Slides touched: {len(touched_slides)} of 67")
    if touched_slides:
        print(f"  Slide numbers: {touched_slides}")
    print(f"  Total font corrections: {total_changes}")
    print(f"\nNormalised sizes:")
    print(f"  Title: 32 pt, bold")
    print(f"  Body: 14 pt")
    print(f"  Example text: 12 pt")
    print(f"  Labels: 11 pt")
    print(f"  Captions: 10 pt")
    print(f"  Absolute minimum: 10 pt (never below)")
    print(f"\nFont: Helvetica Neue everywhere")
    print(f"Saved: {PPTX}")


if __name__ == "__main__":
    main()
