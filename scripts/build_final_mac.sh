#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT="$(dirname "$ROOT")"
VIDEO_DIR="$ROOT/assets/videos"
BUILT="$ROOT/output/.ACMOT_Final_Paper_Realtime_v5_pre_keynote.pptx"
FINAL_KEY="$PARENT/ACMOT_Final_Paper_Realtime_v5_FINAL.key"
FINAL_PPTX="$ROOT/output/ACMOT_Final_Paper_Realtime_v5.pptx"
cd "$ROOT"

echo "Project: $ROOT"
echo "Branch: $(git branch --show-current)"
if [[ "$(git branch --show-current)" != "acmot-paper-realtime-v5" ]]; then
  echo "ERROR: expected branch acmot-paper-realtime-v5" >&2
  exit 1
fi
VIDEO="$VIDEO_DIR/uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4"
if [[ ! -f "$VIDEO" ]]; then
  echo "ERROR: required video not found: $VIDEO" >&2
  exit 1
fi
echo "Video selected: $VIDEO"
python3 build.py
if [[ ! -f "$BUILT" ]]; then
  echo "ERROR: build did not create $BUILT" >&2
  exit 1
fi
rm -rf "$FINAL_KEY"
rm -f "$FINAL_PPTX"
osascript "$ROOT/scripts/finalize_keynote.applescript" \
  "$BUILT" "$VIDEO" "$FINAL_KEY" "$FINAL_PPTX"
if [[ ! -e "$FINAL_KEY" ]]; then
  echo "ERROR: Keynote final file was not created: $FINAL_KEY" >&2
  exit 1
fi
if [[ ! -f "$FINAL_PPTX" ]]; then
  echo "ERROR: final PowerPoint was not created: $FINAL_PPTX" >&2
  exit 1
fi
python3 "$ROOT/scripts/embed_video_v5.py"
python3 "$ROOT/scripts/verify_final_pptx.py" "$FINAL_PPTX"
echo "FINAL KEY : $FINAL_KEY"
du -sh "$FINAL_KEY"
echo "FINAL PPTX: $FINAL_PPTX"
du -h "$FINAL_PPTX"
echo "VIDEO     : $VIDEO"
echo "VIDEO     : embedded natively on slide 59"
open -a Keynote "$FINAL_KEY"
