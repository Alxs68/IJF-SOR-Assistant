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
    "voice_err_generic", "voice_err_noinput",
)


def voice_lang_code(lang):
    """Codigo BCP-47 de reconocimiento para el idioma de la interfaz (por defecto, espanol de Colombia)."""
    return VOICE_LANG.get(lang, VOICE_LANG["es"])


def build_voice_widget_html(lang, labels, theme="auto"):
    """HTML autocontenido del control de dictado. ``labels``: {clave: texto} para LABEL_KEYS.
    ``theme`` solo forma parte de la configuracion para que el iframe se recree al cambiar el tema."""
    cfg = {
        "lang": voice_lang_code(lang),
        "ui": lang,
        "theme": theme,
        "inputLabel": QUERY_INPUT_LABEL,
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
</style></head>
<body>
<div class="row">
  <button id="mic" type="button" aria-pressed="false"><span class="dot" aria-hidden="true"></span><span id="lbl"></span></button>
  <div id="status" class="status" role="status" aria-live="polite"></div>
</div>
<script>
(function () {
  "use strict";
  const CFG = __CFG__;
  const L = CFG.labels;
  const btn = document.getElementById("mic");
  const lbl = document.getElementById("lbl");
  const statusEl = document.getElementById("status");
  let P = null;
  try { P = window.parent; void P.document; } catch (e) { P = null; }
  const pdoc = P ? P.document : null;
  const KEY = "__ijfVoiceRecognition";

  // Colores del tema activo de la aplicacion (variables --ijf-* del documento principal).
  function applyTheme() {
    const fb = { "--fg": "#0f172a", "--ac": "#2563eb", "--rd": "#dc2626", "--bd": "rgba(128,128,128,0.35)", "--mu": "#475569" };
    const map = { "--fg": "--ijf-text-color", "--ac": "--ijf-blue-accent", "--rd": "--ijf-red", "--bd": "--ijf-btn-border", "--mu": "--ijf-caption-color" };
    let cs = null;
    try { cs = pdoc ? P.getComputedStyle(pdoc.documentElement) : null; } catch (e) { cs = null; }
    for (const k in map) {
      const v = cs ? cs.getPropertyValue(map[k]).trim() : "";
      document.documentElement.style.setProperty(k, v || fb[k]);
    }
  }

  function fitHeight() {
    try {
      const h = Math.max(40, Math.ceil(document.body.scrollHeight)) + 4;
      if (window.frameElement) window.frameElement.style.height = h + "px";
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

  function queryInput() {
    if (!pdoc) return null;
    const sel = 'input[aria-label="' + CFG.inputLabel + '"], textarea[aria-label="' + CFG.inputLabel + '"]';
    return pdoc.querySelector(sel);
  }

  // Inserta el texto al final del campo existente sin enviarlo (React necesita el setter nativo + evento input).
  function appendToQuery(text) {
    const el = queryInput();
    if (!el) return false;
    const proto = el.tagName === "TEXTAREA" ? P.HTMLTextAreaElement.prototype : P.HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
    const cur = el.value || "";
    const next = cur.trim() ? cur.replace(/\s+$/, "") + " " + text : text;
    setter.call(el, next);
    el.dispatchEvent(new P.Event("input", { bubbles: true }));
    const touch = (P.matchMedia && P.matchMedia("(pointer: coarse)").matches);
    if (!touch) { try { el.focus(); el.setSelectionRange(next.length, next.length); } catch (e) { /* noop */ } }
    return true;
  }

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
    if (!queryInput()) { setState("error", L.voice_err_noinput, "err"); return; }
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
        else setState("error", L.voice_err_noinput, "err");
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

  btn.title = L.voice_btn_title;
  btn.setAttribute("aria-label", L.voice_btn_title);
  if (!Ctor()) setState("unsupported", L.voice_err_unsupported, "err");
  else if (!secure()) setState("unsupported", L.voice_err_insecure, "err");
  else setState("idle", hadActive ? L.voice_state_lang_changed : "");
})();
</script>
</body></html>
"""
