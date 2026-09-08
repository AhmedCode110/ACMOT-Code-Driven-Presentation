"""
Canonical paths for the AC-MOT presentation build.

Import these rather than constructing paths ad-hoc in scripts.
"""
from __future__ import annotations
from pathlib import Path

# Repository root (this file lives two levels down: config/paths.py)
ROOT = Path(__file__).resolve().parents[1]

# Source reference (the accepted V5 editable deck used as template)
SOURCE_REFERENCE = ROOT / "reference" / "original_presentation.pptx"

# Build intermediates
BUILD_DIR    = ROOT / ".build"
SLIDES_JSON  = BUILD_DIR / "slides_runtime.json"

# Output files
OUTPUT_DIR               = ROOT / "output"
INTERMEDIATE_PPTX        = OUTPUT_DIR / ".ACMOT_Final_Paper_Realtime_v7_pre_keynote.pptx"
FINAL_PPTX               = OUTPUT_DIR / "ACMOT_Final_Paper_Realtime_v7.pptx"

# Assets
ASSETS_DIR   = ROOT / "assets"
VIDEO_DIR    = ASSETS_DIR / "videos"
IMAGES_DIR   = ASSETS_DIR / "images"

# Evidence video (must be present for the media embed step)
EVIDENCE_VIDEO = VIDEO_DIR / "uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4"

# Expected slide count
EXPECTED_SLIDE_COUNT = 67
