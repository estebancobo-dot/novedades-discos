// Prueba de la web en un navegador real (Playwright): móvil y escritorio.
// Uso: node tests/e2e/web.mjs [carpeta_site]   (sirve la carpeta en un puerto local)
// Comprueba que carga sin errores, filtra, busca, abre la ficha, guarda en Mi lista,
// cambia de vista y orden, y que los estados vacíos y los enlaces básicos funcionan.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium, devices } = require('playwright');
const AXE = require.resolve('axe-core/axe.min.js');      // auditoría de accesibilidad (WCAG 2.1 A/AA)

const RAIZ = path.resolve(process.argv[2] || path.join(path.dirname(new URL(import.meta.url).pathname), '../../site'));
const TIPOS = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.xml': 'application/xml', '.ics': 'text/calendar', '.png': 'image/png', '.webmanifest': 'application/manifest+json' };

const servidor = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(RAIZ, p);
  if (!f.startsWith(RAIZ) || !fs.existsSync(f)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TIPOS[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
await new Promise(r => servidor.listen(0, r));
const BASE = `http://localhost:${servidor.address().port}/`;

let fallos = 0;
// Devuelve el número de infracciones graves o críticas de WCAG 2.1 A/AA y las muestra.
async function auditar(p, donde) {
  await p.addScriptTag({ path: AXE });
  const r = await p.evaluate(() => axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }));
  const graves = r.violations.filter(v => v.impact === 'serious' || v.impact === 'critical');
  for (const v of graves) console.log(`   ${donde}: ${v.id} (${v.nodes.length}) ${v.nodes[0].target.join(' ')}`);
  return graves.length;
}
const comprobar = (ok, texto) => { console.log(`${ok ? '✓' : '✗'} ${texto}`); if (!ok) fallos++; };

