#!/usr/bin/env node
// SPDX-License-Identifier: MIT
/*
 * Claude Code status line — card layout with an ADHD-support gradient context bar.
 *
 * Two rows:
 *   row 1  cards:   model · dir · cost · fresh tokens in · tokens out
 *   row 2  anchor:  gradient context bar · % · absolute usage · rate-limit windows
 *
 * The bar starts at column 0 on its own row so it never shifts horizontally when
 * the cards above it change width. A stable anchor is the point: the eye returns
 * to the same spot every time, and colour carries the state without reading.
 *
 * Bar colour is driven by the FILL FRACTION, not by cell position — at 13% the
 * whole fill is green, at 60% amber, at 92% red. Colouring by cell position
 * looks like a gradient in a screenshot but conveys nothing, because a barely
 * filled bar never leaves the green end of the ramp. A short ramp *within* the
 * fill keeps it from reading as a flat slab.
 *
 * The empty track is drawn with full blocks too, so the bar is a continuous
 * rectangle rather than a sparse dotted line — far more legible at a glance.
 *
 * Token card semantics (deliberate):
 *   context_window.total_input_tokens is the *whole current context* for the last
 *   request — the same quantity the bar renders. To avoid printing one number
 *   twice, the 📥 card shows the FRESH (uncached) input of the last request, and
 *   the absolute context usage sits beside the bar.
 *
 * Verified against the real payload from Claude Code 2.1.226+ on Windows.
 * Every field is optional: a missing or null field drops its card, never throws.
 */

'use strict';

/* ---------- color ---------- */

const NO_COLOR = !!process.env.NO_COLOR;

const fg = (r, g, b) => (NO_COLOR ? '' : `\x1b[38;2;${r};${g};${b}m`);
const RESET = NO_COLOR ? '' : '\x1b[0m';
const BOLD = NO_COLOR ? '' : '\x1b[1m';

// Deliberately no \x1b[2m (dim) anywhere: on a dark terminal it drops secondary
// text below readable contrast. Dimmer-but-readable greys do that job instead.
const C_LABEL = fg(150, 160, 178);
const C_MUTED = fg(130, 140, 158);
const C_SEP = fg(96, 104, 122);
const C_MODEL = fg(196, 165, 255);
const C_COST = fg(255, 200, 84);
const C_IN = fg(110, 180, 255);
const C_OUT = fg(255, 140, 158);
const C_DIR = fg(122, 222, 208);
const C_TRACK = fg(74, 80, 94);

/*
 * Warmth is held back until there is actually a decision to make. Amber at 50%
 * of a 1M context means half the ramp is spent on a region with 500k tokens of
 * headroom — a permanently warm indicator habituates, and then the real event
 * arrives already discounted.
 *
 * The alarm colour is also deliberately *brighter* than the calm one, not just
 * redder. Peripheral vision tracks luminance, so a ramp that darkens toward
 * danger whispers exactly when it should shout.
 */
const STOPS = [
  [0.0, [56, 224, 132]],
  [0.6, [150, 222, 92]],
  [0.8, [246, 208, 62]],
  [0.92, [255, 150, 40]],
  [1.0, [255, 108, 138]],
];

// Context exhaustion is an absolute hazard, not a proportional one: 10% left is
// 100k tokens on a 1M model and 20k on a 200k model. Threshold on what remains.
const WARN_REMAINING_TOKENS = 150000;
const ALARM_REMAINING_TOKENS = 60000;

function gradientAt(t) {
  const x = Math.max(0, Math.min(1, Number.isFinite(t) ? t : 0));
  for (let i = 0; i < STOPS.length - 1; i++) {
    const [t0, c0] = STOPS[i];
    const [t1, c1] = STOPS[i + 1];
    if (x >= t0 && x <= t1) {
      const f = t1 === t0 ? 0 : (x - t0) / (t1 - t0);
      return [
        Math.round(c0[0] + (c1[0] - c0[0]) * f),
        Math.round(c0[1] + (c1[1] - c0[1]) * f),
        Math.round(c0[2] + (c1[2] - c0[2]) * f),
      ];
    }
  }
  return STOPS[STOPS.length - 1][1];
}

