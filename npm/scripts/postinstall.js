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

function main() {
  if (shouldSkip()) {
    return;
  }

  const projectRoot = process.env.INIT_CWD;
  const targetPath = path.join(projectRoot, "slopsniff.json");
  const templatePath = path.join(__dirname, "..", "templates", "slopsniff.json");

  if (fs.existsSync(targetPath)) {
    return;
  }

  try {
    fs.copyFileSync(templatePath, targetPath);
    console.log("slopsniff-cli: created starter slopsniff.json");
  } catch (err) {
    console.warn(`slopsniff-cli: could not create slopsniff.json (${err.message})`);
  }
}

main();
