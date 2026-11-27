"use strict";
// Web estática: lee data/discos.json (generado por scraper/web.py) y lo pinta.
// Todo lo que depende de géneros sale de los datos (taxonomía incluida).

const $ = (s, el = document) => el.querySelector(s);
// Lo que se pinta de una vez (Lighthouse: menos elementos = el móvil responde antes). El resto, con "ver más".
const SEMANAS_POR_TANDA = 3, DISCOS_POR_TANDA = 30, PROXIMOS_VISIBLES = 12;
let PRIORITARIAS = 0;     // las primeras portadas de la pantalla se piden ya, sin esperar (mejor LCP)
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES_LARGO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const SERVICIOS = { deezer: "Deezer", spotify: "Spotify", apple: "Apple Music", bandcamp: "Bandcamp", tidal: "Tidal",
  qobuz: "Qobuz", youtube: "YouTube", musicbrainz: "MusicBrainz", discogs: "Discogs", allmusic: "AllMusic" };
const SIN_SUB = "_sin";

let DATOS = null, SUB = {}, HOY = "", POR_ID = {};
const estado = { familia: "todas", subs: new Set(), desde: "", hasta: "", sello: "", q: "",
  orden: "fecha", destacados: false, milista: false, tandas: 1, anio: "" };

// ------------------------------------------------------------ almacenamiento local (sin cuentas)
const local = {
  get(k, d) { try { const v = localStorage.getItem("nd:" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem("nd:" + k, JSON.stringify(v)); } catch (e) { /* modo privado */ } },
};
let MI_LISTA = local.get("milista", {});      // id → copia mínima (por si el disco sale de la ventana)
let VISTA = local.get("vista", "rejilla");

// ------------------------------------------------------------ utilidades
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const norm = s => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const enc = encodeURIComponent;
function fechaLarga(iso, exacta = true) {
  const [y, m, d] = iso.split("-").map(Number);
  return exacta ? `${d} ${MESES[m - 1]} ${y}` : `${MESES[m - 1]} ${y} (aprox.)`;
}
function lunes(iso) {
  const d = new Date(iso + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
}
function restarMeses(iso, n) {
  const d = new Date(iso + "T12:00:00Z");
  d.setUTCMonth(d.getUTCMonth() - n);
  return d.toISOString().slice(0, 10);
}
function color(texto) {
  let h = 0;
  for (const c of texto) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `linear-gradient(135deg, hsl(${h} 45% 38%), hsl(${(h + 40) % 360} 50% 26%))`;
}
function portadaHTML(d, grande = false) {
  const vacia = `<div class="vacia" style="background:${color(d.artista + d.titulo)}">${esc(d.artista)}</div>`;
  const url = grande ? (d.portada_grande || d.portada) : d.portada;
  const alt = d.portada_alt ? ` data-alt="${esc(d.portada_alt)}"` : "";
  const doble = grande ? null : version2x(url);
  const srcset = doble ? ` srcset="${esc(url)} 1x, ${esc(doble)} 2x"` : "";
  const carga = !grande && PRIORITARIAS > 0 ? (PRIORITARIAS--, ' loading="eager" fetchpriority="high"') : ' loading="lazy"';
  return url ? `${vacia}<img src="${esc(url)}"${srcset}${alt} alt=""${carga} decoding="async" onerror="portadaFallida(this)">` : vacia;
}
// La misma portada al doble de tamaño (pantallas de alta densidad), según el servicio que la sirve.
function version2x(url) {
  if (!url) return null;
  if (url.includes("coverartarchive.org") && url.endsWith("front-250")) return url.replace("front-250", "front-500");
  if (url.includes("dzcdn.net") && url.includes("/250x250-")) return url.replace("/250x250-", "/500x500-");
  if (/bcbits\.com\/img\/.*_2\.(jpg|png)$/.test(url)) return url.replace(/_2\.(jpg|png)$/, "_16.$1");
  return null;
}

// portada que no carga: se prueba la alternativa (Deezer) y, si tampoco, queda el fondo con el nombre
function portadaFallida(img) {
  const alt = img.dataset.alt;
  if (alt && img.src !== alt) { img.removeAttribute("data-alt"); img.removeAttribute("srcset"); img.src = alt; } else img.remove();
}
window.portadaFallida = portadaFallida;
function toast(texto) {
  const t = $("#toast"); t.textContent = texto; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => { t.hidden = true; }, 2200);
}
async function compartir(titulo, texto, url) {
  try { if (navigator.share) { await navigator.share({ title: titulo, text: texto, url }); return; } } catch (e) { return; }
  try { await navigator.clipboard.writeText(url); toast("Enlace copiado"); } catch (e) { prompt("Copia el enlace:", url); }
}

// ------------------------------------------------------------ estado <-> URL
function leerURL() {
  const p = new URLSearchParams(location.search);
  estado.familia = p.get("familia") || "todas";
  estado.subs = new Set((p.get("sub") || "").split(",").filter(Boolean));
  estado.desde = p.get("desde") ?? restarMeses(HOY, 5);
  estado.hasta = p.get("hasta") || "";
  estado.sello = p.get("sello") || "";
  estado.q = p.get("q") || "";
  estado.orden = p.get("orden") || "fecha";
  estado.destacados = p.get("dest") === "1";
  estado.milista = p.get("milista") === "1";
  estado.anio = p.get("anio") || "";
}
function urlEstado() {
  const p = new URLSearchParams();
  if (estado.familia !== "todas") p.set("familia", estado.familia);
  if (estado.subs.size) p.set("sub", [...estado.subs].join(","));
  if (estado.desde !== restarMeses(HOY, 5)) p.set("desde", estado.desde);
  if (estado.hasta) p.set("hasta", estado.hasta);
  if (estado.sello) p.set("sello", estado.sello);
  if (estado.q) p.set("q", estado.q);
  if (estado.orden !== "fecha") p.set("orden", estado.orden);
  if (estado.destacados) p.set("dest", "1");
  if (estado.milista) p.set("milista", "1");
  if (estado.orden === "mejor" && estado.anio) p.set("anio", estado.anio);
  const qs = p.toString();
  return qs ? "?" + qs : location.pathname;
}
function escribirURL() { history.replaceState(null, "", urlEstado() + location.hash); }

// ------------------------------------------------------------ filtrado
function pasa(d, ignorar = "") {
  if (estado.orden === "mejor") {             // en "lo mejor del año" manda el año, no el rango de fechas
    if (!d.fecha.startsWith(estado.anio)) return false;
    return pasaSinFechas(d, ignorar);
  }
  return pasaSinFechas(d, ignorar, true);
}
function pasaSinFechas(d, ignorar = "", conFechas = false) {
  if (estado.milista && !MI_LISTA[d.id]) return false;
  if (estado.familia !== "todas" && !d.familias.includes(estado.familia)) return false;
  if (ignorar !== "subs" && estado.subs.size) {
    const ok = d.subgeneros.some(s => estado.subs.has(s)) || (estado.subs.has(SIN_SUB) && !d.subgeneros.length);
    if (!ok) return false;
  }
  if (estado.destacados && !d.destacado) return false;
  if (conFechas && !estado.milista) {
    if (estado.desde && d.fecha < estado.desde) return false;
    if (estado.hasta && d.fecha > estado.hasta) return false;
  }
  if (estado.sello && norm(d.sello) !== norm(estado.sello)) return false;
  if (estado.q) {               // todas las palabras, en cualquier orden ("price margo" → Margo Price)
    const texto = norm(`${d.artista} ${d.titulo} ${d.sello || ""}`);
    if (!norm(estado.q).split(/\s+/).filter(Boolean).every(p => texto.includes(p))) return false;
  }
  return true;
}

// ------------------------------------------------------------ pintar
function pintarFamilias() {
  const nav = $("#familias");
  const opciones = [["todas", "Todo"], ...Object.entries(DATOS.familias).map(([k, f]) => [k, f.corto || f.nombre])];
  nav.innerHTML = opciones.map(([k, n]) =>
    `<button role="tab" data-f="${k}" aria-selected="${estado.familia === k}">${esc(n)}</button>`).join("");
  nav.onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    estado.familia = b.dataset.f;
    if (estado.familia !== "todas") estado.subs = new Set([...estado.subs].filter(s => s === SIN_SUB || SUB[s]?.familias?.includes(estado.familia)));
    estado.tandas = 1; actualizar();
  };
}

