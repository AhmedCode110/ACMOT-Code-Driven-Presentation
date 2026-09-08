"""
fix_layout_fit.py — AC-MOT V7 layout containment + font-attribute repair.

Two problems this fixes:

1. TEXT ESCAPING ITS BLOCK
   Every body text box in the deck uses <a:spAutoFit/> ("resize shape to fit
   text").  When the stored box is smaller than the text needs, PowerPoint and
   Keynote grow the box at render time — so the text spills over whatever sits
   below it.  This is why the later slides look broken.

   Repair order (matches the project spec — shrinking text is the LAST resort):
     a. grow the box downward into genuinely free space on the slide
     b. absorb a little more with line-spacing reduction
     c. only then scale the font, never below FONT_SCALE_FLOOR

   Boxes are switched from spAutoFit to <a:normAutofit/> ("shrink text on
   overflow") so the geometry stays fixed and predictable in both PowerPoint
   and Keynote.

2. INVALID FONT ATTRIBUTES
   scripts/v7_targeted_fixes.py set typeface=/latin=/ea=/cs= as ATTRIBUTES on
   <a:rPr>.  Those are not valid DrawingML attributes — the font was never
   actually applied, and the junk can trigger a repair prompt.  The font must
   live in child elements <a:latin typeface="…"/> and <a:cs typeface="…"/>.

Run:
    python3 scripts/fix_layout_fit.py
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

# ── namespaces ────────────────────────────────────────────────────────────────
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
ET.register_namespace("a", A)
ET.register_namespace("p", P)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")

# ── tuning ────────────────────────────────────────────────────────────────────
EMU_PT           = 12700
AVG_ADV          = 0.52     # em per character, Helvetica Neue mixed case
LINE_FACTOR      = 1.20     # single line spacing
DEFAULT_SZ       = 1200     # hundredths of a point

FIX_THRESHOLD    = 1.15     # only touch shapes overflowing more than this
FONT_SCALE_FLOOR = 88       # never scale text below 88 % — readability first
LNSPC_REDUCTION  = 10       # percent, applied before font scaling
SAFETY_GAP_EMU   = 4 * EMU_PT   # keep 4 pt clear when growing a box
BOTTOM_MARGIN    = 24 * EMU_PT  # keep 24 pt clear of the slide bottom

FONT             = "Helvetica Neue"

# a:rPr attributes that are NOT valid DrawingML and must be stripped
BOGUS_FONT_ATTRS = ("typeface", "latin", "ea", "cs")
RPR_TAGS         = (f"{{{A}}}rPr", f"{{{A}}}defRPr", f"{{{A}}}endParaRPr")


def _int(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d


# ── part 1: font attribute repair ────────────────────────────────────────────

def repair_font_attributes(root: ET.Element) -> int:
    """Strip invalid font attributes off rPr elements; add proper child elements."""
    fixed = 0
    for tag in RPR_TAGS:
        for rpr in root.iter(tag):
            had_bogus = False
            for attr in BOGUS_FONT_ATTRS:
                if attr in rpr.attrib:
                    del rpr.attrib[attr]
                    had_bogus = True
            if had_bogus:
                fixed += 1
            # ensure a proper <a:latin> child so the font really applies
            latin = rpr.find(f"{{{A}}}latin")
            if latin is None:
                latin = ET.SubElement(rpr, f"{{{A}}}latin")
            latin.attrib.clear()
            latin.set("typeface", FONT)
    return fixed


# ── part 2: text measurement ─────────────────────────────────────────────────

def measure_text_height(tx: ET.Element, avail_w_pt: float) -> float:
    """Estimated rendered height of a txBody, in points."""
    total = 0.0
    inherited = DEFAULT_SZ

    for p in tx.findall(f"{{{A}}}p"):
        pPr = p.find(f"{{{A}}}pPr")

        ln_factor = LINE_FACTOR
        extra = 0.0
        width_limit = avail_w_pt
        if pPr is not None:
            lnSpc = pPr.find(f"{{{A}}}lnSpc")
            if lnSpc is not None:
                pct = lnSpc.find(f"{{{A}}}spcPct")
                if pct is not None:
                    ln_factor = LINE_FACTOR * _int(pct.get("val"), 100000) / 100000.0
            for tag in ("spcBef", "spcAft"):
                el = pPr.find(f"{{{A}}}{tag}")
                if el is not None:
                    pts = el.find(f"{{{A}}}spcPts")
                    if pts is not None:
                        extra += _int(pts.get("val"), 0) / 100.0
            width_limit = max(avail_w_pt - _int(pPr.get("marL"), 0) / EMU_PT, 10.0)

        runs = p.findall(f"{{{A}}}r")
        if not runs:
            end = p.find(f"{{{A}}}endParaRPr")
            sz = _int(end.get("sz"), inherited) if end is not None else inherited
            total += sz / 100.0 * ln_factor + extra
            continue

        width_pt = 0.0
        max_sz = 0
        for r in runs:
            rPr = r.find(f"{{{A}}}rPr")
            t = r.find(f"{{{A}}}t")
            text = (t.text or "") if t is not None else ""
            sz = _int(rPr.get("sz"), inherited) if rPr is not None else inherited
            bold = rPr is not None and rPr.get("b") == "1"
            width_pt += len(text) * (sz / 100.0) * AVG_ADV * (1.05 if bold else 1.0)
            max_sz = max(max_sz, sz)

        if max_sz:
            inherited = max_sz
        else:
            max_sz = inherited

        lines = max(1, math.ceil(width_pt / width_limit)) if width_limit > 0 else 1
        total += lines * (max_sz / 100.0) * ln_factor + extra

    return total


# ── part 3: geometry helpers ─────────────────────────────────────────────────

def shape_box(el: ET.Element):
    """Return (x, y, cx, cy) for any shape that carries an a:xfrm, else None."""
    xfrm = el.find(f".//{{{A}}}xfrm")
    if xfrm is None:
        return None
    off, ext = xfrm.find(f"{{{A}}}off"), xfrm.find(f"{{{A}}}ext")
    if off is None or ext is None:
        return None
    return (_int(off.get("x")), _int(off.get("y")),
            _int(ext.get("cx")), _int(ext.get("cy")))


def collect_boxes(tree: ET.Element):
    """All positioned shapes on the slide, as (element, x, y, cx, cy)."""
    out = []
    for tag in ("sp", "pic", "graphicFrame", "grpSp", "cxnSp"):
        for el in tree.findall(f"{{{P}}}{tag}"):
            box = shape_box(el)
            if box:
                out.append((el, *box))
    return out


def free_space_below(target, boxes, slide_h: int) -> int:
    """EMU of clear vertical space beneath `target` before the next shape."""
    _, tx, ty, tcx, tcy = target
    t_bottom = ty + tcy
    t_left, t_right = tx, tx + tcx

    limit = slide_h - BOTTOM_MARGIN
    for el, x, y, cx, cy in boxes:
        if el is target[0]:
            continue
        # only shapes that horizontally overlap can block growth
        if x + cx <= t_left or x >= t_right:
            continue
        if y >= t_bottom:                 # sits below us
            limit = min(limit, y - SAFETY_GAP_EMU)
    return max(0, limit - t_bottom)


# ── part 4: the fit pass ─────────────────────────────────────────────────────

def set_autofit(bodyPr: ET.Element, font_scale: int, lnspc_red: int) -> None:
    """Replace whatever autofit setting exists with a tuned normAutofit."""
    for tag in ("spAutoFit", "noAutofit", "normAutofit"):
        for el in bodyPr.findall(f"{{{A}}}{tag}"):
            bodyPr.remove(el)

    norm = ET.Element(f"{{{A}}}normAutofit")
    if font_scale < 100:
        norm.set("fontScale", str(int(font_scale * 1000)))
    if lnspc_red > 0:
        norm.set("lnSpcReduction", str(int(lnspc_red * 1000)))

    # schema order: normAutofit must follow prstTxWarp if present
    warp = bodyPr.find(f"{{{A}}}prstTxWarp")
    idx = list(bodyPr).index(warp) + 1 if warp is not None else 0
    bodyPr.insert(idx, norm)


def fit_slide(root: ET.Element, slide_h: int):
    """Grow boxes where safe, then shrink text only as far as necessary."""
    tree = root.find(f"{{{P}}}cSld/{{{P}}}spTree")
    if tree is None:
        return []

    boxes = collect_boxes(tree)
    actions = []

    for entry in boxes:
        el, x, y, cx, cy = entry
        if el.tag != f"{{{P}}}sp":
            continue
        tx = el.find(f"{{{P}}}txBody")
        if tx is None:
            continue
        text = " ".join(t.text or "" for t in tx.findall(f".//{{{A}}}t")).strip()
        if len(text) < 25:          # short labels: leave alone
            continue

        bodyPr = tx.find(f"{{{A}}}bodyPr")
        if bodyPr is None:
            continue

        lIns = _int(bodyPr.get("lIns"), 91440)
        rIns = _int(bodyPr.get("rIns"), 91440)
        tIns = _int(bodyPr.get("tIns"), 45720)
        bIns = _int(bodyPr.get("bIns"), 45720)

        avail_w = (cx - lIns - rIns) / EMU_PT
        avail_h = (cy - tIns - bIns) / EMU_PT
        if avail_w <= 0 or avail_h <= 0:
            continue

        need_h = measure_text_height(tx, avail_w)
        ratio = need_h / avail_h
        if ratio <= FIX_THRESHOLD:
            continue

        # ── (a) grow the box downward into free space ────────────────────────
        deficit_emu = int((need_h - avail_h) * EMU_PT)
        room = free_space_below(entry, boxes, slide_h)
        grow = min(deficit_emu, room)

        if grow > 0:
            ext = el.find(f".//{{{A}}}xfrm/{{{A}}}ext")
            if ext is not None:
                ext.set("cy", str(cy + grow))
                avail_h += grow / EMU_PT

        # ── (b)+(c) absorb the rest with line spacing, then font scale ──────
        remaining = need_h / avail_h
        if remaining > 1.0:
            lnspc = LNSPC_REDUCTION if remaining > 1.05 else 0
            effective = remaining * (1 - lnspc / 100.0)
            scale = 100 if effective <= 1.0 else max(FONT_SCALE_FLOOR,
                                                     int(100 / effective))
            set_autofit(bodyPr, scale, lnspc)
            actions.append((round(ratio, 2), round(grow / EMU_PT), scale, text[:45]))
        elif grow > 0:
            set_autofit(bodyPr, 100, 0)
            actions.append((round(ratio, 2), round(grow / EMU_PT), 100, text[:45]))

    return actions


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not PPTX.exists():
        raise SystemExit(f"ERROR: PPTX not found: {PPTX}")

    with ZipFile(PPTX) as zf:
        infos = zf.infolist()
        data = {i.filename: zf.read(i.filename) for i in infos}

    # slide height from presentation.xml
    pres = ET.fromstring(data["ppt/presentation.xml"])
    sldSz = pres.find(f"{{{P}}}sldSz")
    slide_h = _int(sldSz.get("cy"), 6858000) if sldSz is not None else 6858000
    print(f"Slide height: {slide_h} EMU ({slide_h/EMU_PT:.0f} pt)")

    slide_re = re.compile(r"ppt/slides/slide(\d+)\.xml$")
    total_font_fixes = 0
    total_fit_fixes = 0
    touched = []

    for name in sorted(data, key=lambda n: (slide_re.match(n) is None,
                                            _int(slide_re.match(n).group(1)) if slide_re.match(n) else 0)):
        m = slide_re.match(name)
        if not m:
            continue
        num = int(m.group(1))
        root = ET.fromstring(data[name])

        font_fixes = repair_font_attributes(root)
        actions = fit_slide(root, slide_h)

        if font_fixes or actions:
            data[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            total_font_fixes += font_fixes
            total_fit_fixes += len(actions)
            if actions:
                touched.append((num, actions))

    # write package
    with tempfile.NamedTemporaryFile(prefix="acmot_fit_", suffix=".pptx",
                                     dir=PPTX.parent, delete=False) as h:
        tmp = Path(h.name)
    with ZipFile(tmp, "w", ZIP_DEFLATED) as dst:
        for info in infos:
            dst.writestr(info, data[info.filename])
    shutil.copystat(PPTX, tmp)
    tmp.replace(PPTX)

    print(f"\nInvalid font attributes repaired on {total_font_fixes} rPr elements")
    print(f"Text boxes contained: {total_fit_fixes}\n")
    for num, actions in touched:
        print(f"  Slide {num}:")
        for ratio, grew, scale, text in actions:
            bits = []
            if grew:
                bits.append(f"grew {grew}pt")
            if scale < 100:
                bits.append(f"font {scale}%")
            how = ", ".join(bits) or "contained"
            print(f"     was {ratio}x → {how}   {text!r}")

    print(f"\nSaved: {PPTX}")


if __name__ == "__main__":
    main()