/* ---------- formatting ---------- */

function compactNum(n) {
  if (!Number.isFinite(n) || n < 0) return null;
  if (n < 1000) return String(Math.round(n));
  if (n < 1000000) {
    const k = n / 1000;
    return (k < 10 ? k.toFixed(1) : Math.round(k)) + 'k';
  }
  const m = n / 1000000;
  return (m < 10 ? m.toFixed(1) : Math.round(m)) + 'M';
}

function money(n) {
  if (!Number.isFinite(n)) return null;
  return n >= 100 ? '$' + Math.round(n) : '$' + n.toFixed(2);
}

// "Opus 5 (1M context)" -> "Opus 5 (1M)"; short names pass through untouched.
function shortModel(name) {
  if (!name) return null;
  return String(name).replace(/\s*\(([^)]*?)\s*context\)/i, ' ($1)').trim();
}

function untilReset(epochSeconds, nowMs) {
  if (!Number.isFinite(epochSeconds)) return null;
  const ms = epochSeconds * 1000 - nowMs;
  if (ms <= 0) return 'now';
  const mins = Math.round(ms / 60000);
  if (mins < 60) return mins + 'm';
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h < 24) return m ? `${h}h${m}m` : `${h}h`;
  const days = Math.floor(h / 24);
  const rest = h % 24;
  return rest ? `${days}d${rest}h` : `${days}d`;
}

/* ---------- the gradient bar ---------- */

const EIGHTHS = ['', '▏', '▎', '▍', '▌', '▋', '▊', '▉'];
const BAR_WIDTH = 26;

/*
 * `fraction` drives both length and colour. Filled cells ramp from a deeper
 * shade up to the exact fill colour, so the bar always ends on the colour that
 * means "this is how full you are" while still reading as a gradient.
 */
function gradientBar(fraction, width, level) {
  const f = Math.max(0, Math.min(1, Number.isFinite(fraction) ? fraction : 0));
  const exact = f * width;
  const full = Math.floor(exact);
  const partIdx = Math.floor((exact - full) * 8);
  const lit = full + (partIdx > 0 ? 1 : 0);

  /*
   * The ramp spans [0.9f, f], not [0.55f, f]. A wider ramp shades prettily but
   * makes the bar's colour mass lag the true state: at 90% full a 0.55 ramp
   * renders mostly amber, disagreeing with the red number printed beside it.
   */
  const colorFor = (i) => gradientAt(lit <= 1 ? f : f * (0.9 + 0.1 * ((i + 1) / lit)));

  // A categorical glyph change carries the alarm where hue cannot: a green->red
  // sRGB ramp is not separable under deuteranopia (0% and 75% render alike), and
  // a discrete state beats a gradient when the alternative is comparing against
  // your memory of what the bar looked like five minutes ago.
  const fillGlyph = level === 'calm' ? '█' : '▓';
  /*
   * The track is always a light shade, never a full block. Colour is not a
   * reliable channel here: NO_COLOR strips it, and so does copying the line out
   * of the terminal — which is how this was caught, a 41% bar pasted into chat
   * reading as completely full. Three densities (░ ▓ █) stay distinct with no
   * colour at all, and the track still reads as a continuous gauge.
   */
  const trackGlyph = '░';

  let out = '';
  for (let i = 0; i < width; i++) {
    if (i < full) {
      const [r, g, b] = colorFor(i);
      out += fg(r, g, b) + fillGlyph;
    } else if (i === full && partIdx > 0) {
      const [r, g, b] = colorFor(i);
      out += fg(r, g, b) + EIGHTHS[partIdx];
    } else {
      out += C_TRACK + trackGlyph;
    }
  }
  return out + RESET;
}