function tarjeta(d) {
  const subs = d.subgeneros.slice(0, 2).map(s => SUB[s]?.nombre || s).join(" · ");
  const fam = d.familias.length === 1 ? `fam-${d.familias[0]}` : "";
  const insignia = d.nota != null ? `<span class="nota-badge" title="Nota media de ${d.n_notas} reseña(s)">${d.nota.toFixed(1)}</span>`
    : d.n_resenas ? `<span class="insignia">${d.n_resenas} ${d.n_resenas === 1 ? "reseña" : "reseñas"}</span>` : "";
  const lado = `<div class="t-lado">${d.nota != null ? `<b>${d.nota.toFixed(1)}</b>` : ""}${fechaLarga(d.fecha)}</div>`;
  return `<button class="tarjeta" data-id="${esc(d.id)}">
    <div class="portada">${portadaHTML(d)}${insignia}
      ${d.destacado ? '<span class="dest-badge" title="Destacado">✦</span>' : ""}
      ${MI_LISTA[d.id] ? '<span class="lista-badge" title="En mi lista">★</span>' : ""}</div>
    <div><div class="t-artista">${esc(d.artista)}</div>
    <div class="t-titulo">${esc(d.titulo)}</div>
    <div class="t-sub ${fam}">${subs ? esc(subs) : "<i>sin subgénero</i>"}</div></div>
    ${lado}
  </button>`;
}