const navegador = await chromium.launch();
for (const [nombre, opciones] of [['móvil', { ...devices['iPhone 13'] }], ['escritorio', { viewport: { width: 1280, height: 900 } }]]) {
  console.log(`— ${nombre}`);
  const ctx = await navegador.newContext({ ...opciones, serviceWorkers: 'block', reducedMotion: 'reduce' });
  await ctx.route(/^https?:\/\/(?!localhost)/, r => r.abort());      // sin red externa: portadas y Deezer fuera
  const p = await ctx.newPage();
  const errores = [];
  p.on('pageerror', e => errores.push(e.message));
  p.on('console', m => { if (m.type() === 'error' && !/net::ERR_FAILED|Failed to load resource/.test(m.text())) errores.push(m.text()); });

  await p.goto(BASE, { waitUntil: 'networkidle' });
  const n = await p.locator('.tarjeta').count();
  comprobar(n > 0, `carga y pinta tarjetas (${n})`);
  comprobar((await p.locator('#familias [role=tab]').count()) >= 3, 'pestañas de familias');

  // familia
  const pestanas = p.locator('#familias [role=tab]');
  await pestanas.nth(1).click();
  await p.waitForTimeout(200);
  comprobar(p.url().includes('familia='), 'la familia queda en la URL (se puede compartir)');

  // búsqueda por palabras en cualquier orden
  const ejemplo = await p.evaluate(async () => (await (await fetch('data/discos.json')).json()).discos.find(d => d.artista.split(' ').length >= 2));
  if (ejemplo) {
    const alReves = ejemplo.artista.split(' ').reverse().join(' ');
    await p.fill('#q', alReves);
    await p.waitForTimeout(400);
    comprobar(await p.locator('.tarjeta').count() > 0, `búsqueda en otro orden ("${alReves}")`);
  }
  // búsqueda sin resultados → estado vacío
  await p.fill('#q', 'zzzz-no-existe-zzzz');
  await p.waitForTimeout(400);
  comprobar((await p.locator('.tarjeta').count()) === 0 && (await p.locator('#contenido .estado').count()) === 1, 'búsqueda sin resultados muestra aviso');
  await p.fill('#q', '');
  await p.waitForTimeout(400);

  // ficha (se abre de forma asíncrona: espera a que esté abierta y con sus detalles)
  await p.locator('.tarjeta').first().click();
  await p.locator('dialog#ficha[open] h3').first().waitFor({ timeout: 10000 }).catch(() => {});
  comprobar(await p.locator('dialog#ficha[open]').count() === 1, 'abre la ficha');
  comprobar(p.url().includes('#disco='), 'la ficha tiene enlace propio');
  comprobar(await p.locator('dialog#ficha a', { hasText: 'Qobuz' }).count() === 1, 'enlace a Qobuz en la ficha');
  comprobar(await p.locator('dialog#ficha h3', { hasText: 'Aparece en' }).count() === 1, 'la ficha carga sus detalles (fuentes)');
  const conSubs = await p.evaluate(() => document.querySelectorAll('dialog#ficha .chips .chip').length);
  if (conSubs) comprobar(await p.locator('dialog#ficha h3', { hasText: 'Parecidos' }).count() === 1, 'la ficha propone discos parecidos');
  comprobar(await p.locator('.tarjeta img[srcset]').count() > 0 || await p.locator('.tarjeta img').count() === 0, 'portadas con versión para pantallas de alta densidad');
  await p.click('#fGuardar');
  comprobar((await p.textContent('#numLista')).trim() === '1', 'guarda en Mi lista');
  await p.click('dialog#ficha .f-cerrar');
  await p.locator('dialog#ficha[open]').waitFor({ state: 'detached', timeout: 5000 }).catch(() => {});
  await p.waitForFunction(() => !location.hash.includes('disco='), null, { timeout: 5000 }).catch(() => {});
  comprobar(await p.locator('dialog#ficha[open]').count() === 0 && !p.url().includes('#disco='), 'cierra la ficha y limpia su enlace');

  // mi lista sobrevive a recargar
  await p.reload({ waitUntil: 'networkidle' });
  comprobar((await p.textContent('#numLista')).trim() === '1', 'Mi lista persiste al recargar');

  // vista lista y orden
  await p.click('#vLista');
  comprobar(await p.locator('#contenido.lista').count() === 1, 'vista de lista');
  await p.selectOption('#orden', 'nota');
  await p.waitForTimeout(200);
  comprobar(await p.locator('.tarjeta').count() > 0, 'orden por nota');
  await p.selectOption('#orden', 'mejor');
  await p.waitForTimeout(300);
  comprobar(await p.locator('#selAnio:not([hidden])').count() === 1, 'lo mejor del año muestra selector de año');

  // calendario
  await p.selectOption('#orden', 'calendario');
  await p.waitForTimeout(300);
  comprobar(await p.locator('.cal-rejilla').count() === 1, 'calendario de salidas');
  const diaConDiscos = p.locator('button.cal-dia').first();
  if (await diaConDiscos.count()) {
    await diaConDiscos.click();
    await p.waitForTimeout(200);
    comprobar(await p.locator('#contenido .tarjeta').count() > 0, 'al tocar un día salen sus discos');
  }
  await p.selectOption('#orden', 'fecha');
  await p.waitForTimeout(200);

  // filtros
  await p.click('#abrirFiltros');
  comprobar(await p.locator('#panel:not([hidden])').count() === 1, 'abre el panel de filtros');
  comprobar(await p.locator('#subgeneros .chip').count() > 5, 'chips de subgéneros');
  comprobar((await auditar(p, 'panel de filtros')) === 0, 'accesibilidad del panel de filtros (WCAG 2.1 AA)');
  // fechas: una fecha futura lejana deja la lista vacía; "Limpiar" la recupera
  await p.fill('#fDesde', '2099-01-01'); await p.dispatchEvent('#fDesde', 'change');
  comprobar((await p.textContent('#numResultados')).trim() === '0', 'filtro de fechas');
  await p.click('#limpiar');
  comprobar(Number((await p.textContent('#numResultados')).trim()) > 0, 'limpiar filtros');
  // sello: solo discos de ese sello
  const sello = await p.evaluate(async () => {         // un sello con discos en la familia elegida y en fechas
    const fam = new URLSearchParams(location.search).get('familia');
    const desde = document.querySelector('#fDesde').value;
    return (await (await fetch('data/discos.json')).json()).discos
      .find(d => d.sello && (!fam || d.familias.includes(fam)) && d.fecha >= desde)?.sello;
  });
  if (sello) {
    await p.fill('#fSello', sello); await p.dispatchEvent('#fSello', 'change');
    const n = Number((await p.textContent('#numResultados')).trim());
    comprobar(n > 0, `filtro de sello (${sello}: ${n})`);
    await p.click('#limpiar');
  }
  await p.click('#cerrarFiltros');

  // enlace profundo a un disco
  const id = await p.evaluate(async () => (await (await fetch('data/discos.json')).json()).discos[0].id);
  await p.goto(BASE + '#disco=' + encodeURIComponent(id), { waitUntil: 'networkidle' });
  await p.locator('dialog#ficha[open]').waitFor({ timeout: 10000 }).catch(() => {});
  comprobar(await p.locator('dialog#ficha[open]').count() === 1, 'abrir un disco desde su enlace');

  // accesibilidad: auditoría automática con axe (portada y ficha) además de las comprobaciones básicas
  await p.goto(BASE, { waitUntil: 'networkidle' });
  comprobar((await auditar(p, 'portada')) === 0, 'accesibilidad de la portada (WCAG 2.1 AA)');
  await p.locator('.tarjeta').first().click();
  await p.locator('dialog#ficha[open] h3').first().waitFor({ timeout: 10000 }).catch(() => {});
  comprobar((await auditar(p, 'ficha')) === 0, 'accesibilidad de la ficha (WCAG 2.1 AA)');
  await p.click('dialog#ficha .f-cerrar');
  // accesibilidad básica
  const sinNombre = await p.$$eval('button', bs => bs.filter(b => !(b.getAttribute('aria-label') || b.textContent.trim())).length);
  comprobar(sinNombre === 0, 'todos los botones tienen nombre accesible');
  const sinAlt = await p.$$eval('img', is => is.filter(i => !i.hasAttribute('alt')).length);
  comprobar(sinAlt === 0, 'todas las imágenes tienen alt');
  if (nombre === 'móvil') {
    const ancho = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    comprobar(ancho <= 1, 'sin desplazamiento horizontal en móvil');
  }
  comprobar(errores.length === 0, `sin errores de JavaScript${errores.length ? ': ' + errores.slice(0, 3).join(' | ') : ''}`);
  await ctx.close();
}
await navegador.close();
servidor.close();
console.log(fallos ? `${fallos} comprobaciones fallidas` : 'Todo correcto');
process.exit(fallos ? 1 : 0);
