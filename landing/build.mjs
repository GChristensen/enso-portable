// Bundles landing/index.html into a single minified file at the repo root,
// used as the GitHub Pages entry point. Local stylesheets (<link rel="stylesheet">)
// and scripts (<script src>) referenced by index.html are inlined.
// Run via `npm run build:landing` from webui-src
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

const isLocal = (url) => !/^([a-z]+:)?\/\//i.test(url);

let src = await readFile(srcPath, "utf8");
let before = Buffer.byteLength(src, "utf8");

// Collect local asset contents first, since String.replace callbacks can't await.
const assets = new Map();
const assetRefs = [
  ...src.matchAll(/<link\s+rel="stylesheet"\s+href="([^"]+)"\s*\/?>/g),
  ...src.matchAll(/<script\s+src="([^"]+)"\s*><\/script>/g),
];
for (const [, url] of assetRefs) {
  if (isLocal(url) && !assets.has(url)) {
    const content = await readFile(path.join(here, url), "utf8");
    assets.set(url, content);
    before += Buffer.byteLength(content, "utf8");
  }
}

// Function replacers so `$` sequences in asset contents are not interpreted.
src = src
  .replace(/<link\s+rel="stylesheet"\s+href="([^"]+)"\s*\/?>/g,
    (tag, url) => assets.has(url) ? `<style>\n${assets.get(url)}</style>` : tag)
  .replace(/<script\s+src="([^"]+)"\s*><\/script>/g,
    (tag, url) => assets.has(url) ? `<script>\n${assets.get(url)}</script>` : tag);

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

const after = Buffer.byteLength(minified, "utf8");
console.log(`landing: ${srcPath}`);
for (const url of assets.keys()) console.log(`  + ${url}`);
console.log(`  -> ${outPath}`);
console.log(`  ${before} bytes -> ${after} bytes (${(100 * after / before).toFixed(1)}%)`);