function pintarMeses(publ) {
  const nav = $("#meses");
  if (estado.orden !== "fecha") { nav.innerHTML = ""; return; }
  const meses = [...new Set(publ.map(d => d.fecha.slice(0, 7)))].sort().reverse();
  nav.innerHTML = meses.map(m => `<button data-mes="${m}">${MESES_LARGO[+m.slice(5) - 1]}${m.slice(0, 4) !== HOY.slice(0, 4) ? " " + m.slice(0, 4) : ""}</button>`).join("");
  nav.onclick = e => {
    const b = e.target.closest("button"); if (!b) return;
    let sec = document.querySelector(`.semana[data-mes="${b.dataset.mes}"]`);
    while (!sec && $("#mas")) { estado.tandas++; pintar(); sec = document.querySelector(`.semana[data-mes="${b.dataset.mes}"]`); }
    if (sec) window.scrollTo({ top: sec.getBoundingClientRect().top + scrollY - $(".cab").offsetHeight - 8, behavior: "smooth" });
  };
}

function pintar() {
  PRIORITARIAS = 4;
  const lista = DATOS.discos.filter(d => pasa(d));
  const main = $("#contenido");
  main.classList.toggle("lista", VISTA === "lista");
  const info = estado.orden === "mejor" ? DATOS.mejores?.[estado.anio] : null;
  if (!lista.length && !(info && info.tipo === "listas")) {
    main.innerHTML = `<p class="estado">${estado.milista ? "Aún no has guardado discos. Abre uno y pulsa ☆ Guardar." : "No hay discos con estos filtros."}</p>`;
    pintarMeses([]); return;
  }
  let html = "";
  if (estado.orden === "mejor") { pintarMejores(lista, main); return; }
  if (estado.orden === "calendario") { pintarCalendario(lista, main); return; }
  if (estado.milista) {      // discos de los artistas que has guardado y que aún no están en tu lista
    const tuyos = new Set(Object.values(MI_LISTA).map(x => norm(x.a)));
    const nuevos = DATOS.discos.filter(d => !MI_LISTA[d.id] && tuyos.has(norm(d.artista)))
      .sort((a, b) => b.fecha.localeCompare(a.fecha)).slice(0, 24);
    if (nuevos.length) html += `<section class="semana prox"><h2><span>De tus artistas</span><span>${nuevos.length}</span></h2>
      <p class="aviso">Otros discos de artistas que tienes guardados.</p>
      <div class="rejilla">${nuevos.map(tarjeta).join("")}</div></section>`;
  }
  if (estado.orden !== "fecha") {
    const clave = estado.orden === "nota" ? (d => (d.nota ?? -1) * 100 + d.n_notas) : (d => d.n_resenas * 100 + (d.nota ?? 0));
    const orden = [...lista].sort((a, b) => clave(b) - clave(a) || b.fecha.localeCompare(a.fecha));
    const vis = orden.slice(0, estado.tandas * DISCOS_POR_TANDA);
    const titulo = estado.orden === "nota" ? "Mejor valorados" : "Más reseñados";
    html += `<section class="semana"><h2><span>${titulo}</span><span>${orden.length}</span></h2>
      <div class="rejilla">${vis.map(tarjeta).join("")}</div></section>`;
    if (orden.length > vis.length) html += `<button class="mas" id="mas">Ver más</button>`;
    main.innerHTML = html; pintarMeses([]);
  } else {
    const prox = lista.filter(d => d.fecha > HOY).sort((a, b) => a.fecha.localeCompare(b.fecha));
    const publ = lista.filter(d => d.fecha <= HOY);
    const semanas = new Map();
    for (const d of publ) { const k = lunes(d.fecha); if (!semanas.has(k)) semanas.set(k, []); semanas.get(k).push(d); }
    const claves = [...semanas.keys()].sort().reverse();
    const visibles = claves.slice(0, estado.tandas * SEMANAS_POR_TANDA);
    const nProx = estado.verProximos ? prox.length : PROXIMOS_VISIBLES;
    if (prox.length) html += `<section class="semana prox"><h2><span>Próximamente</span><span>${prox.length}</span></h2>
      <div class="rejilla">${prox.slice(0, nProx).map(tarjeta).join("")}</div>
      ${prox.length > nProx ? `<button class="mas" id="masProx">Ver los ${prox.length} próximos</button>` : ""}</section>`;
    for (const k of visibles) {
      const ds = semanas.get(k).sort((a, b) => (b.destacado - a.destacado) || b.n_resenas - a.n_resenas || a.artista.localeCompare(b.artista));
      const mes = ds.reduce((m, d) => d.fecha.slice(0, 7) > m ? d.fecha.slice(0, 7) : m, "");
      html += `<section class="semana" data-mes="${mes}"><h2><span>Semana del ${fechaLarga(k)}</span><span>${ds.length}</span></h2>
        <div class="rejilla">${ds.map(tarjeta).join("")}</div></section>`;
    }
    if (claves.length > visibles.length) html += `<button class="mas" id="mas">Ver semanas anteriores</button>`;
    main.innerHTML = html; pintarMeses(publ);
  }
  const mas = $("#mas");
  if (mas) mas.onclick = () => { estado.tandas++; pintar(); };
  const masProx = $("#masProx");
  if (masProx) masProx.onclick = () => { estado.verProximos = true; pintar(); };
}