/* ---------- assembly ---------- */

const card = (icon, color, value) => `${icon} ${color}${BOLD}${value}${RESET}`;

function render(d) {
  const nowMs = Date.now();
  const SEP = ` ${C_SEP}│${RESET} `;

  /* --- row 1: cards --- */
  const top = [];

  const model = shortModel(d?.model?.display_name || d?.model?.id);
  if (model) top.push(card('🧠', C_MODEL, d?.fast_mode ? model + ' ⚡' : model));

  const dirRaw = d?.workspace?.git_worktree
    || d?.workspace?.project_dir
    || d?.workspace?.current_dir
    || d?.cwd;
  if (dirRaw) {
    const leaf = String(dirRaw).split(/[\\/]/).filter(Boolean).pop();
    // Row 1 sits ~72 columns wide; a long worktree name pushes it to two lines,
    // which moves the bar down a row and destroys the fixed-anchor property that
    // the whole layout exists to provide.
    if (leaf) top.push(card('📁', C_DIR, leaf.length > 24 ? leaf.slice(0, 23) + '…' : leaf));
  }

  const cost = money(d?.cost?.total_cost_usd);
  if (cost) top.push(card('💰', C_COST, cost));

  // current_usage is null before the first API call and again after /compact.
  const cw = d?.context_window || {};
  const cu = cw.current_usage || {};
  const freshIn = (Number.isFinite(cu.input_tokens) || Number.isFinite(cu.cache_creation_input_tokens))
    ? (cu.input_tokens || 0) + (cu.cache_creation_input_tokens || 0)
    : null;
  const tin = compactNum(freshIn);
  if (tin) top.push(card('📥', C_IN, tin));

  const outTokens = Number.isFinite(cw.total_output_tokens) ? cw.total_output_tokens : cu.output_tokens;
  const tout = compactNum(outTokens);
  if (tout) top.push(card('📤', C_OUT, tout));

  /* --- row 2: the anchor --- */
  let pct = cw.used_percentage;
  if (!Number.isFinite(pct)) {
    const used = cw.total_input_tokens;
    const size = cw.context_window_size;
    pct = Number.isFinite(used) && Number.isFinite(size) && size > 0 ? (used / size) * 100 : null;
  }

  const bottom = [];
  if (Number.isFinite(pct)) {
    const frac = pct / 100;

    const size = cw.context_window_size;
    const remaining = Number.isFinite(size) && Number.isFinite(cw.total_input_tokens)
      ? size - cw.total_input_tokens
      : null;
    let level = 'calm';
    if (remaining !== null) {
      if (remaining <= ALARM_REMAINING_TOKENS) level = 'alarm';
      else if (remaining <= WARN_REMAINING_TOKENS) level = 'warn';
    } else if (frac >= 0.92) level = 'alarm';
    else if (frac >= 0.8) level = 'warn';

    const [r, g, b] = gradientAt(frac);
    const pctText = `${fg(r, g, b)}${BOLD}${String(Math.round(pct)).padStart(3)}%${RESET}`;

    // "470k left" instead of "530k/1.0M": the number the user acts on, without
    // making them subtract first. Working memory is the resource in deficit.
    const left = remaining === null ? null : compactNum(Math.max(0, remaining));
    const scale = left ? ` ${C_MUTED}${left} left${RESET}` : '';

    let flag = '';
    if (level === 'warn') flag = ` ${fg(255, 150, 40)}${BOLD}!${RESET}`;
    else if (level === 'alarm') flag = ` ${fg(255, 108, 138)}${BOLD}! COMPACT${RESET}`;

    bottom.push(`${gradientBar(frac, BAR_WIDTH, level)} ${pctText}${scale}${flag}`);
  }

  const rl = d?.rate_limits || {};
  const rlParts = [];
  for (const [label, w] of [['5h', rl.five_hour], ['7d', rl.seven_day]]) {
    if (!w || !Number.isFinite(w.used_percentage)) continue;
    const [r, g, b] = gradientAt(w.used_percentage / 100);
    const reset = untilReset(w.resets_at, nowMs);
    const tail = reset ? ` ${C_MUTED}↻ ${reset}${RESET}` : '';
    rlParts.push(`${C_LABEL}${label}${RESET} ${fg(r, g, b)}${BOLD}${Math.round(w.used_percentage)}%${RESET}${tail}`);
  }
  if (rlParts.length) bottom.push(rlParts.join(` ${C_SEP}·${RESET} `));

  const rows = [];
  if (top.length) rows.push(top.join(SEP));
  if (bottom.length) rows.push(bottom.join(SEP));
  return rows.join('\n');
}

