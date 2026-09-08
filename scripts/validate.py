from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from content.slides import SLIDES
from theme.constants import OUTPUT_FILE

OUTPUT = ROOT / OUTPUT_FILE
EXPECTED_SLIDES = 67
SLIDE59_REQUIRED = (
    "19.718",
    "22.999",
    "28.418",
    "33.017",
    "32.716",
    "40.021",
    "1238",
    "994",
    "44.181",
    "37.686",
)
SLIDE59_FORBIDDEN_HISTORICAL = (
    "0.2161",
    "0.4449",
    "0.3505",
    "0.5359",
    "+0.2287",
    "+0.1854",
)


def _slide_number(name: str) -> int:
    m = re.search(r"slide(\d+)\.xml$", name)
    return int(m.group(1)) if m else -1


def _pptx_text(xml_bytes: bytes) -> str:
    text = xml_bytes.decode("utf-8", errors="replace")
    return " ".join(re.findall(r"<a:t>(.*?)</a:t>", text, flags=re.S))


def main() -> None:
    ids = list(SLIDES)
    problems: list[str] = []

    if len(ids) != len(set(ids)):
        problems.append("Duplicate slide IDs")
    if sorted(ids) != list(range(1, len(ids) + 1)):
        problems.append("Slide IDs are not contiguous")
    if len(SLIDES) != EXPECTED_SLIDES:
        problems.append(f"Source metadata slide count {len(SLIDES)} != expected {EXPECTED_SLIDES}")

    for sid, slide in SLIDES.items():
        if not slide.get("title"):
            problems.append(f"Slide {sid} has no title")

    if not OUTPUT.exists():
        problems.append(f"Missing output: {OUTPUT}")
    else:
        try:
            with ZipFile(OUTPUT) as zf:
                bad_member = zf.testzip()
                if bad_member:
                    problems.append(f"Corrupt ZIP member: {bad_member}")

                names = set(zf.namelist())
                for required in ("[Content_Types].xml", "ppt/presentation.xml"):
                    if required not in names:
                        problems.append(f"Missing PPTX package member: {required}")

                ppt_slides = sorted(
                    (
                        n
                        for n in names
                        if n.startswith("ppt/slides/slide") and n.endswith(".xml")
                    ),
                    key=_slide_number,
                )
                if len(ppt_slides) != len(SLIDES):
                    problems.append(
                        f"Output slide count {len(ppt_slides)} != source metadata {len(SLIDES)}"
                    )
                if len(ppt_slides) != EXPECTED_SLIDES:
                    problems.append(
                        f"Output slide count {len(ppt_slides)} != expected {EXPECTED_SLIDES}"
                    )

                slide59 = "ppt/slides/slide59.xml"
                if slide59 not in names:
                    problems.append("Missing slide 59 XML")
                else:
                    s59_text = _pptx_text(zf.read(slide59))
                    missing = [value for value in SLIDE59_REQUIRED if value not in s59_text]
                    if missing:
                        problems.append(
                            "Slide 59 is missing official metric value(s): " + ", ".join(missing)
                        )
                    historical = [
                        value for value in SLIDE59_FORBIDDEN_HISTORICAL if value in s59_text
                    ]
                    if historical:
                        problems.append(
                            "Slide 59 still contains historical ablation value(s): "
                            + ", ".join(historical)
                        )
        except Exception as exc:
            problems.append(f"PPTX integrity read failed: {exc}")

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        raise SystemExit(1)

    print(
        f"OK: {EXPECTED_SLIDES} slides; PPTX package readable; slide 59 contains all "
        f"10 official final values and no historical ablation values; output={OUTPUT}"
    )


if __name__ == "__main__":
    main()