// Calendario de salidas: un mes por bloque (lunes a domingo); cada día con su número de discos y
// una portada. Al tocar un día se muestran sus discos debajo. Por defecto, el mes en curso.
function pintarCalendario(lista, main) {
  const porDia = new Map();
  for (const d of lista) { if (!porDia.has(d.fecha)) porDia.set(d.fecha, []); porDia.get(d.fecha).push(d); }
  const meses = [...new Set(lista.map(d => d.fecha.slice(0, 7)))].sort();
  if (!estado.mesCal || !meses.includes(estado.mesCal)) estado.mesCal = meses.includes(HOY.slice(0, 7)) ? HOY.slice(0, 7) : meses[meses.length - 1];
  const mes = estado.mesCal, [y, m] = mes.split("-").map(Number);
  const primero = new Date(Date.UTC(y, m - 1, 1)), dias = new Date(Date.UTC(y, m, 0)).getUTCDate();
  const hueco = (primero.getUTCDay() + 6) % 7;                 // lunes = 0
  const i = meses.indexOf(mes);
  let celdas = "";
  for (let k = 0; k < hueco; k++) celdas += `<div class="cal-dia vacio" aria-hidden="true"></div>`;
  for (let dia = 1; dia <= dias; dia++) {
    const f = `${mes}-${String(dia).padStart(2, "0")}`, ds = porDia.get(f) || [];
    const portada = ds.find(d => d.portada)?.portada;
    celdas += ds.length
      ? `<button class="cal-dia${f === HOY ? " hoy" : ""}${f === estado.diaCal ? " activo" : ""}" data-dia="${f}" aria-label="${dia}: ${ds.length} discos">
          ${portada ? `<img src="${esc(portada)}" alt="" loading="lazy" onerror="this.remove()">` : ""}<span class="n">${dia}</span><b>${ds.length}</b></button>`
      : `<div class="cal-dia${f === HOY ? " hoy" : ""}"><span class="n">${dia}</span></div>`;
  }
  const delDia = estado.diaCal?.startsWith(mes) ? (porDia.get(estado.diaCal) || []) : [];
  main.innerHTML = `<section class="semana calendario"><h2>
      <button class="cal-nav" id="calAnt" ${i <= 0 ? "disabled" : ""} aria-label="Mes anterior">‹</button>
      <span>${MESES_LARGO[m - 1]} ${y}</span>
      <button class="cal-nav" id="calSig" ${i >= meses.length - 1 ? "disabled" : ""} aria-label="Mes siguiente">›</button></h2>
      <div class="cal-cab">${["L", "M", "X", "J", "V", "S", "D"].map(x => `<span>${x}</span>`).join("")}</div>
      <div class="cal-rejilla">${celdas}</div></section>
    ${delDia.length ? `<section class="semana"><h2><span>${fechaLarga(estado.diaCal)}</span><span>${delDia.length}</span></h2>
      <div class="rejilla">${delDia.map(tarjeta).join("")}</div></section>` : `<p class="aviso">Toca un día para ver sus discos.</p>`}`;
  $("#calAnt").onclick = () => { estado.mesCal = meses[i - 1]; pintar(); };
  $("#calSig").onclick = () => { estado.mesCal = meses[i + 1]; pintar(); };
  main.querySelectorAll("[data-dia]").forEach(b => { b.onclick = () => { estado.diaCal = b.dataset.dia; pintar(); }; });
  pintarMeses([]);
}

function pintarMejores(lista, main) {
  const info = DATOS.mejores?.[estado.anio] || {};
  pintarMeses([]);
  if (info.tipo === "discos") {
    const orden = [...lista].sort((a, b) => b.puntos - a.puntos || b.fecha.localeCompare(a.fecha)).slice(0, 100);
    main.innerHTML = `<section class="semana"><h2><span>Lo mejor de ${estado.anio}</span><span>top ${orden.length}</span></h2>
      <p class="aviso">Orden: nota media de las reseñas, listas de fin de año, número de reseñas y de fuentes.</p>
      <div class="rejilla">${orden.map((d, i) => tarjeta(d).replace('<div class="portada">', `<div class="portada"><span class="puesto">${i + 1}</span>`)).join("")}</div></section>`;
    return;
  }
  const filas = (info.lista || []).filter(e => estado.familia === "todas" || (e.familias || []).includes(estado.familia))
    .filter(e => !estado.q || norm(`${e.artista} ${e.titulo}`).includes(norm(estado.q)));
  main.innerHTML = `<section class="semana"><h2><span>Lo mejor de ${estado.anio}</span><span>${filas.length}</span></h2>
    <p class="aviso">Según las listas de fin de año de la prensa especializada (más arriba, en más listas).</p>
    <ol class="ranking">${filas.map(e => `<li><b>${esc(e.artista)}</b> – ${esc(e.titulo)}
      <span class="aviso">${esc(e.listas.join(" · "))}</span>
      <a class="busqueda" href="https://www.albumoftheyear.org/search/albums/?q=${enc(e.artista + " " + e.titulo)}" target="_blank" rel="noopener">AOTY 🔍</a></li>`).join("")}</ol></section>`;
}

