/* Reads the TV home screen's own layout for every plate in the README hero, from the real page (tv-setup.html served
   by the TV hub on this laptop), so the hero copies it rather than guessing:

     node tools/measure_tv.mjs [--hub=http://127.0.0.1:8790] [--shots=<dir>]

   For each plate it shows the painting, swaps the clock's text for ETHAN / SOH (hours-over-minutes layout, the TV's
   own two-line clock), lets the TV's placeClock() and legibility check place and colour it, and records where every
   letter's ink box landed, the clock's ink, opacity, blend and halo, the date line, and the widget cards' boxes.
   Output: tools/tv-layout.json. Read only: every request other than GET is refused, so nothing reaches the hub's
   saved settings. Playwright's bundled Chromium, headless (Playwright spawns it with windowsHide). */
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const require = createRequire("C:/Users/ethan/Vault/Projects/phone-fleet/app/package.json");
const { chromium } = require("playwright-core");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2), opt = (k, d) => (args.find(a => a.startsWith(`--${k}=`)) || `--${k}=${d}`).slice(k.length + 3);
const HUB = opt("hub", "http://127.0.0.1:8790"), SHOTS = opt("shots", "");
const EXE = "C:/Users/ethan/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe";
const IDS = JSON.parse(fs.readFileSync(path.join(HERE, "plates.json"), "utf8")).map(p => p.id);
const MODE = opt("mode", "auto"), TAG = opt("tag", "Applied AI · AI security");
const GAP = [446, 1474];   // between the widget column (ends 434) and the Claude cards (start 1486), 12 px clear each side
const STACK_BELOW = 0.52;  // auto: a one-line name smaller than this share of his size goes on two lines instead

const browser = await chromium.launch({ executablePath: EXE, headless: true });
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, reducedMotion: "reduce" });
await ctx.route("**/*", r => (r.request().method() === "GET" || r.request().method() === "HEAD" ? r.continue() : r.abort()));
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", e => errors.push(String(e)));
await page.goto(HUB + "/tv-setup.html?kiosk=tv", { waitUntil: "load" });
await page.waitForTimeout(6000);
// the minute's roll redraws the clock's text; while measuring, every redraw draws the name instead
await page.evaluate(() => { const orig = fillTime; fillTime = (time, text) => orig(time, window.__NAME || text); });
const out ={ when: new Date().toISOString(), hub: HUB, plates: {} };

for (const id of IDS) {
  const r = await page.evaluate(async ({ id, TAG, MODE, GAP, STACK_BELOW }) => {
    const i = PLATES.findIndex(p => p.id === id);
    if (i < 0) return { error: "no plate " + id };
    show(i);
    await new Promise(r => setTimeout(r, 1800));
    const s = rec[id].settings, saved = JSON.parse(JSON.stringify(s));
    const dk = curDk;
    // the name instead of the time (in memory only; nothing is saved), its size brought down until it fits between the
    // two widget columns (the rule his own pipeline used for f1ceiling, PROPOSED in tv-setup.html). One line, "ETHAN SOH",
    // where that keeps most of his size; otherwise the TV's two-line layout (hours over minutes), "ETHAN" over "SOH"
    const size0 = s.size, room = GAP[1] - GAP[0];
    const span = () => { const r = dk.cells.map(c => c.el.getBoundingClientRect()); return Math.max(...r.map(b => b.right)) - Math.min(...r.map(b => b.left)); };
    const fitTo = (orient, text) => {
      window.__NAME = text; s.orient = orient; s.size = size0; styleDeck(dk); setText(dk, text);
      const w = span(), f = Math.min(1, room / w);
      if (f < 1) { s.size = Math.floor(size0 * f * 10) / 10; styleDeck(dk); setText(dk, text); }
      return f;
    };
    let orient = MODE === "stack" ? "stack" : "row", NAME = orient === "stack" ? "ETHAN\nSOH" : "ETHAN SOH";
    let fit = fitTo(orient, NAME);
    if (MODE === "auto" && fit < STACK_BELOW) { orient = "stack"; NAME = "ETHAN\nSOH"; fit = fitTo(orient, NAME); }
    dk.dateIn.textContent = TAG; dk.date.textContent = TAG;
    await placeClock(dk);
    await new Promise(r => setTimeout(r, 400));
    const st = document.querySelector(".stage").getBoundingClientRect();
    const box = e => { const b = e.getBoundingClientRect(); return [b.left - st.left, b.top - st.top, b.width, b.height].map(v => +v.toFixed(1)); };
    const cs = getComputedStyle(dk.time), ds = getComputedStyle(dk.date);
    const M = dk.M;
    const cells = dk.cells.map(c => { const b = c.el.getBoundingClientRect(); return { ch: c.ch, box: box(c.el), ink: [b.left - st.left, b.top - st.top + M.inkTop * b.height, b.width, M.inkH * b.height].map(v => +v.toFixed(1)) }; });
    const cards = [...document.querySelectorAll(".stage *")].filter(e => {
      const c = getComputedStyle(e), b = e.getBoundingClientRect();
      return parseFloat(c.borderTopLeftRadius) >= 20 && b.width > 250 && b.width < 500 && c.visibility !== "hidden" && +c.opacity > .05 && b.height > 60;
    }).map(e => ({ cls: e.className, box: box(e), r: getComputedStyle(e).borderTopLeftRadius }));
    // the painting's palette, as the TV gives it to the cards: the accent (labels, today, the heatmap ramp) and the glass tint
    const lab = [...document.querySelectorAll(".stage *")].find(e => !e.childElementCount && /^next$/i.test(e.textContent.trim()));
    const tintEl = document.querySelector(".stage .tint");
    const tintBg = tintEl ? getComputedStyle(tintEl).backgroundImage : "";
    const res = {
      acc: lab ? getComputedStyle(lab).color : null,
      tint: (tintBg.match(/rgba?\([^)]*\)/) || [null])[0],
      settings: saved, size: s.size, fit, orient, name: NAME, stage: [st.width, st.height], autoPause: !!dk.autoPause, cls: dk.d.className,
      top: dk.d.style.top, left: dk.d.style.left,
      ink: dk.d.style.getPropertyValue("--ink"), op: dk.d.style.getPropertyValue("--op"), halo: dk.d.style.getPropertyValue("--halo"),
      time: { fontSize: cs.fontSize, family: cs.fontFamily, weight: cs.fontWeight, spacing: cs.letterSpacing, transform: cs.transform,
              opacity: cs.opacity, blend: cs.mixBlendMode, color: cs.color, filter: cs.filter, box: box(dk.time) },
      metrics: M, cells,
      date: { box: box(dk.date), color: ds.color, shadow: ds.textShadow, fontSize: ds.fontSize, weight: ds.fontWeight, family: ds.fontFamily, spacing: ds.letterSpacing, off: dk.date.classList.contains("off") },
      cards,
    };
    Object.assign(s, saved);
    return res;
  }, { id, TAG, MODE, GAP, STACK_BELOW });
  out.plates[id] = r;
  if (SHOTS) await page.screenshot({ path: path.join(SHOTS, `tv-${id}.png`) });
  console.log(id, r.error || `${r.time && r.time.fontSize} top ${r.top} ink ${r.ink} op ${r.op || "-"} cards ${r.cards ? r.cards.length : 0}`);
}
out.errors = errors.slice(0, 20);
fs.writeFileSync(path.join(HERE, "tv-layout.json"), JSON.stringify(out, null, 1));
await browser.close();
