/* The README banner, captured from his real TV home screen (tv-setup.html as the TV hub serves it), not rebuilt:

     node tools/capture_tv.mjs --data=<profile.json> --out=<dir> [--hub=http://127.0.0.1:8790] [--plates=id,id]
                               [--tframes=8] [--hold=5000] [--wxfps=8] [--wxhold=1500] [--only-stills]

   The page loads as the TV loads it (?kiosk=tv, 1920 x 1080, the hub's saved config: the same plate files, clock face,
   size, height, ink and depth cut-out per painting, the same rotation). Then, in memory only, two things change:
     1. the clock's text is ETHAN: the TV's own fillTime() draws it, so its own face, height, placement, ink and depth
        layering apply. ETHAN is wider than the time, so where it would reach into a widget column the clock's size is
        brought down, for that painting only, until it clears both columns by 12 px (the TV's own size setting, nothing
        else); nothing ever covers or clips it.
     2. the widget cards say his profile (tools/tv-profile.js): the TV's own cards, glass and accent.
   Plus the banner's weather: the TV's own layer (wxBuild: rain, heavy, snow, mist) and tools/wx-extra.js (sun, moon,
   clouds, lightning), one condition per painting, so the range shows.
   Every painting he kept, in the TV's order from Agamemnon (the TV's ?start=), held still; between them the TV's real
   change (swapTo) stepped frame by frame on a paused timeline (the page's own ?measure hooks), so each frame is exact.
   Writes <out>/frames/*.jpg, <out>/stills/<id>.png and <out>/frames.json ({ frames: [{ f, ms }], plates, fit }).
   Read only: every request but GET and HEAD is refused, so nothing reaches the hub's saved settings. Playwright's
   bundled Chromium, headless, one instance (Playwright spawns it with windowsHide). Never his Chrome or Edge. */
import { createRequire } from "module";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire("C:/Users/ethan/Vault/Projects/phone-fleet/app/package.json");
const { chromium } = require("playwright-core");
const args = process.argv.slice(2), opt = (k, d) => { const a = args.find(x => x.startsWith(`--${k}=`)); return a ? a.slice(k.length + 3) : d; };
const HUB = opt("hub", "http://127.0.0.1:8790"), OUT = opt("out", path.join(HERE, "..", ".live", "cap"));
const DATA = JSON.parse(fs.readFileSync(opt("data", path.join(HERE, "..", ".live", "profile.json")), "utf8"));
const TFRAMES = +opt("tframes", 4), HOLD = +opt("hold", 5000), WXFPS = +opt("wxfps", 8), WXHOLD = +opt("wxhold", 1500);
const ONLY = opt("plates", ""), STEPS = +opt("steps", 999), STILLS_ONLY = args.includes("--only-stills");
const EXE = fs.readdirSync("C:/Users/ethan/AppData/Local/ms-playwright").filter(d => /^chromium-\d+$/.test(d)).sort().reverse()
  .map(d => `C:/Users/ethan/AppData/Local/ms-playwright/${d}/chrome-win64/chrome.exe`).find(f => fs.existsSync(f));
const NAME = "ETHAN";
const KEEP_DEPTH = args.includes("--keep-depth");   // comparison renders: never fall back to depth off
/* one condition per painting (TV = the TV's own layer, + = wx-extra), chosen to suit each one */
const WX = {
  spartan: ["moon"], surfers: ["sun", { sx: .86, sy: -.1 }], monaco: ["sun", { sx: .1, sy: -.1 }], gt62: ["clouds"],
  "plane-concorde-climb": ["rain"], "bronkhorst-skiers": ["snow"], "bronkhorst-snowboard": ["sun", { sx: .8, sy: -.12 }],
  "plane-f22-vapour": ["storm", { lx: .72 }], "plane-f22-vapour-oil": ["clouds"], "bronkhorst-streets-s": [null],
  "plane-typhoon-mist-oil": ["mist"], "plane-airport-impasto": ["drizzle"], biplane: ["clouds"], spa: ["rain"],
  porschelake: ["sun", { sx: .88, sy: -.06 }], nightcity: ["moon"], f1ceiling: [null], planetop: ["sun", { sx: .9, sy: -.1 }],
  muse911: [null], ship: ["storm", { lx: .3 }], alps: ["sun", { sx: .82, sy: -.12 }], snow911: ["snow"], wave: ["drizzle"],
};
// the change's frames, ms after the press (the TV's change runs about 1.8 s: dissolve 1050, settle 1500, push 1750)
const T_END = 1750, TS = Array.from({ length: TFRAMES }, (_, k) => Math.round(T_END * (k + 1) / (TFRAMES + 1)));

