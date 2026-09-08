#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PARENT="$(dirname "$ROOT")"
VIDEO_NAME="uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4"
VIDEO="$ROOT/assets/videos/$VIDEO_NAME"
BUILT="$ROOT/output/ACMOT_Final_Paper_Realtime_v2.pptx"
FINAL_KEY="$PARENT/ACMOT_Final_Paper_Realtime_v2_FINAL.key"
FINAL_PPTX="$PARENT/ACMOT_Final_Paper_Realtime_v2_FINAL.pptx"

cd "$ROOT"

echo "Project: $ROOT"
echo "Branch: $(git branch --show-current)"
if [[ "$(git branch --show-current)" != "acmot-paper-realtime-v2" ]]; then
  echo "ERROR: expected branch acmot-paper-realtime-v2" >&2
  exit 1
fi

# Use the repository copy when present. If it is missing, search only nearby
# presentation/project copies under the same 09_Presentation parent folder.
if [[ ! -f "$VIDEO" ]]; then
  echo "Video not found in repo; searching nearby exact filename only..."
  FOUND="$(find "$PARENT" -maxdepth 5 -type f -name "$VIDEO_NAME" -not -path "$VIDEO" -print -quit 2>/dev/null || true)"
  if [[ -z "$FOUND" ]]; then
    echo "ERROR: could not find $VIDEO_NAME under $PARENT" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$VIDEO")"
  cp -p "$FOUND" "$VIDEO"
  echo "Copied video from: $FOUND"
fi

# Build the editable 67-slide PPTX from the current branch source.
python3 build.py

if [[ ! -f "$BUILT" ]]; then
  echo "ERROR: build did not create $BUILT" >&2
  exit 1
fi

# Remove only the requested final outputs so Keynote can save/export cleanly.
rm -rf "$FINAL_KEY"
rm -f "$FINAL_PPTX"

# Import the generated PPTX into Keynote, embed the MP4 natively on slide 59,
# save the primary .key file, then export that same document back to PPTX.
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
echo "VIDEO     : embedded natively by Keynote on slide 59"
echo
# Open the primary result in Keynote for the final visual pass.
open -a Keynote "$FINAL_KEY"
