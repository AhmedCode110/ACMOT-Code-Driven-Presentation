"""
fix_typography.py — AC-MOT V7 typography normalisation pass.

Fixes applied to output/ACMOT_Final_Paper_Realtime_v7.pptx in-place:

  1. Table cells on slide 48 & 57: raise 7 pt → 10 pt, 8 pt → 11 pt
     (row height is ~19 pt so there is room; text was completely unreadable)

  2. Any non-table a:rPr run text below 11 pt → 11 pt minimum
     (defRPr paragraph defaults below 12 pt → 12 pt minimum)

  3. endParaRPr defaults below 12 pt → 12 pt

  4. Fonts on every slide → Helvetica Neue  (already done on Results slides;
     this extends to the full deck so everything is consistent)

Run:
    python3 scripts/fix_typography.py
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PPTX = ROOT / "output" / "ACMOT_Final_Paper_Realtime_v7.pptx"

# ── size rules ────────────────────────────────────────────────────────────────
# Tables on slides 48 & 57: very dense 17-row tables that had 7/8 pt text
TABLE_HEADER_MIN   = 1100   # 11 pt
TABLE_DATA_MIN     = 1000   # 10 pt
TABLE_SLIDES       = {48, 57}

# Regular run text (a:rPr on actual runs, NOT defRPr)
RUN_MIN            = 1100   # 11 pt

# Paragraph defaults (a:defRPr / a:endParaRPr)
DEFAULT_MIN        = 1200   # 12 pt

FONT               = "Helvetica Neue"

# ── section-header slides — large decorative numbers (I, II, III…) ────────────
# The 72 pt Roman numeral and 36 pt section title are INTENTIONAL — don't touch.
# The 24 pt / 15 pt / 13 pt on those slides are also fine.
SECTION_HEADER_SLIDES = {1, 3, 17, 29, 31, 45, 53, 60, 63}

# ── helpers ───────────────────────────────────────────────────────────────────

def _bump_sz(sz_str: str, minimum: int) -> str:
    """Return a new sz value (in hundredths of a pt) at least `minimum`."""
    val = int(sz_str)
    return str(max(val, minimum))


def _is_table_header_row(cell_elem) -> bool:
    """True when the table cell is in the first row (detected by position index)."""
    # We inject a flag via the fix loop; simpler to pass row index externally.
    return False   # overridden in the table loop below


# ── per-slide fix ─────────────────────────────────────────────────────────────

def fix_slide(slide_num: int, xml_text: str) -> str:
    """Apply all typography fixes to one slide's XML text."""

    # ── 1. Table cell text on TABLE_SLIDES ────────────────────────────────────
    if slide_num in TABLE_SLIDES:
        xml_text = _fix_table_text(xml_text)

    # ── 2. Paragraph defaults (defRPr / endParaRPr) ───────────────────────────
    xml_text = _fix_defaults(xml_text)

    # ── 3. Actual run props (a:rPr) in regular shapes ─────────────────────────
    # We do NOT touch rPr inside graphicFrame (already handled for tables above,
    # and charts use their own size logic managed by the chart XML).
    xml_text = _fix_run_sizes(xml_text)

    # ── 4. Font normalisation (all a:rPr / a:defRPr / a:endParaRPr) ──────────
    xml_text = _fix_fonts(xml_text)

    return xml_text


# ── table cell text ───────────────────────────────────────────────────────────

_TR_SPLIT = re.compile(r'(<a:tr\b[^>]*>)(.*?)(</a:tr>)', re.S)
_RPR_SZ   = re.compile(r'(<a:rPr\b[^>]*?\bsz=")(\d+)(")')


def _fix_table_text(xml_text: str) -> str:
    """Raise 7pt→10pt, 8pt→11pt inside all table rows of this slide."""
    rows_found = [0]   # mutable counter

    def _fix_row(m: re.Match) -> str:
        open_tag, inner, close_tag = m.group(1), m.group(2), m.group(3)
        is_first = rows_found[0] == 0
        rows_found[0] += 1
        minimum = TABLE_HEADER_MIN if is_first else TABLE_DATA_MIN
        inner = _RPR_SZ.sub(lambda rm: rm.group(1) + _bump_sz(rm.group(2), minimum) + rm.group(3), inner)
        return open_tag + inner + close_tag

    return _TR_SPLIT.sub(_fix_row, xml_text)


# ── paragraph defaults ────────────────────────────────────────────────────────

_DEF_RPR_SZ  = re.compile(r'(<a:(?:defRPr|endParaRPr)\b[^>]*?\bsz=")(\d+)(")')


