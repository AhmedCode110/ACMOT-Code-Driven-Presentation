#!/bin/bash
# build_final_mac.sh — AC-MOT V7 one-command Mac build
#
# Normal workflow (Codex runtime available):
#   1. python3 build.py          — generates intermediate PPTX via Node.js/Codex
#   2. embed_video_v7.py         — physically embeds the MP4 into the PPTX
#   3. v7_targeted_fixes.py      — applies A1/30.1 FPS label + font normalisation
#   4. scripts/validate.py       — comprehensive A–J validation
#
# Direct workflow (no Codex runtime — Claude Code / local Mac):
#   Run scripts/build_v7_from_source.py which applies XML patches directly.
#
# Keynote round-trip is OPTIONAL and disabled by default because AppleScript
# automation has historically produced -1708/-1700/-1728/-1712 errors.
# Set KEYNOTE=1 to enable it.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VIDEO="$ROOT/assets/videos/uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4"
INTERMEDIATE="$ROOT/output/.ACMOT_Final_Paper_Realtime_v7_pre_keynote.pptx"
FINAL="$ROOT/output/ACMOT_Final_Paper_Realtime_v7.pptx"
KEYNOTE="${KEYNOTE:-0}"

echo "============================================================"
echo "  AC-MOT V7 — Mac build"
echo "  Branch : $(git branch --show-current)"
echo "  Root   : $ROOT"
echo "============================================================"

if [[ "$(git branch --show-current)" != "acmot-paper-realtime-v7" ]]; then
  echo "ERROR: expected branch acmot-paper-realtime-v7" >&2
  exit 1
fi

if [[ ! -f "$VIDEO" ]]; then
  echo "ERROR: evidence video not found: $VIDEO" >&2
  exit 1
fi
echo "Video    : $VIDEO"

mkdir -p "$ROOT/output"

# ── Step 1: generate the presentation ────────────────────────────────────────
if python3 build.py 2>/dev/null; then
  echo "Step 1   : Codex build succeeded"
else
  echo "Step 1   : Codex Node.js runtime unavailable — running direct XML build"
  python3 scripts/build_v7_from_source.py
fi

if [[ ! -f "$INTERMEDIATE" ]] && [[ ! -f "$FINAL" ]]; then
  echo "ERROR: neither intermediate nor final PPTX was produced" >&2
  exit 1
fi

# ── Step 2: embed video (only if intermediate was produced by Codex build) ───
if [[ -f "$INTERMEDIATE" ]] && [[ ! -f "$FINAL" ]]; then
  echo "Step 2   : embedding evidence video"
  python3 scripts/embed_video_v7.py
fi

# ── Step 3: apply targeted XML fixes ─────────────────────────────────────────
if [[ -f "$FINAL" ]]; then
  echo "Step 3   : applying targeted V7 XML fixes"
  python3 scripts/v7_targeted_fixes.py
  echo "Step 3b  : raising tiny table text, normalising font sizes"
  python3 scripts/fix_typography.py
  echo "Step 3c  : containing text inside its blocks, repairing font attributes"
  python3 scripts/fix_layout_fit.py
fi

# ── Step 4 (optional): Keynote round-trip ────────────────────────────────────
if [[ "$KEYNOTE" == "1" ]] && [[ -f "$INTERMEDIATE" ]]; then
  echo "Step 4   : Keynote round-trip (optional)"
  FINAL_KEY="$(dirname "$ROOT")/ACMOT_Final_Paper_Realtime_v7_FINAL.key"
  osascript "$ROOT/scripts/finalize_keynote.applescript" \
    "$INTERMEDIATE" "$VIDEO" "$FINAL_KEY" "$FINAL" || {
    echo "WARNING: Keynote step failed — continuing with existing PPTX"
  }
fi

# ── Step 5: comprehensive A–J validation ─────────────────────────────────────
echo "Step 5   : validating final PPTX"
python3 scripts/validate.py "$FINAL"

# ── Step 6: export a native Keynote document for Mac presenting ──────────────
# Optional and non-fatal: the PPTX stays the authoritative deliverable.
FINAL_KEY="$ROOT/output/ACMOT_Final_Paper_Realtime_v7.key"
if [[ "${SKIP_KEY:-0}" != "1" ]]; then
  echo "Step 6   : exporting native Keynote document"
  rm -rf "$FINAL_KEY"
  if osascript "$ROOT/scripts/export_keynote.applescript" "$FINAL" "$FINAL_KEY"; then
    echo "           Keynote export OK"
  else
    echo "           WARNING: Keynote export failed — PPTX is still valid"
  fi
fi

echo ""
echo "============================================================"
echo "  FINAL PPTX : $FINAL"
du -sh "$FINAL"
if [[ -e "$FINAL_KEY" ]]; then
  echo "  FINAL KEY  : $FINAL_KEY"
  du -sh "$FINAL_KEY"
fi
echo "============================================================"
