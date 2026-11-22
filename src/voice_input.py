"""Consulta por voz: componente minimo de la interfaz basado en la Web Speech API del navegador.

Diseno
- Se renderiza con ``streamlit.components.v1.html`` (iframe del mismo origen), el mismo patron que ya usa app.py
  para el acordeon de la barra lateral. No anade dependencias ni componentes compilados.
- El reconocimiento lo hace el navegador (``SpeechRecognition`` / ``webkitSpeechRecognition``). La aplicacion no
  graba, no guarda ni envia audio a ningun servidor propio: solo recibe el texto que el usuario envie con el boton
  de consulta. Segun el navegador, el propio navegador puede procesar la voz en los servidores de su proveedor.
- La transcripcion se ANADE al campo de consulta existente (al final del texto que ya hubiera) y NUNCA se envia
  sola: el usuario la revisa, la edita y pulsa el boton de envio de siempre. No toca RRE, ADA ni el motor.
- El idioma sale del selector de la barra lateral (es -> es-CO, en -> en-US). Al cambiar el idioma el iframe se
  vuelve a crear con otra configuracion y cualquier reconocimiento activo se aborta.
- Si el navegador no lo soporta o la pagina no es segura (HTTPS), el control se desactiva con un aviso y la consulta
  escrita sigue funcionando igual.
"""
import json

VOICE_LANG = {"es": "es-CO", "en": "en-US"}
QUERY_INPUT_LABEL = "Query input"          # etiqueta (aria-label) del campo de consulta de app.py
WIDGET_HEIGHT = 46

LABEL_KEYS = (
    "voice_btn_start", "voice_btn_stop", "voice_btn_title", "voice_state_requesting", "voice_state_listening",
    "voice_state_processing", "voice_state_ready", "voice_state_nospeech", "voice_state_lang_changed",
    "voice_err_denied", "voice_err_nomic", "voice_err_unsupported", "voice_err_insecure", "voice_err_network",
    "voice_err_generic", "voice_err_noinput", "voice_btn_copy", "voice_state_copied",
)


def voice_lang_code(lang):
    """Codigo BCP-47 de reconocimiento para el idioma de la interfaz (por defecto, espanol de Colombia)."""
    return VOICE_LANG.get(lang, VOICE_LANG["es"])


