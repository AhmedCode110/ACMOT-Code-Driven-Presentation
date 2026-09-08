from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import re
import sys
import xml.etree.ElementTree as ET


REQUIRED = (
    "19.718", "22.999", "28.418", "33.017", "32.716",
    "40.021", "1238", "994", "44.181", "37.686",
)
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
REL_NS = {"pr": "http://schemas.openxmlformats.org/package/2006/relationships"}


def pptx_text(xml_bytes: bytes) -> str:
    text = xml_bytes.decode("utf-8", errors="replace")
    return " ".join(re.findall(r"<a:t>(.*?)</a:t>", text, flags=re.S))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/verify_final_pptx.py <final.pptx>")

    path = Path(sys.argv[1]).resolve()
    problems: list[str] = []
    if not path.exists():
        raise SystemExit(f"ERROR: missing final PPTX: {path}")

    with ZipFile(path) as zf:
        names = set(zf.namelist())
        bad = zf.testzip()
        if bad:
            problems.append(f"corrupt ZIP member: {bad}")

        slides = [
            n for n in names
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
        ]
        if len(slides) != 67:
            problems.append(f"expected 67 slides, found {len(slides)}")

        slide59 = "ppt/slides/slide59.xml"
        if slide59 not in names:
            problems.append("slide59.xml missing")
        else:
            text = pptx_text(zf.read(slide59))
            missing = [v for v in REQUIRED if v not in text]
            if missing:
                problems.append("slide 59 missing official values: " + ", ".join(missing))

        rel_name = "ppt/slides/_rels/slide59.xml.rels"
        embedded_targets: list[str] = []
        if rel_name in names:
            root = ET.fromstring(zf.read(rel_name))
            for rel in root.findall("pr:Relationship", REL_NS):
                target = rel.get("Target") or ""
                suffix = Path(target).suffix.lower()
                if "../media/" in target and suffix in VIDEO_EXTS:
                    embedded_targets.append(target)

        if not embedded_targets:
            # Keynote exports can use media relationships indirectly; as a second
            # package-level check require at least one embedded video media file.
            package_videos = [
                n for n in names
                if n.startswith("ppt/media/") and Path(n).suffix.lower() in VIDEO_EXTS
            ]
            if not package_videos:
                problems.append("no embedded video media found in PPTX package")
        else:
            for target in embedded_targets:
                media_name = "ppt/media/" + Path(target).name
                if media_name not in names:
                    problems.append(f"slide 59 video relationship target missing: {media_name}")

    if problems:
        for item in problems:
            print("ERROR:", item)
        raise SystemExit(1)

    print(f"OK: final PPTX verified: {path}")
    print(f"OK: file size = {path.stat().st_size:,} bytes")
    print("OK: 67 slides; all 10 official slide-59 values present; embedded video media present")


if __name__ == "__main__":
    main()
