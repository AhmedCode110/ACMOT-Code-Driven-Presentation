"""
Presentation-level constants consumed by the Node.js build runner
(build_deck.mjs → xml_apply_overrides.py → final_polish_xml.py).

Typography and layout tokens live here; research data lives in config/metrics.py.
"""

SLIDE_WIDTH  = 1280
SLIDE_HEIGHT = 720

BACKGROUND_COLOR = "#FFFFFF"
TEXT_COLOR       = "#111827"
ACCENT_COLOR     = "#2563EB"

# Canonical font — all post-build XML normalisers enforce this.
TITLE_FONT = "Helvetica Neue"
BODY_FONT  = "Helvetica Neue"

# Semantic size defaults (detailed roles are in config/typography.py)
TITLE_SIZE  = 38
BODY_SIZE   = 20
FOOTER_SIZE = 12

# Layout margins (EMU for python-pptx / EMU-scale reference; pixel equivalent shown)
MARGIN_LEFT   = 58   # ~58 px at 96 dpi
MARGIN_RIGHT  = 58
MARGIN_TOP    = 42
MARGIN_BOTTOM = 42

# Layout tokens for consistent spacing across slides
PAGE_MARGIN  = 58
TITLE_Y      = 42
CONTENT_TOP  = 120
CARD_GAP     = 16
SECTION_GAP  = 32
FOOTER_Y     = 680

# Build outputs
# INTERMEDIATE_PPTX  — produced by the Node.js builder + XML passes
# FINAL_PPTX         — produced by embed_video_v7.py + v7_targeted_fixes.py
OUTPUT_FILE       = "output/.ACMOT_Final_Paper_Realtime_v7_pre_keynote.pptx"
FINAL_OUTPUT_FILE = "output/ACMOT_Final_Paper_Realtime_v7.pptx"

SOURCE_REFERENCE  = "reference/original_presentation.pptx"
