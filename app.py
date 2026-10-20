import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import base64
import re
import html
import io
import pypdf

from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from rag_engine import RagEngine
from citation_resolver import RESOURCE_DETAILS, resolve_url, _rrm_manager
from llm_provider import MultiProviderLLMManager
from feedback_manager import record_observation, MOTIVOS_VALIDOS
from i18n import t

logo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
logo_path = os.path.join(logo_dir, 'logo.svg')

st.set_page_config(
    page_title="IJF SOR Assistant",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern premium UI
st.markdown("""
<style>
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 1.5rem !important;
    }

    .status-badge-connected {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.2rem 0.4rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-badge-offline {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.2rem 0.4rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    :root {
        --ijf-blue: #003399;
        --ijf-blue-light: #1d4ed8;
        --ijf-red: #ED1C24;
        --kun-bg: #F9FAFB;
    }
    .kun-card {
        border-left: 3px solid var(--ijf-blue);
        background-color: var(--kun-bg);
        padding: 0.6rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: var(--ijf-blue) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: #4B5563 !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        padding-top: 0.15rem !important;
        padding-bottom: 0.15rem !important;
    }
    .element-container {
        margin-bottom: 0.4rem !important;
    }
    .active-query-card {
        background-color: rgba(234, 179, 8, 0.08) !important;
        border-left: 5px solid #eab308 !important;
        border-right: 1px solid rgba(234, 179, 8, 0.15) !important;
        border-top: 1px solid rgba(234, 179, 8, 0.15) !important;
        border-bottom: 1px solid rgba(234, 179, 8, 0.15) !important;
        padding: 1rem 1.25rem !important;
        border-radius: 0 8px 8px 0 !important;
        margin-bottom: 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03) !important;
        color: var(--text-color) !important;
    }
    div[data-testid="stButton"] button {
        background-color: transparent;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 9999px;
        padding: 0.4rem 0.85rem !important;
        text-align: center !important;
        color: var(--text-color);
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        line-height: 1.3;
        white-space: nowrap;
        display: block;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease;
        opacity: 0.8;
    }
    div[data-testid="stButton"] button p {
        margin: 0;
        text-align: center !important;
    }
    div[data-testid="stButton"] button:hover {
        border-color: var(--ijf-blue) !important;
        color: var(--ijf-blue) !important;
        background-color: rgba(0, 51, 153, 0.08) !important;
        opacity: 1;
    }
    div[data-testid="stButton"] button:active {
        background-color: rgba(29, 78, 216, 0.14) !important;
    }
    /* Estilos específicos para píldoras interactivas de citas normativas */
    .citation-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
        margin-bottom: 14px;
        align-items: center;
    }
    .citation-title-label {
        font-size: 0.82rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-right: 6px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .pdf-viewer-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white;
        padding: 10px 14px;
        border-radius: 8px 8px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.9rem;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6 {
            font-size: 1rem !important;
            font-weight: 600 !important;
            line-height: 1.3 !important;
            margin-top: 0.75rem !important;
            margin-bottom: 0.5rem !important;
        }
    }
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown h5,
    .stMarkdown h6 {
        font-weight: 600 !important;
        line-height: 1.35 !important;
    }
    .stMarkdown h1 { font-size: 1.4rem !important; }
    .stMarkdown h2 { font-size: 1.2rem !important; }
    .stMarkdown h3 { font-size: 1.05rem !important; }
</style>
""", unsafe_allow_html=True)

def get_base64_logo(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception:
            return None
    return None

LOCAL_PDF_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "raw", "sor_2026_08_rebuild", "IJF_Sport_and_Organisation_Rules_2026_08_14.pdf"
)

@st.cache_data(max_entries=128)
def get_pdf_page_base64(page_number: int) -> str:
    """Extracts a single page from the local official SOR PDF and returns it as a base64 string."""
    try:
        if not os.path.exists(LOCAL_PDF_PATH):
            return ""
        reader = pypdf.PdfReader(LOCAL_PDF_PATH)
        idx = max(0, min(len(reader.pages) - 1, page_number - 1))
        writer = pypdf.PdfWriter()
        writer.add_page(reader.pages[idx])
        buf = io.BytesIO()
        writer.write(buf)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error extracting PDF page {page_number}: {e}")
        return ""

def render_pdf_viewer(pdf_url: str, initial_page: int = 1, search_quote: str = "", zoom_level: float = 1.0, height: int = 820, page_b64: str = ""):
    """
    Renders an interactive embedded PDF viewer using PDF.js CDN with range streaming,
    canvas rendering, text layer selection, and automated citation query highlighting.
    Uses base64-encoded page data when available to bypass CDN CORS limitations.
    """
    safe_quote = html.escape(search_quote).replace("'", "\\'")
    viewer_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="utf-8">
      <title>Visor PDF SOR IJF</title>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.css">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
          background-color: #0f172a;
          color: #f8fafc;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          height: 100vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }}
        #toolbar {{
          background: #1e293b;
          border-bottom: 1px solid #334155;
          padding: 8px 12px;
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          font-size: 0.85rem;
          user-select: none;
        }}
        .btn {{
          background: #334155;
          color: #f8fafc;
          border: 1px solid #475569;
          border-radius: 4px;
          padding: 4px 10px;
          cursor: pointer;
          font-weight: 500;
          font-size: 0.82rem;
          transition: background 0.15s, border-color 0.15s;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
        }}
        .btn:hover {{
          background: #475569;
          border-color: #64748b;
        }}
        .btn-primary {{
          background: #2563eb;
          border-color: #3b82f6;
        }}
        .btn-primary:hover {{
          background: #1d4ed8;
          border-color: #2563eb;
        }}
        .btn:disabled {{
          opacity: 0.4;
          cursor: not-allowed;
        }}
        .input-page {{
          background: #0f172a;
          color: #f8fafc;
          border: 1px solid #475569;
          border-radius: 4px;
          padding: 3px 6px;
          width: 52px;
          text-align: center;
          font-size: 0.85rem;
        }}
        #search-box {{
          background: #0f172a;
          color: #f8fafc;
          border: 1px solid #475569;
          border-radius: 4px;
          padding: 3px 8px;
          font-size: 0.82rem;
          min-width: 140px;
          max-width: 220px;
        }}
        #status-bar {{
          font-size: 0.78rem;
          color: #94a3b8;
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 8px;
        }}
        #highlight-badge {{
          background: rgba(234, 179, 8, 0.2);
          color: #fde047;
          border: 1px solid #ca8a04;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 0.74rem;
          display: none;
        }}
        #viewer-container {{
          flex: 1;
          overflow: auto;
          display: flex;
          justify-content: center;
          align-items: flex-start;
          padding: 16px;
          background-color: #0b0f19;
          position: relative;
        }}
        #canvas-wrapper {{
          position: relative;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
          background: white;
          border-radius: 2px;
        }}
        #the-canvas {{
          display: block;
        }}
        .textLayer {{
          position: absolute;
          left: 0;
          top: 0;
          right: 0;
          bottom: 0;
          overflow: hidden;
          opacity: 0.8;
          line-height: 1.0;
          pointer-events: auto;
        }}
        .textLayer > span {{
          color: transparent;
          position: absolute;
          white-space: pre;
          cursor: text;
          transform-origin: 0% 0%;
        }}
        .highlight {{
          background-color: rgba(255, 230, 0, 0.45) !important;
          border-bottom: 2px solid #ca8a04;
          border-radius: 2px;
          color: transparent;
        }}
        #loading-overlay {{
          position: absolute;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(15, 23, 42, 0.75);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 10px;
          z-index: 100;
          font-size: 0.9rem;
          color: #93c5fd;
        }}
        .spinner {{
          width: 32px;
          height: 32px;
          border: 3px solid rgba(147, 197, 253, 0.2);
          border-top-color: #3b82f6;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }}
        @keyframes spin {{
          to {{ transform: rotate(360deg); }}
        }}
      </style>
    </head>
    <body>
      <div id="toolbar">
        <button class="btn" id="prev-btn" title="Página anterior">◀ Ant</button>
        <span>Pág.</span>
        <input type="number" id="page-num" class="input-page" value="{initial_page}" min="1">
        <span id="page-count">/ ...</span>
        <button class="btn" id="next-btn" title="Página siguiente">Sig ▶</button>
        <div style="border-left: 1px solid #334155; height: 18px; margin: 0 4px;"></div>
        <button class="btn" id="zoom-out-btn" title="Reducir zoom">-</button>
        <span id="zoom-label" style="font-size: 0.78rem; min-width: 44px; text-align: center;">100%</span>
        <button class="btn" id="zoom-in-btn" title="Aumentar zoom">+</button>
        <button class="btn" id="zoom-fit-btn" title="Ajustar ancho">Ajustar</button>
        <div style="border-left: 1px solid #334155; height: 18px; margin: 0 4px;"></div>
        <input type="text" id="search-box" placeholder="Buscar texto en pág..." value="{safe_quote}">
        <button class="btn btn-primary" id="search-btn">🔍 Resaltar</button>
        <span id="highlight-badge">Cita resaltada</span>
        <div id="status-bar">
          <a class="btn" href="{pdf_url}#page={initial_page}" target="_blank" rel="noopener noreferrer" style="text-decoration: none;" title="Abrir en pestaña nueva con visor nativo">↗ Pestaña oficial</a>
        </div>
      </div>
      <div id="viewer-container">
        <div id="loading-overlay">
          <div class="spinner"></div>
          <div id="loading-text">Cargando PDF oficial IJF SOR (Streaming 29MB)...</div>
        </div>
        <div id="canvas-wrapper">
          <canvas id="the-canvas"></canvas>
          <div id="text-layer" class="textLayer"></div>
        </div>
      </div>

      <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        const pdfUrl = '{pdf_url}';
        let pdfDoc = null;
        let pageNum = {initial_page};
        let pageRendering = false;
        let pageNumPending = null;
        let scale = {zoom_level};
        let currentSearch = '{safe_quote}'.trim();

        const canvas = document.getElementById('the-canvas');
        const ctx = canvas.getContext('2d');
        const textLayerDiv = document.getElementById('text-layer');
        const canvasWrapper = document.getElementById('canvas-wrapper');
        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        const pageNumInput = document.getElementById('page-num');
        const pageCountSpan = document.getElementById('page-count');
        const zoomLabel = document.getElementById('zoom-label');
        const highlightBadge = document.getElementById('highlight-badge');

        function showLoading(msg) {{
          loadingText.textContent = msg || 'Cargando...';
          loadingOverlay.style.display = 'flex';
        }}

        function hideLoading() {{
          loadingOverlay.style.display = 'none';
        }}

        function updateZoomLabel() {{
          zoomLabel.textContent = Math.round(scale * 100) + '%';
        }}

        function renderPage(num) {{
          pageRendering = true;
          showLoading('Renderizando página ' + pageNum + '...');
          pageNumInput.value = pageNum;

          pdfDoc.getPage(num).then(function(page) {{
            const viewport = page.getViewport({{ scale: scale }});
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            canvasWrapper.style.width = viewport.width + 'px';
            canvasWrapper.style.height = viewport.height + 'px';

            textLayerDiv.innerHTML = '';
            textLayerDiv.style.width = viewport.width + 'px';
            textLayerDiv.style.height = viewport.height + 'px';

            const renderContext = {{
              canvasContext: ctx,
              viewport: viewport
            }};
            const renderTask = page.render(renderContext);

            renderTask.promise.then(function() {{
              return page.getTextContent();
            }}).then(function(textContent) {{
              const textLayerFrag = document.createDocumentFragment();
              pdfjsLib.renderTextLayer({{
                textContentSource: textContent,
                container: textLayerDiv,
                viewport: viewport,
                textDivs: []
              }}).promise.then(function() {{
                pageRendering = false;
                hideLoading();
                highlightText();
                if (pageNumPending !== null) {{
                  renderPage(pageNumPending);
                  pageNumPending = null;
                }}
              }});
            }}).catch(function(err) {{
              console.error('Error en render:', err);
              pageRendering = false;
              hideLoading();
            }});
          }}).catch(function(err) {{
            console.error('Error al obtener página:', err);
            pageRendering = false;
            hideLoading();
          }});

          document.getElementById('prev-btn').disabled = (num <= 1);
          document.getElementById('next-btn').disabled = (num >= pdfDoc.numPages);
        }}

        function queueRenderPage(num) {{
          if (pageRendering) {{
            pageNumPending = num;
          }} else {{
            renderPage(num);
          }}
        }}

        function goToPage(n) {{
          if (!pdfDoc) return;
          let target = parseInt(n, 10);
          if (isNaN(target)) target = 1;
          if (target < 1) target = 1;
          if (target > pdfDoc.numPages) target = pdfDoc.numPages;
          pageNum = target;
          queueRenderPage(pageNum);
        }}

        function highlightText() {{
          const query = (document.getElementById('search-box').value || '').trim();
          if (!query) {{
            highlightBadge.style.display = 'none';
            return;
          }}

          // Normalizar tokens de búsqueda ignorando puntuación
          const cleanQuery = query.toLowerCase().replace(/[-.,/#!$%^&*;:{{}}=_`~()]/g, " ").replace(/\\s+/g, " ").trim();
          const tokens = cleanQuery.split(" ").filter(t => t.length >= 3);

          if (tokens.length === 0) return;

          let matchesFound = 0;
          const spans = textLayerDiv.querySelectorAll('span');
          spans.forEach(span => {{
            const txt = (span.textContent || '').toLowerCase().replace(/[-.,/#!$%^&*;:{{}}=_`~()]/g, " ").replace(/\\s+/g, " ").trim();
            if (!txt) return;

            let isMatch = false;
            // 1. Coincidencia de subcadena exacta
            if (txt.includes(cleanQuery) || cleanQuery.includes(txt)) {{
              // Solo considerar si la coincidencia tiene una longitud sustantiva
              const overlap = Math.min(txt.length, cleanQuery.length);
              if (overlap >= 8) {{
                isMatch = true;
              }}
            }}

            // 2. Coincidencia estricta de tokens consecutivos o conjunto mayoritario (al menos 3 tokens o el 70% si son pocos)
            if (!isMatch) {{
              const hits = tokens.filter(tok => txt.includes(tok));
              const requiredHits = tokens.length <= 3 ? tokens.length : Math.max(3, Math.ceil(tokens.length * 0.6));
              if (hits.length >= requiredHits) {{
                isMatch = true;
              }}
            }}

            if (isMatch) {{
              span.classList.add('highlight');
              matchesFound++;
            }}
          }});

          if (matchesFound > 0) {{
            highlightBadge.style.display = 'inline-block';
            highlightBadge.textContent = '✓ ' + matchesFound + ' fragmento(s) resaltado(s)';
            const firstMatch = textLayerDiv.querySelector('.highlight');
            if (firstMatch) {{
              firstMatch.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
          }} else {{
            highlightBadge.style.display = 'none';
          }}
        }}

        // Listeners de controles
        document.getElementById('prev-btn').addEventListener('click', function() {{
          if (pageNum <= 1) return;
          pageNum--;
          queueRenderPage(pageNum);
        }});

        document.getElementById('next-btn').addEventListener('click', function() {{
          if (!pdfDoc || pageNum >= pdfDoc.numPages) return;
          pageNum++;
          queueRenderPage(pageNum);
        }});

        pageNumInput.addEventListener('change', function() {{
          goToPage(this.value);
        }});

        pageNumInput.addEventListener('keydown', function(e) {{
          if (e.key === 'Enter') {{
            goToPage(this.value);
          }}
        }});

        document.getElementById('zoom-in-btn').addEventListener('click', function() {{
          scale = Math.min(3.0, scale + 0.15);
          updateZoomLabel();
          queueRenderPage(pageNum);
        }});

        document.getElementById('zoom-out-btn').addEventListener('click', function() {{
          scale = Math.max(0.5, scale - 0.15);
          updateZoomLabel();
          queueRenderPage(pageNum);
        }});

        document.getElementById('zoom-fit-btn').addEventListener('click', function() {{
          const containerWidth = document.getElementById('viewer-container').clientWidth - 40;
          if (pdfDoc && containerWidth > 200) {{
            pdfDoc.getPage(pageNum).then(function(page) {{
              const baseViewport = page.getViewport({{ scale: 1.0 }});
              scale = containerWidth / baseViewport.width;
              updateZoomLabel();
              queueRenderPage(pageNum);
            }});
          }}
        }});

        document.getElementById('search-btn').addEventListener('click', function() {{
          highlightText();
        }});

        document.getElementById('search-box').addEventListener('keydown', function(e) {{
          if (e.key === 'Enter') {{
            highlightText();
          }}
        }});

        // Carga inicial del documento: usar datos base64 locales de la página o streaming de URL
        const rawB64 = '{page_b64}';
        let loadSource = null;
        if (rawB64 && rawB64.length > 50) {{
          try {{
            const binaryString = window.atob(rawB64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {{
              bytes[i] = binaryString.charCodeAt(i);
            }}
            loadSource = {{
              data: bytes,
              cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
              cMapPacked: true
            }};
          }} catch(e) {{
            console.error('Error decodificando base64:', e);
          }}
        }}

        if (!loadSource) {{
          loadSource = {{
            url: pdfUrl,
            cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
            cMapPacked: true,
            enableXfa: true,
            disableAutoFetch: true,
            disableStream: false
          }};
        }}

        const loadingTask = pdfjsLib.getDocument(loadSource);

        loadingTask.promise.then(function(pdf) {{
          pdfDoc = pdf;
          pageCountSpan.textContent = '/ 298';
          updateZoomLabel();
          // Si estamos usando un PDF de una sola página extraída, renderizamos página 1 internamente
          const targetInternalPage = (pdfDoc.numPages === 1) ? 1 : pageNum;
          renderPage(targetInternalPage);
        }}).catch(function(error) {{
          console.error('Error al cargar documento PDF:', error);
          loadingText.innerHTML = '⚠️ Error al cargar PDF en el visor interactivo.<br><a href="' + pdfUrl + '#page=' + pageNum + '" target="_blank" style="color: #60a5fa; text-decoration: underline;">Haga clic aquí para abrirlo directamente en nueva pestaña</a>';
        }});
      </script>
    </body>
    </html>
    """
    components.html(viewer_html, height=height, scrolling=False)


# Session state for internationalization and LLM provider configuration
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "es"
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = os.environ.get("LLM_PROVIDER", "Gemini").capitalize()
if "fallback_policy" not in st.session_state:
    st.session_state.fallback_policy = "Automatic"
if "gemini_model" not in st.session_state:
    st.session_state.gemini_model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
if "groq_model" not in st.session_state:
    st.session_state.groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

@st.cache_resource
def get_llm_manager(provider, fallback, g_model, q_model):
    fb_code = "automatic" if fallback in ("Automatic", "Automático") else "manual"
    return MultiProviderLLMManager(
        primary_provider=provider,
        fallback_policy=fb_code,
        gemini_model=g_model,
        groq_model=q_model
    )

llm_manager = get_llm_manager(
    st.session_state.llm_provider,
    st.session_state.fallback_policy,
    st.session_state.gemini_model,
    st.session_state.groq_model
)

@st.cache_resource
def get_rag_engine():
    brain_path = os.path.dirname(os.path.abspath(__file__))
    return RagEngine(brain_path, llm_manager=llm_manager)

try:
    engine = get_rag_engine()
    # Ensure current session LLM manager is injected
    engine.llm_manager = llm_manager
    if engine.is_2026_08 and engine.ada:
        engine.ada.llm_manager = llm_manager
    kg_metrics = engine.kg.get_metrics()
except Exception as e:
    st.error(f"Error initializing RAG Engine: {e}")
    st.stop()

provider_status = llm_manager.get_provider_status()
active_prov_info = provider_status["providers"].get(st.session_state.llm_provider, {})
is_connected = active_prov_info.get("available", False)

if "history" not in st.session_state:
    st.session_state.history = []
if "active_index" not in st.session_state:
    st.session_state.active_index = -1
if "query_to_run" not in st.session_state:
    st.session_state.query_to_run = None
if "pdf_page" not in st.session_state:
    st.session_state.pdf_page = 1
if "pdf_quote" not in st.session_state:
    st.session_state.pdf_quote = ""
if "pdf_article" not in st.session_state:
    st.session_state.pdf_article = ""
if "pdf_visible" not in st.session_state:
    st.session_state.pdf_visible = True
if "pdf_zoom" not in st.session_state:
    st.session_state.pdf_zoom = 1.0

preguntas_ejemplo = [
    "Elige una pregunta para consultar...",
    "¿Se permite la defensa con la cabeza?",
    "¿Cuáles son las dimensiones del tatami?",
    "¿Cuántas intervenciones médicas se permiten por combate?",
    "¿Qué es la tecnología Smart Judogi con chip NFC?",
    "¿Cómo se sanciona el abrazo de oso (bear hug)?",
    "¿Cómo se sanciona el reverse seoi-nage en cadetes?",
    "¿Qué sucede si un competidor se desmaya por estrangulación (shime-waza)?",
    "¿Qué es el Sokuteiki y cómo se usa?",
    "¿Cuáles son las reglas de color de Judogi (blanco y azul)?",
    "¿Cómo funciona el protocolo de conmoción cerebral (head trauma) y cuántos días de inhabilitación genera?",
    "¿Cuál es el tiempo de tolerancia para presentarse en el tatami antes de la descalificación?",
    "¿Cuáles son las diferencias de tolerancia de peso entre el pesaje oficial y el pesaje aleatorio?",
    "¿Cómo se dividen las llaves de competencia con repechaje en el sistema oficial?",
    "¿Cuál es el código de vestimenta oficial para los médicos de los equipos?",
    "¿Está permitido el uso de vendajes (taping) en los dedos y cómo debe ser aprobado?"
]

def load_example():
    sel = st.session_state.get("example_select_widget")
    if sel and sel != "Elige una pregunta para consultar...":
        st.session_state.query_to_run = sel

# Sidebar
with st.sidebar:
    # Language Selection Widget (Español | English, Spanish as Default)
    lang_options = [("Español", "es"), ("English", "en")]
    cur_lang_idx = 0 if st.session_state.ui_lang == "es" else 1
    selected_lang_tuple = st.selectbox(
        t("lang_selector_label", st.session_state.ui_lang),
        options=lang_options,
        index=cur_lang_idx,
        format_func=lambda x: x[0],
        help="Selecciona el idioma de la interfaz / Select user interface language."
    )
    if selected_lang_tuple[1] != st.session_state.ui_lang:
        st.session_state.ui_lang = selected_lang_tuple[1]
        st.rerun()

    lang = st.session_state.ui_lang

    st.markdown(f"**{t('sidebar_info_title', lang)}**")

    with st.expander(t("sidebar_project_title", lang), expanded=False):
        st.markdown(t("sidebar_project_content", lang))

    with st.expander(t("sidebar_purpose_title", lang), expanded=False):
        st.markdown(t("sidebar_purpose_content", lang))

    with st.expander(t("sidebar_sources_title", lang), expanded=False):
        st.markdown(t("sidebar_sources_content", lang))

    with st.expander(t("sidebar_author_title", lang), expanded=False):
        st.markdown(t("sidebar_author_content", lang))

    with st.expander(t("sidebar_version_title", lang), expanded=False):
        st.markdown(f"""
**IJF SOR Assistant**

{t("sidebar_version_label", lang)}

{t("sidebar_based_on", lang)} **{engine.config['version_label']}**

{t("sidebar_source_hash", lang)} `{engine.config['source_sha256'][:16]}...`
        """)

    st.write("---")
    st.markdown(f"**{t('edition_title', lang)}**")
    st.info(t("edition_info", lang, version_label=engine.config['version_label']))

    st.write("---")
    st.markdown(f"**{t('model_config_title', lang)}**")

    prov_options = ["Gemini", "Groq"]
    cur_prov_idx = prov_options.index(st.session_state.llm_provider) if st.session_state.llm_provider in prov_options else 0
    selected_prov = st.selectbox(
        t("primary_provider_label", lang),
        prov_options,
        index=cur_prov_idx,
        help=t("primary_provider_help", lang)
    )
    if selected_prov != st.session_state.llm_provider:
        st.session_state.llm_provider = selected_prov
        st.rerun()

    models_available = MultiProviderLLMManager.SUPPORTED_PROVIDERS[selected_prov]["models"]
    cur_model = st.session_state.gemini_model if selected_prov == "Gemini" else st.session_state.groq_model
    cur_model_idx = models_available.index(cur_model) if cur_model in models_available else 0
    selected_model = st.selectbox(
        t("model_label", lang, provider=selected_prov),
        models_available,
        index=cur_model_idx,
        help=t("model_help", lang, provider=selected_prov)
    )
    if selected_prov == "Gemini" and selected_model != st.session_state.gemini_model:
        st.session_state.gemini_model = selected_model
        st.rerun()
    elif selected_prov == "Groq" and selected_model != st.session_state.groq_model:
        st.session_state.groq_model = selected_model
        st.rerun()

    fb_options = [t("fallback_opt_auto", lang), t("fallback_opt_manual", lang)]
    cur_fb_idx = 0 if st.session_state.fallback_policy in ("Automatic", "Automático") else 1
    selected_fb = st.selectbox(
        t("fallback_policy_label", lang),
        fb_options,
        index=cur_fb_idx,
        help=t("fallback_policy_help", lang)
    )
    canonical_fb = "Automatic" if selected_fb in ("Automatic", "Automático") else "Manual"
    if canonical_fb != st.session_state.fallback_policy:
        st.session_state.fallback_policy = canonical_fb
        st.rerun()

    # Status of keys and provider availability
    p_info = provider_status["providers"].get(selected_prov, {})
    if p_info.get("available"):
        st.caption(t("key_active", lang, provider=selected_prov, masked_key=p_info.get('masked_key')))
    else:
        env_var_name = MultiProviderLLMManager.SUPPORTED_PROVIDERS[selected_prov]["env_key"]
        st.caption(t("key_missing", lang, env_var=env_var_name))

    st.write("---")
    st.markdown(f"**{t('search_settings_title', lang)}**")
    k_param = st.slider(
        t("k_slider_label", lang),
        1, 5, 3,
        help=t("k_slider_help", lang)
    )
    min_score_param = st.slider(
        t("min_score_label", lang),
        0.05, 0.50, 0.10, 0.05,
        help=t("min_score_help", lang)
    )

    st.write("---")
    st.markdown(f"**{t('quick_suggestions_title', lang)}**")
    example_list = t("example_queries", lang)
    st.selectbox(
        t("example_select_placeholder", lang),
        example_list,
        key="example_select_widget",
        on_change=load_example,
        label_visibility="collapsed",
        help=t("example_select_help", lang)
    )

    if len(st.session_state.history) > 0:
        st.write("---")
        st.markdown(f"**{t('history_title', lang)}**")
        options = [f"#{i+1}: {item['query'][:15]}..." for i, item in enumerate(st.session_state.history)]
        selected_option = st.selectbox(
            t("history_select_label", lang),
            options,
            index=st.session_state.active_index,
            help=t("history_select_help", lang)
        )
        new_active = options.index(selected_option)
        if new_active != st.session_state.active_index:
            st.session_state.active_index = new_active
            st.rerun()

    st.write("---")
    st.markdown(f"### {t('kg_title', lang)}")
    if is_connected:
        st.markdown(f'<span class="status-badge-connected">{t("badge_connected", lang, provider=st.session_state.llm_provider)}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-badge-offline">{t("badge_offline", lang)}</span>', unsafe_allow_html=True)

    st.markdown(f"**{t('kg_modules_title', lang)}**")
    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.metric(t("kg_total_kuns", lang), kg_metrics['nodes_count'])
    with mcol2:
        st.metric(t("kg_relations", lang), kg_metrics['edges_count'])
    st.metric(t("kg_avg_degree", lang), f"{kg_metrics['avg_degree']:.2f}")

    st.markdown(f"**{t('kg_hubs_title', lang)}**")
    for node, deg in kg_metrics['hubs'][:2]:
        st.markdown(f"- `{node}` ({deg} {t('kg_links_suffix', lang)})", unsafe_allow_html=True)



# Header
base64_logo = get_base64_logo(logo_path)
if base64_logo:
    st.markdown(f"""
    <style>
    .ijf-tooltip {{
        position: relative;
        display: inline-flex;
        align-items: center;
        cursor: default;
    }}
    .ijf-tooltip .ijf-tooltiptext {{
        visibility: hidden;
        background-color: #1e293b;
        color: #e2e8f0;
        text-align: left;
        padding: 0.5rem 0.8rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-family: 'Inter', sans-serif;
        white-space: nowrap;
        position: absolute;
        z-index: 999;
        top: 130%;
        left: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    .ijf-tooltip:hover .ijf-tooltiptext {{
        visibility: visible;
    }}
    .ijf-help-icon {{
        width: 16px; height: 16px;
        background: rgba(29,78,216,0.15);
        border: 1px solid #1d4ed8;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.65rem;
        color: #1d4ed8;
        font-weight: 700;
        margin-left: 0.5rem;
        font-family: 'Inter', sans-serif;
        flex-shrink: 0;
    }}
    </style>
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: var(--secondary-background-color); border-bottom: 2px solid #1d4ed8; padding: 1.5rem 1rem; margin-top: 1.2rem; margin-bottom: 1.2rem; width: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-radius: 6px; position: relative; z-index: 99; text-align: center; gap: 0.8rem;">
        <div style="display: flex; align-items: center; justify-content: center;">
            <img src="data:image/svg+xml;base64,{base64_logo}" style="width: 80px; height: 80px; object-fit: contain; display: block;" />
        </div>
        <div style="position: relative; display: inline-block;">
            <h2 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 2.8rem; margin: 0; font-weight: 700; line-height: 1.1;">{t('app_title', lang)}</h2>
            <div class="ijf-tooltip" style="position: absolute; right: -28px; top: 50%; transform: translateY(-50%);">
                <div class="ijf-help-icon" style="margin-left: 0;">?</div>
                <div class="ijf-tooltiptext" style="left: 50%; transform: translateX(-50%); top: 130%;">{t('header_tooltip', lang)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: var(--secondary-background-color); border-bottom: 2px solid #1d4ed8; padding: 1.5rem 1rem; margin-top: 1.2rem; margin-bottom: 1.2rem; width: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-radius: 6px; text-align: center;">
        <h2 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 2.8rem; margin: 0; font-weight: 700; line-height: 1.1;">{t('app_title', lang)}</h2>
    </div>
    """, unsafe_allow_html=True)

# Handle user input
query_to_run = None

# Check if a suggestion card was clicked
if st.session_state.get("query_to_run"):
    query_to_run = st.session_state.pop("query_to_run")

# Chat input for manual queries
with st.container():
    with st.form(key="chat_form", clear_on_submit=True, border=False):
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            user_input = st.text_input("Query input", placeholder=t("chat_input_placeholder", lang), label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button(t("send_btn", lang), use_container_width=True)

        if submit_button and user_input:
            query_to_run = user_input.strip()


if query_to_run:
    with st.status(t("status_querying", lang), expanded=True) as status:
        rre_mode = getattr(engine.rre, 'operating_mode', 'HYBRID')
        if rre_mode == "HYBRID":
            status.write(t("status_rre_hybrid", lang))
        else:
            status.write(t("status_rre_degraded", lang, reason=getattr(engine.rre, 'degradation_reason', 'Model unavailable')))

        res = engine.query(query_to_run, k=k_param, min_score=min_score_param, language=lang)
        retrieved_kuns = res.get('retrieved_kuns_data', [])
        if res.get("source_sha256_verified", False):
            status.write(t("status_sha_verified", lang))
        else:
            status.write(t("status_sha_unverified", lang))
        status.write(t("status_ada_analyzing", lang, count=len(retrieved_kuns)))
        if is_connected:
            status.write(t("status_llm_synthesizing", lang))
        else:
            status.write(t("status_local_compiling", lang))

        dot_code = "digraph {\n  rankdir=LR;\n  node [shape=box, style=filled, fontname=\"Arial\", fontsize=10];\n"
        retrieved_ids = {k['id_conocimiento'] for k in retrieved_kuns}
        for kun in retrieved_kuns:
            color = "#3B82F6" if kun['tipo'] == 'REG' else "#EF4444" if kun['tipo'] == 'PEN' else "#10B981"
            dot_code += f'  "{kun["id_conocimiento"]}" [fillcolor="{color}", fontcolor="white", label="{kun["id_conocimiento"]}\\n{kun["tipo"]}"];\n'
        for kun in retrieved_kuns:
            node_id = kun['id_conocimiento']
            if node_id in engine.kg.edges:
                for edge in engine.kg.edges[node_id]:
                    dest_id = edge['id_destino']
                    if dest_id in retrieved_ids:
                        dot_code += f'  "{node_id}" -> "{dest_id}" [label="{edge["tipo_relacion"]}", fontsize=8];\n'
        dot_code += "}"

        st.session_state.history.append({
            "query": query_to_run,
            "answer": res['answer'],
            "structured_answer": res.get('structured_answer'),
            "trazabilidad": retrieved_kuns,
            "dot_code": dot_code,
            "llm_meta": res.get("llm_meta", {}),
            "rre_operating_mode": res.get("rre_operating_mode", getattr(engine.rre, "operating_mode", "UNKNOWN")),
            "degradation_reason": res.get("degradation_reason"),
            "source_sha256_verified": res.get("source_sha256_verified", False)
        })
        st.session_state.active_index = len(st.session_state.history) - 1
        status.update(label=t("status_done", lang), state="complete", expanded=False)

if st.session_state.active_index >= 0:
    history_to_show = st.session_state.history[:st.session_state.active_index + 1]

    st.write("---")

    # Layout Dividido: Chat interactivo (izquierda) + Visor PDF Oficial (derecha)
    official_pdf_url = "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf"

    # Barra de control de layout (toggle para expandir/ocultar visor)
    col_t1, col_t2 = st.columns([0.7, 0.3])
    with col_t2:
        vis_label = t("btn_hide_pdf", lang) if st.session_state.pdf_visible else t("btn_show_pdf", lang)
        if st.button(vis_label, key="toggle_pdf_btn", use_container_width=True):
            st.session_state.pdf_visible = not st.session_state.pdf_visible
            st.rerun()

    if st.session_state.pdf_visible:
        col_chat, col_viewer = st.columns([0.52, 0.48], gap="medium")
    else:
        col_chat = st.container()
        col_viewer = None

    with col_chat:
        for original_i, item in reversed(list(enumerate(history_to_show))):
            with st.chat_message("user", avatar="👤"):
                st.markdown(item['query'])
            with st.chat_message("assistant", avatar="⚖️"):
                # Inform user if automatic fallback was triggered and succeeded
                item_llm_meta = item.get("llm_meta", {})
                succ_prov = item_llm_meta.get("successful_provider")
                prim_prov = item_llm_meta.get("primary_provider", "")

                if item_llm_meta.get("fallback_triggered") and succ_prov:
                    st.caption(t("fallback_badge_notice", lang, primary=prim_prov, secondary=succ_prov))
                elif item_llm_meta.get("fallback_attempted") and not succ_prov:
                    st.caption(t("fallback_all_failed_notice", lang))

                mode = item.get("rre_operating_mode", "UNKNOWN")
                st.caption(t("rre_mode_caption", lang, mode=mode) + (f" — {item.get('degradation_reason')}" if item.get("degradation_reason") else ""))
                if item.get("source_sha256_verified", False):
                    st.caption(t("pdf_source_caption", lang))
                else:
                    st.caption(t("pdf_source_unverified_caption", lang))

                # Two-tier UI presentation contract: La síntesis directa es la respuesta principal destacada
                struct = item.get("structured_answer")
                citations_list = []
                if struct and isinstance(struct, dict):
                    citations_list = struct.get("citations", [])

                if struct and isinstance(struct, dict) and struct.get("summary"):
                    summary_text = struct["summary"].strip()
                    # Eliminar cualquier prefijo o encabezado accidental que pueda preceder a la conclusión
                    summary_text = re.sub(
                        r'^(?:⚖️\s*\*\*Síntesis Analítica IA.*?\*\*\s*|📋\s*\*\*Resumen de Evidencias.*?\*\*\s*|⚖️\s*\*\*AI Analytical Synthesis.*?\*\*\s*|📋\s*\*\*Normative Evidence Summary.*?\*\*\s*)',
                        '',
                        summary_text,
                        flags=re.IGNORECASE
                    ).strip()

                    # Nivel 1: Respuesta directa destacada en bloque visual visible inmediatamente
                    box_title = t("tier1_box_header", lang)
                    st.markdown(
                        f"""<div style="background-color: rgba(59, 130, 246, 0.08); border-left: 4px solid #2563eb; padding: 12px 16px; border-radius: 4px; margin-bottom: 12px; font-size: 1.05rem; line-height: 1.5;">
                        <strong>{box_title}</strong><br>{summary_text}
                        </div>""",
                        unsafe_allow_html=True
                    )

                    # Píldoras Interactivas de Citas Normativas (en Nivel 1)
                    if citations_list:
                        cit_title = t("citations_title_label", lang)
                        st.markdown(f'<div class="citation-title-label">{cit_title}</div>', unsafe_allow_html=True)
                        pill_cols = st.columns(min(len(citations_list), 4))
                        for c_idx, cite in enumerate(citations_list):
                            col_p = pill_cols[c_idx % len(pill_cols)]
                            with col_p:
                                if isinstance(cite, dict):
                                    art_label = cite.get("article_id") or cite.get("title") or "Cita"
                                    page_num = cite.get("page_number")
                                    exact_q = cite.get("exact_quote", "")
                                    p_label = "Page" if lang == "en" else "Pág."
                                    btn_text = f"📍 {art_label} | {p_label} {page_num}" if page_num else f"📍 {art_label}"
                                    tooltip = f"{cite.get('text_snippet', '')}"
                                    if st.button(btn_text, key=f"pill_{original_i}_{c_idx}", help=tooltip, use_container_width=True):
                                        if page_num:
                                            st.session_state.pdf_page = int(page_num)
                                        if exact_q:
                                            st.session_state.pdf_quote = exact_q
                                        st.session_state.pdf_article = str(art_label)
                                        st.session_state.pdf_visible = True
                                        st.rerun()
                                else:
                                    st.button(f"📍 {cite}", key=f"pill_{original_i}_{c_idx}", use_container_width=True)

                    # Si el validador detectó inconsistencias normativas o límites probatorios, avisar visiblemente en Nivel 1
                    if "Control de Rigor Normativo" in str(struct.get("limitations", "")) or "Normative Rigor Control" in str(struct.get("limitations", "")):
                        st.warning(t("normative_rigor_warning", lang))

                    # Nivel 2: Fundamentación completa inicialmente contraída
                    has_details = bool(
                        struct.get("normative_basis") or
                        struct.get("conditions_and_exceptions") or
                        struct.get("extended_analysis") or
                        struct.get("limitations")
                    )
                    if has_details:
                        with st.expander(t("view_details_expander", lang), expanded=False):
                            if struct.get("normative_basis"):
                                st.markdown(f"#### {t('sec_normative_basis', lang)}")
                                st.markdown(struct["normative_basis"])
                            if struct.get("conditions_and_exceptions"):
                                st.markdown(f"#### {t('sec_conditions', lang)}")
                                st.markdown(struct["conditions_and_exceptions"])
                            if struct.get("extended_analysis"):
                                st.markdown(f"#### {t('sec_extended', lang)}")
                                st.markdown(struct["extended_analysis"])
                            if struct.get("limitations"):
                                st.markdown(f"#### {t('sec_limitations', lang)}")
                                st.markdown(struct["limitations"])
                else:
                    # Backward compatibility for legacy flat text entries: extraer respuesta directa sin título redundante
                    raw_ans = item['answer']
                    clean_raw = re.sub(
                        r'^(?:⚖️\s*\*\*Síntesis Analítica IA.*?\*\*\s*|📋\s*\*\*Resumen de Evidencias.*?\*\*\s*|⚖️\s*\*\*AI Analytical Synthesis.*?\*\*\s*|📋\s*\*\*Normative Evidence Summary.*?\*\*\s*)',
                        '',
                        raw_ans,
                        flags=re.IGNORECASE
                    ).strip()
                    box_title = t("tier1_box_header", lang)
                    if "\n\n---\n\n" in clean_raw:
                        parts = clean_raw.split("\n\n---\n\n", 1)
                        st.markdown(
                            f"""<div style="background-color: rgba(59, 130, 246, 0.08); border-left: 4px solid #2563eb; padding: 12px 16px; border-radius: 4px; margin-bottom: 12px; font-size: 1.05rem; line-height: 1.5;">
                            <strong>{box_title}</strong><br>{parts[0]}
                            </div>""",
                            unsafe_allow_html=True
                        )
                        with st.expander(t("view_details_expander", lang), expanded=False):
                            st.markdown(parts[1])
                    else:
                        st.markdown(
                            f"""<div style="background-color: rgba(59, 130, 246, 0.08); border-left: 4px solid #2563eb; padding: 12px 16px; border-radius: 4px; margin-bottom: 12px; font-size: 1.05rem; line-height: 1.5;">
                            <strong>{box_title}</strong><br>{clean_raw}
                            </div>""",
                            unsafe_allow_html=True
                        )

                is_fallback = "lo siento" in item['answer'].lower() or "sorry" in item['answer'].lower()
                if not is_fallback and item.get('trazabilidad'):
                    with st.expander(t("expander_traceability", lang), expanded=False):
                        tab_cite, tab_graph = st.tabs([t("tab_traceability", lang), t("tab_graph", lang)])

                        with tab_cite:
                            with st.expander(t("sidebar_sources_title", lang), expanded=False):
                                st.markdown(t("source_availability_notice", lang), unsafe_allow_html=True)

                            for kun in item['trazabilidad']:
                                res = _rrm_manager.resolve_reference(kun['id_conocimiento'], kun)
                                url = res.get("url")
                                is_clickable = res.get("is_clickable", True)
                                op_status = res.get("operational_status", "AVAILABLE")

                                source_id = kun['fuente_origen']
                                ref_spec = kun.get('referencia_especifica', 'Rules')
                                name = RESOURCE_DETAILS[source_id]["name"] if source_id in RESOURCE_DETAILS else "Official Source"

                                if is_clickable and url:
                                    source_link = f"[{name} ({ref_spec})]({url})"
                                elif op_status == "DELETED":
                                    source_link = f"~~{name} ({ref_spec})~~"
                                else:
                                    source_link = f"{name} ({ref_spec})"

                                badge_emoji = "🟢"
                                if op_status == "MIGRATED":
                                    badge_emoji = "🟡"
                                elif op_status == "FALLBACK_GENERAL":
                                    badge_emoji = "🔵"
                                elif op_status == "DELETED":
                                    badge_emoji = "🔴"

                                st.markdown(f"**{kun['id_conocimiento']}: {kun['titulo']}** &nbsp; {badge_emoji} *{res.get('ux_message', '')}*")
                                st.markdown(f"* **{t('source_label', lang)}** {source_link}")
                                st.write(f"* {t('original_text_label', lang)} *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                                st.write(f"* {t('interpretation_label', lang)} {kun['interpretacion']}")
                                st.write("---")

                        with tab_graph:
                            if item.get('dot_code'):
                                st.graphviz_chart(item['dot_code'])
                            else:
                                st.info(t("no_graph_msg", lang))
                elif not is_fallback:
                    with st.expander(t("expander_traceability", lang), expanded=False):
                        st.info(t("no_traceability_msg", lang))

                # Friendly feedback observation channel
                with st.expander(t("feedback_expander", lang), expanded=False):
                    st.caption(t("feedback_caption", lang))
                    with st.form(key=f"feedback_form_{original_i}", clear_on_submit=True):
                        motivo_sel = st.selectbox(
                            t("feedback_reason_label", lang),
                            MOTIVOS_VALIDOS,
                            key=f"feedback_motivo_{original_i}",
                            label_visibility="collapsed"
                        )
                        comentario_user = st.text_area(
                            t("feedback_comment_label", lang),
                            placeholder=t("feedback_comment_placeholder", lang),
                            height=80,
                            key=f"feedback_comment_{original_i}"
                        )
                        submit_obs = st.form_submit_button(t("feedback_submit_btn", lang), use_container_width=True)

                        if submit_obs:
                            res_obs = record_observation(
                                motivo=motivo_sel,
                                comentario=comentario_user,
                                query=item.get("query"),
                                response_summary=summary_text if (struct and isinstance(struct, dict) and struct.get("summary")) else item.get("answer"),
                                citations=citations_list,
                                edition="2026-08 (Official)" if engine.is_2026_08 else "2026-01 (Historical)"
                            )
                            if res_obs.get("success"):
                                st.success(t("feedback_success", lang, message=res_obs.get('message'), obs_id=res_obs.get('observation_id')))
                            else:
                                st.error(t("feedback_error", lang, message=res_obs.get('message')))

    # Panel Derecho: Visor interactivo PDF con PDF.js streaming
    if col_viewer is not None:
        with col_viewer:
            active_art = st.session_state.pdf_article or "SOR 2026"
            active_p = st.session_state.pdf_page
            viewer_title = t("pdf_viewer_title", lang, article=active_art, page=active_p)
            badge_label = t("pdf_edition_badge", lang)
            st.markdown(
                f"""<div class="pdf-viewer-header">
                <span>{viewer_title}</span>
                <span style="font-size: 0.78rem; opacity: 0.9;">{badge_label}</span>
                </div>""",
                unsafe_allow_html=True
            )
            page_b64_data = get_pdf_page_base64(st.session_state.pdf_page)
            render_pdf_viewer(
                pdf_url=official_pdf_url,
                initial_page=st.session_state.pdf_page,
                search_quote=st.session_state.pdf_quote,
                zoom_level=st.session_state.pdf_zoom,
                height=840,
                page_b64=page_b64_data
            )
else:
    st.markdown(f"""
    <div style="text-align: center; margin-top: 1.6rem; margin-bottom: 1.2rem;">
        <h1 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 2.05rem; font-weight: 700; line-height: 1.05; margin-bottom: 0.4rem; max-width: 28rem; margin-left: auto; margin-right: auto;">{t('welcome_title', lang)}</h1>
        <p style="font-size: 0.85rem; color: rgba(212, 175, 55, 0.45); max-width: 640px; margin: 0 auto; line-height: 1.45; margin-bottom: 1rem; font-weight: 400;">{t('app_subtitle', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""<div style=\"font-size: 0.8rem; font-weight: 500; text-align: center; margin-bottom: 0.6rem; margin-top: 1.5rem; color: #94a3b8; letter-spacing: 0.04em;\">{t('sample_queries_prompt', lang)}</div>""", unsafe_allow_html=True)

    suggestion_chips = t("chips", lang)
    chip_cols = st.columns(len(suggestion_chips))
    for i, (label, full_query) in enumerate(suggestion_chips):
        with chip_cols[i]:
            if st.button(label, key=f"chip_{i}", help=full_query):
                st.session_state.query_to_run = full_query
                st.rerun()

st.write("---")
with st.expander(t("scope_expander_title", lang)):
    st.markdown(t("scope_certified_kuns", lang, count=kg_metrics['nodes_count']))
    col_cov, col_uncov = st.columns(2)
    with col_cov:
        st.markdown(f"{t('scope_covered_title', lang)}\n{t('scope_covered_body', lang)}")
    with col_uncov:
        st.markdown(f"{t('scope_uncovered_title', lang)}\n{t('scope_uncovered_body', lang)}")
