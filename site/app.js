"use strict";
// Web estática: lee data/discos.json (generado por scraper/web.py) y lo pinta.
// Todo lo que depende de géneros sale de los datos (taxonomía incluida).

const $ = (s, el = document) => el.querySelector(s);
const SEMANAS_POR_TANDA = 8;
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const SERVICIOS = { bandcamp: "Bandcamp", spotify: "Spotify", apple: "Apple Music", deezer: "Deezer", tidal: "Tidal",
  qobuz: "Qobuz", youtube: "YouTube", musicbrainz: "MusicBrainz", discogs: "Discogs", allmusic: "AllMusic" };

let DATOS = null, SUB = {}, HOY = "";
const estado = { familia: "todas", subs: new Set(), desde: "", hasta: "", sello: "", q: "", tandas: 1 };

// ------------------------------------------------------------ utilidades
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const norm = s => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
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
function portadaHTML(d, clase = "") {
  const vacia = `<div class="vacia" style="background:${color(d.artista + d.titulo)}">${esc(d.artista)}</div>`;
  if (!d.portada) return vacia;
  return `${vacia}<img src="${esc(d.portada)}" alt="" loading="lazy" decoding="async" ${clase}
           onerror="this.remove()">`;
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
}
function escribirURL() {
  const p = new URLSearchParams();
  if (estado.familia !== "todas") p.set("familia", estado.familia);
  if (estado.subs.size) p.set("sub", [...estado.subs].join(","));
  if (estado.desde !== restarMeses(HOY, 5)) p.set("desde", estado.desde);
  if (estado.hasta) p.set("hasta", estado.hasta);
  if (estado.sello) p.set("sello", estado.sello);
  if (estado.q) p.set("q", estado.q);
  const qs = p.toString();
  history.replaceState(null, "", (qs ? "?" + qs : location.pathname) + location.hash);
}

// ------------------------------------------------------------ filtrado
function pasa(d, ignorar = "") {
  if (estado.familia !== "todas" && !d.familias.includes(estado.familia)) return false;
  if (ignorar !== "subs" && estado.subs.size && !d.subgeneros.some(s => estado.subs.has(s))) return false;
  if (estado.desde && d.fecha < estado.desde) return false;
  if (estado.hasta && d.fecha > estado.hasta) return false;
  if (estado.sello && norm(d.sello) !== norm(estado.sello)) return false;
  if (estado.q) {
    const q = norm(estado.q);
    if (!norm(`${d.artista} ${d.titulo} ${d.sello || ""}`).includes(q)) return false;
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
    // quitar subgéneros que no son de la familia elegida
    if (estado.familia !== "todas") estado.subs = new Set([...estado.subs].filter(s => SUB[s]?.familia === estado.familia));
    estado.tandas = 1; actualizar();
  };
}

function tarjeta(d) {
  const subs = d.subgeneros.slice(0, 2).map(s => SUB[s]?.nombre || s).join(" · ");
  const fam = d.familias.length === 1 ? `fam-${d.familias[0]}` : "";
  const resenas = d.resenas.length ? `<span class="insignia">${d.resenas.length} ${d.resenas.length === 1 ? "reseña" : "reseñas"}</span>` : "";
  return `<button class="tarjeta" data-id="${esc(d.id)}" aria-label="${esc(d.artista)} – ${esc(d.titulo)}">
    <div class="portada">${portadaHTML(d)}${resenas}</div>
    <div class="t-artista">${esc(d.artista)}</div>
    <div class="t-titulo">${esc(d.titulo)}</div>
    <div class="t-sub ${fam}">${subs ? esc(subs) : "<i>sin subgénero</i>"}</div>
  </button>`;
}

