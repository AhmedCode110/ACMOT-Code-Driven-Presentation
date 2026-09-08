#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT="$(dirname "$ROOT")"
VIDEO_DIR="/Users/ahmedgouda/CLAUDECODEX/Master/macneo_wrk/09_Presentation/Code_Driven_ACMOT_Deck/assets/videos"
BUILT="$ROOT/output/ACMOT_Final_Paper_Realtime_v3.pptx"
FINAL_KEY="$PARENT/ACMOT_Final_Paper_Realtime_v3_FINAL.key"
FINAL_PPTX="$PARENT/ACMOT_Final_Paper_Realtime_v3_FINAL.pptx"

cd "$ROOT"

echo "Project: $ROOT"
echo "Branch: $(git branch --show-current)"
if [[ "$(git branch --show-current)" != "acmot-paper-realtime-v3" ]]; then
  echo "ERROR: expected branch acmot-paper-realtime-v3" >&2
  exit 1
fi

if [[ ! -d "$VIDEO_DIR" ]]; then
  echo "ERROR: video directory not found: $VIDEO_DIR" >&2
  exit 1
fi

# Prefer a comparison video whose name contains both baseline and AC-MOT/ACMOT.
VIDEO="$(find "$VIDEO_DIR" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.m4v' \) -print | \
  awk 'BEGIN{IGNORECASE=1} /baseline/ && /ac[-_ ]?mot|acmot/ {print; exit}')"

# If there is no explicitly named comparison file, prefer files with compare/comparison.
if [[ -z "$VIDEO" ]]; then
  VIDEO="$(find "$VIDEO_DIR" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.m4v' \) -print | \
    awk 'BEGIN{IGNORECASE=1} /compar|vs/ {print; exit}')"
fi

# Final fallback: use the first video in the supplied folder, but print it clearly.
if [[ -z "$VIDEO" ]]; then
  VIDEO="$(find "$VIDEO_DIR" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.m4v' \) -print -quit)"
fi

if [[ -z "$VIDEO" || ! -f "$VIDEO" ]]; then
  echo "ERROR: no supported video found in $VIDEO_DIR" >&2
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

python3 "$ROOT/scripts/verify_final_pptx.py" "$FINAL_PPTX"

echo
echo "FINAL KEY : $FINAL_KEY"
du -sh "$FINAL_KEY"
echo "FINAL PPTX: $FINAL_PPTX"
du -h "$FINAL_PPTX"
echo "VIDEO     : $VIDEO"
echo "VIDEO     : embedded natively on slide 59"
echo
open -a Keynote "$FINAL_KEY"
