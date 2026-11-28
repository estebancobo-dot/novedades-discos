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
// Cada comprobación se apunta con el nombre que usa data/requisitos.yaml ("web:NOMBRE"); al final se
// escribe data/validacion_web.json, que lee la validación automática (scraper/validar.py).
const RESULTADOS = {};
const CLAVES = [[/^carga y pinta tarjetas/, 'portada_semanas'], [/pestañas|familia queda|filtro|limpiar|chips|panel/, 'filtros'],
  [/búsqueda/, 'busqueda'], [/ficha tiene enlace|abre la ficha|cierra la ficha|abrir un disco/, 'ficha'], [/Qobuz/, 'escuchar'],
  [/detalles \(fuentes\)/, 'fuentes'], [/parecidos/, 'parecidos'], [/Mi lista/, 'mi_lista'], [/vista de lista/, 'vistas'],
  [/orden por/, 'orden'], [/lo mejor/, 'mejores'], [/calendario|tocar un día/, 'calendario'], [/accesibilidad|nombre accesible|tienen alt/, 'accesibilidad'],
  [/desplazamiento horizontal|alta densidad/, 'movil'], [/errores de JavaScript/, 'contenido']];
const apuntar = (clave, ok) => { if (clave) RESULTADOS[clave] = (RESULTADOS[clave] ?? true) && !!ok; };
const comprobar = (ok, texto, clave) => {
  console.log(`${ok ? '✓' : '✗'} ${texto}`); if (!ok) fallos++;
  apuntar(clave || CLAVES.find(([r]) => r.test(texto))?.[1], ok);
};
// Criterios de aceptación del diseño nuevo (docs/requisitos-web.md): se apuntan pero no rompen la prueba
// mientras la fase W correspondiente no esté hecha.
const aceptacion = (ok, texto, clave) => { console.log(`${ok ? '✓' : '○'} [${clave}] ${texto}`); apuntar(clave, ok); };

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

  // ---- aceptación de la portada y la tarjeta nuevas (W1)
  const portada = await p.evaluate(() => {
    const secs = [...document.querySelectorAll('[data-seccion], .semana')];
    const primera = secs[0]?.querySelector('h2')?.textContent || '';
    const tarjetas = [...document.querySelectorAll('.tarjeta')].slice(0, 12);
    const emoji = /\p{Extended_Pictographic}/u;
    const textosUI = [...document.querySelectorAll('header button, header a, #orden option, .vistas button')].map(e => e.textContent);
    const t0 = tarjetas[0];
    return {
      primera, secciones: [...document.querySelectorAll('[data-seccion]')].map(e => e.dataset.seccion),
      cuadrosColor: tarjetas.filter(t => !t.querySelector('img') && (t.querySelector('.portada')?.textContent || '').trim()).length,
      conImg: tarjetas.filter(t => t.querySelector('.portada img')).length, n: tarjetas.length,
      titulo: !!t0?.querySelector('.t-titulo'), artista: !!t0?.querySelector('.t-artista'),
      artistaUnaVez: t0 ? (t0.innerText.split(t0.querySelector('.t-artista')?.textContent?.trim() || '§').length - 1) === 1 : false,
      meta: !!t0?.querySelector('.t-meta'),
      conNota: tarjetas.filter(t => t.dataset.nota).length, cajasNota: tarjetas.filter(t => t.querySelector('.nota-caja.verde, .nota-caja.amarillo, .nota-caja.rojo')).length,
      serif: t0?.querySelector('.t-titulo') ? /serif/.test(getComputedStyle(t0.querySelector('.t-titulo')).fontFamily) && !/sans-serif\s*$/.test(getComputedStyle(t0.querySelector('.t-titulo')).fontFamily) : false,
      semanaTexto: /Semana del \d+/.test(document.body.innerText), mesesFuera: !document.querySelector('#meses button') || !!document.querySelector('#meses')?.closest('#panel'),
      emojis: textosUI.filter(t => emoji.test(t)).length,
      proximosCompactos: !!document.querySelector('[data-seccion=proximos] .lista-compacta'),
    };
  });
  aceptacion(/esta semana/i.test(portada.primera), `la portada abre en "Esta semana" (abre en "${portada.primera.trim()}")`, 'A1');
  aceptacion(['semana', 'destacados', 'recientes', 'proximos'].every(x => portada.secciones.includes(x)), 'secciones Esta semana, Destacados, Recientes y Próximos', 'A2');
  aceptacion(portada.proximosCompactos && !/próximamente/i.test(portada.primera), 'próximos aparte, en lista compacta', 'A4');
  aceptacion(portada.cuadrosColor === 0, `sin cuadros de color con el nombre (${portada.cuadrosColor} en las 12 primeras)`, 'A5');
  aceptacion(portada.mesesFuera, 'cabecera limpia: la fila de meses va dentro de Filtros', 'A6');
  aceptacion(portada.semanaTexto, '"Semana del …" visible', 'A7');
  aceptacion(portada.secciones.includes('mejores-notas'), '"Mejores notas recientes" en la portada', 'A9');
  aceptacion(portada.n > 0 && portada.conImg >= Math.ceil(portada.n * 0.75), `portadas en las primeras tarjetas (${portada.conImg} de ${portada.n})`, 'B1');
  aceptacion(portada.titulo && portada.artista && portada.artistaUnaVez, 'tarjeta: título y artista, sin repetir el nombre', 'B2');
  aceptacion(portada.meta, 'tarjeta: fecha · estilo en una línea', 'B3');
  aceptacion(portada.conNota > 0 && portada.cajasNota === portada.conNota, `nota en cuadro de color en las tarjetas con nota (${portada.cajasNota} de ${portada.conNota})`, 'B4');
  aceptacion(portada.serif, 'títulos con letra con remate', 'I1');
  aceptacion(portada.emojis === 0, `sin emojis en la interfaz (${portada.emojis})`, 'I4');

  // familia
  const pestanas = p.locator('#familias [role=tab]');
  await pestanas.nth(1).click();
  await p.waitForTimeout(200);
  comprobar(p.url().includes('familia='), 'la familia queda en la URL (se puede compartir)');

  // búsqueda por palabras en cualquier orden
  // un artista de dos o más palabras entre los discos que se ven (la página ya tiene familia y fechas)
  const ejemplo = await p.evaluate(() => [...document.querySelectorAll('.tarjeta .t-artista')]
    .map(e => ({ artista: e.textContent.trim() })).find(d => d.artista.split(' ').length >= 2 && !/[^\p{L}\p{N} ]/u.test(d.artista)));
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
  // ---- aceptación de la página del disco nueva (W2, estilo Metacritic / AnyDecentMusic)
  const ficha = await p.evaluate(() => {
    const f = document.querySelector('dialog#ficha'); const t = f?.innerText || '';
    const tarjetas = [...(f?.querySelectorAll('.resena-tarjeta') || [])];
    return { migas: !!f?.querySelector('.migas'), h1: !!f?.querySelector('h1, .f-titulo'), deArtista: !!f?.querySelector('.de-artista a, a.de-artista, .de-artista button'),
      notaGrande: !!f?.querySelector('.nota-grande'), segun: /según \d+ reseñas?/i.test(t),
      palabra: /muy favorable|favorable|dividida|desfavorable/i.test(t), barra: !!f?.querySelector('.barra-resenas'),
      resenas: tarjetas.length, resenasCompletas: tarjetas.filter(r => r.querySelector('.medio') && r.querySelector('a[href]')).length };
  });
  aceptacion(ficha.migas, 'ficha: migas Artista / Disco', 'C2');
  aceptacion(ficha.h1 && ficha.deArtista, 'ficha: título grande y "de Artista" enlazado', 'C3');
  aceptacion(ficha.notaGrande && ficha.segun, 'ficha: nota grande y "según N reseñas"', 'C4');
  aceptacion(ficha.resenas > 0 && ficha.resenasCompletas === ficha.resenas, `ficha: "Qué dice la crítica" con medio y enlace (${ficha.resenasCompletas}/${ficha.resenas})`, 'C5');
  aceptacion(ficha.palabra, 'ficha: nota con palabra (favorable, dividida…)', 'C15');
  aceptacion(ficha.barra, 'ficha: barra de reseñas positivas / mixtas / negativas', 'C16');
  aceptacion(ficha.resenas > 0, 'ficha: cada reseña como tarjeta', 'C18');
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
  // ---- aceptación del ranking (W3, estilo AOTY): lista numerada con portada, nota y nº de reseñas
  const ranking = await p.evaluate(() => { const f = [...document.querySelectorAll('.ranking-disco')].slice(0, 10);
    return { n: f.length, completas: f.filter(x => x.querySelector('.puesto') && x.querySelector('.nota-caja') && /reseña/i.test(x.innerText)).length }; });
  aceptacion(ranking.n > 0 && ranking.completas === ranking.n, `lo mejor: lista numerada con nota y nº de reseñas (${ranking.completas}/${ranking.n})`, 'F1');

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
  comprobar(await p.evaluate(() => getComputedStyle(document.body).overflow) === 'hidden', 'con el panel abierto, la página de detrás no se desplaza');
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
  comprobar(await p.evaluate(() => getComputedStyle(document.body).overflow) !== 'hidden', 'al cerrar el panel, la página vuelve a desplazarse');

  // enlace profundo a un disco
  // la ficha más completa (con subgéneros y reseñas): así la auditoría cubre todos sus bloques
  const id = await p.evaluate(async () => { const ds = (await (await fetch('data/discos.json')).json()).discos;
    return (ds.find(d => d.subgeneros.length && d.n_resenas) || ds[0]).id; });
  await p.goto(BASE + '#disco=' + encodeURIComponent(id), { waitUntil: 'networkidle' });
  await p.locator('dialog#ficha[open]').waitFor({ timeout: 10000 }).catch(() => {});
  comprobar(await p.locator('dialog#ficha[open]').count() === 1, 'abrir un disco desde su enlace');
  await p.locator('dialog#ficha[open] h3').first().waitFor({ timeout: 10000 }).catch(() => {});
  comprobar((await auditar(p, 'ficha completa')) === 0, 'accesibilidad de una ficha completa (subgéneros, reseñas, parecidos)');

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
// K2: pruebas de contenido de la portada y la tarjeta
apuntar('contenido', ['A1', 'A5', 'B1', 'B2', 'B4', 'C3', 'C4'].every(k => RESULTADOS[k]));
const SALIDA_VALIDACION = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../../data/validacion_web.json');
fs.writeFileSync(SALIDA_VALIDACION, JSON.stringify(RESULTADOS, null, 1));
console.log(`Resultados por requisito → ${path.relative(process.cwd(), SALIDA_VALIDACION)}`);
console.log(fallos ? `${fallos} comprobaciones fallidas` : 'Todo correcto');
process.exit(fallos ? 1 : 0);