fs.mkdirSync(path.join(OUT, "frames"), { recursive: true }); fs.mkdirSync(path.join(OUT, "stills"), { recursive: true });
for (const f of fs.readdirSync(path.join(OUT, "frames"))) fs.rmSync(path.join(OUT, "frames", f));   // our own scratch frames

const browser = await chromium.launch({ executablePath: EXE, headless: true });
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await ctx.route("**/*", r => (["GET", "HEAD"].includes(r.request().method()) ? r.continue() : r.abort()));
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", e => errors.push(String(e)));
const order0 = DATA.start || "spartan";
await page.goto(`${HUB}/tv-setup.html?kiosk=tv&measure&t=12:34&start=${encodeURIComponent(order0)}`, { waitUntil: "load" });
await page.waitForFunction(() => typeof swap !== "undefined" && swap.booted, null, { timeout: 30000 });
await page.waitForTimeout(3500);                       // the hub's first readings (Claude usage, the heatmap)
await page.addStyleTag({ content: fs.readFileSync(path.join(HERE, "wx-extra.css"), "utf8") });
await page.addScriptTag({ content: fs.readFileSync(path.join(HERE, "wx-extra.js"), "utf8") });
await page.addScriptTag({ content: fs.readFileSync(path.join(HERE, "tv-profile.js"), "utf8") });

const setup = await page.evaluate(async ({ NAME, DATA, ONLY, KEEP_DEPTH }) => {
  // a still home screen: no night, no AOD or dim, no rotation timer, no burn-in orbit, no music card, no hub restyle
  nightBySchedule = () => {}; view.night = false; stage.classList.remove("night");
  armAod = () => {}; aodFromIdle = () => {}; clearTimeout(amb.timer); if (amb.on) setAmb(false); if (dim.on) setDim(false);
  kioskCatchUp = () => {}; clearInterval(kioskTimer); pixelShift = () => {}; stage.style.setProperty("--px", "0px"); stage.style.setProperty("--py", "0px");
  pickNow = () => paintNp(null); paintNp(null);
  applyRemote = () => {};
  // the clock draws the name: every deck the TV builds from here on goes through its own fillTime
  const orig = fillTime; fillTime = (time, text) => orig(time, /\d/.test(text) ? NAME : text);
  window.__profile.install(DATA);
  WxExtra.mount(stage);
  // ETHAN against the room between the widget columns: the TV's size for that painting, brought down only if needed
  const L = document.querySelector("#widgets").getBoundingClientRect(), R = document.querySelector("#cw").getBoundingClientRect();
  const half = Math.min(stW() / 2 - L.right, R.left - stW() / 2) - 12;
  const ids = []; let j = view.i; for (let k = 0; k < PLATES.length; k++) { if (inRotation(j)) ids.push(PLATES[j].id); j = (j + 1) % PLATES.length; }
  const want = ONLY ? ONLY.split(",") : ids;
  const fit = {};
  for (const id of ids) {
    const i = PLATES.findIndex(p => p.id === id), s = rec[id].settings;
    await faceReady(s.face);
    const dk = makeDeck(i, true);
    const span = () => { const r = dk.cells.map(c => c.el.getBoundingClientRect()); return Math.max(...r.map(b => b.right)) - Math.min(...r.map(b => b.left)); };
    // first the TV's own Width setting, down to 82 % of his (a slight condense keeps his height), then its Size
    const w0 = span(), f = Math.min(1, (2 * half) / w0), size0 = s.size, width0 = s.width;
    if (f < 1) { const wf = Math.max(.82, f); s.width = Math.floor(width0 * wf); s.size = Math.floor(size0 * Math.min(1, f / (s.width / width0)) * 100) / 100; }
    styleDeck(dk); setText(dk, NAME);
    for (let k = 0; k < 20 && span() > 2 * half; k++) { s.size = Math.floor(s.size * 98) / 100; styleDeck(dk); setText(dk, NAME); }
    // every letter stays readable: the TV's depth may hide part of a letter behind the subject, never most of one.
    // Placed as the TV places it (placeClock, with this painting's cut-out); while a letter is over 60 % covered the
    // name comes down 4 % at a time (it stays centred, so it moves off the subject's edges), at most to 80 %; past
    // that the depth goes off for this painting, as the TV's own autoPause does when the subject would cover the digits
    let cover = 0, depthOff = false;
    const sizeA = s.size;
    for (let k = 0; k < 7; k++) {
      spare.set(i, dk); await placeClock(dk); spare.delete(i);
      if (!dk.m || !dk.m.a || s.depth === "off" || dk.autoPause) { cover = 0; break; }
      measureDeck(dk);
      const W = stW(), H = stH(), m = dk.m;
      cover = Math.max(...dk.rest.map(b => {
        const x0 = Math.max(0, Math.floor(b.x / W * m.w)), x1 = Math.min(m.w, Math.ceil((b.x + b.w) / W * m.w));
        const y0 = Math.max(0, Math.floor(b.y / H * m.h)), y1 = Math.min(m.h, Math.ceil((b.y + b.h) / H * m.h));
        let t = 0, n = 0; for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) { t += m.a[y * m.w + x]; n++; }
        return n ? t / n : 0;
      }));
      if (cover <= .6) break;
      if (s.size <= sizeA * .8 + 1e-6) { if (KEEP_DEPTH) break; s.depth = "off"; depthOff = true; s.size = sizeA; styleDeck(dk); setText(dk, NAME); break; }
      s.size = Math.floor(s.size * 96) / 100; styleDeck(dk); setText(dk, NAME);
    }
    fit[id] = { face: s.face, size: size0, fitted: s.size, width: width0, widthFitted: s.width, span: Math.round(w0), after: Math.round(span()), room: Math.round(2 * half), cover: +cover.toFixed(2), depthOff };
    dropDeck(dk);
  }
  dropSpares();
  styleDeck(curDk); setText(curDk, NAME); await placeClock(curDk); measureDeck(curDk);
  fitTv();
  return { ids, want, fit, start: PLATES[view.i].id };
}, { NAME, DATA, ONLY, KEEP_DEPTH });
console.log("plates", setup.ids.length, setup.ids.join(" "));
for (const [id, f] of Object.entries(setup.fit)) console.log(`  ${id.padEnd(24)} ${f.face.padEnd(10)} size ${f.size} -> ${f.fitted}, width ${f.width} -> ${f.widthFitted}  ETHAN ${f.span}px -> ${f.after}px of ${f.room}, worst letter ${Math.round(f.cover * 100)}% covered${f.depthOff ? ", DEPTH OFF" : ""}`);

