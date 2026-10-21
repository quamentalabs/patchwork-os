#!/usr/bin/env node
// SPDX-License-Identifier: MIT
/*
 * Patchwork-OS hybrid statusline for Claude Code (cc-cli).
 *
 * Renders BOTH the primary 2-row card/gradient-bar statusline and graft's
 * repository context statusline, preserving the multi-row layout exactly.
 *
 * Composition rule:
 * - Primary source passes through WHOLE (every line preserved so row 2's
 *   fixed-anchor context bar and rate-limit windows are never dropped).
 * - Secondary source (graft) has duplicate context-usage segments stripped via
 *   DROP_SECONDARY_SEGMENTS and is appended to row 1 (out[0]).
 * - Each source runs in isolation with its own timeout so a failing or absent
 *   secondary never blanks the terminal HUD.
 */

'use strict';

const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const SEPARATOR = '  ·  ';
const PER_SOURCE_TIMEOUT_MS = 4000;
const MAX_LINES = 12;

const DROP_SECONDARY_SEGMENTS = [
  { name: 'context-usage', test: /\bctx\b[^%]{0,12}\d+(?:\.\d+)?\s*%/i },
];

const MARKER = '▸';

const HOME = process.platform === 'win32'
  ? (process.env.USERPROFILE || process.env.HOME || '')
  : os.homedir();
const REPO = process.env.CLAUDE_PROJECT_DIR || path.resolve(__dirname, '..', '..');

const BUNDLED_PRIMARY = path.join(REPO, '.claude', 'helpers', 'statusline.js');
const USER_PRIMARY = path.join(HOME, '.claude', 'statusline.js');

const PRIMARY = {
  name: 'operator',
  script: process.env.PATCHWORK_PRIMARY_STATUSLINE
    || (fs.existsSync(BUNDLED_PRIMARY) ? BUNDLED_PRIMARY : USER_PRIMARY),
};
const SECONDARY = {
  name: 'graft',
  script: path.join(REPO, '.claude', 'helpers', 'graft-statusline.cjs'),
};

function readStdin() {
  try {
    return fs.readFileSync(0);
  } catch (_) {
    return Buffer.from('{}', 'utf8');
  }
}

function stripAnsi(text) {
  return String(text).replace(/\u001b\[[0-9;]*[A-Za-z]/g, '');
}

function isBlank(line) {
  return stripAnsi(line).trim() === '';
}

function composeSecondary(lines) {
  const joined = lines.filter(function (line) { return !isBlank(line); }).join(' ');
  if (!joined) return '';
  const parts = joined.split(new RegExp('(?=(?:\\u001b\\[[0-9;]*m)*' + MARKER + ')'));
  const kept = parts.filter(function (part, index) {
    if (index === 0) return true;
    const plain = stripAnsi(part);
    return !DROP_SECONDARY_SEGMENTS.some(function (rule) { return rule.test.test(plain); });
  });
  return kept.join('').trim();
}

function runSource(source, payload) {
  try {
    if (!fs.existsSync(source.script)) return [];
    const result = spawnSync(process.execPath, [source.script], {
      input: payload,
      timeout: PER_SOURCE_TIMEOUT_MS,
      maxBuffer: 4 * 1024 * 1024,
      encoding: 'utf8',
      cwd: REPO,
      env: process.env,
      windowsHide: true,
    });
    const text = (result && result.stdout) || '';
    const lines = String(text).split(/\r?\n/);
    while (lines.length && isBlank(lines[lines.length - 1])) lines.pop();
    return lines.slice(0, MAX_LINES);
  } catch (_) {
    return [];
  }
}

function main() {
  const payload = readStdin();
  const primary = runSource(PRIMARY, payload);
  const secondary = runSource(SECONDARY, payload);
  const tail = composeSecondary(secondary);

  if (primary.length === 0 && !tail) {
    process.stdout.write('patchwork-statusline-hybrid: both sources silent\n');
    return;
  }

  if (primary.length === 0) {
    process.stdout.write(tail + '\n');
    return;
  }

  const out = primary.slice();
  if (tail) {
    out[0] = isBlank(out[0]) ? tail : out[0] + SEPARATOR + tail;
  }
  process.stdout.write(out.join('\n') + '\n');
}

if (require.main !== module) {
  module.exports = {
    composeSecondary: composeSecondary,
    stripAnsi: stripAnsi,
    DROP_SECONDARY_SEGMENTS: DROP_SECONDARY_SEGMENTS,
  };
  return;
}

try {
  main();
} catch (error) {
  process.stdout.write(
    'patchwork-statusline-hybrid: ' + String(error && error.message).slice(0, 160) + '\n'
  );
}
