// Bundles landing/index.html into a single minified file at the repo root,
// used as the GitHub Pages entry point. Run via `npm run build:landing` from webui-src
// so it resolves html-minifier-terser from webui-src/node_modules.
import { readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

// Resolved from cwd (webui-src, via `npm run build:landing`) so the package
// is found in webui-src/node_modules without landing/ needing its own install.
const requireFromCwd = createRequire(path.join(process.cwd(), "package.json"));
const { minify } = await import(pathToFileURL(requireFromCwd.resolve("html-minifier-terser")).href);

const here = path.dirname(fileURLToPath(import.meta.url));
const srcPath = path.join(here, "index.html");
const outPath = path.join(here, "..", "index.html");

const src = await readFile(srcPath, "utf8");
// landing/index.html previews locally with paths relative to landing/;
// the deployed copy lives at the repo root next to media/.
const rewritten = src.replaceAll("../media/", "media/");

const minified = await minify(rewritten, {
  collapseWhitespace: true,
  conservativeCollapse: false,
  removeComments: true,
  removeRedundantAttributes: true,
  removeScriptTypeAttributes: true,
  removeStyleLinkTypeAttributes: true,
  useShortDoctype: true,
  minifyCSS: true,
  minifyJS: true,
});

await writeFile(outPath, minified, "utf8");

const before = Buffer.byteLength(src, "utf8");
const after = Buffer.byteLength(minified, "utf8");
console.log(`landing: ${srcPath}`);
console.log(`  -> ${outPath}`);
console.log(`  ${before} bytes -> ${after} bytes (${(100 * after / before).toFixed(1)}%)`);