/* time: the change's own animations (WAAPI) are stepped to t; the CSS animations (weather, pulses) run on one clock of
   our own, so the rain keeps falling across the hold and the change */
let cssClock = 0, frameNo = 0;
const frames = [];
const seek = (t, css, wxOp) => page.evaluate(({ t, css, wxOp }) => {
  for (const a of document.getAnimations()) {
    if (typeof CSSTransition === "function" && a instanceof CSSTransition) { a.finish(); continue; }   // a style change in flight lands
    a.pause();
    if (a instanceof CSSAnimation) a.currentTime = css;
    else if (t != null) a.currentTime = t;
  }
  if (t != null) cues.forEach(c => { if (!c.done && c.at <= t) { c.done = true; c.fn(); } });   // the change's timed cues, as __seek runs them
  if (wxOp != null) for (const s of ["#wxl", "#wxx"]) { const e = document.querySelector(s); if (e) e.style.opacity = wxOp; }
  window.__profile.frame(css);
  return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
}, { t, css, wxOp });
const weather = id => page.evaluate(({ spec }) => {
  const [kind, o] = spec || [null];
  const tv = ["drizzle", "rain", "heavy", "snow", "mist"].includes(kind) ? kind : kind === "storm" ? "heavy" : null;
  const ex = ["sun", "moon", "clouds"].includes(kind) ? kind : kind === "storm" ? "lightning" : null;
  const wl = document.querySelector("#wxl");
  wl.style.transition = "none"; wxBuild(tv); wx.built = tv; wl.hidden = !tv; wl.classList.toggle("on", !!tv);
  WxExtra.build(ex, { ...(o || {}), seed: [...String(kind)].reduce((a, c) => a + c.charCodeAt(0), 7), at: 0 });
}, { spec: WX[id] });
const shot = async (ms, still, kind = "change") => {   // kind: hold | wx (the weather's motion) | change
  const f = `frames/${String(frameNo++).padStart(4, "0")}.jpg`;
  await page.screenshot({ path: path.join(OUT, f), type: "jpeg", quality: 93 });
  frames.push({ f, ms, kind });
  if (still) fs.copyFileSync(path.join(OUT, f), path.join(OUT, "stills", still + ".jpg"));
};

