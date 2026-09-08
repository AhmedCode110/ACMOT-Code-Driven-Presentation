"""
Semantic typography system for the AC-MOT presentation.

All text roles are defined here.  Slide scripts should import the role they need
rather than setting arbitrary font sizes.  This ensures equivalent elements across
the deck have consistent family, weight, size and colour.
"""
from __future__ import annotations
from dataclasses import dataclass


FONT_FAMILY = "Helvetica Neue"


@dataclass(frozen=True)
class TextRole:
    font: str
    size_pt: float      # points
    bold: bool = False
    italic: bool = False
    color: str | None = None   # hex without '#', None = inherit from theme


# ── Hierarchy ─────────────────────────────────────────────────────────────────
TITLE         = TextRole(FONT_FAMILY, 38, bold=True)
SECTION_TITLE = TextRole(FONT_FAMILY, 32, bold=True)
SLIDE_TITLE   = TextRole(FONT_FAMILY, 28, bold=True)
SUBTITLE      = TextRole(FONT_FAMILY, 22, bold=False)

BODY          = TextRole(FONT_FAMILY, 18)
BODY_SMALL    = TextRole(FONT_FAMILY, 14)

CARD_TITLE    = TextRole(FONT_FAMILY, 16, bold=True)
CARD_BODY     = TextRole(FONT_FAMILY, 13)

CHART_LABEL   = TextRole(FONT_FAMILY, 12)
CHART_VALUE   = TextRole(FONT_FAMILY, 13, bold=True)

TABLE_HEADER  = TextRole(FONT_FAMILY, 13, bold=True)
TABLE_BODY    = TextRole(FONT_FAMILY, 12)

METRIC_VALUE  = TextRole(FONT_FAMILY, 36, bold=True)
METRIC_LABEL  = TextRole(FONT_FAMILY, 14)

FOOTNOTE      = TextRole(FONT_FAMILY, 11, italic=True)
