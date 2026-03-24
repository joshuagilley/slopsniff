#!/usr/bin/env node
/* eslint-disable no-console */

const fs = require("node:fs");
const path = require("node:path");

function shouldSkip() {
  if (process.env.npm_config_global === "true") {
    return true;
  }
  if (!process.env.INIT_CWD) {
    return true;
  }
  return false;
}

function readJsonObject(filePath, label) {
  const raw = fs.readFileSync(filePath, "utf8");
  const data = JSON.parse(raw);
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    throw new Error(`${label} must be a JSON object`);
  }
  return data;
}

/** Add keys from template that are missing in existing (does not overwrite user values). */
function mergeMissingConfigKeys(existing, template) {
  let added = 0;
  const out = { ...existing };
  for (const key of Object.keys(template)) {
    if (!(key in out)) {
      out[key] = JSON.parse(JSON.stringify(template[key]));
      added += 1;
    }
  }
  return { merged: out, added };
}

function main() {
  if (shouldSkip()) {
    return;
  }

  const projectRoot = process.env.INIT_CWD;
  const targetPath = path.join(projectRoot, "slopsniff.json");
  const templatePath = path.join(__dirname, "..", "templates", "slopsniff.json");

  try {
    const template = readJsonObject(templatePath, "package template");

    if (!fs.existsSync(targetPath)) {
      fs.copyFileSync(templatePath, targetPath);
      console.log("slopsniff-cli: created starter slopsniff.json");
      return;
    }

    let existing;
    try {
      existing = readJsonObject(targetPath, "slopsniff.json");
    } catch (err) {
      console.warn(`slopsniff-cli: skipped config merge (${err.message})`);
      return;
    }

    const { merged, added } = mergeMissingConfigKeys(existing, template);
    if (added === 0) {
      return;
    }

    fs.writeFileSync(targetPath, `${JSON.stringify(merged, null, 2)}\n`, "utf8");
    console.log(
      `slopsniff-cli: added ${added} missing config key(s) to slopsniff.json (existing values unchanged)`
    );
  } catch (err) {
    console.warn(`slopsniff-cli: could not update slopsniff.json (${err.message})`);
  }
}

main();