const ids = setup.ids, want = setup.want, order = [];
const moving = id => { const k = (WX[id] || [null])[0]; return !!k; };
for (let n = 0; n < ids.length; n++) {
  const id = await page.evaluate(() => PLATES[view.i].id);
  order.push(id);
  if (!want.includes(id)) { /* not asked for: step on without frames */ }
  else {
    await weather(id);
    // lightning strikes inside the hold: start the CSS clock so the flash (59-67 % of a 7 s cycle) lands mid-hold
    if ((WX[id] || [])[0] === "storm") cssClock = Math.ceil(cssClock / 7000) * 7000 + 4130 - WXHOLD / 2 + 500;
    await seek(null, cssClock, 1);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(OUT, "stills", id + ".png") });
    if (args.includes("--debug")) console.log("  state", JSON.stringify(await page.evaluate(() => ({ cls: stage.className, night: view.night, amb: amb.on, dim: dim.on, np: !!Hub.np, music: view.music, reloaded: !window.__profile, cells: curDk.cells.map(c => { const b = c.el.getBoundingClientRect(), cs = getComputedStyle(c.el); return [c.ch, Math.round(b.left), Math.round(b.width), cs.opacity, cs.transform.slice(0, 40), getComputedStyle(c.g).opacity, c.win.style.transform, c.g.style.transform]; }) }))));
    if (STILLS_ONLY) { /* stills only */ }
    else if (moving(id)) {
      const n = Math.max(2, Math.round(WXHOLD / 1000 * WXFPS)), dt = 1000 / WXFPS;
      for (let k = 0; k < n; k++) { await seek(null, cssClock, 1); await shot(k === n - 1 ? HOLD - (n - 1) * dt : dt, k === 0 ? id : null, k === n - 1 ? "hold" : "wx"); cssClock += dt; }
    } else { await shot(HOLD, id, "hold"); cssClock += HOLD; }
  }
  if (n === ids.length - 1 && STILLS_ONLY) break;
  // the change to the next painting: wait until the TV has it ready (decoded, its clock built and placed while idle)
  const to = await page.evaluate(() => kioskStep(1));
  await page.waitForFunction(j => window.__ready(j), to, { timeout: 15000 }).catch(() => console.log("  (not ready in 15 s:", to, ")"));
  const doFrames = !STILLS_ONLY && want.includes(id);
  await page.evaluate(() => { window.__seekMode(true); for (const a of document.getAnimations()) a.pause(); window.__swap(1); });
  await page.waitForTimeout(300);
  if (doFrames) {
    const nextId = await page.evaluate(j => PLATES[j].id, to);
    let prev = 0, swapped = false;
    for (const t of TS) {
      // the weather crossfades with the painting: out over the first 40 %, the next painting's in from 55 %
      const u = t / T_END;
      if (!swapped && u >= .5) { await weather(nextId); swapped = true; }
      const op = u < .45 ? 1 - u / .45 : u < .55 ? 0 : Math.min(1, (u - .55) / .4);
      await seek(t, cssClock + t, op.toFixed(3));
      await shot(t - prev); prev = t;
    }
    frames[frames.length - 1].ms += 1800 - prev;          // the change's tail, to the TV's full length
    cssClock += 1800;
  }
  // let the change finish exactly as the TV's does, and settle
  await page.evaluate(() => { cues.forEach(c => { if (!c.done) { c.done = true; c.fn(); } }); window.__seekMode(false); for (const a of document.getAnimations()) { if (a instanceof CSSAnimation) a.play(); else { try { a.finish(); } catch {} } } });
  await page.waitForFunction(() => !xfBusy, null, { timeout: 8000 }).catch(() => console.log("  (still settling)"));
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const s of ["#wxl", "#wxx"]) { const e = document.querySelector(s); if (e) e.style.opacity = ""; } });
  process.stdout.write(`  ${id} -> ${await page.evaluate(() => PLATES[view.i].id)}\n`);
  if (await page.evaluate(() => PLATES[view.i].id) === order0 && n > 0) break;
  if (n + 1 >= STEPS) break;
}
const total = frames.reduce((a, f) => a + f.ms, 0);
fs.writeFileSync(path.join(OUT, "frames.json"), JSON.stringify({ when: new Date().toISOString(), hub: HUB, order, fit: setup.fit, frames, totalMs: total, tframes: TS, errors: errors.slice(0, 20) }, null, 1));
console.log(`frames ${frames.length}, loop ${(total / 1000).toFixed(1)} s, errors ${errors.length}`);
await browser.close();
