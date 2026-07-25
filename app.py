import streamlit as st
import os
import sys
import base64

from dotenv import load_dotenv

if os.path.exists('.env'):
    load_dotenv()

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from rag_engine import RagEngine
from citation_resolver import RESOURCE_DETAILS, resolve_url, _rrm_manager

logo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
logo_path = os.path.join(logo_dir, 'logo.svg')
if not os.path.exists(logo_path):
    try:
        os.makedirs(logo_dir, exist_ok=True)
        import urllib.request
        req = urllib.request.Request(
            'https://upload.wikimedia.org/wikipedia/fr/7/70/International_Judo_Federation_logo.svg',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            with open(logo_path, 'wb') as f:
                f.write(response.read())
    except Exception:
        pass

st.set_page_config(
    page_title="Asistente del SOR de la FIJ",
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
    .kun-card {
        border-left: 3px solid #3B82F6;
        background-color: #F9FAFB;
        padding: 0.6rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
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
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
    }
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

@st.cache_resource
def get_rag_engine():
    brain_path = os.path.dirname(os.path.abspath(__file__))
    return RagEngine(brain_path)

try:
    engine = get_rag_engine()
    kg_metrics = engine.kg.get_metrics()
except Exception as e:
    st.error(f"Error initializing RAG Engine: {e}")
    st.stop()

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
is_connected = api_key is not None

if "history" not in st.session_state:
    st.session_state.history = []
if "active_index" not in st.session_state:
    st.session_state.active_index = -1
if "query_to_run" not in st.session_state:
    st.session_state.query_to_run = None

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
    st.markdown("### 🥋 Gobernanza del Grafo")
    if is_connected:
        st.markdown('<span class="status-badge-connected">🟢 Modo Conectado (Gemini)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-offline">🟡 Modo Offline (Simulado)</span>', unsafe_allow_html=True)
        
    st.write("---")
    
    st.markdown("**📈 Módulos de Conocimiento**")
    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.metric("Total KUNs", kg_metrics['nodes_count'])
    with mcol2:
        st.metric("Relaciones", kg_metrics['edges_count'])
    st.metric("Grado Promedio", f"{kg_metrics['avg_degree']:.2f}")
    
    st.write("---")
    st.markdown("**🧭 Ajustes de Búsqueda**")
    k_param = st.slider("Cantidad de Reglas a Consultar", 1, 5, 3)
    min_score_param = st.slider("Filtro Anti-Distracciones", 0.05, 0.50, 0.10, 0.05)
    
    st.write("---")
    st.markdown("**🕸️ Nodos Hub**")
    for node, deg in kg_metrics['hubs'][:2]:
        st.markdown(f"- `{node}` ({deg} enlaces)", unsafe_allow_html=True)

    st.write("---")
    st.markdown("**💡 Sugerencias Rápidas**")
    st.selectbox(
        "Selecciona una pregunta ejemplo:",
        preguntas_ejemplo,
        key="example_select_widget",
        on_change=load_example,
        label_visibility="collapsed"
    )

    if len(st.session_state.history) > 0:
        st.write("---")
        st.markdown("**📚 Historial**")
        options = [f"#{i+1}: {item['query'][:15]}..." for i, item in enumerate(st.session_state.history)]
        selected_option = st.selectbox("Revisar consulta:", options, index=st.session_state.active_index)
        new_active = options.index(selected_option)
        if new_active != st.session_state.active_index:
            st.session_state.active_index = new_active
            st.rerun()

# Header
base64_logo = get_base64_logo(logo_path)
if base64_logo:
    st.markdown(f"""
    <div style="display: flex; align-items: center; background-color: var(--secondary-background-color); border-bottom: 2px solid #1d4ed8; padding: 0.8rem 1.2rem 0.8rem 4.5rem; margin-top: 1.2rem; margin-bottom: 1.2rem; width: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-radius: 6px; position: relative; z-index: 99; pointer-events: none;">
        <div style="flex-shrink: 0; display: flex; align-items: center; margin-right: 1.5rem; pointer-events: auto;">
            <img src="data:image/svg+xml;base64,{base64_logo}" style="width: 60px; height: 60px; object-fit: contain; display: block;" />
        </div>
        <div style="flex-grow: 1; display: flex; align-items: center; gap: 1.2rem; flex-wrap: wrap; pointer-events: auto;">
            <h2 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 1.7rem; margin: 0; font-weight: 700; line-height: 1.1;">Asistente del SOR de la FIJ</h2>
            <span style="font-family: 'Inter', sans-serif; color: var(--text-color); opacity: 0.85; font-size: 1.0rem; margin: 0; line-height: 1.1;">Reglamento de la Federación Internacional de Judo (SOR 2026)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="display: flex; align-items: center; background-color: var(--secondary-background-color); border-bottom: 2px solid #1d4ed8; padding: 0.8rem 1.2rem 0.8rem 4.5rem; margin-top: 1.2rem; margin-bottom: 1.2rem; width: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-radius: 6px;">
        <h2 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 1.7rem; margin: 0; font-weight: 700; line-height: 1.1;">Asistente del SOR de la FIJ</h2>
        <span style="font-family: 'Inter', sans-serif; color: var(--text-color); opacity: 0.85; font-size: 1.0rem; margin-left: 1.2rem; line-height: 1.1;">Reglamento de la Federación Internacional de Judo (SOR 2026)</span>
    </div>
    """, unsafe_allow_html=True)

query_to_run = None
user_input = st.chat_input("Escribe tu consulta sobre el reglamento de la FIJ...")

if user_input:
    query_to_run = user_input.strip()
elif st.session_state.query_to_run:
    query_to_run = st.session_state.query_to_run
    st.session_state.query_to_run = None

if query_to_run:
    with st.spinner("Buscando en la base de datos..."):
        res = engine.query(query_to_run, k=k_param, min_score=min_score_param)
        retrieved_kuns = res.get('retrieved_kuns_data', [])
        
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
            "trazabilidad": retrieved_kuns,
            "dot_code": dot_code
        })
        st.session_state.active_index = len(st.session_state.history) - 1

