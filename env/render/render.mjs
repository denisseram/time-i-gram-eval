#!/usr/bin/env node
/**
 * render <deliverable>
 *
 * The one rendering command of the evaluation, identical for all four tools. Agents use it to check
 * their work; evaluators use it to produce the official render. Chosen by file name:
 *
 *   index.html     D3           served from its folder and opened in Chromium
 *   spec.vl.json   Vega-Lite    vega-embed 7.3.0 (Vega 6.4.0, Vega-Lite 6.5.0), default options
 *   spec.json      time-i-gram  embed(element, spec) from time-i-gram 0.1.0
 *   plot.R         ggtime       `Rscript plot.R` in the file's folder; its plot.png (or plot.svg) is the result
 *
 * Writes render.png (1400 x 900) and render-log.txt next to the deliverable, prints the same log, and
 * exits 0 if the deliverable rendered (warnings allowed) or 1 if it could not be rendered.
 * Libraries are served from this folder's node_modules (RENDER_LIB_DIR overrides it), never from a CDN.
 */
import { chromium } from 'playwright';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const WIDTH = 1400;
const HEIGHT = 900;
const PAGE_TIMEOUT_MS = 60_000;
const SETTLE_MS = 2_000;
const R_TIMEOUT_MS = 300_000;
const MAX_MESSAGES = 50;
const LIB_DIR = process.env.RENDER_LIB_DIR || path.join(path.dirname(fileURLToPath(import.meta.url)), 'node_modules');

const TOOLS = {
    'index.html': 'D3',
    'spec.vl.json': 'Vega-Lite',
    'spec.json': 'time-i-gram',
    'plot.R': 'ggtime'
};

const messages = [];
// Chromium's own graphics-driver chatter; it comes from the headless browser, not from any tool.
const BROWSER_NOISE = /GL Driver Message|GPU stall due to ReadPixels|Automatic fallback to software WebGL/;
function note(kind, text) {
    if (BROWSER_NOISE.test(String(text))) return;
    if (messages.length < MAX_MESSAGES) messages.push(`[${kind}] ${String(text).replace(/\s+/g, ' ').slice(0, 500)}`);
    else if (messages.length === MAX_MESSAGES) messages.push('[render] further messages omitted');
}

function finish(file, ok, reason) {
    const name = path.basename(file);
    const lines = [
        `render: ${name} (${TOOLS[name] ?? 'unknown'}) -> render.png`,
        `status: ${ok ? 'OK' : 'FAILED'}${reason ? ` (${reason})` : ''}`,
        `messages (${messages.length}):`,
        ...(messages.length ? messages.map(m => `  ${m}`) : ['  none'])
    ];
    const text = lines.join('\n') + '\n';
    process.stdout.write(text);
    try {
        fs.writeFileSync(path.join(path.dirname(file), 'render-log.txt'), text);
    } catch {}
    process.exit(ok ? 0 : 1);
}

const MIME = {
    '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8', '.css': 'text/css; charset=utf-8', '.csv': 'text/csv; charset=utf-8',
    '.tsv': 'text/tab-separated-values; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.txt': 'text/plain; charset=utf-8'
};

