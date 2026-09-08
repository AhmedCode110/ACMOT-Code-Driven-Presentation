import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const root = process.env.PRESENTATION_PROJECT_ROOT;
const runtimeJson = process.env.PRESENTATION_RUNTIME_JSON;
const skillDir = process.env.SKILL_DIR;
const runtimePython = process.env.RUNTIME_PYTHON;
if (!root || !runtimeJson || !skillDir || !runtimePython) {
  throw new Error("Missing PRESENTATION_PROJECT_ROOT, PRESENTATION_RUNTIME_JSON, SKILL_DIR, or RUNTIME_PYTHON");
}

const data = JSON.parse(await fs.readFile(runtimeJson, "utf8"));
const presentation = await PresentationFile.importPptx(await FileBlob.load(data.source));

function rowsFromInspection(result) {
  return result.ndjson
    .split("\n")
    .filter(Boolean)
    .map(line => JSON.parse(line));
}

function candidateOnSlide(rows, slide) {
  return rows.find(row => row.slide === slide && row.id && row.kind === "textbox");
}

function fallbackProbe(text) {
  // Artifact-tool search treats some punctuation (notably '*') specially.
  // Pick the longest plain-text fragment so we can locate the same textbox,
  // while still applying the exact literal replacement afterwards.
  const fragments = text
    .split(/[\*;:,.()\[\]{}<>→–—|/\\]+/u)
    .map(part => part.replace(/\s+/g, " ").trim())
    .filter(part => part.length >= 12);
  fragments.sort((a, b) => b.length - a.length);
  return fragments[0] || text.replace(/[^\p{L}\p{N}\s_-]/gu, " ").replace(/\s+/g, " ").trim();
}

async function findTextboxForOverride(edit) {
  const exact = await presentation.inspect({
    kind: "slide,textbox,shape,table,chart,notes",
    search: edit.search,
    maxChars: 12000,
  });
  let candidate = candidateOnSlide(rowsFromInspection(exact), edit.slide);
  if (candidate) return candidate;

  const probe = fallbackProbe(edit.search);
  if (probe && probe !== edit.search) {
    const fallback = await presentation.inspect({
      kind: "slide,textbox,shape,table,chart,notes",
      search: probe,
      maxChars: 12000,
    });
    candidate = candidateOnSlide(rowsFromInspection(fallback), edit.slide);
    if (candidate) {
      console.log(`Override lookup fallback on slide ${edit.slide}: ${probe}`);
      return candidate;
    }
  }
  return null;
}

for (const edit of data.overrides || []) {
  if (edit.action === "replace_text") {
    const candidate = await findTextboxForOverride(edit);
    if (!candidate) {
      throw new Error(`Could not find text override target on slide ${edit.slide}: ${edit.search}`);
    }
    const target = presentation.resolve(candidate.id);
    target.text.replace(edit.search, edit.replace);
  }
}

const outputPath = data.output;
const finalizerDir = path.join(root, ".codex-finalizer");
await fs.mkdir(finalizerDir, { recursive: true });
await fs.mkdir(path.dirname(outputPath), { recursive: true });
const candidatePath = path.join(finalizerDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

try {
  await fs.unlink(outputPath);
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}

const { finalizePresentation } = await import(pathToFileURL(
  path.join(skillDir, "container_tools/artifact_tool_utils.mjs"),
).href);

await finalizePresentation({
  workspaceDir: root,
  candidatePath,
  finalPath: outputPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000"],
  explicitTotalSlideCount: presentation.slides.items.length,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  fontPolicy: {
    basis: "reference",
    families: ["Helvetica Neue"],
    referencePath: path.join(root, "reference/original_presentation.pptx"),
    referenceSha256: "40a0bbbee9c16c0b6272096bdb1cfa9201e2aa74eb0905962ab39234c98a0636",
  },
  verifyArtifactToolImport: true,
  receiptPath: path.join(finalizerDir, `presentation_${Date.now()}.validation.json`),
});