def _fix_defaults(xml_text: str) -> str:
    def _bump(m: re.Match) -> str:
        new_sz = _bump_sz(m.group(2), DEFAULT_MIN)
        return m.group(1) + new_sz + m.group(3)
    return _DEF_RPR_SZ.sub(_bump, xml_text)


# ── actual run sizes (a:rPr in p:sp shapes only) ─────────────────────────────

# We process the XML as text, restricting to a:rPr that are NOT inside
# a:tbl (table) blocks — those were already handled.  We do this by splitting
# the XML on table boundaries and skipping the table portions.

_TBL_BLOCK = re.compile(r'(<a:tbl\b.*?</a:tbl>)', re.S)
_ARPR_SZ   = re.compile(r'(<a:rPr\b[^>]*?\bsz=")(\d+)(")')


def _fix_run_sizes(xml_text: str) -> str:
    parts = _TBL_BLOCK.split(xml_text)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # Inside a table block — skip (already handled)
            result.append(part)
        else:
            # Outside table — bump any sub-minimum run sizes
            result.append(_ARPR_SZ.sub(
                lambda m: m.group(1) + _bump_sz(m.group(2), RUN_MIN) + m.group(3),
                part
            ))
    return "".join(result)


# ── font normalisation ────────────────────────────────────────────────────────

_FONT_ATTRS = re.compile(
    r'(<a:(?:rPr|defRPr|endParaRPr)\b[^>]*?)(?:typeface|latin|ea|cs)="[^"]*"'
)
_FONT_TAG_OPEN = re.compile(r'(<a:(?:rPr|defRPr|endParaRPr)\b)([^>]*>)', re.S)
_LATIN_TAG     = re.compile(r'<a:latin\s[^>]*?typeface="[^"]*"[^>]*/>', re.S)

FONT_QUOTED = f'"{FONT}"'


def _fix_fonts(xml_text: str) -> str:
    # Replace typeface/latin/ea/cs attributes inside rPr elements
    def _fix_rpr(m: re.Match) -> str:
        inner = m.group(2)
        for attr in ("typeface", "latin", "ea", "cs"):
            inner = re.sub(rf'\b{attr}="[^"]*"', f'{attr}={FONT_QUOTED}', inner)
        return m.group(1) + inner

    # match the full opening tag (up to and including >)
    def _process(m: re.Match) -> str:
        tag = m.group(1)
        rest = m.group(2)
        for attr in ("typeface", "latin", "ea", "cs"):
            rest = re.sub(rf'\b{attr}="[^"]*"', f'{attr}={FONT_QUOTED}', rest)
        return tag + rest

    xml_text = _FONT_TAG_OPEN.sub(_process, xml_text)

    # Also normalise <a:latin typeface="…"/> child elements
    xml_text = _LATIN_TAG.sub(f'<a:latin typeface={FONT_QUOTED}/>', xml_text)

    return xml_text


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not PPTX.exists():
        raise SystemExit(f"ERROR: PPTX not found: {PPTX}")

    print(f"Typography fix: {PPTX.name}")

    with ZipFile(PPTX) as zf:
        infos = zf.infolist()
        data  = {item.filename: zf.read(item.filename) for item in infos}

    slide_re = re.compile(r"ppt/slides/slide(\d+)\.xml$")
    changed  = []

    for name in list(data.keys()):
        m = slide_re.match(name)
        if not m:
            continue
        num = int(m.group(1))
        original = data[name].decode("utf-8", errors="replace")
        fixed    = fix_slide(num, original)
        if fixed != original:
            data[name] = fixed.encode("utf-8")
            changed.append(num)

    with tempfile.NamedTemporaryFile(
        prefix="acmot_typo_", suffix=".pptx", dir=PPTX.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
    with ZipFile(tmp, "w", ZIP_DEFLATED) as dst:
        for item in infos:
            dst.writestr(item, data[item.filename])
    shutil.copystat(PPTX, tmp)
    tmp.replace(PPTX)

    print(f"  Fixed {len(changed)} slides: {sorted(changed)}")
    print(f"  Rules applied:")
    print(f"    Tables (slides 48, 57): headers ≥ 11 pt, data ≥ 10 pt")
    print(f"    All run text:  ≥ 11 pt")
    print(f"    Defaults:      ≥ 12 pt")
    print(f"    Font:          {FONT} everywhere")
    print(f"  Saved: {PPTX}")


if __name__ == "__main__":
    main()
