from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from content.overrides import OVERRIDES
from content.final_polish import FINAL_OVERRIDES
from presentation import slide_count
from theme.constants import OUTPUT_FILE, SOURCE_REFERENCE


ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / ".build"
NODE_BUILDER = ROOT / "scripts" / "build_deck.mjs"
XML_FORMATTER = ROOT / "scripts" / "xml_apply_overrides.py"
FINAL_POLISH_XML = ROOT / "scripts" / "final_polish_xml.py"
SLIDES_JSON = BUILD_DIR / "slides_runtime.json"
OUTPUT = ROOT / OUTPUT_FILE

DEFAULT_NODE = "/Users/ahmedgouda/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
DEFAULT_NODE_MODULES = "/Users/ahmedgouda/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
DEFAULT_SKILL_GLOB = "/Users/ahmedgouda/.codex/plugins/cache/openai-primary-runtime/presentations/*/skills/presentations"
DEFAULT_RUNTIME_PYTHON = "/Users/ahmedgouda/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"


def _first_existing(candidates: list[str | Path]) -> Path | None:
    for item in candidates:
        path = Path(item).expanduser()
        if path.exists():
            return path
    return None


def resolve_node() -> str:
    requested = os.environ.get("RUNTIME_NODE")
    if requested and Path(requested).exists():
        return requested
    default = Path(DEFAULT_NODE)
    if default.exists():
        return str(default)
    found = shutil.which("node")
    if found:
        return found
    raise RuntimeError(
        "Node.js was not found. Install Node.js or set RUNTIME_NODE to the executable path."
    )


def resolve_node_modules() -> Path:
    requested = os.environ.get("RUNTIME_NODE_MODULES")
    candidates: list[str | Path] = []
    if requested:
        candidates.append(requested)
    candidates.extend(
        [
            DEFAULT_NODE_MODULES,
            ROOT / "node_modules",
        ]
    )
    found = _first_existing(candidates)
    if found:
        return found
    raise RuntimeError(
        "Node modules were not found. Set RUNTIME_NODE_MODULES to the directory that contains "
        "@oai/artifact-tool (normally the Codex runtime node_modules directory)."
    )


def resolve_skill_dir() -> Path:
    requested = os.environ.get("SKILL_DIR")
    if requested and Path(requested).exists():
        return Path(requested)

    matches = [Path(p) for p in glob.glob(DEFAULT_SKILL_GLOB) if Path(p).is_dir()]
    if matches:
        return max(matches, key=lambda p: p.stat().st_mtime)

    raise RuntimeError(
        "Presentation skill directory was not found. Set SKILL_DIR to the Codex presentations skill directory."
    )


def resolve_runtime_python() -> str:
    requested = os.environ.get("RUNTIME_PYTHON")
    if requested and Path(requested).exists():
        return requested
    if Path(DEFAULT_RUNTIME_PYTHON).exists():
        return DEFAULT_RUNTIME_PYTHON
    return sys.executable


def backup_existing_output() -> Path | None:
    if not OUTPUT.exists():
        return None
    backup_dir = BUILD_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"{OUTPUT.stem}_{stamp}.pptx"
    shutil.copy2(OUTPUT, backup)
    print(f"Backed up previous generated PPTX -> {backup}")
    return backup


def prepare_runtime_files(node_modules: Path) -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    for link in (BUILD_DIR / "node_modules", ROOT / "node_modules"):
        if link.is_symlink() and not link.exists():
            link.unlink()
        if not link.exists():
            link.symlink_to(node_modules, target_is_directory=True)

    SLIDES_JSON.write_text(
        __import__("json").dumps(
            {
                "source": str(ROOT / SOURCE_REFERENCE),
                "overrides": OVERRIDES + FINAL_OVERRIDES,
                "output": str(OUTPUT),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    node = resolve_node()
    node_modules = resolve_node_modules()
    skill_dir = resolve_skill_dir()
    runtime_python = resolve_runtime_python()

    backup_existing_output()
    prepare_runtime_files(node_modules)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["SKILL_DIR"] = str(skill_dir)
    env["RUNTIME_NODE_MODULES"] = str(node_modules)
    env["RUNTIME_PYTHON"] = runtime_python
    env["PRESENTATION_PROJECT_ROOT"] = str(ROOT)
    env["PRESENTATION_RUNTIME_JSON"] = str(SLIDES_JSON)
    env["TMP_DIR"] = str(BUILD_DIR)

    print(f"Node: {node}")
    print(f"Node modules: {node_modules}")
    print(f"Presentation skill: {skill_dir}")
    print(f"Runtime Python: {runtime_python}")

    subprocess.run([node, str(NODE_BUILDER)], check=True, env=env)

    # First pass: preserve the established editable typography/chart cleanup.
    subprocess.run([sys.executable, str(XML_FORMATTER), str(OUTPUT)], check=True)

    # Second pass: Results-only polish for slides 54,55,56,58,59. This changes
    # native text formatting/alignment only and keeps charts/shapes editable.
    subprocess.run([sys.executable, str(FINAL_POLISH_XML), str(OUTPUT)], check=True)

    # Validate post-processed package, exact slide count, exact official values,
    # and rejection of historical slide-59 ablation numerics.
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py")], check=True)
    print(f"Built {slide_count()} slides -> {OUTPUT}")


if __name__ == "__main__":
    main()