def build_voice_widget_html(lang, labels, theme="auto", placeholder=""):
    """HTML autocontenido del control de dictado. ``labels``: {clave: texto} para LABEL_KEYS.
    ``theme`` solo forma parte de la configuracion para que el iframe se recree al cambiar el tema.
    ``placeholder``: texto de ayuda del campo, criterio de busqueda alternativo a la etiqueta."""
    cfg = {
        "lang": voice_lang_code(lang),
        "ui": lang,
        "theme": theme,
        "inputLabel": QUERY_INPUT_LABEL,
        "placeholder": str(placeholder or ""),
        "labels": {k: str(labels.get(k, k)) for k in LABEL_KEYS},
    }
    cfg_json = json.dumps(cfg, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return _TEMPLATE.replace("__CFG__", cfg_json)


_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html, body { margin: 0; padding: 0; background: transparent; overflow: hidden;
               font-family: "Source Sans Pro", "Source Sans 3", system-ui, -apple-system, "Segoe UI", sans-serif; }
  .row { display: flex; align-items: center; gap: 0.6rem; min-height: 40px; }
  button { flex: 0 0 auto; display: inline-flex; align-items: center; gap: 0.35rem; cursor: pointer;
           font: inherit; font-size: 0.9rem; font-weight: 600; line-height: 1.2; padding: 0.38rem 0.85rem;
           border-radius: 0.5rem; border: 1px solid var(--bd); background: transparent; color: var(--fg); }
  button:hover:not(:disabled) { border-color: var(--ac); color: var(--ac); }
  button:focus-visible { outline: 2px solid var(--ac); outline-offset: 2px; }
  button:disabled { cursor: not-allowed; opacity: 0.55; }
  button.listening { border-color: var(--rd); color: var(--rd); }
  .dot { width: 0.55rem; height: 0.55rem; border-radius: 50%; background: var(--rd); display: none; }
  button.listening .dot { display: inline-block; animation: pulse 1s ease-in-out infinite; }
  @keyframes pulse { 50% { opacity: 0.25; } }
  @media (prefers-reduced-motion: reduce) { button.listening .dot { animation: none; } }
  .status { flex: 1 1 auto; min-width: 0; font-size: 0.82rem; line-height: 1.3; color: var(--mu);
            overflow-wrap: anywhere; }
  .status.err { color: var(--rd); }
  .status.ok { color: var(--fg); }
  .interim { font-style: italic; }
  .copyrow { display: none; align-items: center; gap: 0.6rem; margin-top: 0.35rem; }
  body[data-copy="1"] .copyrow { display: flex; }
  .copytext { flex: 1 1 auto; min-width: 0; font-size: 0.9rem; color: var(--fg); padding: 0.3rem 0.5rem;
              border: 1px dashed var(--bd); border-radius: 0.4rem; user-select: all; -webkit-user-select: all;
              overflow-wrap: anywhere; }
</style></head>
<body>
<div class="row">
  <button id="mic" type="button" aria-pressed="false"><span class="dot" aria-hidden="true"></span><span id="lbl"></span></button>
  <div id="status" class="status" role="status" aria-live="polite"></div>
</div>
<div class="copyrow">
  <div id="copytext" class="copytext"></div>
  <button id="copy" type="button"></button>
</div>
<script>
(function () {
  "use strict";
  const CFG = __CFG__;
  const L = CFG.labels;
  const btn = document.getElementById("mic");
  const lbl = document.getElementById("lbl");
  const statusEl = document.getElementById("status");
  const copyBtn = document.getElementById("copy");
  const copyText = document.getElementById("copytext");
  let P = null;
  try { P = window.parent; void P.document; } catch (e) { P = null; }
  const KEY = "__ijfVoiceRecognition";

  // Documentos donde puede estar el campo, consultados en cada uso (no se guarda una referencia que pueda quedar
  // obsoleta): el del marco padre y, si es distinto, el de la ventana superior. Se omiten los no accesibles.
  function docs() {
    const out = [];
    for (const w of [window.parent, window.top]) {
      try { if (w && w !== window && w.document && out.indexOf(w.document) < 0) out.push(w.document); } catch (e) { /* noop */ }
    }
    return out;
  }
  const pdocNow = function () { const d = docs(); return d.length ? d[0] : null; };

  // Colores del tema activo de la aplicacion (variables --ijf-* del documento principal).
  function applyTheme() {
    const fb = { "--fg": "#0f172a", "--ac": "#2563eb", "--rd": "#dc2626", "--bd": "rgba(128,128,128,0.35)", "--mu": "#475569" };
    const map = { "--fg": "--ijf-text-color", "--ac": "--ijf-blue-accent", "--rd": "--ijf-red", "--bd": "--ijf-btn-border", "--mu": "--ijf-caption-color" };
    let cs = null;
    try { const d = pdocNow(); cs = d ? d.defaultView.getComputedStyle(d.documentElement) : null; } catch (e) { cs = null; }
    for (const k in map) {
      const v = cs ? cs.getPropertyValue(map[k]).trim() : "";
      document.documentElement.style.setProperty(k, v || fb[k]);
    }
  }

  function fitHeight() {
    try {
      const h = Math.max(40, Math.ceil(document.body.scrollHeight)) + 4;
      const fe = window.frameElement;
      if (fe) {
        fe.style.height = h + "px";
        // El contenedor de Streamlit fija la altura inicial: si no se ajusta, el contenido desbordado (avisos largos en
        // el movil, boton Copiar) queda bajo el bloque siguiente y no recibe toques.
        const box = fe.closest && fe.closest('[data-testid="stElementContainer"]');
        if (box) { box.style.height = h + "px"; box.style.minHeight = h + "px"; }
      }
    } catch (e) { /* sin acceso al marco: se mantiene la altura fija */ }
  }

  let readyTimer = null;
  function setState(state, msg, cls) {
    applyTheme();
    if (readyTimer) { clearInterval(readyTimer); readyTimer = null; }
    if (state === "ready") {
      // Tras enviar (el formulario vacia el campo) o borrar el texto, el aviso vuelve al estado inactivo.
      readyTimer = setInterval(function () {
        const el = queryInput();
        if (!el || !(el.value || "").trim()) setState("idle", "");
      }, 1000);
    }
    const listening = state === "listening" || state === "requesting";
    btn.classList.toggle("listening", listening);
    btn.setAttribute("aria-pressed", listening ? "true" : "false");
    btn.dataset.state = state;
    lbl.textContent = listening ? L.voice_btn_stop : L.voice_btn_start;
    btn.disabled = state === "unsupported" || state === "processing";
    statusEl.className = "status" + (cls ? " " + cls : "");
    statusEl.textContent = msg || "";
    document.body.dataset.state = state;
    fitHeight();
  }

  // Campos que nunca reciben el dictado: credenciales, tokens, administracion o autenticacion.
  const SENSITIVE = /token|password|passwd|contrase|clave|admin|auth|login|credencial|credential|secret|otp|one-time/i;
  // Areas principales de Streamlit (versiones actuales y anteriores). Fuera de ellas no se busca.
  const MAIN_SCOPES = '[data-testid="stMain"], section.main';

  // Un campo es apto solo si es un campo de texto visible y editable del area principal, fuera de la barra lateral,
  // sin indicios de credenciales y en un formulario que no pida contrasenas.
  function eligible(el) {
    try {
      const tag = el.tagName;
      if (tag !== "TEXTAREA" && !(tag === "INPUT" && ["text", "search", ""].indexOf((el.getAttribute("type") || "").toLowerCase()) >= 0)) return false;
      if (el.disabled || el.readOnly) return false;
      if (!el.closest(MAIN_SCOPES) || el.closest('[data-testid="stSidebar"]')) return false;
      if (!el.getClientRects().length) return false;                     // oculto (display:none, expansor cerrado)
      const W = el.ownerDocument.defaultView, cs = W.getComputedStyle(el);
      if (cs.visibility === "hidden" || cs.display === "none") return false;
      const attrs = ["aria-label", "name", "id", "autocomplete", "placeholder"].map(function (a) { return el.getAttribute(a) || ""; });
      if (attrs.some(function (v) { return SENSITIVE.test(v); })) return false;
      const form = el.closest('[data-testid="stForm"], form');
      if (form && form.querySelector('input[type="password"]')) return false;
      return true;
    } catch (e) { return false; }
  }

  // Campos aptos que cumplen un selector, en todos los documentos accesibles y solo dentro del area principal.
  function candidates(sel) {
    const out = [];
    for (const d of docs()) {
      let scopes = [];
      try { scopes = Array.prototype.slice.call(d.querySelectorAll(MAIN_SCOPES)); } catch (e) { scopes = []; }
      for (const sc of scopes) {
        let found = [];
        try { found = Array.prototype.slice.call(sc.querySelectorAll(sel)); } catch (e) { found = []; }
        for (const el of found) if (eligible(el) && out.indexOf(el) < 0) out.push(el);
      }
    }
    return out;
  }

  // Busca el campo de consulta con criterios de mas a menos especificos: texto de ayuda, etiqueta accesible y, por
  // ultimo, el unico campo de texto apto dentro de un formulario del area principal. Si un criterio da mas de un
  // candidato, el campo es ambiguo y no se escribe en ninguno (el texto se ofrece para copiarlo).
  function queryInput() {
    const q = function (s) { return s.replace(/["\\]/g, "\\$&"); };
    const steps = [];
    if (CFG.placeholder) steps.push('input[placeholder="' + q(CFG.placeholder) + '"], textarea[placeholder="' + q(CFG.placeholder) + '"]');
    steps.push('input[aria-label="' + q(CFG.inputLabel) + '"], textarea[aria-label="' + q(CFG.inputLabel) + '"]');
    steps.push('[data-testid="stForm"] input, [data-testid="stForm"] textarea, form input, form textarea');
    for (const sel of steps) {
      const c = candidates(sel);
      if (c.length === 1) return c[0];
      if (c.length > 1) return null;
    }
    return null;
  }

  // Codigo breve para diagnosticar en el dispositivo del usuario por que no se encontro el campo.
  function diag() {
    let parentOk = 0;
    try { void window.parent.document; parentOk = 1; } catch (e) { parentOk = 0; }
    const ua = navigator.userAgent;
    const os = ["Android", "iPhone", "iPad", "Windows", "Mac OS X", "Linux"].find(function (k) { return ua.indexOf(k) >= 0; }) || "?";
    return "[doc " + parentOk + "/" + docs().length + " · " + os + "]";
  }

  // Inserta el texto al final del campo existente sin enviarlo (React necesita el setter nativo + evento input).
  function appendToQuery(text) {
    const el = queryInput();
    if (!el) return false;
    const W = el.ownerDocument.defaultView;
    const proto = el.tagName === "TEXTAREA" ? W.HTMLTextAreaElement.prototype : W.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
    const cur = el.value || "";
    const next = cur.trim() ? cur.replace(/\s+$/, "") + " " + text : text;
    setter.call(el, next);
    el.dispatchEvent(new W.Event("input", { bubbles: true }));
    const touch = (W.matchMedia && W.matchMedia("(pointer: coarse)").matches);
    if (!touch) { try { el.focus(); el.setSelectionRange(next.length, next.length); } catch (e) { /* noop */ } }
    return true;
  }

  // Si el texto no puede escribirse en el campo, se muestra con un boton para copiarlo y pegarlo a mano.
  function offerCopy(text) {
    copyText.textContent = text;
    document.body.dataset.copy = "1";
    setState("error", L.voice_err_noinput + " " + diag(), "err");
    try { console.warn("IJF voz: campo de consulta no encontrado", diag()); } catch (e) { /* noop */ }
  }
  function hideCopy() { document.body.dataset.copy = ""; copyText.textContent = ""; }
  copyBtn.addEventListener("click", function () {
    const text = copyText.textContent || "";
    const done = function () { statusEl.className = "status ok"; statusEl.textContent = L.voice_state_copied; fitHeight(); };
    const fallback = function () {
      try {
        const r = document.createRange(); r.selectNodeContents(copyText);
        const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        if (document.execCommand && document.execCommand("copy")) done();
      } catch (e) { /* el texto queda seleccionado para copiarlo a mano */ }
    };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
      else fallback();
    } catch (e) { fallback(); }
  });

  function Ctor() {
    // Se usa el constructor del documento principal (permiso de microfono del sitio) y, si no, el del iframe.
    const w = [P, window];
    for (const x of w) {
      if (!x) continue;
      try { const c = x.SpeechRecognition || x.webkitSpeechRecognition; if (c) return c; } catch (e) { /* noop */ }
    }
    return null;
  }

  function secure() {
    try { return (P && P.isSecureContext) || window.isSecureContext; } catch (e) { return window.isSecureContext; }
  }

  function abortActive() {
    try {
      const r = P && P[KEY];
      if (r) { r.__ijfAborted = true; P[KEY + "Interrupted"] = Date.now(); r.abort(); }
    } catch (e) { /* noop */ }
    try { if (P) P[KEY] = null; } catch (e) { /* noop */ }
  }

  let rec = null;
  let finalText = "";
  let errored = false;

  function start() {
    const C = Ctor();
    if (!C) { setState("unsupported", L.voice_err_unsupported, "err"); return; }
    hideCopy();
    abortActive();
    finalText = ""; errored = false;
    try {
      rec = new C();
      rec.lang = CFG.lang;
      rec.interimResults = true;
      rec.maxAlternatives = 1;
      // En Android el modo continuo duplica resultados: alli se usa una frase por pulsacion.
      rec.continuous = !/Android/i.test(navigator.userAgent);
    } catch (e) { rec = null; setState("error", L.voice_err_generic, "err"); return; }
    const me = rec;
    me.onstart = function () { if (rec === me) setState("listening", L.voice_state_listening); };
    me.onresult = function (ev) {
      if (rec !== me) return;
      let fin = "", interim = "";
      for (let i = 0; i < ev.results.length; i++) {
        const r = ev.results[i];
        const tx = (r[0] && r[0].transcript) || "";
        if (r.isFinal) fin += tx; else interim += tx;
      }
      finalText = fin.replace(/\s+/g, " ").trim();
      const shown = (finalText + " " + interim).replace(/\s+/g, " ").trim();
      if (shown) {
        applyTheme();
        statusEl.className = "status interim";
        statusEl.textContent = L.voice_state_listening + " " + shown;
        fitHeight();
      }
    };
    me.onerror = function (ev) {
      if (rec !== me || me.__ijfAborted) return;
      const code = ev && ev.error;
      if (code === "aborted") return;
      if (code === "no-speech") { errored = true; setState("idle", L.voice_state_nospeech, "err"); return; }
      errored = true;
      const msg = (code === "not-allowed" || code === "service-not-allowed") ? L.voice_err_denied
        : code === "audio-capture" ? L.voice_err_nomic
        : code === "network" ? L.voice_err_network
        : code === "language-not-supported" ? L.voice_err_unsupported
        : L.voice_err_generic;
      setState("error", msg, "err");
    };
    me.onend = function () {
      if (rec !== me) return;
      rec = null;
      try { if (P && P[KEY] === me) P[KEY] = null; } catch (e) { /* noop */ }
      if (me.__ijfAborted) return;
      if (finalText) {
        if (appendToQuery(finalText)) setState("ready", L.voice_state_ready, "ok");
        else offerCopy(finalText);
      } else if (!errored) {
        setState("idle", L.voice_state_nospeech, "err");
      }
    };
    try { if (P) P[KEY] = me; } catch (e) { /* noop */ }
    setState("requesting", L.voice_state_requesting);
    try { me.start(); } catch (e) { rec = null; setState("error", L.voice_err_generic, "err"); }
  }

  function stop() {
    if (!rec) return;
    setState("processing", L.voice_state_processing);
    try { rec.stop(); } catch (e) { abortActive(); rec = null; setState("idle", ""); }
  }

  btn.addEventListener("click", function () {
    if (btn.dataset.state === "listening" || btn.dataset.state === "requesting") stop(); else start();
  });

  // Este iframe se recrea al cambiar idioma o tema: se aborta cualquier reconocimiento anterior.
  abortActive();
  const hadActive = (function () {
    try {
      const ts = P && P[KEY + "Interrupted"];
      if (P) P[KEY + "Interrupted"] = 0;
      return !!ts && Date.now() - ts < 15000;
    } catch (e) { return false; }
  })();
  window.addEventListener("pagehide", abortActive);

  copyBtn.textContent = L.voice_btn_copy;
  btn.title = L.voice_btn_title;
  btn.setAttribute("aria-label", L.voice_btn_title);
  if (!Ctor()) setState("unsupported", L.voice_err_unsupported, "err");
  else if (!secure()) setState("unsupported", L.voice_err_insecure, "err");
  else setState("idle", hadActive ? L.voice_state_lang_changed : "");
})();
</script>
</body></html>
"""