/** Static server: the deliverable's folder at /, libraries at /_lib/, generated pages from `pages`. */
function serve(root, pages) {
    const server = http.createServer((req, res) => {
        const url = decodeURIComponent(new URL(req.url, 'http://x').pathname);
        if (pages[url]) {
            res.writeHead(200, { 'content-type': MIME['.html'] });
            return res.end(pages[url]);
        }
        const base = url.startsWith('/_lib/') ? LIB_DIR : root;
        const rel = url.startsWith('/_lib/') ? url.slice('/_lib/'.length) : url.slice(1) || 'index.html';
        const file = path.resolve(base, rel);
        if (!file.startsWith(path.resolve(base)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('not found');
        }
        res.writeHead(200, { 'content-type': MIME[path.extname(file)] ?? 'application/octet-stream' });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise(resolve => server.listen(0, '127.0.0.1', () => resolve(server)));
}

const VEGA_LITE_PAGE = `<!doctype html><html><head><meta charset="utf-8">
<script src="/_lib/vega/build/vega.min.js"></script>
<script src="/_lib/vega-lite/build/vega-lite.min.js"></script>
<script src="/_lib/vega-embed/build/vega-embed.min.js"></script></head>
<body style="margin:0"><div id="vis"></div><script>
fetch('/spec.vl.json').then(r => r.json())
  .then(spec => vegaEmbed('#vis', spec))
  .then(() => { window.__renderDone = 'ok'; })
  .catch(e => { window.__renderDone = 'error: ' + (e && e.message || e); });
</script></body></html>`;

const TIME_I_GRAM_PAGE = `<!doctype html><html><head><meta charset="utf-8"></head>
<body style="margin:0"><div id="vis"></div><script type="module">
import { embed } from '/_lib/time-i-gram/dist/index.js';
try {
  const spec = await (await fetch('/spec.json')).json();
  await embed(document.getElementById('vis'), spec);
  window.__renderDone = 'ok';
} catch (e) { window.__renderDone = 'error: ' + (e && e.message || e); }
</script></body></html>`;

const SVG_PAGE = `<!doctype html><html><body style="margin:0;background:white"><img src="/plot.svg" style="max-width:100%"></body></html>`;

async function browserRender(file, pageUrl, pages, waitForFlag) {
    const server = await serve(path.dirname(file), pages);
    const { port } = server.address();
    const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
    const browser = await chromium.launch(proxy ? { proxy: { server: proxy, bypass: '127.0.0.1,localhost' } } : {});
    let failure = null;
    try {
        const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT } });
        page.on('console', m => {
            if (m.type() === 'error' || m.type() === 'warning') note(`console.${m.type() === 'warning' ? 'warn' : 'error'}`, m.text());
        });
        page.on('pageerror', e => note('page error', e.message));
        page.on('requestfailed', r => note('request failed', `${r.url()} (${r.failure()?.errorText ?? 'failed'})`));
        page.on('response', r => {
            if (r.status() >= 400 && !r.url().endsWith('/favicon.ico')) note('http error', `${r.status()} ${r.url()}`);
        });
        await page.goto(`http://127.0.0.1:${port}${pageUrl}`, { waitUntil: 'load', timeout: PAGE_TIMEOUT_MS });
        if (waitForFlag) {
            await page.waitForFunction(() => window.__renderDone, null, { timeout: PAGE_TIMEOUT_MS }).catch(() => {
                failure = `no result after ${PAGE_TIMEOUT_MS / 1000} s`;
            });
            const done = await page.evaluate(() => window.__renderDone);
            if (done && done !== 'ok') failure = done;
        }
        await page.waitForLoadState('networkidle', { timeout: PAGE_TIMEOUT_MS }).catch(() => note('render', 'network still busy after 60 s'));
        await page.waitForTimeout(SETTLE_MS);
        await page.screenshot({ path: path.join(path.dirname(file), 'render.png') });
    } catch (e) {
        failure = e.message.split('\n')[0];
    } finally {
        await browser.close();
        server.close();
    }
    return failure;
}

function rRender(file) {
    const dir = path.dirname(file);
    for (const f of ['plot.png', 'plot.svg']) fs.rmSync(path.join(dir, f), { force: true });
    const r = spawnSync('Rscript', [path.basename(file)], { cwd: dir, encoding: 'utf8', timeout: R_TIMEOUT_MS });
    if (r.error) return r.error.code === 'ETIMEDOUT' ? `Rscript did not finish in ${R_TIMEOUT_MS / 1000} s` : r.error.message;
    for (const line of (r.stderr || '').split('\n').filter(l => l.trim())) note('R', line);
    if (r.status !== 0) return `Rscript exited with status ${r.status}`;
    return null;
}

async function main() {
    const arg = process.argv[2];
    if (!arg) {
        console.log('usage: render <index.html | spec.vl.json | spec.json | plot.R>');
        process.exit(2);
    }
    const file = path.resolve(arg);
    const name = path.basename(file);
    if (!TOOLS[name]) {
        note('render', `unknown deliverable name "${name}"; expected one of ${Object.keys(TOOLS).join(', ')}`);
        finish(file, false, 'unknown deliverable');
    }
    if (!fs.existsSync(file)) finish(file, false, 'file not found');
    fs.rmSync(path.join(path.dirname(file), 'render.png'), { force: true });

    let failure = null;
    if (name.endsWith('.json')) {
        try {
            JSON.parse(fs.readFileSync(file, 'utf8'));
        } catch (e) {
            note('json', e.message);
            finish(file, false, 'not valid JSON');
        }
    }
    if (name === 'index.html') failure = await browserRender(file, '/index.html', {}, false);
    if (name === 'spec.vl.json') failure = await browserRender(file, '/_render.html', { '/_render.html': VEGA_LITE_PAGE }, true);
    if (name === 'spec.json') failure = await browserRender(file, '/_render.html', { '/_render.html': TIME_I_GRAM_PAGE }, true);
    if (name === 'plot.R') {
        failure = rRender(file);
        const dir = path.dirname(file);
        if (!failure) {
            if (fs.existsSync(path.join(dir, 'plot.png'))) fs.copyFileSync(path.join(dir, 'plot.png'), path.join(dir, 'render.png'));
            else if (fs.existsSync(path.join(dir, 'plot.svg'))) failure = await browserRender(file, '/_svg.html', { '/_svg.html': SVG_PAGE }, false);
            else failure = 'the script wrote neither plot.png nor plot.svg';
        }
    }
    if (!failure && !fs.existsSync(path.join(path.dirname(file), 'render.png'))) failure = 'no render.png produced';
    finish(file, !failure, failure);
}

main().catch(e => {
    note('render', e.stack || e.message);
    finish(path.resolve(process.argv[2] || '.'), false, 'render crashed');
});