function pintar() {
  const lista = DATOS.discos.filter(d => pasa(d));
  const main = $("#contenido");
  if (!lista.length) { main.innerHTML = `<p class="estado">No hay discos con estos filtros.</p>`; return; }
  const prox = lista.filter(d => d.fecha > HOY).sort((a, b) => a.fecha.localeCompare(b.fecha));
  const publ = lista.filter(d => d.fecha <= HOY);
  const semanas = new Map();
  for (const d of publ) {
    const k = lunes(d.fecha);
    if (!semanas.has(k)) semanas.set(k, []);
    semanas.get(k).push(d);
  }
  const claves = [...semanas.keys()].sort().reverse();
  const visibles = claves.slice(0, estado.tandas * SEMANAS_POR_TANDA);
  let html = "";
  if (prox.length) {
    html += `<section class="semana prox"><h2><span>Próximamente</span><span>${prox.length}</span></h2>
      <div class="rejilla">${prox.slice(0, 60).map(tarjeta).join("")}</div></section>`;
  }
  for (const k of visibles) {
    const ds = semanas.get(k).sort((a, b) => b.resenas.length - a.resenas.length || a.artista.localeCompare(b.artista));
    html += `<section class="semana"><h2><span>Semana del ${fechaLarga(k)}</span><span>${ds.length}</span></h2>
      <div class="rejilla">${ds.map(tarjeta).join("")}</div></section>`;
  }
  if (claves.length > visibles.length) html += `<button class="mas" id="mas">Ver semanas anteriores</button>`;
  main.innerHTML = html;
  const mas = $("#mas");
  if (mas) mas.onclick = () => { estado.tandas++; pintar(); };
}

function pintarPanel() {
  // recuentos de cada subgénero con el resto de filtros aplicados
  const base = DATOS.discos.filter(d => pasa(d, "subs"));
  const cuenta = {};
  for (const d of base) for (const s of d.subgeneros) cuenta[s] = (cuenta[s] || 0) + 1;
  let html = "";
  for (const [fk, fam] of Object.entries(DATOS.familias)) {
    if (estado.familia !== "todas" && estado.familia !== fk) continue;
    if (estado.familia === "todas") html += `<p class="fam-titulo fam-${fk}">${esc(fam.nombre)}</p>`;
    for (const g of fam.grupos) {
      const chips = g.subs.map(s => `<button class="chip" data-s="${s.id}" aria-pressed="${estado.subs.has(s.id)}">
        ${esc(s.nombre)}<small>${cuenta[s.id] || 0}</small></button>`).join("");
      html += `<div class="grupo"><h4>${esc(g.nombre)}</h4><div class="chips">${chips}</div></div>`;
    }
  }
  $("#subgeneros").innerHTML = html;
  $("#fDesde").value = estado.desde; $("#fHasta").value = estado.hasta; $("#fSello").value = estado.sello;
  $("#numResultados").textContent = DATOS.discos.filter(d => pasa(d)).length;
}

function contarFiltros() {
  const n = estado.subs.size + (estado.sello ? 1 : 0) + (estado.hasta ? 1 : 0) + (estado.desde !== restarMeses(HOY, 5) ? 1 : 0);
  const el = $("#numFiltros"); el.hidden = !n; el.textContent = n;
}

function actualizar() {
  escribirURL(); pintarFamilias(); pintar(); contarFiltros();
  if (!$("#panel").hidden) pintarPanel();
}

