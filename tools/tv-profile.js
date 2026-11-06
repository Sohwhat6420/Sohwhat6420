/* The README banner's widget content, written into the TV home screen's own widget DOM at capture time
   (tools/capture_tv.mjs injects this into tv-setup.html as the TV hub serves it; the file on disk is never edited).

   The TV's cards, glass, tints, accent and layout stay exactly as the TV draws them. What changes is what they say:
     calendar      -> this month with his GitHub contributions shaded behind each day, a 30-day sparkline, the total
     Next          -> the Year 3 internship countdown, with a progress arc
     buses         -> credentials: certification badges, leadership, the diploma
     battery rings -> competitions: Hack The Box 30th of 6,744 and the rest, as rings with icons
     a 4th right card (the heatmap card's own glass and class) -> projects
   The Claude usage card, the Claude Code heatmap and the usage-today card are the TV's own, live from the hub; the
   heatmap's all-time total becomes a rolling odometer.
   window.__profile.install(data) once; window.__profile.frame(ms) on every captured frame (the odometer, the clone's
   glass following the heatmap card's). */
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const ICON = {
    claude: '<g stroke-linecap="round"><path d="M12 3.2v17.6M3.2 12h17.6M5.8 5.8l12.4 12.4M18.2 5.8 5.8 18.2"/></g>',
    shield: '<path d="M12 3 4.6 6v5.4c0 4.5 3.1 8.3 7.4 9.6 4.3-1.3 7.4-5.1 7.4-9.6V6z"/><path d="m8.7 12.2 2.3 2.3 4.4-4.6"/>',
    book: '<path d="M4 5.5C6.5 4.6 9.3 4.8 12 6.4c2.7-1.6 5.5-1.8 8-.9v13c-2.5-.9-5.3-.7-8 .9-2.7-1.6-5.5-1.8-8-.9zM12 6.4v13"/>',
    chevron: '<path d="m5 11 7-4.5 7 4.5M5 16.5 12 12l7 4.5"/>',
    medal: '<circle cx="12" cy="14.5" r="5.2"/><path d="m8.6 10.6-2.4-6.8h4.1l1.7 4.6M15.4 10.6l2.4-6.8h-4.1l-1.7 4.6"/><path d="m12 12.3.8 1.6 1.7.2-1.3 1.2.4 1.7-1.6-.9-1.6.9.4-1.7-1.3-1.2 1.7-.2z"/>',
    cap: '<path d="M2.5 9.5 12 5l9.5 4.5L12 14zM6.5 11.6v4.2c1.4 1.4 3.4 2.2 5.5 2.2s4.1-.8 5.5-2.2v-4.2M21.5 9.5v5"/>',
    flag: '<path d="M6.5 21V4M6.5 4.5h10.5l-2.3 3.8 2.3 3.8H6.5"/>',
    trophy: '<path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4"/>',
    target: '<circle cx="12" cy="12" r="8.2"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1.2"/>',
    bulb: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.4 1.1 2.2v.5h5v-.5c0-.8.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
    phone: '<rect x="7" y="2.8" width="10" height="18.4" rx="2.3"/><path d="M11 18h2"/><path d="m10 9.2 2-1.6 2 1.6M10 12.6l2-1.6 2 1.6" opacity=".8"/>',
    layers: '<path d="m12 3.5 8.5 4.3L12 12 3.5 7.8z"/><path d="m3.5 12 8.5 4.2 8.5-4.2M3.5 16.2l8.5 4.3 8.5-4.3"/>',
    people: '<circle cx="9" cy="8.5" r="3.2"/><path d="M3.2 19.5c.6-3.2 3-5 5.8-5s5.2 1.8 5.8 5"/><circle cx="16.6" cy="9.4" r="2.5"/><path d="M15.8 14.6c2.4-.2 4.4 1.3 5 4.4"/>',
    tv: '<rect x="2.8" y="4.5" width="18.4" height="12.2" rx="1.8"/><path d="M8.5 20.2h7M12 16.7v3.5"/>',
    case: '<rect x="3.2" y="7.2" width="17.6" height="12" rx="2"/><path d="M9 7.2V5.6c0-.8.6-1.4 1.4-1.4h3.2c.8 0 1.4.6 1.4 1.4v1.6M3.2 12.2h17.6M11 12.2v1.6h2v-1.6"/>',
    commit: '<circle cx="12" cy="12" r="3.4"/><path d="M3 12h5.6M15.4 12H21"/>',
  };
  const svg = (k, cls = "") => `<svg class="pf-ic ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICON[k] || ""}</svg>`;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const CSS = `
  /* sizes in cqw like the TV's own cards, so they scale with them (--wz, --cz) */
  .pf-ic { width: 1.05cqw; height: 1.05cqw; fill: none; stroke: #fff; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; flex: none; }
  .pf-tile { width: 2.05cqw; height: 2.05cqw; border-radius: .55cqw; display: grid; place-items: center; flex: none;
    background: color-mix(in srgb, var(--acc, #fff) 30%, rgba(14,16,20,.5)); box-shadow: inset 0 0 0 .06cqw color-mix(in srgb, var(--acc, #fff) 45%, transparent); }
  .pf-tile .pf-ic { width: 1.12cqw; height: 1.12cqw; }
  .pf-rows { display: grid; gap: .5cqw; margin-top: .55cqw; font-variant-numeric: tabular-nums; }
  .pf-sec { font-size: .66cqw; letter-spacing: .08em; text-transform: uppercase; color: #b8bcc4; margin-top: .35cqw; }
  .pf-sec:first-child { margin-top: 0; }
  .pf-r { display: grid; grid-template-columns: 2.05cqw minmax(0, 1fr) auto; align-items: center; column-gap: .65cqw; }
  .pf-r b { display: block; font: 600 .84cqw/1.2 var(--ui); color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .pf-r small { display: block; font: 500 .66cqw/1.25 var(--ui); color: #b8bcc4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: .08cqw; }
  .pf-tag { font: 700 .62cqw/1 var(--ui); letter-spacing: .05em; padding: .2cqw .38cqw; border-radius: .32cqw; color: #fff;
    background: rgba(255,255,255,.14); box-shadow: inset 0 0 0 .06cqw color-mix(in srgb, var(--acc, #fff) 50%, transparent); white-space: nowrap; }
  .pf-chips { display: flex; flex-wrap: wrap; gap: .32cqw; margin-top: .1cqw; }
  .pf-chip { display: inline-flex; align-items: center; gap: .3cqw; font: 600 .66cqw/1 var(--ui); color: #e3e5e9; padding: .3cqw .45cqw; border-radius: .4cqw; background: rgba(255,255,255,.1); white-space: nowrap; }
  .pf-chip .pf-ic { width: .8cqw; height: .8cqw; stroke: var(--acc, #fff); }
  .pf-r.notag { grid-template-columns: 2.05cqw minmax(0, 1fr); }
  .pf-r b .pf-tag { margin-left: .4cqw; vertical-align: .08cqw; font-size: .5cqw; padding: .14cqw .3cqw; }
  .pf-tag.acc { background: var(--acc, #fff); color: #111; box-shadow: none; }
  .pf-head { display: flex; align-items: center; justify-content: space-between; gap: .5cqw; }
  .pf-head .pf-meta { display: flex; align-items: center; gap: .3cqw; font: 600 .66cqw/1 var(--ui); letter-spacing: .06em; color: #aeb3bb; text-transform: uppercase; font-variant-numeric: tabular-nums; }
  .pf-head .pf-meta .pf-ic { width: .85cqw; height: .85cqw; stroke: #aeb3bb; }
  /* the calendar: GitHub contributions shaded behind each day */
  .cal .d.g1 span, .cal .d.g2 span, .cal .d.g3 span, .cal .d.g4 span { display: grid; place-items: center; height: 118%; aspect-ratio: 1; border-radius: 50%; }
  .cal .d.g1 span { background: color-mix(in srgb, var(--acc, #fff) 16%, transparent); }
  .cal .d.g2 span { background: color-mix(in srgb, var(--acc, #fff) 28%, transparent); }
  .cal .d.g3 span { background: color-mix(in srgb, var(--acc, #fff) 42%, transparent); }
  .cal .d.g4 span { background: color-mix(in srgb, var(--acc, #fff) 60%, transparent); }
  .cal .d.fut { opacity: .5; }
  .pf-ghf { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: end; column-gap: .8cqw; margin-top: .6cqw; padding-top: .55cqw; border-top: .06cqw solid rgba(255,255,255,.14); }
  .pf-ghf .n { font: 600 1.05cqw/1 var(--ui); color: #fff; font-variant-numeric: tabular-nums; }
  .pf-ghf .n small { display: block; font: 500 .62cqw/1.2 var(--ui); color: #b8bcc4; margin-top: .18cqw; letter-spacing: .02em; }
  .pf-ghf svg { width: 100%; height: 2.1cqw; overflow: visible; }
  .pf-ghf .ln { fill: none; stroke: var(--acc, #fff); stroke-width: 1.6; stroke-linejoin: round; stroke-linecap: round; vector-effect: non-scaling-stroke; }
  .pf-ghf .ar { fill: color-mix(in srgb, var(--acc, #fff) 18%, transparent); }
  .pf-ghf .dot { fill: var(--acc, #fff); }
  /* the internship countdown: an arc */
  .ev.pf-ev { position: relative; padding-right: 5.6cqw !important; }
  .ev.pf-ev .ev-t, .ev.pf-ev .ev-w, .ev.pf-ev .ev-c { white-space: nowrap; }
  .pf-arc { position: absolute; right: 1cqw; top: 50%; translate: 0 -50%; width: 4.1cqw; height: 4.1cqw; display: grid; place-items: center; }
  .pf-arc svg.a { position: absolute; inset: 0; width: 100%; height: 100%; rotate: -90deg; }
  .pf-arc .trk { fill: none; stroke: rgba(255,255,255,.16); stroke-width: 2.6; }
  .pf-arc .val { fill: none; stroke: var(--acc, #fff); stroke-width: 2.6; stroke-linecap: round; }
  .pf-arc .c { text-align: center; line-height: 1; }
  .pf-arc .c b { display: block; font: 600 1.05cqw/1 var(--ui); color: #fff; font-variant-numeric: tabular-nums; }
  .pf-arc .c small { display: block; font: 600 .5cqw/1 var(--ui); letter-spacing: .1em; text-transform: uppercase; color: #b8bcc4; margin-top: .14cqw; }
  /* competitions: the battery rings' own ring, with icons and captions */
  .dev.pf-dev { display: block !important; }
  .pf-dev .pf-rings { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); justify-items: center; margin-top: .7cqw; }
  .pf-dev .ring { margin-bottom: 2.15cqw !important; }
  .pf-dev .ring b { bottom: -1.3cqw; font-size: .9cqw; }
  .pf-dev .ring i { position: absolute; bottom: -2.1cqw; left: 50%; translate: -50% 0; font: 500 .54cqw/1 var(--ui); color: #b8bcc4; white-space: nowrap; font-style: normal; }
  .pf-dev .pf-foot { font: 500 .64cqw/1.35 var(--ui); color: #b8bcc4; text-align: left; }
  .pf-dev .pf-head { text-align: left; }
  .pf-dev .ring { width: 2.9cqw; height: 2.9cqw; }
  .pf-dev .pf-foot b { color: #fff; font-weight: 600; }
  /* projects, on the heatmap card's own glass */
  .cwh.pf-pj .pf-rows { gap: .62cqw; margin-top: .2cqw; }
  .pf-odo { font-variant-numeric: tabular-nums; }
  `;
  const P = { data: null, t0: 0, odo: null };
  const q = s => document.querySelector(s);
  const lvlOf = vals => { const v = vals.filter(Boolean).sort((a, b) => a - b), at = p => v[Math.min(v.length - 1, Math.floor(p * (v.length - 1)))] || 0, c = [at(.25), at(.5), at(.75)]; return n => !n ? 0 : n <= c[0] ? 1 : n <= c[1] ? 2 : n <= c[2] ? 3 : 4; };
  const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

  function cal() {
    const D = P.data, gh = D.github || {}, days = gh.days || {}, now = new Date(), y = now.getFullYear(), mo = now.getMonth();
    const lvl = lvlOf(Object.values(days));
    q("#calMonth").outerHTML = `<div class="pf-head"><div class="w-label" id="calMonth">${now.toLocaleDateString("en-GB", { month: "long" })}</div><span class="pf-meta">${svg("commit")}GitHub</span></div>`;
    const first = (new Date(y, mo, 1).getDay() + 6) % 7, n = new Date(y, mo + 1, 0).getDate();
    let h = ["M", "T", "W", "T", "F", "S", "S"].map(d => `<span class="dow">${d}</span>`).join("");
    for (let k = 0; k < first; k++) h += "<span></span>";
    for (let d = 1; d <= n; d++) {
      const L = d < now.getDate() ? lvl(days[iso(new Date(y, mo, d))] || 0) : 0;
      h += `<span class="d${d === now.getDate() ? " today" : ""}${L ? " g" + L : ""}${d > now.getDate() ? " fut" : ""}"><span>${d}</span></span>`;
    }
    q("#cal").innerHTML = h;
    // the last 30 days, as a sparkline
    const pts = []; for (let k = 29; k >= 0; k--) { const d = new Date(now); d.setDate(d.getDate() - k); pts.push(days[iso(d)] || 0); }
    const mx = Math.max(1, ...pts), W = 100, H = 30, xy = pts.map((v, k) => [k / 29 * W, H - 2 - v / mx * (H - 4)]);
    const line = xy.map(([x, y], k) => `${k ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    let f = q("#pfGhf"); if (!f) { f = document.createElement("div"); f.id = "pfGhf"; f.className = "pf-ghf"; q("#cal").after(f); }
    const tot = gh.contributions, last = xy[xy.length - 1];
    f.innerHTML = `<div class="n">${tot != null ? tot.toLocaleString("en-GB") : "–"}<small>contributions · ${gh.repos ?? 0} public repos</small></div>
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><path class="ar" d="${line} L${W} ${H} L0 ${H}Z"/><path class="ln" d="${line}"/><circle class="dot" cx="${last[0]}" cy="${last[1]}" r="2.2" vector-effect="non-scaling-stroke"/></svg>`;
  }

  function next() {
    const I = P.data.internship, card = q("#evCard"), from = new Date(I.from + "T00:00:00"), now = new Date();
    const left = Math.max(0, Math.ceil((from - now) / 864e5)), runup = Math.max(1, I.runup_days || 365), frac = Math.max(.02, Math.min(1, 1 - left / runup));
    card.classList.add("pf-ev"); card.classList.remove("now", "wpend");
    q("#evT").textContent = I.title; q("#evW").textContent = I.line; q("#evC").textContent = I.detail;
    let a = card.querySelector(".pf-arc"); if (!a) { a = document.createElement("div"); a.className = "pf-arc"; card.append(a); }
    const C = 2 * Math.PI * 15.5;
    a.innerHTML = `<svg class="a" viewBox="0 0 36 36"><circle class="trk" cx="18" cy="18" r="15.5"/><circle class="val" cx="18" cy="18" r="15.5" stroke-dasharray="${(C * frac).toFixed(1)} ${C.toFixed(1)}"/></svg><div class="c"><b>${left}</b><small>days</small></div>`;
  }

  const row = (icon, main, detail, tag, accTag) => `<div class="pf-r"><span class="pf-tile">${svg(icon)}</span><span><b>${esc(main)}</b><small>${esc(detail)}</small></span>${tag ? `<span class="pf-tag${accTag ? " acc" : ""}">${esc(tag)}</span>` : "<span></span>"}</div>`;
  function creds() {
    const D = P.data, box = q("#busRows"), card = box.closest(".bus");
    card.querySelector(".w-label").textContent = "Credentials";
    card.classList.remove("stale");
    box.className = "pf-rows"; box.removeAttribute("data-shape");
    box.innerHTML = `<div class="pf-sec">Certified</div>` + D.certified.map(c => row(c.icon, c.main, c.detail, c.tag, c.acc)).join("")
      + `<div class="pf-sec">Leadership and study</div><div class="pf-chips">` + D.leadership.map(c => `<span class="pf-chip">${svg(c.icon)}${esc(c.main)}</span>`).join("") + `</div>`;
  }

  function comps() {
    const D = P.data, box = q("#devRings"), C = 2 * Math.PI * 15.5;
    box.classList.add("pf-dev"); box.removeAttribute("data-shape");
    const rings = D.rings.map(r => `<div class="ring"><svg class="arc" viewBox="0 0 36 36"><circle class="trk" cx="18" cy="18" r="15.5"/><circle class="val" cx="18" cy="18" r="15.5" stroke-dasharray="${(C * r.fill).toFixed(1)} ${C.toFixed(1)}"/></svg>
      <svg class="gly" viewBox="0 0 24 24">${ICON[r.icon]}</svg><b>${esc(r.label)}</b><i>${esc(r.caption)}</i></div>`).join("");
    const html = `<div class="pf-head"><div class="w-label">Competitions</div><span class="pf-meta">${svg("trophy")}2026</span></div><div class="pf-rings">${rings}</div><div class="pf-foot">${D.comp_foot}</div>`;
    const tints = [...box.children].filter(e => e.classList.contains("tint"));
    box.innerHTML = html; box.prepend(...tints);
  }

  function projects() {
    const D = P.data, src = q("#cwh");
    let c = q("#pfPj");
    if (!c) {
      c = document.createElement("div"); c.id = "pfPj"; c.className = "cwh wc pf-pj"; c.setAttribute("aria-hidden", "true");
      src.after(c);
    }
    const tints = [...src.children].filter(e => e.classList.contains("tint")).map(e => e.cloneNode(false));
    c.innerHTML = `<div class="cwh-h"><b>Projects</b><span>${esc(D.projects_meta)}</span></div><div class="pf-rows">${D.projects.map(p => `<div class="pf-r notag"><span class="pf-tile">${svg(p.icon)}</span><span><b>${esc(p.name)}<span class="pf-tag${p.acc ? " acc" : ""}">${esc(p.tag)}</span></b><small>${esc(p.desc)}</small></span></div>`).join("")}</div>`;
    c.prepend(...tints);
  }

  // the heatmap card's all-time token total as an odometer: every digit, rolling at his recent rate
  function odoText(ms) {
    const o = P.odo; if (!o) return null;
    const v = Math.floor(o.base + o.rate * ms);
    return v.toLocaleString("en-GB") + " tokens";
  }

  function sync(ms) {
    const acc = (typeof setAcc === "function" && setAcc.cur) || getComputedStyle(q("#calMonth")).getPropertyValue("--acc") || null;
    for (const e of [q("#pfGhf"), q("#evCard .pf-arc"), q("#busRows"), q("#devRings"), q("#pfPj"), q("#calMonth")?.parentElement]) if (e) { if (acc) e.style.setProperty("--acc", acc); else e.style.removeProperty("--acc"); }
    // the projects card wears the heatmap card's glass, scale, tints and opacity, and sits under the usage card
    const pj = q("#pfPj"), src = q("#cwh"), ud = q("#ud");
    if (pj && src && ud) {
      const cs = getComputedStyle(src);
      pj.style.setProperty("--cz", src.style.getPropertyValue("--cz") || "1"); pj.style.setProperty("--wg", src.style.getPropertyValue("--wg") || "");
      pj.style.opacity = cs.opacity;
      const st = q("#stage").getBoundingClientRect(), u = ud.getBoundingClientRect(), a = q("#cw").getBoundingClientRect(), b = src.getBoundingClientRect();
      const gap = Math.max(8, b.top - a.bottom);
      pj.style.top = (u.bottom - st.top + gap).toFixed(1) + "px";
      const from = [...src.children].filter(e => e.classList.contains("tint")), to = [...pj.children].filter(e => e.classList.contains("tint"));
      from.forEach((e, k) => { const t = to[k]; if (!t) return; t.style.background = e.style.background; t.style.opacity = getComputedStyle(e).opacity; t.style.setProperty("--wg", e.style.getPropertyValue("--wg")); });
    }
    const f = q("#cwhWeek"), txt = odoText(ms);
    if (f && txt) { f.textContent = txt; f.classList.add("pf-odo"); }
  }

  window.__profile = {
    install(data) {
      P.data = data;
      if (!q("#pfCss")) { const s = document.createElement("style"); s.id = "pfCss"; s.textContent = CSS; document.head.append(s); }
      // the TV's painters for these cards now paint his profile, so a hub event or the minute's tick redraws the same thing
      window.buildCal = cal; window.paintNext = next; window.paintBus = creds; window.paintBusAge = () => {}; window.paintDevs = comps;
      cal(); next(); creds(); comps(); projects();
      const tok = data.activity || {};
      if (tok.total) P.odo = { base: tok.total, rate: (tok.recent_per_day || 0) / 864e5 };
      ["#evCard", "#widgets > .bus", "#devRings", "#cw", "#cwh", "#ud"].forEach(s => { const e = q(s); if (e) e.classList.remove("wpend"); });
      if (typeof fitTv === "function") fitTv();
      sync(0);
      return { ok: true };
    },
    frame(ms) { sync(ms); },
  };
})();