function pintarPanel() {
  const base = DATOS.discos.filter(d => pasa(d, "subs"));
  const cuenta = {};
  for (const d of base) { for (const s of d.subgeneros) cuenta[s] = (cuenta[s] || 0) + 1; if (!d.subgeneros.length) cuenta[SIN_SUB] = (cuenta[SIN_SUB] || 0) + 1; }
  const chip = (id, nombre, desc) => `<span class="chip-grupo"><button class="chip" data-s="${id}" data-vacio="${cuenta[id] ? 0 : 1}" aria-pressed="${estado.subs.has(id)}">
      ${esc(nombre)}<small>${cuenta[id] || 0}</small></button>${desc ? `<button class="info" data-info="${id}" aria-label="Qué es ${esc(nombre)}">ⓘ</button>` : ""}</span>`;
  let html = `<p class="sub-desc nota-info" id="subInfo" hidden></p>`;
  for (const [fk, fam] of Object.entries(DATOS.familias)) {
    if (estado.familia !== "todas" && estado.familia !== fk) continue;
    if (estado.familia === "todas") html += `<p class="fam-titulo fam-${fk}">${esc(fam.nombre)}</p>`;
    for (const g of fam.grupos) {
      if (estado.familia === "todas" && g.nombre === "De otras familias") continue;
      html += `<div class="grupo"><h4>${esc(g.nombre)}</h4><div class="chips">${g.subs.map(s => chip(s.id, s.nombre, s.descripcion)).join("")}</div></div>`;
    }
  }
  html += `<div class="grupo"><h4>Otros</h4><div class="chips">${chip(SIN_SUB, "Sin subgénero", "")}</div></div>`;
  $("#subgeneros").innerHTML = html;
  $("#fDesde").value = estado.desde; $("#fHasta").value = estado.hasta; $("#fSello").value = estado.sello;
  $("#numResultados").textContent = DATOS.discos.filter(d => pasa(d)).length;
  // suscripciones: la familia elegida (o todo) y, si hay un solo subgénero, el suyo
  const fam = estado.familia === "todas" ? "todo" : estado.familia;
  const nombreFam = fam === "todo" ? "todas las novedades" : DATOS.familias[fam].nombre;
  const base_url = new URL(".", location.href).href;
  let sus = `<a href="rss/${fam}.xml">RSS · ${esc(nombreFam)}</a>
    <a href="${esc(base_url.replace(/^https?:/, "webcal:"))}cal/${fam}.ics">📅 Próximos · ${esc(nombreFam)}</a>`;
  const subsReales = [...estado.subs].filter(s => s !== SIN_SUB);
  if (subsReales.length === 1) sus += `<a href="rss/${subsReales[0]}.xml">RSS · ${esc(SUB[subsReales[0]]?.nombre)}</a>`;
  $("#suscribir").innerHTML = sus;
}

function contarFiltros() {
  const n = estado.subs.size + (estado.sello ? 1 : 0) + (estado.hasta ? 1 : 0) + (estado.desde !== restarMeses(HOY, 5) ? 1 : 0);
  const el = $("#numFiltros"); el.hidden = !n; el.textContent = n;
  $("#numLista").textContent = Object.keys(MI_LISTA).length;
  $("#btnLista").setAttribute("aria-pressed", estado.milista);
  $("#btnDest").setAttribute("aria-pressed", estado.destacados);
  $("#orden").value = estado.orden;
  $("#selAnio").hidden = estado.orden !== "mejor";
  $("#vRejilla").setAttribute("aria-pressed", VISTA === "rejilla");
  $("#vLista").setAttribute("aria-pressed", VISTA === "lista");
}

function actualizar() {
  escribirURL(); pintarFamilias(); pintar(); contarFiltros();
  if (!$("#panel").hidden) pintarPanel();
}

