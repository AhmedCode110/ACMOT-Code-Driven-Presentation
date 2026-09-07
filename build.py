from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from content.overrides import OVERRIDES
from presentation import slide_count
from theme.constants import OUTPUT_FILE, SOURCE_REFERENCE


ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / ".build"
NODE_BUILDER = ROOT / "scripts" / "build_deck.mjs"
SLIDES_JSON = BUILD_DIR / "slides_runtime.json"
OUTPUT = ROOT / OUTPUT_FILE

DEFAULT_NODE = "/Users/ahmedgouda/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
DEFAULT_NODE_MODULES = "/Users/ahmedgouda/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
DEFAULT_SKILL_DIR = "/Users/ahmedgouda/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations"
DEFAULT_RUNTIME_PYTHON = "/Users/ahmedgouda/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"


def resolve_node() -> str:
    requested = os.environ.get("RUNTIME_NODE") or DEFAULT_NODE
    if Path(requested).exists():
        return requested
    found = shutil.which("node")
    if found:
        return found
    raise RuntimeError("Node.js was not found. Set RUNTIME_NODE to the Codex bundled node path.")


def prepare_runtime_files() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    modules = Path(os.environ.get("RUNTIME_NODE_MODULES") or DEFAULT_NODE_MODULES)
    for link in (BUILD_DIR / "node_modules", ROOT / "node_modules"):
        if modules.exists() and not link.exists():
            link.symlink_to(modules, target_is_directory=True)
    SLIDES_JSON.write_text(
        __import__("json").dumps(
            {
                "source": str(ROOT / SOURCE_REFERENCE),
                "overrides": OVERRIDES,
                "output": str(OUTPUT),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    prepare_runtime_files()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("SKILL_DIR", DEFAULT_SKILL_DIR)
    env.setdefault("RUNTIME_NODE_MODULES", DEFAULT_NODE_MODULES)
    env.setdefault("RUNTIME_PYTHON", DEFAULT_RUNTIME_PYTHON)
    env["PRESENTATION_PROJECT_ROOT"] = str(ROOT)
    env["PRESENTATION_RUNTIME_JSON"] = str(SLIDES_JSON)
    env["TMP_DIR"] = str(BUILD_DIR)
    subprocess.run([resolve_node(), str(NODE_BUILDER)], check=True, env=env)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py")], check=True)
    print(f"Built {slide_count()} slides -> {OUTPUT}")


if __name__ == "__main__":
    main()