if st.session_state.active_index >= 0:
    col_chat, col_trace = st.columns([0.60, 0.40], gap="large")
    
    with col_chat:
        for i, item in enumerate(st.session_state.history):
            if i <= st.session_state.active_index:
                with st.chat_message("user"):
                    st.markdown(item['query'])
                with st.chat_message("assistant"):
                    st.markdown(item['answer'])
                    
    with col_trace:
        active_item = st.session_state.history[st.session_state.active_index]
        is_fallback = "lo siento" in active_item['answer'].lower()
        
        tab_cite, tab_graph = st.tabs(["📚 Trazabilidad y Citas", "🕸️ Subgrafo Relacional"])
        
        with tab_cite:
            if not is_fallback and active_item['trazabilidad']:
                with st.container():
                    st.markdown(
                        "ℹ️ **Disponibilidad de las fuentes oficiales**\n\n"
                        "La visualización y navegación hacia videos, documentos y otros recursos oficiales depende de las características técnicas y de la disponibilidad de las plataformas de origen (por ejemplo, YouTube o los portales oficiales de la IJF).\n\n"
                        "Algunas fuentes pueden:\n"
                        "* Permitir acceso directo al contenido específico;\n"
                        "* Redirigir únicamente al portal oficial;\n"
                        "* Haber sido migradas;\n"
                        "* Dejar de estar disponibles debido a cambios en la plataforma de origen o por otros motivos externos al asistente.\n\n"
                        "Cuando esto ocurra, el Reference Resolution Manager (RRM) informará el estado de la referencia y, cuando exista una referencia oficial disponible y registrada en el sistema, el RRM la presentará al usuario."
                    )
                    st.markdown(
                        "**Leyenda de Estados:** &nbsp; "
                        "🟢 *Disponible* &nbsp;&nbsp; "
                        "🟡 *Migrada* &nbsp;&nbsp; "
                        "🔵 *Portal General* &nbsp;&nbsp; "
                        "🔴 *No Disponible*"
                    )
                    st.markdown("---")
                
                st.caption("📱 *En celulares, desplázate manualmente a la página indicada (función en proceso de mejora).*")
                for kun in active_item['trazabilidad']:
                    res = _rrm_manager.resolve_reference(kun['id_conocimiento'], kun)
                    url = res.get("url")
                    is_clickable = res.get("is_clickable", True)
                    op_status = res.get("operational_status", "AVAILABLE")
                    
                    source_id = kun['fuente_origen']
                    ref_spec = kun.get('referencia_especifica', 'Reglamento')
                    name = RESOURCE_DETAILS[source_id]["name"] if source_id in RESOURCE_DETAILS else "Fuente Oficial"
                    
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
                    st.markdown(f"* **Fuente:** {source_link}")
                    st.write(f"* Original: *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                    st.write(f"* Interpretación: {kun['interpretacion']}")
                    st.write("---")
            else:
                st.info("No hay trazabilidad legal disponible para esta consulta.")
                
        with tab_graph:
            if not is_fallback and active_item['dot_code']:
                st.graphviz_chart(active_item['dot_code'])
            else:
                st.info("No hay relaciones de grafo disponibles para esta consulta.")
else:
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; margin-bottom: 1.5rem;">
        <h1 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 2.1rem; font-weight: 700; margin-bottom: 0.8rem;">🥋 Bienvenido al Asistente del SOR de la IJF</h1>
        <p style="font-size: 1.05rem; opacity: 0.85; max-width: 600px; margin: 0 auto; line-height: 1.4;">Tu consultor experto del Reglamento de Organización y Deporte (SOR 2026). Pregúntame abajo sobre arbitraje, uniformes (Sokuteiki), pesaje o asistencia médica.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="font-size: 0.85rem; font-weight: 600; text-align: center; margin-bottom: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">💡 Temas Sugeridos</div>
    """, unsafe_allow_html=True)
    
    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        st.markdown("""
        <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 0.8rem; text-align: left; height: 100%;">
            <div style="font-weight: 700; color: #1d4ed8; margin-bottom: 0.3rem; font-size: 0.9rem;">🚫 Reglas de Arbitraje</div>
            <p style="font-size: 0.75rem; margin: 0; opacity: 0.8;">¿Se permite la defensa con la cabeza? o ¿Cómo se sanciona el abrazo de oso?</p>
        </div>
        """, unsafe_allow_html=True)
    with scol2:
        st.markdown("""
        <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 0.8rem; text-align: left; height: 100%;">
            <div style="font-weight: 700; color: #1d4ed8; margin-bottom: 0.3rem; font-size: 0.9rem;">📐 Control de Uniformes</div>
            <p style="font-size: 0.75rem; margin: 0; opacity: 0.8;">¿Qué es el Sokuteiki y cómo se usa? o Medidas oficiales del judogi</p>
        </div>
        """, unsafe_allow_html=True)
    with scol3:
        st.markdown("""
        <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; padding: 0.8rem; text-align: left; height: 100%;">
            <div style="font-weight: 700; color: #1d4ed8; margin-bottom: 0.3rem; font-size: 0.9rem;">⏱️ Pesaje y Médicos</div>
            <p style="font-size: 0.75rem; margin: 0; opacity: 0.8;">Tolerancia de peso aleatorio o Límite de atenciones médicas</p>
        </div>
        """, unsafe_allow_html=True)

st.write("---")
with st.expander("📝 Alcance del Asistente & Cobertura de Temas"):
    st.markdown(f"El asistente cuenta con **{kg_metrics['nodes_count']} Unidades de Conocimiento certificadas** extraídas de las fuentes oficiales de la IJF.")
    col_cov, col_uncov = st.columns(2)
    with col_cov:
        st.markdown("""
        #### ✅ Temas Cubiertos
        *   **🚫 Reglas de Arbitraje (Apéndice D - 100%):** Todos los artículos (1 al 21), gestos oficiales, puntuaciones, Osaekomi, Mate, luxaciones, descalificaciones directas (Hansoku-make) y conmoción cerebral.
        *   **🥋 Control de Judogi (Apéndice C - 100%):** Proceso de control, medidas permitidas, Sokuteiki, colocación de logotipos, colores (blanco/azul) e indumentaria.
        *   **⏱️ Sistemas y Pesaje (Secciones 2, 3, 4):** Pesaje oficial y sorteo aleatorio, tolerancias, llaves de competencia con repechaje, siembra de cabezas de serie y gestión de categorías.
        *   **🏥 Manual Médico (Sección 6):** Asistencia médica en tatami, límite de 2 atenciones para lesiones con sangrado, conmociones y días de inhabilitación.
        *   **🎖️ Protocolos de Premiación (Sección 8):** Ceremonias de medallas, izado de banderas, himnos nacionales y código de vestimenta oficial.
        """)
    with col_uncov:
        st.markdown("""
        #### ❌ Fuera de Alcance (No Cubiertos)
        *   **🏫 Educación y Coaches (Sección 5):** Códigos de vestimenta para entrenadores en la silla, acreditaciones técnicas y penalización de tarjetas en la silla de coach.
        *   **📢 Marketing y Difusión (Sección 10):** Contratos de patrocinadores oficiales de la IJF, derechos de transmisión de televisión y publicidad permitida en los banners.
        *   **🏟️ Infraestructura del Recinto (Sección 11):** Disposición física del pabellón, áreas VIP, vestuarios, requisitos de iluminación y climatización de la arena.
        *   **📋 Estatutos y Apelaciones (Apéndices A, B):** Normas internas de la IJF, elecciones directivas, el Código Disciplinario y procesos de apelación federativos.
        *   **🧬 Transición y Categorías Especiales (Apéndices E, F, G, H):** Reglamentos de transición de género, control antidopaje de laboratorio, reglas modificadas para veteranos/masters y arbitraje de competencias de Kata.
        """)
