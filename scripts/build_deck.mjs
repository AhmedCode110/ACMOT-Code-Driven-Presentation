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

for (const edit of data.overrides || []) {
  if (edit.action === "replace_text") {
    const before = await presentation.inspect({
      kind: "slide,textbox,shape,table,chart,notes",
      search: edit.search,
      maxChars: 12000,
    });
    const candidate = before.ndjson
      .split("\n")
      .filter(Boolean)
      .map(line => JSON.parse(line))
      .find(row => row.slide === edit.slide && row.id && row.kind === "textbox");
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
