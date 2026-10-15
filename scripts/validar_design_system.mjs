import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import ts from "typescript";

function files(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? files(path) : [path];
  });
}

const errors = [];
for (const path of files("app")) {
  const source = readFileSync(path, "utf8");
  if (path.endsWith(".css") && path !== "app/styles/tokens.css") {
    const css = source.replace(/\/\*[\s\S]*?\*\//g, "");
    if (/#[\da-f]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\(/i.test(css)) {
      errors.push(`${path}: use tokens semânticos em vez de cores literais.`);
    }
    if (/font-size\s*:\s*[^;{}]*\d(?:px|rem)\b/i.test(css)) {
      errors.push(`${path}: use a escala tipográfica de tokens.css.`);
    }
  }
  if (!path.endsWith(".tsx")) continue;
  const tree = ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  function visit(node) {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const name = node.tagName.getText(tree);
      if ((name === "button" && path !== "app/components/ui/button.tsx") ||
          (name === "select" && path !== "app/components/ui/select-field.tsx")) {
        const { line } = tree.getLineAndCharacterOfPosition(node.getStart(tree));
        errors.push(`${path}:${line + 1}: reutilize ${name === "button" ? "Button" : "SelectField"}.`);
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(tree);
}
if (errors.length) {
  console.error(errors.join("\n"));
  process.exitCode = 1;
} else console.log("Design system: cores, tipografia e controles sem duplicações locais.");
