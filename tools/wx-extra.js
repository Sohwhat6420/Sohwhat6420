/* Extra weather for the TV home screen: sun, moon, clouds, lightning (see wx-extra.css). Standalone, so the TV page can
   adopt it later without changes: it makes one layer, .wxx, right after the TV's own weather layer (#wxl), which is
   between the paintings and the clock, so the depth cut-out (#fgs) stays in front of it exactly as it does of the rain.

     WxExtra.mount(stage)            -> the layer (made once)
     WxExtra.build(kind, opts)       kind: "sun" | "moon" | "clouds" | "lightning" | null (clears)
                                     opts: { sx, sy } where the sun sits (fractions), { lx } where lightning strikes
   Every duration lands on the 24 fps grid (the TV's WX_FPS), with steps(), like the TV's rain. Random placement comes
   from a seeded generator, so one plate always gets the same sky. */
(() => {
  const FPS = 24;
  const wq = s => Math.max(1, Math.round(s * FPS)) / FPS;
  const anim = (name, dur, delay, extra = "") => `animation:${name} ${wq(dur)}s steps(${Math.round(wq(dur) * FPS)}, end) ${-wq(delay)}s infinite${extra}`;
  const seeded = seed => { let s = seed >>> 0 || 1; return () => ((s = Math.imul(s ^ (s >>> 15), 2246822507) ^ Math.imul(s ^ (s >>> 13), 3266489909), (s ^= s >>> 16) >>> 0) / 4294967296); };
  let el = null, cloudTex = null;
  function mount(stage) {
    if (el && el.isConnected) return el;
    el = document.createElement("div"); el.className = "layer wxx"; el.id = "wxx"; el.setAttribute("aria-hidden", "true"); el.hidden = true;
    const wxl = stage.querySelector("#wxl"), plates = stage.querySelector("#plates");
    (wxl || plates).after(el);
    return el;
  }
  function clouds() {   // drawn once at a quarter of the screen and scaled up, wrapped at the sides so the strip tiles
    if (cloudTex) return cloudTex;
    const w = 480, h = 270, c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d"), r = seeded(7);
    for (let i = 0; i < 34; i++) {
      const cx = r() * w, cy = h * (.06 + r() * .42), rad = 30 + r() * 90, a = .05 + r() * .12;
      for (const ox of [-w, 0, w]) {
        const g = x.createRadialGradient(cx + ox, cy, 0, cx + ox, cy, rad);
        g.addColorStop(0, `rgba(240,242,248,${a})`); g.addColorStop(.6, `rgba(232,236,244,${a * .45})`); g.addColorStop(1, "rgba(232,236,244,0)");
        x.fillStyle = g; x.beginPath(); x.ellipse(cx + ox, cy, rad * 1.7, rad * .75, 0, 0, Math.PI * 2); x.fill();
      }
    }
    return (cloudTex = c.toDataURL("image/png"));
  }
  function bolt(r) {      // a jagged main stroke and two forks, in a 100 x 100 box
    let x = 50, y = 0; const main = [[x, y]];
    while (y < 100) { y += 6 + r() * 9; x += (r() - .5) * 22; main.push([Math.max(5, Math.min(95, x)), Math.min(100, y)]); }
    const fork = k => { let [fx, fy] = main[k]; const pts = [[fx, fy]], dir = r() < .5 ? -1 : 1; for (let j = 0; j < 4; j++) { fy += 5 + r() * 7; fx += dir * (4 + r() * 9); pts.push([fx, fy]); } return pts; };
    const d = p => p.map(([a, b], k) => `${k ? "L" : "M"}${a.toFixed(1)} ${b.toFixed(1)}`).join(" ");
    return `<svg class="bolt" viewBox="0 0 100 100" preserveAspectRatio="none" style="${anim("wxx-bolt", 7, 0)}"><path d="${d(main)}"/><path class="f" d="${d(fork(2))}"/><path class="f" d="${d(fork(4))}"/></svg>`;
  }
  function build(kind, opts = {}) {
    if (!el) return;
    el.innerHTML = ""; el.dataset.kind = kind || "";
    if (!kind) { el.hidden = true; return; }
    const r = seeded(opts.seed || 1), H = [];
    if (kind === "sun") {
      el.style.setProperty("--sx", ((opts.sx ?? .9) * 100) + "%"); el.style.setProperty("--sy", ((opts.sy ?? -.08) * 100) + "%");
      H.push(`<div class="sun-bloom" style="${anim("wxx-breathe", 9, r() * 9, " alternate")}"></div>`);
      const two = (a, b) => a + "," + b.replace(/^animation:/, "");
      H.push(`<div class="sun-rays" style="${two(anim("wxx-sway", 26, r() * 26, " alternate"), anim("wxx-shimmer", 7, r() * 7, " alternate"))}"></div>`);
      H.push(`<div class="sun-rays b" style="${two(anim("wxx-sway", 34, r() * 34, " alternate-reverse"), anim("wxx-shimmer", 9, r() * 9, " alternate-reverse"))}"></div>`);
    } else if (kind === "moon") {
      H.push(`<div class="moon-veil"></div><div class="moon-glow" style="${anim("wxx-breathe", 11, r() * 11, " alternate")}"></div>`);
      for (let i = 0; i < 70; i++) {
        const s = 1.4 + r() * 2.2, o = .25 + r() * .55;
        H.push(`<i class="star" style="left:${(r() * 100).toFixed(2)}%;top:${(r() * r() * 46).toFixed(2)}%;--s:${s.toFixed(1)}px;--o:${o.toFixed(2)};${anim("wxx-twinkle", 2.5 + r() * 4, r() * 6, " alternate")}"></i>`);
      }
    } else if (kind === "clouds") {
      const t = clouds();
      H.push(`<div class="cloud" style="top:-6%;height:70%;opacity:.75;background-image:url(${t});${anim("wxx-drift", 160, r() * 160)}"></div>`);
      H.push(`<div class="cloud" style="top:4%;height:55%;opacity:.5;background-image:url(${t});${anim("wxx-drift-r", 230, r() * 230)}"></div>`);
    } else if (kind === "lightning") {
      el.style.setProperty("--lx", ((opts.lx ?? .7) * 100) + "%");
      H.push(`<div class="flash" style="${anim("wxx-flash", 7, opts.at ?? 0)}"></div>`);
      H.push(bolt(r).replace(anim("wxx-bolt", 7, 0), anim("wxx-bolt", 7, opts.at ?? 0)));
    }
    el.innerHTML = H.join("");
    el.hidden = false;
  }
  window.WxExtra = { mount, build, FPS };
})();