/* ---------- quota observation: best effort, no UI output ---------- */
function appendQuotaObservation(d) {
  try {
    const limits = d?.rate_limits;
    if (!limits || typeof limits !== 'object' || Array.isArray(limits)) return;
    const fs = require('fs'), os = require('os'), path = require('path');
    const canonical = (v) => {
      if (Array.isArray(v)) return v.map(canonical);
      if (v && typeof v === 'object') return Object.fromEntries(Object.keys(v).sort().map(k => [k, canonical(v[k])]));
      return v;
    };
    const digest = require('crypto').createHash('sha256').update(JSON.stringify(canonical(limits))).digest('hex');
    const now = Date.now();
    const dir = path.join(os.homedir(), '.claude', 'quota');
    const log = path.join(dir, 'cc-rate-limits.jsonl');
    const sidecar = log + '.last.json';
    let previous;
    try { previous = JSON.parse(fs.readFileSync(sidecar, 'utf8')); } catch (_) {}
    if (previous?.digest === digest && now >= previous.ts_ms && now - previous.ts_ms < 60000 && fs.existsSync(log)) return;
    const transcript = typeof d.transcript_path === 'string' ? d.transcript_path.split(/[\\/]/).pop() : null;
    const record = {ts: new Date(now).toISOString(), host: os.hostname(), session_id: d.session_id ?? null,
      model: d.model?.id ?? null, transcript_path: transcript, rate_limits: limits, source: 'statusline-stdin', schema: 1};
    const line = JSON.stringify(record) + '\n';
    fs.mkdirSync(dir, {recursive: true});
    let bytes = 0;
    try { bytes = fs.statSync(log).size; } catch (_) {}
    if (bytes + Buffer.byteLength(line) >= 5 * 1024 * 1024 && bytes > 0) {
      try { fs.unlinkSync(log + '.1'); } catch (e) { if (e.code !== 'ENOENT') throw e; }
      fs.renameSync(log, log + '.1');
    }
    fs.appendFileSync(log, line, {encoding: 'utf8', mode: 0o600});
    fs.writeFileSync(sidecar, JSON.stringify({digest, ts_ms: now}), {encoding: 'utf8', mode: 0o600});
  } catch (_) {} // QUOTA_BEST_EFFORT_GUARD
}

/* ---------- io ---------- */

if (require.main !== module) {
  module.exports = {
    render,
    gradientBar,
    gradientAt,
    compactNum,
    money,
    shortModel,
    untilReset,
  };
  return;
}


// A blank status line is indistinguishable from a crash, so always print
// something: an unreadable payload still yields a visible, honest marker.
const FALLBACK = `${C_MUTED}claude${RESET}`;

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => { raw += c; });
process.stdin.on('end', () => {
  let out;
  try {
    const payload = JSON.parse(raw) || {};
    out = render(payload);
    appendQuotaObservation(payload);
  } catch (_) {
    out = '';
  }
  process.stdout.write(out || FALLBACK);
});
process.stdin.on('error', () => { process.stdout.write(FALLBACK); });
