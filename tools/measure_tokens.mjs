#!/usr/bin/env node
// Read-only token measurement helper for the public GitHub profile README.
// Zero model calls, zero network calls, zero keys, zero writes.
//
// Outputs one JSON object on stdout:
//   stats_total              Claude Code /stats total (raw un-deduplicated: input + output +
//                            cache_creation + cache_read, matching Claude Code's /stats screen)
//   stats_as_of              Local date string "D Mon YYYY" (e.g. "27 Nov 2026")
//   active_days              Count of distinct local days with Claude Code activity
//   since_label              Month + year of earliest active day (e.g. "May 2026")
//   cross_model_dedup_total  Deduplicated total (once per reply: message.id|requestId) across
//                            Claude (main, worker, retired), Gemini lanes, Anthropic API runs,
//                            Codex (state_5.sqlite), and OmniRoute (carried 2M floor).
//   breakdown                Per-source byte/token breakdown for diagnostics.

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const HOME = os.homedir();
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function localDateStr(ms) {
  const d = new Date(ms);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function formatAsOf(d) {
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

function formatSince(isoDay) {
  if (!isoDay || isoDay.length < 7) return 'May 2026';
  const [y, m] = isoDay.split('-');
  const mi = Number(m) - 1;
  return `${MONTHS[mi] || 'May'} ${y}`;
}

function walkJsonl(dir, minMtimeMs, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  let entries;
  try { entries = fs.readdirSync(dir); } catch { return acc; }
  for (const name of entries) {
    const p = path.join(dir, name);
    let st;
    try { st = fs.statSync(p); } catch { continue; }
    if (st.isDirectory()) {
      walkJsonl(p, minMtimeMs, acc);
    } else if (name.endsWith('.jsonl') && (minMtimeMs == null || st.mtimeMs >= minMtimeMs)) {
      acc.push(p);
    }
  }
  return acc;
}

function measureClaudeStats() {
  const scPath = path.join(HOME, '.claude', 'stats-cache.json');
  const projectsDir = path.join(HOME, '.claude', 'projects');
  let scModelTotal = 0;
  let scBaseTotal = 0;
  let lastComputedDate = null;
  const activeDays = new Set();

  if (fs.existsSync(scPath)) {
    const sc = JSON.parse(fs.readFileSync(scPath, 'utf8'));
    lastComputedDate = sc.lastComputedDate || null;
    for (const v of Object.values(sc.modelUsage || {})) {
      scModelTotal +=
        (v.inputTokens || 0) +
        (v.outputTokens || 0) +
        (v.cacheCreationInputTokens || 0) +
        (v.cacheReadInputTokens || 0);
    }
    let partialAfterLast = 0;
    if (lastComputedDate) {
      for (const d of sc.dailyModelTokens || []) {
        if (d.date && d.date > lastComputedDate) {
          for (const v of Object.values(d.tokensByModel || {})) partialAfterLast += v || 0;
        }
      }
    }
    scBaseTotal = Math.max(0, scModelTotal - partialAfterLast);
    for (const d of sc.dailyActivity || []) {
      if (d.date) activeDays.add(d.date);
    }
  }

  // Scan only JSONL files modified near or after lastComputedDate (48h margin for timezone).
  const cutoffMs = lastComputedDate
    ? Date.parse(`${lastComputedDate}T00:00:00Z`) - 48 * 3600 * 1000
    : null;
  const files = walkJsonl(projectsDir, cutoffMs);
  let tailRaw = 0;
  const tailDays = new Set();

  for (const f of files) {
    let txt;
    try { txt = fs.readFileSync(f, 'utf8'); } catch { continue; }
    let pos = 0;
    while (pos < txt.length) {
      let nl = txt.indexOf('\n', pos);
      if (nl === -1) nl = txt.length;
      const line = txt.slice(pos, nl);
      pos = nl + 1;
      if (line.indexOf('"usage"') === -1) continue;
      let j;
      try { j = JSON.parse(line); } catch { continue; }
      const u = j.message?.usage;
      if (!u || !j.timestamp) continue;
      const ms = Date.parse(j.timestamp);
      if (Number.isNaN(ms)) continue;
      const localDay = localDateStr(ms);
      if (!lastComputedDate || localDay > lastComputedDate) {
        tailRaw +=
          (u.input_tokens || 0) +
          (u.output_tokens || 0) +
          (u.cache_creation_input_tokens || 0) +
          (u.cache_read_input_tokens || 0);
        tailDays.add(localDay);
        activeDays.add(localDay);
      }
    }
  }

  const total = Math.max(scModelTotal, scBaseTotal + tailRaw);
  const sortedDays = [...activeDays].sort();
  return {
    total,
    scModelTotal,
    scBaseTotal,
    tailRaw,
    lastComputedDate,
    activeDays: activeDays.size,
    firstDay: sortedDays[0] || '2026-05-29',
    lastDay: sortedDays[sortedDays.length - 1] || localDateStr(Date.now()),
    tailFilesScanned: files.length,
  };
}

function tailClaudeDedup(root, minUtcDay, minMtimeMs) {
  const files = walkJsonl(root, minMtimeMs);
  const seen = new Set();
  const byDay = {};
  for (const f of files) {
    let txt;
    try { txt = fs.readFileSync(f, 'utf8'); } catch { continue; }
    let pos = 0;
    while (pos < txt.length) {
      let nl = txt.indexOf('\n', pos);
      if (nl === -1) nl = txt.length;
      const line = txt.slice(pos, nl);
      pos = nl + 1;
      if (line.indexOf('"usage"') === -1) continue;
      let j;
      try { j = JSON.parse(line); } catch { continue; }
      const u = j.message?.usage;
      if (!u || !j.timestamp) continue;
      const utcDay = j.timestamp.slice(0, 10);
      if (minUtcDay && utcDay < minUtcDay) continue;
      const k = `${j.message.id || ''}|${j.requestId || ''}`;
      if (k !== '|' && seen.has(k)) continue;
      if (k !== '|') seen.add(k);
      const n =
        (u.input_tokens || 0) +
        (u.output_tokens || 0) +
        (u.cache_creation_input_tokens || 0) +
        (u.cache_read_input_tokens || 0);
      byDay[utcDay] = (byDay[utcDay] || 0) + n;
    }
  }
  return byDay;
}

async function measureCrossModelDedup() {
  const ledgerCandidates = [
    path.join(HOME, 'Vault', 'Projects', 'career-2027', 'linkedin', 'ledger', 'token-ledger-daily.jsonl'),
  ];
  const ledger = new Map();
  let ledgerLoaded = false;

  for (const lp of ledgerCandidates) {
    if (!fs.existsSync(lp)) continue;
    try {
      for (const line of fs.readFileSync(lp, 'utf8').split('\n')) {
        if (!line.trim()) continue;
        const r = JSON.parse(line);
        if (r.source && r.day && typeof r.total === 'number') {
          const k = `${r.source}|${r.day}`;
          const prev = ledger.get(k);
          if (!prev || r.total > prev.total) ledger.set(k, { source: r.source, day: r.day, total: r.total });
        }
      }
      ledgerLoaded = true;
      break;
    } catch { /* ignore */ }
  }

  const maxDayFor = (src) => {
    let best = null;
    for (const r of ledger.values()) {
      if (r.source === src && (!best || r.day > best)) best = r.day;
    }
    return best;
  };

  const upsert = (src, byDay) => {
    for (const [day, total] of Object.entries(byDay)) {
      const k = `${src}|${day}`;
      const prev = ledger.get(k);
      if (!prev || total > prev.total) ledger.set(k, { source: src, day, total });
    }
  };

  // Top up claude-main and claude-worker from recent JSONL files since the ledger's last recorded day.
  for (const [src, root] of [
    ['claude-main', path.join(HOME, '.claude', 'projects')],
    ['claude-worker', path.join(HOME, '.claude-worker', 'projects')],
  ]) {
    const maxDay = maxDayFor(src);
    const minDay = maxDay || null;
    const minMtimeMs = maxDay ? Date.parse(`${maxDay}T00:00:00Z`) - 48 * 3600 * 1000 : null;
    upsert(src, tailClaudeDedup(root, minDay, minMtimeMs));
  }

  // Gemini lanes (dispatch-run-logs)
  const gdir = path.join(HOME, '.claude', 'ai-pools', 'dispatch-run-logs');
  if (fs.existsSync(gdir)) {
    const gemByDay = {};
    for (const f of fs.readdirSync(gdir)) {
      const dm = f.match(/^(\d{4})(\d{2})(\d{2})-/);
      if (!dm) continue;
      let txt;
      try { txt = fs.readFileSync(path.join(gdir, f), 'utf8'); } catch { continue; }
      const m = txt.match(/^- stats\s*:\s*(\{.*\})\s*$/m);
      if (!m) continue;
      try {
        const s = JSON.parse(m[1]);
        const day = `${dm[1]}-${dm[2]}-${dm[3]}`;
        gemByDay[day] =
          (gemByDay[day] || 0) +
          (s.input_tokens || 0) +
          (s.output_tokens || 0) +
          (s.thinking_tokens || 0) +
          (s.cache_read_tokens || 0);
      } catch { /* skip */ }
    }
    upsert('gemini-lanes', gemByDay);
  }

  // Anthropic API runs
  const adir = path.join(HOME, '.claude', 'ai-pools', 'anthropic-runs');
  if (fs.existsSync(adir)) {
    const apiByDay = {};
    for (const f of fs.readdirSync(adir)) {
      if (!f.endsWith('.json')) continue;
      const day = f.slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) continue;
      let mu;
      try { mu = JSON.parse(fs.readFileSync(path.join(adir, f), 'utf8')).output?.modelUsage || {}; } catch { continue; }
      for (const v of Object.values(mu)) {
        apiByDay[day] =
          (apiByDay[day] || 0) +
          (v.inputTokens || 0) +
          (v.outputTokens || 0) +
          (v.cacheCreationInputTokens || 0) +
          (v.cacheReadInputTokens || 0);
      }
    }
    upsert('anthropic-api-runs', apiByDay);
  }

  const bySource = {};
  let sum = 0;
  for (const r of ledger.values()) {
    bySource[r.source] = (bySource[r.source] || 0) + r.total;
    sum += r.total;
  }

  // Codex (state_5.sqlite thread totals)
  let codex = 0;
  const codexDb = path.join(HOME, '.codex', 'state_5.sqlite');
  if (fs.existsSync(codexDb)) {
    try {
      const { DatabaseSync } = await import('node:sqlite');
      const db = new DatabaseSync(codexDb, { readOnly: true });
      const row = db.prepare('select sum(tokens_used) as t from threads').get();
      codex = Number(row?.t || 0);
      db.close();
    } catch { /* ignore if sqlite unavailable */ }
  }
  if (codex > 0) {
    bySource.codex = codex;
    sum += codex;
  }

  // OmniRoute gateway carried floor (same 7 Nov census convention as token-totals-all.mjs)
  const omni = 2_000_000;
  bySource.omniroute = omni;
  sum += omni;

  return { total: sum, ledgerLoaded, bySource };
}

const stats = measureClaudeStats();
const cross = await measureCrossModelDedup();

const out = {
  measured_at: new Date().toISOString(),
  stats_total: stats.total,
  stats_as_of: formatAsOf(new Date()),
  active_days: stats.activeDays,
  since_label: formatSince(stats.firstDay),
  cross_model_dedup_total: cross.total,
  breakdown: {
    stats_cache_total: stats.scModelTotal,
    stats_cache_last_computed: stats.lastComputedDate,
    stats_tail_raw: stats.tailRaw,
    stats_tail_files: stats.tailFilesScanned,
    cross_model_ledger_loaded: cross.ledgerLoaded,
    cross_model_by_source: cross.bySource,
  },
};

process.stdout.write(JSON.stringify(out, null, 2) + '\n');