// ------------------------------------------------------------ ficha
function abrirFicha(id) {
  const d = DATOS.discos.find(x => x.id === id); if (!d) return;
  const subs = d.subgeneros.map(s => `<span class="chip" aria-pressed="false">${esc(SUB[s]?.nombre || s)}</span>`).join(" ");
  const resenas = d.resenas.map(r => `<li><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.nombre)}</a>
      <span class="nota">${esc(r.nota || "")}</span></li>`).join("");
  const fuentes = d.fuentes.map(f => `<li><a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.nombre)}</a>
      <span class="aviso">${f.fecha ? fechaLarga(f.fecha) : ""}</span></li>`).join("");
  const enlaces = Object.entries(d.enlaces || {}).filter(([k]) => SERVICIOS[k])
    .sort(([a], [b]) => Object.keys(SERVICIOS).indexOf(a) - Object.keys(SERVICIOS).indexOf(b))
    .map(([k, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener">${SERVICIOS[k]}</a>`).join("");
  const dlg = $("#ficha");
  dlg.innerHTML = `<div class="f-portada">${portadaHTML({ ...d, portada: d.portada_grande || d.portada })}
      <button class="f-cerrar" aria-label="Cerrar">×</button></div>
    <div class="f-cuerpo">
      <h2 id="fichaTitulo">${esc(d.titulo)}</h2>
      <p class="f-artista">${esc(d.artista)}</p>
      <dl class="f-datos">
        <dt>Fecha</dt><dd>${fechaLarga(d.fecha, d.fecha_exacta)}${d.fecha > HOY ? " · próximamente" : ""}</dd>
        <dt>Sello</dt><dd>${esc(d.sello || "—")}</dd>
        ${d.pistas ? `<dt>Pistas</dt><dd>${d.pistas}</dd>` : ""}
        ${d.tipo && d.tipo !== "álbum" ? `<dt>Tipo</dt><dd>${esc(d.tipo)}</dd>` : ""}
      </dl>
      <div class="chips">${subs || '<span class="aviso">Sin subgénero asignado</span>'}</div>
      <h3>Reseñado en</h3>
      ${resenas ? `<ul class="f-lista">${resenas}</ul>` : '<p class="aviso">Sin reseñas encontradas todavía.</p>'}
      <h3>Aparece en</h3><ul class="f-lista">${fuentes}</ul>
      ${enlaces ? `<h3>Escuchar</h3><div class="enlaces">${enlaces}</div>` : ""}
      ${d.idioma ? "" : '<p class="aviso">Idioma sin verificar.</p>'}
    </div>`;
  $(".f-cerrar", dlg).onclick = () => dlg.close();
  dlg.onclose = () => { if (location.hash) history.replaceState(null, "", location.pathname + location.search); };
  dlg.onclick = e => { if (e.target === dlg) dlg.close(); };
  if (!dlg.open) dlg.showModal();
  history.replaceState(null, "", location.pathname + location.search + "#disco=" + encodeURIComponent(id));
}

// ------------------------------------------------------------ eventos
function eventos() {
  $("#contenido").addEventListener("click", e => {
    const t = e.target.closest(".tarjeta"); if (t) abrirFicha(t.dataset.id);
  });
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
    const c = e.target.closest(".chip"); if (!c) return;
    const s = c.dataset.s;
    estado.subs.has(s) ? estado.subs.delete(s) : estado.subs.add(s);
    estado.tandas = 1; actualizar();
  });
  $("#fDesde").onchange = e => { estado.desde = e.target.value; actualizar(); };
  $("#fHasta").onchange = e => { estado.hasta = e.target.value; actualizar(); };
  $("#fSello").onchange = e => { estado.sello = e.target.value.trim(); actualizar(); };
  $("#limpiar").onclick = () => {
    estado.subs.clear(); estado.sello = ""; estado.hasta = ""; estado.desde = restarMeses(HOY, 5); actualizar();
  };
}

// ------------------------------------------------------------ inicio
fetch("data/discos.json", { cache: "no-cache" })
  .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(datos => {
    DATOS = datos;
    HOY = datos.actualizado;
    for (const [fk, f] of Object.entries(datos.familias))
      for (const g of f.grupos) for (const s of g.subs) SUB[s.id] = { ...s, familia: fk };
    const sellos = [...new Set(datos.discos.map(d => d.sello).filter(Boolean))].sort((a, b) => a.localeCompare(b));
    $("#sellos").innerHTML = sellos.map(s => `<option value="${esc(s)}">`).join("");
    $("#actualizado").textContent = `${datos.discos.length} discos · actualizado el ${fechaLarga(datos.actualizado)}`;
    leerURL(); eventos(); actualizar();
    const m = location.hash.match(/disco=([^&]+)/);
    if (m) abrirFicha(decodeURIComponent(m[1]));
  })
  .catch(err => { $("#estado").textContent = "No se pudieron cargar los datos (" + err.message + ")."; });
