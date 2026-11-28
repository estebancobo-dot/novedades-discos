// Estudio del estado del arte, repetible: node estudio/capturar.mjs [salida]
// Para cada web de estudio/referencias.yaml: abre las páginas en móvil y escritorio (en directo o,
// si la web bloquea, la copia más reciente de la Wayback Machine), guarda capturas y la estructura
// de cada página (títulos, controles, campos de las tarjetas) en <salida>/<web>/.
import fs from 'node:fs'; import path from 'node:path'; import { createRequire } from 'node:module';
const require = createRequire(new URL('../tests/e2e/web.mjs', import.meta.url));
const { chromium, devices } = require('playwright');
const yaml = (await import('node:child_process')).execFileSync('python3', ['-c',
  'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))', new URL('referencias.yaml', import.meta.url).pathname]).toString();
const { webs } = JSON.parse(yaml);
const SAL = process.argv[2] || 'docs/estado-del-arte';
const BLOQUEO = /just a moment|attention required|access denied|verify you are human|cf-chl|captcha/i;
const b = await chromium.launch();
const resumen = {};

async function abrir(ctx, url) {
  const p = await ctx.newPage();
  for (const [via, u] of [['directo', url], ['wayback', 'https://web.archive.org/web/2026/' + url]]) {
    try {
      const r = await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await p.waitForTimeout(via === 'wayback' ? 5000 : 3500);
      const t = (await p.title()) + ' ' + (await p.evaluate(() => document.body.innerText.slice(0, 400)));
      if (r && r.status() < 400 && !BLOQUEO.test(t)) {
        if (via === 'wayback') await p.addStyleTag({ content: '#wm-ipp-base,#wm-ipp,#donato{display:none!important}' }).catch(() => {});
        return { p, via, final: p.url(), estado: r.status() };
      }
    } catch (e) { /* se prueba la siguiente vía */ }
  }
  await p.close(); return null;
}

async function estructura(p) {
  return p.evaluate(() => {
    const vis = e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0; };
    const txt = e => (e.getAttribute('aria-label') || e.textContent || e.placeholder || '').trim().replace(/\s+/g, ' ');
    return {
      titulo: document.title,
      encabezados: [...document.querySelectorAll('h1,h2,h3')].filter(vis).map(h => h.tagName + ': ' + txt(h).slice(0, 70)).slice(0, 40),
      navegacion: [...new Set([...document.querySelectorAll('nav a, header a')].filter(vis).map(a => txt(a).slice(0, 30)).filter(Boolean))].slice(0, 40),
      controles: [...new Set([...document.querySelectorAll('select, input:not([type=hidden]), button, [role=tab]')].filter(vis)
        .map(e => e.tagName === 'SELECT' ? 'SELECT[' + [...e.options].map(o => o.text.trim()).slice(0, 15).join(' | ') + ']' : txt(e).slice(0, 35)).filter(Boolean))].slice(0, 50),
      imagenes: document.querySelectorAll('img').length,
      texto: document.body.innerText.replace(/\n{2,}/g, '\n').slice(0, 4000),
      enlaces: [...document.querySelectorAll('a[href]')].map(a => a.href),
    };
  });
}

for (const web of webs) {
  const dir = path.join(SAL, web.id); fs.mkdirSync(dir, { recursive: true });
  resumen[web.id] = { nombre: web.nombre, paginas: [] };
  const paginas = [...web.urls];
  for (const d of web.descubrir || []) {
    const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
    const r = await abrir(ctx, d.desde);
    if (r) {
      const enl = await r.p.evaluate(() => [...document.querySelectorAll('a[href]')].map(a => a.href));
      const re = new RegExp(d.patron); const vistos = new Set();
      for (const e of enl) {
        const orig = e.replace(/^https?:\/\/web\.archive\.org\/web\/\d+[a-z_]*\//, '');
        if (re.test(orig) && !vistos.has(orig.split('#')[0]) && vistos.size < d.max) vistos.add(orig.split('#')[0]);
      }
      paginas.push(...vistos);
    }
    await ctx.close();
  }
  let n = 0;
  for (const url of paginas) {
    n++;
    const fila = { n, url };
    for (const [disp, opc] of [['movil', { ...devices['iPhone 13'] }], ['escritorio', { viewport: { width: 1280, height: 900 } }]]) {
      const ctx = await b.newContext(opc);
      const r = await abrir(ctx, url);
      if (!r) { fila[disp] = 'no accesible (ni en directo ni en Wayback)'; await ctx.close(); continue; }
      const img = `${String(n).padStart(2, '0')}-${disp}.jpg`;
      await r.p.screenshot({ path: path.join(dir, img), type: 'jpeg', quality: 55, fullPage: true, clip: { x: 0, y: 0, width: disp === 'movil' ? 390 : 1280, height: disp === 'movil' ? 3000 : 2200 } })
        .catch(() => r.p.screenshot({ path: path.join(dir, img), type: 'jpeg', quality: 55 }));
      const est = await estructura(r.p); delete est.enlaces;
      Object.assign(fila, { [disp]: img, via: r.via, final: r.final });
      if (disp === 'movil') fs.writeFileSync(path.join(dir, `${String(n).padStart(2, '0')}.json`), JSON.stringify({ url, via: r.via, final: r.final, ...est }, null, 1));
      await ctx.close();
    }
    resumen[web.id].paginas.push(fila);
    console.log(web.id, n, fila.via || '-', url.slice(0, 80), fila.movil?.endsWith('.jpg') ? 'ok' : fila.movil);
  }
}
fs.writeFileSync(path.join(SAL, 'capturas.json'), JSON.stringify({ fecha: new Date().toISOString(), webs: resumen }, null, 1));
await b.close();
