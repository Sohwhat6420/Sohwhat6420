// Focused before/after README previews, using headless bundled Chromium only.
// node tools/preview_linkedin.mjs --playwright=<playwright-core entry> --chromium=<bundled executable>
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const opt = name => process.argv.find(arg => arg.startsWith(`--${name}=`))?.slice(name.length + 3);
const playwright = opt('playwright');
const executablePath = opt('chromium');
if (!playwright || !executablePath) throw new Error('Pass --playwright and --chromium (bundled Chromium only).');
const { default: { chromium } } = await import(pathToFileURL(playwright));
const base = opt('base') || '95107b4';
const previous = spawnSync('git', ['show', `${base}:README.md`], { cwd: root, encoding: 'utf8', windowsHide: true });
if (previous.status !== 0) throw new Error(previous.error?.message || previous.stderr);
const documents = { before: previous.stdout, after: fs.readFileSync(path.join(root, 'README.md'), 'utf8') };
const out = path.join(root, 'docs', 'previews', 'linkedin');
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const results = [];
try {
  // One browser, sequential captures; the excerpt contains only existing inline HTML.
  for (const [stage, source] of Object.entries(documents)) {
    const markdown = source.replace(/\r\n/g, '\n');
    const start = markdown.indexOf('<picture>');
    const end = markdown.indexOf('\n\n<p align="center">', markdown.indexOf('## Projects'));
    const excerpt = markdown.slice(start, end).replace('## Projects', '<h2>Projects</h2>');
    // Preserve Markdown's paragraph spacing around inline HTML blocks.
    const content = excerpt.split(/\r?\n\r?\n/).map(block =>
      /^<(p[ >]|h2>)/.test(block) ? block : `<p>${block}</p>`
    ).join('\n');
    for (const theme of ['dark', 'light']) {
      for (const [device, width] of [['desktop', 1280], ['phone', 390]]) {
        const context = await browser.newContext({ viewport: { width, height: 1000 }, colorScheme: theme, reducedMotion: 'reduce', deviceScaleFactor: 1 });
        const page = await context.newPage();
        const failures = [];
        page.on('pageerror', error => failures.push(String(error)));
        // Embed local SVG bytes to avoid a server, external assets or network requests.
        const inline = content.replace(/(src|srcset)="(assets\/[^\"]+\.svg)"/g, (_, attr, asset) => {
          // Image documents do not consistently inherit reduced-motion emulation.
          // Freeze the fixture, including SMIL, so untouched tiles compare equally.
          const svg = fs.readFileSync(path.join(root, asset), 'utf8')
            .replace(/<animate\w*\b[^>]*\/>/g, '')
            .replace('</svg>', '<style>*{animation:none!important;transition:none!important}.motion{display:none!important}.still{display:inline!important}</style></svg>');
          return `${attr}="data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}"`;
        });
        await page.setContent(`<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
          *{box-sizing:border-box}body{margin:0;padding:32px 16px;background:${theme === 'dark' ? '#0d1117' : '#fff'};color:${theme === 'dark' ? '#f0f6fc' : '#1f2328'};font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
          article{max-width:896px;margin:auto;padding:32px;border:1px solid ${theme === 'dark' ? '#3d444d' : '#d1d9e0'};border-radius:6px}p{margin:0 0 16px}img{max-width:100%;vertical-align:middle}a{color:${theme === 'dark' ? '#4493f8' : '#0969da'};text-decoration:none}sub{font-size:75%;line-height:0;position:relative;bottom:-.25em}h2{font-size:24px;line-height:1.25;margin:24px 0 16px;padding-bottom:.3em;border-bottom:1px solid ${theme === 'dark' ? '#3d444db3' : '#d1d9e0b3'}}article>:last-child{margin-bottom:0}
          @media(max-width:600px){body{padding:16px 0}article{border:0;padding:16px}}
          </style></head><body><article>${inline}</article></body></html>`);
        await page.evaluate(async () => { await Promise.all([...document.images].map(img => img.decode())); await document.fonts.ready; });
        const checks = await page.evaluate(() => ({
          overflow: document.documentElement.scrollWidth > innerWidth,
          brokenImages: [...document.images].filter(img => !img.naturalWidth).length,
          linkedIn: [...document.querySelectorAll('a')].filter(a => a.href === 'https://www.linkedin.com/in/ethan-soh2008').length,
          selectedCard: [...document.images].find(img => img.alt === 'Find me on LinkedIn.')?.naturalWidth ?? null,
        }));
        if (failures.length || checks.overflow || checks.brokenImages || checks.linkedIn !== 1) throw new Error(JSON.stringify({ failures, checks }));
        if (stage === 'after' && checks.selectedCard !== (device === 'phone' ? 420 : 830)) throw new Error('Wrong responsive source selected.');
        const filename = `${stage}-${theme}-${device}.png`;
        await page.screenshot({ path: path.join(out, filename), fullPage: true });
        results.push({ filename, viewport: { width, height: 1000 }, theme, checks });
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
fs.writeFileSync(path.join(out, 'checks.json'), JSON.stringify({ base, renderer: 'Playwright bundled Chromium; local GitHub-style README excerpt, from focus line through Projects heading; animations frozen in the preview fixture only', results }, null, 2) + '\n');
console.log(`Saved ${results.length} previews; no overflow, broken images or page errors.`);