// ------------------------------------------------------------ ficha
function enlacesEscucha(d) {
  const q = enc(`${d.artista} ${d.titulo}`);
  const directos = Object.entries(d.enlaces || {}).filter(([k]) => SERVICIOS[k] && k !== "musicbrainz" && k !== "discogs" && k !== "allmusic");
  const tiene = new Set(directos.map(([k]) => k));
  const busquedas = [
    ["spotify", "Spotify", `https://open.spotify.com/search/${q}`],
    ["youtube", "YouTube Music", `https://music.youtube.com/search?q=${q}`],
    ["bandcamp", "Bandcamp", `https://bandcamp.com/search?q=${q}&item_type=a`],
    ["apple", "Apple Music", `https://music.apple.com/search?term=${q}`],
    ["qobuz", "Qobuz", `https://www.qobuz.com/search?q=${q}`],
  ].filter(([k]) => !tiene.has(k));
  return directos.map(([k, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener">${SERVICIOS[k]}</a>`).join("") +
    busquedas.map(([, n, u]) => `<a class="busqueda" href="${u}" target="_blank" rel="noopener" title="Búsqueda">${n} 🔍</a>`).join("");
}

function icsDisco(d) {
  const dia = d.fecha.replace(/-/g, "");
  const fin = new Date(d.fecha + "T12:00:00Z"); fin.setUTCDate(fin.getUTCDate() + 1);
  const txt = s => String(s || "").replace(/[\\;,]/g, m => "\\" + m);
  const ics = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//novedades-discos//ES", "BEGIN:VEVENT",
    `UID:${d.id}@novedades-discos`, `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`,
    `DTSTART;VALUE=DATE:${dia}`, `DTEND;VALUE=DATE:${fin.toISOString().slice(0, 10).replace(/-/g, "")}`,
    `SUMMARY:${txt(d.artista + " – " + d.titulo)}`, `DESCRIPTION:${txt(d.sello)}`, "END:VEVENT", "END:VCALENDAR"].join("\r\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
  a.download = `${norm(d.artista + "-" + d.titulo).replace(/[^a-z0-9]+/g, "-").slice(0, 50)}.ics`;
  a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

function alternarLista(d) {
  if (MI_LISTA[d.id]) delete MI_LISTA[d.id];
  else MI_LISTA[d.id] = { a: d.artista, t: d.titulo, f: d.fecha, guardado: HOY };
  local.set("milista", MI_LISTA);
  toast(MI_LISTA[d.id] ? "Guardado en tu lista" : "Quitado de tu lista");
}

// Detalles de la ficha (enlaces, fuentes, reseñas…): un archivo por mes, que se pide al abrir un disco.
const FICHAS = new Map();
function cargarDetalle(d) {
  const mes = d.fecha.slice(0, 7);
  if (!FICHAS.has(mes)) FICHAS.set(mes, fetch(`data/fichas/${mes}.json`).then(r => r.ok ? r.json() : {}).catch(() => null));
  return FICHAS.get(mes).then(dets => {
    if (dets === null) FICHAS.delete(mes);            // sin red: se volverá a intentar
    Object.assign(d, { resenas: [], fuentes: [], enlaces: {}, dicen: [] }, (dets || {})[d.id] || {}, { _detalle: !!dets });
    return d;
  });
}

async function abrirFicha(id) {
  const d = POR_ID[id]; if (!d) return;
  if (!d._detalle) await cargarDetalle(d);
  const subs = d.subgeneros.map(s => `<span class="chip">${esc(SUB[s]?.nombre || s)}</span>`).join(" ");
  const descs = d.subgeneros.filter(s => SUB[s]?.descripcion).map(s => `<p class="sub-desc"><b>${esc(SUB[s].nombre)}:</b> ${esc(SUB[s].descripcion)}</p>`).join("");
  const resenas = d.resenas.map(r => `<li><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.nombre)}</a>
      <span class="nota">${esc(r.nota || "")}</span></li>`).join("");
  const fuentes = d.fuentes.map(f => `<li><a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.nombre)}</a>
      <span class="aviso">${f.fecha ? fechaLarga(f.fecha) : ""}</span></li>`).join("");
  const q = enc(`${d.artista} ${d.titulo}`);
  const otras = `<a class="busqueda" href="https://www.albumoftheyear.org/search/albums/?q=${q}" target="_blank" rel="noopener">Album of the Year 🔍</a>
    <a class="busqueda" href="https://www.metacritic.com/search/${enc(d.titulo)}/" target="_blank" rel="noopener">Metacritic 🔍</a>
    <a class="busqueda" href="https://rateyourmusic.com/search?searchterm=${q}&searchtype=l" target="_blank" rel="noopener">Rate Your Music 🔍</a>`;
  const proximo = d.fecha > HOY;
  const mismos = DATOS.discos.filter(x => x.id !== d.id && norm(x.artista) === norm(d.artista)).sort((a, b) => b.fecha.localeCompare(a.fecha));
  // parecidos: comparten algún subgénero, de otro artista, ordenados por subgéneros en común y cercanía de fecha
  const subsD = new Set(d.subgeneros), tD = Date.parse(d.fecha);
  const parecidos = subsD.size ? DATOS.discos
    .filter(x => x.id !== d.id && norm(x.artista) !== norm(d.artista) && x.subgeneros.some(s => subsD.has(s)))
    .map(x => [x, x.subgeneros.filter(s => subsD.has(s)).length, Math.abs(Date.parse(x.fecha) - tD)])
    .sort((a, b) => b[1] - a[1] || a[2] - b[2]).slice(0, 6).map(([x]) => x) : [];
  const dlg = $("#ficha");
  dlg.innerHTML = `<div class="f-portada">${portadaHTML(d, true)}
      <button class="f-cerrar" aria-label="Cerrar">×</button></div>
    <div class="f-cuerpo">
      <h2 id="fichaTitulo">${esc(d.titulo)}</h2>
      <p class="f-artista"><button class="enlace-filtro" id="fichaArtista" title="Ver todos sus discos">${esc(d.artista)}</button></p>
      <div class="f-acciones">
        <button id="fGuardar" aria-pressed="${!!MI_LISTA[d.id]}">${MI_LISTA[d.id] ? "★ En mi lista" : "☆ Guardar"}</button>
        <button id="fCompartir">Compartir</button>
        ${proximo ? '<button id="fCal">📅 Añadir al calendario</button>' : ""}
      </div>
      <dl class="f-datos">
        <dt>Fecha</dt><dd>${fechaLarga(d.fecha, d.fecha_exacta)}${proximo ? " · próximamente" : ""}</dd>
        <dt>Sello</dt><dd>${d.sello ? `<button class="enlace-filtro" id="fichaSello" title="Ver todos los discos del sello">${esc(d.sello)}</button>` : "—"}</dd>
        ${d.pistas ? `<dt>Pistas</dt><dd>${d.pistas}</dd>` : ""}
        ${d.tipo && d.tipo !== "álbum" ? `<dt>Tipo</dt><dd>${esc(d.tipo)}</dd>` : ""}
        ${d.nota != null ? `<dt>Nota</dt><dd><span class="f-nota">${d.nota.toFixed(1)}</span>media de ${d.n_notas} ${d.n_notas === 1 ? "reseña" : "reseñas"}${d.destacado ? " · ✦ Destacado" : ""}</dd>` : ""}
      </dl>
      <div class="chips">${subs || '<span class="aviso">Sin subgénero asignado</span>'}</div>${descs}
      ${d.dicen?.length ? `<h3>Lo que dicen</h3><ul class="dicen">${d.dicen.map(t => `<li>${esc(t)}</li>`).join("")}</ul>` : ""}
      <h3>Escuchar</h3>
      ${d.deezer_id ? `<div class="reproductor"><iframe title="Reproductor de Deezer" loading="lazy"
         src="https://widget.deezer.com/widget/auto/album/${d.deezer_id}?tracklist=true" allow="encrypted-media; clipboard-write"></iframe></div>` : ""}
      <div class="enlaces" style="margin-top:8px">${enlacesEscucha(d)}</div>
      ${d.etiquetas?.length ? `<h3>Etiquetas de estilo</h3><p class="etiquetas">${d.etiquetas.map(t => `<span>${esc(t)}</span>`).join("")}</p>` : ""}
      ${parecidos.length ? `<h3>Parecidos</h3><ul class="f-lista">${parecidos.map(x => `<li><button class="enlace-filtro" data-abrir="${esc(x.id)}">${esc(x.artista)} – ${esc(x.titulo)}</button>
        <span class="aviso">${fechaLarga(x.fecha, x.fecha_exacta)}</span></li>`).join("")}</ul>` : ""}
      ${mismos.length ? `<h3>Del mismo artista</h3><ul class="f-lista">${mismos.map(x => `<li><button class="enlace-filtro" data-abrir="${esc(x.id)}">${esc(x.titulo)}</button>
        <span class="aviso">${fechaLarga(x.fecha, x.fecha_exacta)}</span></li>`).join("")}</ul>` : ""}
      <h3>Reseñado en</h3>
      ${resenas ? `<ul class="f-lista">${resenas}</ul>` : '<p class="aviso">Sin reseñas encontradas todavía.</p>'}
      <h3>Ver la nota en</h3><div class="enlaces">${otras}</div>
      <h3>Aparece en</h3><ul class="f-lista">${fuentes}</ul>
      ${d.enlaces?.musicbrainz ? `<p class="aviso"><a href="${esc(d.enlaces.musicbrainz)}" target="_blank" rel="noopener">Ficha en MusicBrainz</a></p>` : ""}
      ${d.idioma ? "" : '<p class="aviso">Idioma sin verificar.</p>'}
    </div>`;
  $(".f-cerrar", dlg).onclick = () => dlg.close();
  $("#fGuardar", dlg).onclick = e => { alternarLista(d); e.target.setAttribute("aria-pressed", !!MI_LISTA[d.id]);
    e.target.textContent = MI_LISTA[d.id] ? "★ En mi lista" : "☆ Guardar"; contarFiltros(); };
  $("#fCompartir", dlg).onclick = () => compartir(`${d.artista} – ${d.titulo}`, `${d.artista} – ${d.titulo}`,
    location.origin + location.pathname + "#disco=" + enc(d.id));
  if (proximo) $("#fCal", dlg).onclick = () => icsDisco(d);
  // artista y sello: cierran la ficha y filtran todos sus discos (sin límite de fechas)
  const filtrarPor = (campo, valor) => {
    Object.assign(estado, { familia: "todas", subs: new Set(), desde: "", hasta: "", q: "", sello: "", milista: false, destacados: false, orden: "fecha", tandas: 1 });
    estado[campo] = valor; $("#q").value = estado.q;
    dlg.close(); actualizar(); window.scrollTo({ top: 0 });
    toast(campo === "q" ? `Discos de ${valor}` : `Discos del sello ${valor}`);
  };
  $("#fichaArtista", dlg).onclick = () => filtrarPor("q", d.artista);
  if (d.sello) $("#fichaSello", dlg).onclick = () => filtrarPor("sello", d.sello);
  dlg.querySelectorAll("[data-abrir]").forEach(b => { b.onclick = () => abrirFicha(b.dataset.abrir); });
  dlg.onclose = () => { if (location.hash) history.replaceState(null, "", location.pathname + location.search); pintar(); };
  dlg.onclick = e => { if (e.target === dlg) dlg.close(); };
  if (!dlg.open) dlg.showModal();
  history.replaceState(null, "", location.pathname + location.search + "#disco=" + enc(id));
}

// ------------------------------------------------------------ eventos
function eventos() {
  $("#contenido").addEventListener("click", e => { const t = e.target.closest(".tarjeta"); if (t) abrirFicha(t.dataset.id); });
  let temp;
  $("#q").value = estado.q;
  $("#q").addEventListener("input", e => {
    clearTimeout(temp);
    temp = setTimeout(() => { estado.q = e.target.value.trim(); estado.tandas = 1; actualizar(); }, 200);
  });
  const panel = $("#panel");
  const abrir = () => { panel.hidden = false; $("#abrirFiltros").setAttribute("aria-expanded", "true"); pintarPanel(); };
  const cerrar = () => { panel.hidden = true; $("#abrirFiltros").setAttribute("aria-expanded", "false"); };
  $("#abrirFiltros").onclick = abrir;
  $("#cerrarFiltros").onclick = cerrar;
  $("#aplicar").onclick = cerrar;
  panel.addEventListener("click", e => { if (e.target === panel) cerrar(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !panel.hidden) cerrar(); });
  $("#subgeneros").addEventListener("click", e => {
    const i = e.target.closest(".info");
    if (i) { const s = SUB[i.dataset.info]; const p = $("#subInfo"); p.hidden = false;
      p.innerHTML = `<b>${esc(s.nombre)}:</b> ${esc(s.descripcion)}`; return; }
    const c = e.target.closest(".chip"); if (!c) return;
    const s = c.dataset.s;
    estado.subs.has(s) ? estado.subs.delete(s) : estado.subs.add(s);
    estado.tandas = 1; actualizar();
  });
  $("#fDesde").onchange = e => { estado.desde = e.target.value; actualizar(); };
  $("#fHasta").onchange = e => { estado.hasta = e.target.value; actualizar(); };
  $("#fSello").onchange = e => { estado.sello = e.target.value.trim(); actualizar(); };
  $("#limpiar").onclick = () => { estado.subs.clear(); estado.sello = ""; estado.hasta = ""; estado.desde = restarMeses(HOY, 5); actualizar(); };
  $("#orden").onchange = e => {
    estado.orden = e.target.value; estado.tandas = 1;
    if (estado.orden === "mejor" && !estado.anio) estado.anio = Object.keys(DATOS.mejores || {}).sort().reverse()[0] || HOY.slice(0, 4);
    actualizar();
  };
  $("#anio").value = estado.anio || $("#anio").value;
  $("#anio").onchange = e => { estado.anio = e.target.value; actualizar(); };
  $("#btnDest").onclick = () => { estado.destacados = !estado.destacados; estado.tandas = 1; actualizar(); };
  $("#btnLista").onclick = () => { estado.milista = !estado.milista; estado.tandas = 1; actualizar(); };
  $("#vRejilla").onclick = () => { VISTA = "rejilla"; local.set("vista", VISTA); actualizar(); };
  $("#vLista").onclick = () => { VISTA = "lista"; local.set("vista", VISTA); actualizar(); };
}

// ------------------------------------------------------------ inicio
fetch("data/discos.json", { cache: "no-cache" })
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(datos => {
    DATOS = datos;
    HOY = datos.actualizado;
    for (const [fk, f] of Object.entries(datos.familias))
      for (const g of f.grupos) for (const s of g.subs) {
        const prev = SUB[s.id];
        SUB[s.id] = { ...(prev || s), familias: [...new Set([...(prev?.familias || []), fk])] };
      }
    for (const d of datos.discos) POR_ID[d.id] = d;
    const sellos = [...new Set(datos.discos.map(d => d.sello).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    $("#sellos").innerHTML = sellos.map(s => `<option value="${esc(s)}">`).join("");
    $("#actualizado").textContent = `${datos.discos.length} discos · actualizado el ${fechaLarga(datos.actualizado)}`;
    $("#anio").innerHTML = Object.keys(datos.mejores || {}).sort().reverse().map(a => `<option>${a}</option>`).join("");
    leerURL();
    if (estado.anio) $("#anio").value = estado.anio;
    eventos(); actualizar();
    const m = location.hash.match(/disco=([^&]+)/);
    if (m) abrirFicha(decodeURIComponent(m[1]));
    // un enlace a otro disco abierto con la web ya cargada (misma pestaña) también abre su ficha
    addEventListener("hashchange", () => {
      const h = location.hash.match(/disco=([^&]+)/);
      if (h && !$("#ficha").open) abrirFicha(decodeURIComponent(h[1]));
    });
  })
  .catch(err => { $("#estado").textContent = "No se pudieron cargar los datos (" + err.message + ")."; });

if ("serviceWorker" in navigator) addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));

// cabecera que se esconde al bajar y reaparece al subir (solo pantallas estrechas)
(() => {
  const cab = document.querySelector(".cab");
  if (!cab) return;
  let ultima = window.scrollY, pendiente = false;
  window.addEventListener("scroll", () => {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(() => {
      const y = window.scrollY, estrecha = window.innerWidth < 760;
      const abierto = document.querySelector("dialog[open]") || !document.querySelector("#panel")?.hidden;
      if (!estrecha || y < 160 || abierto) cab.classList.remove("oculta");
      else if (y > ultima + 6) cab.classList.add("oculta");
      else if (y < ultima - 6) cab.classList.remove("oculta");
      ultima = y; pendiente = false;
    });
  }, { passive: true });
  cab.addEventListener("focusin", () => cab.classList.remove("oculta"));
})();
