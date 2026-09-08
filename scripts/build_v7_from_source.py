"""
build_v7_from_source.py — Direct V7 build without Codex Node.js runtime.

This script rebuilds output/ACMOT_Final_Paper_Realtime_v7.pptx by applying
all required patches directly to the source reference PPTX.  It is equivalent
to the full Codex pipeline (build.py → embed_video_v7.py → v7_targeted_fixes.py)
but runs entirely in standard Python with no external dependencies.

Use when:
  - The Codex Node.js runtime is unavailable (e.g. Claude Code, clean Mac)
  - A single metric or slide text needs to change without a full Codex rebuild

Pipeline:
  1. Copy reference/original_presentation.pptx → output intermediate
  2. Apply text overrides (content/overrides.py + content/final_polish.py)
  3. Normalise fonts to Helvetica Neue on Results slides 54-59
  4. Embed the evidence MP4 (assets/videos/uav0000249_…)
  5. Apply V7 targeted fixes (A1 / 30.1 FPS; Slide 59 video frame; fonts)
  6. Save as output/ACMOT_Final_Paper_Realtime_v7.pptx
  7. Run comprehensive A–J validation
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

# ── Project root on sys.path so config/ and content/ resolve correctly ────────
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.paths import (
    EVIDENCE_VIDEO,
    EXPECTED_SLIDE_COUNT,
    FINAL_PPTX,
    INTERMEDIATE_PPTX,
    SOURCE_REFERENCE,
)
from content.overrides import OVERRIDES
from content.final_polish import FINAL_OVERRIDES

NS_P  = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A  = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_R  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PR = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
for _k, _v in [("p", NS_P), ("a", NS_A), ("r", NS_R)]:
    ET.register_namespace(_k, _v)


# ── 1. Load source ────────────────────────────────────────────────────────────

def load_source(src: Path) -> tuple[list, dict[str, bytes]]:
    with ZipFile(src) as zf:
        infos = zf.infolist()
        data = {item.filename: zf.read(item.filename) for item in infos}
    return infos, data


# ── 2. Apply text overrides ───────────────────────────────────────────────────

def _replace_in_slide(xml_bytes: bytes, search: str, replace: str) -> bytes:
    text = xml_bytes.decode("utf-8", errors="replace")
    updated = text.replace(search, replace)
    return updated.encode("utf-8")


def apply_overrides(data: dict[str, bytes], overrides: list[dict]) -> None:
    for override in overrides:
        if override.get("action") != "replace_text":
            continue
        slide_num = override.get("slide")
        if not slide_num:
            continue
        name = f"ppt/slides/slide{slide_num}.xml"
        if name not in data:
            continue
        data[name] = _replace_in_slide(
            data[name], override["search"], override["replace"]
        )


# ── 3. Normalise fonts on Results slides ─────────────────────────────────────

def normalise_fonts(root: ET.Element) -> None:
    for el in list(root.findall(f".//{{{NS_A}}}rPr")) + list(
        root.findall(f".//{{{NS_A}}}defRPr")
    ):
        for attr in ("typeface", "latin", "ea", "cs"):
            el.set(attr, "Helvetica Neue")


def apply_font_normalisation(data: dict[str, bytes], slide_nums: tuple[int, ...]) -> None:
    for num in slide_nums:
        name = f"ppt/slides/slide{num}.xml"
        if name not in data:
            continue
        root = ET.fromstring(data[name])
        normalise_fonts(root)
        data[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)


# ── 4. Embed MP4 video on Slide 59 ───────────────────────────────────────────

def embed_video(data: dict[str, bytes], video_path: Path) -> None:
    slide_name = "ppt/slides/slide59.xml"
    rels_name  = "ppt/slides/_rels/slide59.xml.rels"
    media_name = "ppt/media/acmot_v7_evidence.mp4"
    video_rid  = "rIdACMOTVideo59"

    rels = ET.fromstring(data[rels_name])
    image_rid = None
    for rel in rels.findall(f"{{{NS_PR}}}Relationship"):
        t = rel.get("Target", "")
        if "/media/" in t and t.lower().endswith((".png", ".jpeg", ".jpg")):
            image_rid = rel.get("Id")
            break
    if not image_rid:
        print("WARNING: no poster image relationship on slide 59 — video embed skipped")
        return

    ET.SubElement(
        rels, f"{{{NS_PR}}}Relationship",
        {
            "Id": video_rid,
            "Type": f"{NS_R.replace('officeDocument', 'officeDocument')}/video",
            "Target": "../media/acmot_v7_evidence.mp4",
        },
    )
    data[rels_name] = ET.tostring(rels, encoding="utf-8", xml_declaration=True)

    slide = ET.fromstring(data[slide_name])
    sp = slide.find(f"p:cSld/p:spTree", {"p": NS_P})
    if sp is None:
        print("WARNING: slide 59 shape tree not found — video embed skipped")
        return

    ids = []
    for c in sp.findall(f".//{{{NS_P}}}cNvPr"):
        try:
            ids.append(int(c.get("id", "0")))
        except ValueError:
            pass

    pic = ET.Element(f"{{{NS_P}}}pic")
    nv  = ET.SubElement(pic, f"{{{NS_P}}}nvPicPr")
    ET.SubElement(nv, f"{{{NS_P}}}cNvPr", {"id": str(max(ids + [1]) + 1), "name": "AC-MOT embedded video evidence"})
    ET.SubElement(nv, f"{{{NS_P}}}cNvPicPr")
    nvpr = ET.SubElement(nv, f"{{{NS_P}}}nvPr")
    ET.SubElement(nvpr, f"{{{NS_A}}}videoFile", {f"{{{NS_R}}}link": video_rid})
    bf = ET.SubElement(pic, f"{{{NS_P}}}blipFill")
    ET.SubElement(bf, f"{{{NS_A}}}blip", {f"{{{NS_R}}}embed": image_rid})
    st = ET.SubElement(bf, f"{{{NS_A}}}stretch")
    ET.SubElement(st, f"{{{NS_A}}}fillRect")
    sppr = ET.SubElement(pic, f"{{{NS_P}}}spPr")
    xfrm = ET.SubElement(sppr, f"{{{NS_A}}}xfrm")
    ET.SubElement(xfrm, f"{{{NS_A}}}off", {"x": "609600", "y": "1320800"})
    ET.SubElement(xfrm, f"{{{NS_A}}}ext", {"cx": "8128000", "cy": "4572000"})
    pg = ET.SubElement(sppr, f"{{{NS_A}}}prstGeom", {"prst": "rect"})
    ET.SubElement(pg, f"{{{NS_A}}}avLst")
    sp.append(pic)
    data[slide_name] = ET.tostring(slide, encoding="utf-8", xml_declaration=True)

    # Add mp4 content type if absent
    ct = ET.fromstring(data["[Content_Types].xml"])
    if not any(e.get("Extension") == "mp4" for e in ct.findall(f"{{{NS_CT}}}Default")):
        ET.SubElement(ct, f"{{{NS_CT}}}Default", {"Extension": "mp4", "ContentType": "video/mp4"})
    data["[Content_Types].xml"] = ET.tostring(ct, encoding="utf-8", xml_declaration=True)

    data[media_name] = video_path.read_bytes()
    print(f"  Embedded {video_path.name} as {media_name} (rId={video_rid})")


# ── 5. Add A1 / 30.1 FPS label on Slide 55 ───────────────────────────────────

def _shape_text(shape: ET.Element) -> str:
    return " / ".join(t.text or "" for t in shape.findall(f".//{{{NS_A}}}t"))


def _set_text(shape: ET.Element, value: str) -> None:
    runs = shape.findall(f".//{{{NS_A}}}t")
    if not runs:
        return
    runs[0].text = value
    for run in runs[1:]:
        run.text = ""


def _set_geom(shape: ET.Element, x: int, y: int, cx: int | None = None, cy: int | None = None) -> None:
    off = shape.find(f".//{{{NS_A}}}xfrm/{{{NS_A}}}off")
    ext = shape.find(f".//{{{NS_A}}}xfrm/{{{NS_A}}}ext")
    if off is None or ext is None:
        return
    off.set("x", str(x))
    off.set("y", str(y))
    if cx is not None:
        ext.set("cx", str(cx))
    if cy is not None:
        ext.set("cy", str(cy))


def add_a1_fps_label(data: dict[str, bytes]) -> None:
    name = "ppt/slides/slide55.xml"
    if name not in data:
        return

    # Check if already present
    existing = _slide_text_quick(data[name])
    if "A1" in existing and "30.1" in existing:
        print("  Slide 55: A1/30.1 FPS already present — skipping")
        return

    root = ET.fromstring(data[name])
    tree = root.find(f"p:cSld/p:spTree", {"p": NS_P})
    if tree is None:
        return
    shapes = tree.findall(f"{{{NS_P}}}sp")

    category = next((s for s in shapes if _shape_text(s).strip() == "A2"), None)
    value    = next((s for s in shapes if _shape_text(s).strip() == "29.8 FPS"), None)
    if category is None or value is None:
        print("  WARNING: Slide 55 A2/29.8 FPS source labels not found — A1 label not added")
        return

    new_cat = deepcopy(category)
    _set_text(new_cat, "A1")
    _set_geom(new_cat, 609479, 4279859)
    tree.append(new_cat)

    new_val = deepcopy(value)
    _set_text(new_val, "30.1 FPS")
    _set_geom(new_val, 2077873, 4293535)
    tree.append(new_val)

    data[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    print("  Added A1 / 30.1 FPS label to Slide 55")


def _slide_text_quick(xml_bytes: bytes) -> str:
    return " ".join(re.findall(r"<a:t>(.*?)</a:t>", xml_bytes.decode("utf-8", errors="replace"), re.S))


# ── 6. Fix Slide 59 video frame geometry ─────────────────────────────────────

def fix_slide59_video_frame(data: dict[str, bytes]) -> None:
    name = "ppt/slides/slide59.xml"
    if name not in data:
        return
    root = ET.fromstring(data[name])
    for pic in root.findall(f".//{{{NS_P}}}pic"):
        if pic.find(f".//{{{NS_A}}}videoFile") is not None:
            _set_geom(pic, 609600, 1320800, 8128000, 4572000)
            data[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            print("  Fixed Slide 59 video frame geometry (16:9, correct position)")
            return
    print("  INFO: Slide 59 video object not yet present (will be added by embed step)")


# ── 7. Save PPTX ──────────────────────────────────────────────────────────────

def save_pptx(infos: list, data: dict[str, bytes], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="acmot_v7_build_", suffix=".pptx", dir=output.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
    with ZipFile(tmp, "w", ZIP_DEFLATED) as dst:
        for info in infos:
            if info.filename in data:
                dst.writestr(info, data[info.filename])
        # write any new entries (e.g. embedded video) not in original infos
        existing = {i.filename for i in infos}
        for name, content in data.items():
            if name not in existing:
                dst.writestr(name, content)
    tmp.replace(output)
    print(f"  Saved  {output}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("AC-MOT V7 — direct XML build (no Codex runtime required)")
    print(f"  Source  : {SOURCE_REFERENCE}")

    if not SOURCE_REFERENCE.exists():
        raise SystemExit(f"ERROR: source reference not found: {SOURCE_REFERENCE}")
    if not EVIDENCE_VIDEO.exists():
        print(f"  WARNING : evidence video not found: {EVIDENCE_VIDEO}")
        print("            Slide 59 will not contain the embedded MP4.")

    print("Step 1: loading source reference...")
    infos, data = load_source(SOURCE_REFERENCE)

    print("Step 2: applying text overrides...")
    apply_overrides(data, OVERRIDES)
    apply_overrides(data, FINAL_OVERRIDES)

    print("Step 3: normalising fonts on Results slides...")
    apply_font_normalisation(data, (54, 55, 56, 57, 58, 59))

    if EVIDENCE_VIDEO.exists():
        print("Step 4: embedding evidence video...")
        embed_video(data, EVIDENCE_VIDEO)
    else:
        print("Step 4: SKIPPED (evidence video not found)")

    print("Step 5: applying V7 targeted fixes...")
    add_a1_fps_label(data)
    fix_slide59_video_frame(data)

    print("Step 6: saving final PPTX...")
    save_pptx(infos, data, FINAL_PPTX)

    print("Step 7: running A–J validation...")
    import subprocess
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate.py"), str(FINAL_PPTX)],
        capture_output=False,
    )
    if result.returncode != 0:
        raise SystemExit("Validation failed — see errors above")

    print(f"\nDone.  Final PPTX: {FINAL_PPTX}")
    print(f"       Size       : {FINAL_PPTX.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
