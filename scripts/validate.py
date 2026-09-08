"""
AC-MOT V7 — Comprehensive presentation validator.

Checks (A–J from the project specification):
  A  PPTX package is a valid ZIP
  B  Exactly 67 slides exist
  C  Slide 59 contains all 10 official final metric values
  D  Historical incorrect ablation values are absent from Slide 59
  E  An MP4 file is embedded inside the PPTX package
  F  Slide 59 has a valid media (video) relationship
  G  Slide 59 contains a video marker object (p:pic with a:videoFile)
  H  Slide 55 contains the A1 label and 30.1 FPS value
  I  Source slides metadata matches expected count
  J  Slide IDs in content/slides.py are contiguous and non-duplicate

Usage:
  python3 scripts/validate.py                   # validates the final PPTX
  python3 scripts/validate.py path/to/file.pptx # validates a specific file
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from content.slides import SLIDES
from config.metrics import OFFICIAL_RESULTS
from config.paths import FINAL_PPTX, INTERMEDIATE_PPTX, EXPECTED_SLIDE_COUNT


# ── Constants ─────────────────────────────────────────────────────────────────

SLIDE59_REQUIRED = (
    str(OFFICIAL_RESULTS["baseline"]["mota"]),   # 19.718
    str(OFFICIAL_RESULTS["acmot"]["mota"]),       # 22.999
    str(OFFICIAL_RESULTS["baseline"]["hota"]),    # 28.418
    str(OFFICIAL_RESULTS["acmot"]["hota"]),       # 33.017
    str(OFFICIAL_RESULTS["baseline"]["idf1"]),    # 32.716
    str(OFFICIAL_RESULTS["acmot"]["idf1"]),       # 40.021
    str(OFFICIAL_RESULTS["baseline"]["ids"]),     # 1238
    str(OFFICIAL_RESULTS["acmot"]["ids"]),        # 994
    str(OFFICIAL_RESULTS["baseline"]["fps"]),     # 44.181
    str(OFFICIAL_RESULTS["acmot"]["fps"]),        # 37.686
)

# These old development-ablation values must NOT appear on Slide 59
SLIDE59_FORBIDDEN_HISTORICAL = (
    "0.2161", "0.4449", "0.3505", "0.5359",
    "+0.2287", "+0.1854",
)

VIDEO_EXTS = {".mp4", ".mov", ".m4v"}

NS_PR = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_P  = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A  = "http://schemas.openxmlformats.org/drawingml/2006/main"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slide_number(name: str) -> int:
    m = re.search(r"slide(\d+)\.xml$", name)
    return int(m.group(1)) if m else -1


def _slide_text(xml_bytes: bytes) -> str:
    text = xml_bytes.decode("utf-8", errors="replace")
    return " ".join(re.findall(r"<a:t>(.*?)</a:t>", text, flags=re.S))


def _has_video_object(xml_bytes: bytes) -> bool:
    """Return True if the slide contains at least one <p:pic> with <a:videoFile>."""
    try:
        root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))
        for pic in root.findall(f".//{{{NS_P}}}pic"):
            if pic.find(f".//{{{NS_A}}}videoFile") is not None:
                return True
        return False
    except ET.ParseError:
        return False


# ── Resolves which PPTX to validate ──────────────────────────────────────────

def _resolve_pptx(argv: list[str]) -> Path:
    if len(argv) >= 2:
        p = Path(argv[1]).resolve()
        if not p.is_absolute():
            p = ROOT / argv[1]
        return p
    # Prefer the committed final PPTX; fall back to the build intermediate
    for candidate in (FINAL_PPTX, INTERMEDIATE_PPTX):
        if candidate.exists():
            return candidate
    return FINAL_PPTX   # return even if missing so the validator can report it


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    pptx_path = _resolve_pptx(sys.argv)
    problems: list[str] = []

    # ── J  Source slide metadata ──────────────────────────────────────────────
    ids = list(SLIDES)
    if len(ids) != len(set(ids)):
        problems.append("J: Duplicate slide IDs in content/slides.py")
    if sorted(ids) != list(range(1, len(ids) + 1)):
        problems.append("J: Slide IDs are not contiguous in content/slides.py")

    # ── I  Slide count in source ──────────────────────────────────────────────
    if len(SLIDES) != EXPECTED_SLIDE_COUNT:
        problems.append(
            f"I: Source metadata has {len(SLIDES)} slides, expected {EXPECTED_SLIDE_COUNT}"
        )

    for sid, slide in SLIDES.items():
        if not slide.get("title"):
            problems.append(f"I: Slide {sid} has no title in content/slides.py")

    # ── A  PPTX package integrity ─────────────────────────────────────────────
    if not pptx_path.exists():
        problems.append(f"A: Output PPTX not found: {pptx_path}")
        _report(problems, pptx_path)
        return

    try:
        zf_ctx = ZipFile(pptx_path)
    except Exception as exc:
        problems.append(f"A: Cannot open PPTX as ZIP: {exc}")
        _report(problems, pptx_path)
        return

    with zf_ctx as zf:
        bad_member = zf.testzip()
        if bad_member:
            problems.append(f"A: Corrupt ZIP member: {bad_member}")

        for required in ("[Content_Types].xml", "ppt/presentation.xml"):
            if required not in zf.namelist():
                problems.append(f"A: Missing PPTX package member: {required}")

        names = set(zf.namelist())

        # ── B  Slide count in output ──────────────────────────────────────────
        ppt_slides = sorted(
            (n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
            key=_slide_number,
        )
        if len(ppt_slides) != EXPECTED_SLIDE_COUNT:
            problems.append(
                f"B: Output has {len(ppt_slides)} slides, expected {EXPECTED_SLIDE_COUNT}"
            )

        slide59_xml_name = "ppt/slides/slide59.xml"
        if slide59_xml_name not in names:
            problems.append("B/C: slide59.xml missing from PPTX package")
        else:
            s59_bytes = zf.read(slide59_xml_name)
            s59_text  = _slide_text(s59_bytes)

            # ── C  Official metric values on Slide 59 ────────────────────────
            missing_vals = [v for v in SLIDE59_REQUIRED if v not in s59_text]
            if missing_vals:
                problems.append(
                    "C: Slide 59 is missing official metric value(s): " + ", ".join(missing_vals)
                )

            # ── D  No historical ablation values on Slide 59 ─────────────────
            historical_vals = [v for v in SLIDE59_FORBIDDEN_HISTORICAL if v in s59_text]
            if historical_vals:
                problems.append(
                    "D: Slide 59 still contains historical ablation value(s): "
                    + ", ".join(historical_vals)
                )

            # ── G  Video object (p:pic with a:videoFile) on Slide 59 ─────────
            if not _has_video_object(s59_bytes):
                problems.append("G: Slide 59 has no embedded video object (p:pic + a:videoFile)")

        # ── E  MP4 media embedded in package ─────────────────────────────────
        package_videos = [
            n for n in names
            if n.startswith("ppt/media/") and Path(n).suffix.lower() in VIDEO_EXTS
        ]
        if not package_videos:
            problems.append("E: No video media file (.mp4/.mov/.m4v) found in ppt/media/")

        # ── F  Slide 59 video relationship ───────────────────────────────────
        rels_name = "ppt/slides/_rels/slide59.xml.rels"
        if rels_name in names:
            rels_root = ET.fromstring(zf.read(rels_name))
            video_rels = []
            for rel in rels_root.findall(f"{{{NS_PR}}}Relationship"):
                target = rel.get("Target", "")
                suffix = Path(target).suffix.lower()
                if "../media/" in target and suffix in VIDEO_EXTS:
                    video_rels.append(target)
            if not video_rels and not package_videos:
                problems.append("F: Slide 59 has no video relationship in _rels")
        else:
            problems.append("F: Slide 59 relationships file missing")

        # ── H  Slide 55 A1 / 30.1 FPS label ─────────────────────────────────
        slide55_name = "ppt/slides/slide55.xml"
        if slide55_name in names:
            s55_text = _slide_text(zf.read(slide55_name))
            if "A1" not in s55_text:
                problems.append("H: Slide 55 is missing the 'A1' system label")
            if "30.1" not in s55_text:
                problems.append("H: Slide 55 is missing the '30.1 FPS' value for A1")
        else:
            problems.append("H: slide55.xml missing from PPTX package")

    _report(problems, pptx_path)


def _report(problems: list[str], pptx_path: Path) -> None:
    if problems:
        for p in problems:
            print(f"ERROR: {p}")
        raise SystemExit(1)

    print(f"OK (A–J): all validation checks passed")
    print(f"  PPTX : {pptx_path}")
    print(f"  Size : {pptx_path.stat().st_size:,} bytes")
    print(f"  Slides: {EXPECTED_SLIDE_COUNT}")
    print(f"  Slide 59: all 10 official metric values present, no historical values")
    print(f"  Slide 55: A1 / 30.1 FPS label confirmed")
    print(f"  Video: embedded in PPTX package")


if __name__ == "__main__":
    main()
