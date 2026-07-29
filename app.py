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

st.set_page_config(
    page_title="Asistente SOR IJF",
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
    st.markdown("**ℹ️ Información**")
    
    with st.expander("1. Proyecto", expanded=False):
        st.markdown("""
**IJF SOR Assistant**

El IJF SOR Assistant es un asistente especializado diseñado para facilitar la consulta y comprensión del *Sport and Organisation Rules (SOR)* de la Federación Internacional de Judo (IJF).

Su propósito es ofrecer respuestas fundamentadas exclusivamente en documentación oficial, permitiendo acceder de manera rápida y organizada a la información normativa utilizada en el arbitraje y la competición internacional.
        """)
        
    with st.expander("2. Propósito", expanded=False):
        st.markdown("""
Esta aplicación fue desarrollada con el objetivo de apoyar el estudio, la preparación y la consulta del reglamento oficial de la IJF.

El asistente organiza y presenta la información oficial de forma clara, facilitando el acceso al contenido normativo para árbitros, entrenadores, deportistas y demás miembros de la comunidad del judo.

Las respuestas generadas constituyen una ayuda documental y educativa. En caso de discrepancia o interpretación, siempre prevalecen los documentos oficiales publicados por la Federación Internacional de Judo y las decisiones adoptadas por sus órganos competentes.
        """)
        
    with st.expander("3. Fuentes", expanded=False):
        st.markdown("""
Este asistente utiliza exclusivamente fuentes oficiales publicadas por la Federación Internacional de Judo (IJF), incluyendo reglamentos, documentos técnicos, comunicados y otros recursos oficiales.
        """)
        
    with st.expander("4. Autor", expanded=False):
        st.markdown("""
**Alexis Oliveros**

National Judo Referee – Colombia

2nd Dan

Desarrollador del proyecto **IJF SOR Assistant**.

© 2026 Alexis Oliveros. Todos los derechos reservados.
        """)
        
    with st.expander("5. Versión", expanded=False):
        st.markdown("""
**IJF SOR Assistant**

Versión **1.0.0**

Basado en **Sport and Organisation Rules (SOR) 2026**

Última actualización: **Julio de 2026**
        """)

    st.write("---")
    st.markdown("**🧭 Ajustes de Búsqueda**")
    k_param = st.slider(
        "Cantidad de Reglas a Consultar", 
        1, 5, 3,
        help="Define cuántas reglas oficiales revisará el asistente antes de elaborar la respuesta. Un valor mayor puede ofrecer respuestas más completas, aunque también puede aumentar ligeramente el tiempo de búsqueda."
    )
    min_score_param = st.slider(
        "Filtro Anti-Distracciones", 
        0.05, 0.50, 0.10, 0.05,
        help="Controla qué tan relacionadas deben estar las reglas encontradas con tu consulta. Valores bajos permiten considerar más información; valores altos muestran únicamente las coincidencias más relevantes."
    )

    st.write("---")
    st.markdown("**💡 Sugerencias Rápidas**")
    st.selectbox(
        "Selecciona una pregunta ejemplo:",
        preguntas_ejemplo,
        key="example_select_widget",
        on_change=load_example,
        label_visibility="collapsed",
        help="Elige una pregunta predefinida para ver cómo responde el asistente."
    )

    if len(st.session_state.history) > 0:
        st.write("---")
        st.markdown("**📚 Historial**")
        options = [f"#{i+1}: {item['query'][:15]}..." for i, item in enumerate(st.session_state.history)]
        selected_option = st.selectbox(
            "Revisar consulta:", 
            options, 
            index=st.session_state.active_index,
            help="Te permite volver a ver cualquiera de las consultas realizadas anteriormente en esta sesión de forma instantánea."
        )
        new_active = options.index(selected_option)
        if new_active != st.session_state.active_index:
            st.session_state.active_index = new_active
            st.rerun()

    st.write("---")
    st.markdown("### 🥋 Gobernanza del Grafo")
    if is_connected:
        st.markdown('<span class="status-badge-connected">🟢 Modo Conectado (Gemini)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-offline">🟡 Modo Offline (Simulado)</span>', unsafe_allow_html=True)
        
    st.markdown("**📈 Módulos de Conocimiento**")
    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.metric("Total KUNs", kg_metrics['nodes_count'])
    with mcol2:
        st.metric("Relaciones", kg_metrics['edges_count'])
    st.metric("Grado Promedio", f"{kg_metrics['avg_degree']:.2f}")
    
    st.markdown("**🕸️ Nodos Hub**")
    for node, deg in kg_metrics['hubs'][:2]:
        st.markdown(f"- `{node}` ({deg} enlaces)", unsafe_allow_html=True)



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
            <h2 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 2.8rem; margin: 0; font-weight: 700; line-height: 1.1;">Asistente SOR IJF</h2>
            <div class="ijf-tooltip" style="position: absolute; right: -28px; top: 50%; transform: translateY(-50%);">
                <div class="ijf-help-icon" style="margin-left: 0;">?</div>
                <div class="ijf-tooltiptext" style="left: 50%; transform: translateX(-50%); top: 130%;">Reglamento de la Federación Internacional de Judo (SOR 2026)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: var(--secondary-background-color); border-bottom: 2px solid #1d4ed8; padding: 1.5rem 1rem; margin-top: 1.2rem; margin-bottom: 1.2rem; width: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-radius: 6px; text-align: center;">
        <h2 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 2.8rem; margin: 0; font-weight: 700; line-height: 1.1;">Asistente SOR IJF</h2>
    </div>
    """, unsafe_allow_html=True)

# Handle user input
query_to_run = None

# Check if a suggestion card was clicked
if st.session_state.get("query_to_run"):
    query_to_run = st.session_state.pop("query_to_run")

# Chat input for manual queries
user_input = st.chat_input("Haga su consulta")
if user_input:
    query_to_run = user_input.strip()


if query_to_run:
    with st.status("Consultando el Reglamento SOR 2026...", expanded=True) as status:
        status.write("🔍 Buscando en la base de conocimiento...")
        res = engine.query(query_to_run, k=k_param, min_score=min_score_param)
        retrieved_kuns = res.get('retrieved_kuns_data', [])
        status.write(f"📚 {len(retrieved_kuns)} regla(s) recuperada(s) del grafo...")
        status.write("✍️ Generando respuesta con el modelo...")
        
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
        status.update(label="✅ Respuesta generada", state="complete", expanded=False)

if st.session_state.active_index >= 0:
    history_to_show = st.session_state.history[:st.session_state.active_index + 1]
    
    st.write("---")
    
    for original_i, item in reversed(list(enumerate(history_to_show))):
        with st.chat_message("user", avatar="👤"):
            st.markdown(item['query'])
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown(item['answer'])
            
            is_fallback = "lo siento" in item['answer'].lower()
            if not is_fallback and item.get('trazabilidad'):
                with st.expander("🔍 Mostrar Trazabilidad y Grafo", expanded=False):
                    tab_cite, tab_graph = st.tabs(["📚 Trazabilidad y Citas", "🕸️ Subgrafo Relacional"])
                    
                    with tab_cite:
                        with st.expander("ℹ️ Sobre la disponibilidad de las fuentes oficiales", expanded=False):
                            st.markdown(
                                '<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">'
                                'La visualización y navegación hacia videos, documentos y otros recursos oficiales depende de las características técnicas y de la disponibilidad de las plataformas de origen (por ejemplo, YouTube o los portales oficiales de la IJF).<br><br>'
                                'Algunas fuentes pueden: permitir acceso directo al contenido específico; redirigir únicamente al portal oficial; haber sido migradas; o dejar de estar disponibles debido a cambios en la plataforma de origen.<br><br>'
                                'Cuando esto ocurra, el Reference Resolution Manager (RRM) informará el estado de la referencia y presentará una referencia alternativa cuando exista.<br><br>'
                                '<strong>Leyenda:</strong> &nbsp; '
                                '🟢 <em>Disponible</em> &nbsp;&nbsp; '
                                '🟡 <em>Migrada</em> &nbsp;&nbsp; '
                                '🔵 <em>Portal General</em> &nbsp;&nbsp; '
                                '🔴 <em>No Disponible</em>'
                                '</div>', unsafe_allow_html=True
                            )
                        
                        st.caption("📱 *En celulares, el documento se abre pero no siempre dirige al detalle. En navegadores web funciona como enlace directo al contenido relevante.*")
                        for kun in item['trazabilidad']:
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
                            
                    with tab_graph:
                        if item.get('dot_code'):
                            st.graphviz_chart(item['dot_code'])
                        else:
                            st.info("No hay relaciones de grafo disponibles para esta consulta.")
            elif not is_fallback:
                with st.expander("🔍 Mostrar Trazabilidad y Grafo", expanded=False):
                    st.info("No hay trazabilidad legal disponible para esta consulta.")
else:
    st.markdown("""
    <div style="text-align: center; margin-top: 1.6rem; margin-bottom: 1.2rem;">
        <h1 style="font-family: 'Outfit', sans-serif; color: #1d4ed8; font-size: 2.05rem; font-weight: 700; line-height: 1.05; margin-bottom: 0.4rem; max-width: 28rem; margin-left: auto; margin-right: auto;">Bienvenido</h1>
        <p style="font-size: 0.85rem; color: rgba(212, 175, 55, 0.45); max-width: 640px; margin: 0 auto; line-height: 1.45; margin-bottom: 1rem; font-weight: 400;">Tu consultor del Reglamento de Organización y Deporte (SOR 2026). Pregúntame sobre arbitraje, uniformes, pesaje o asistencia médica.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style=\"font-size: 0.8rem; font-weight: 500; text-align: center; margin-bottom: 0.6rem; margin-top: 1.5rem; color: #94a3b8; letter-spacing: 0.04em;\">Prueba con alguna de estas consultas</div>""", unsafe_allow_html=True)

    suggestion_chips = [
        ("Defensa con la cabeza", "¿Se permite la defensa con la cabeza?"),
        ("Dimensiones del tatami", "¿Cuáles son las dimensiones del tatami?"),
        ("Intervenciones médicas", "¿Cuántas intervenciones médicas se permiten por combate?"),
        ("Sokuteiki y su uso", "¿Qué es el Sokuteiki y cómo se usa?"),
        ("Reverse seoi-nage", "¿Cómo se sanciona el reverse seoi-nage en cadetes?"),
        ("Color de Judogi", "¿Cuáles son las reglas de color de Judogi?"),
    ]
    chip_cols = st.columns(len(suggestion_chips))
    for i, (label, full_query) in enumerate(suggestion_chips):
        with chip_cols[i]:
            if st.button(label, key=f"chip_{i}", help=full_query):
                st.session_state.query_to_run = full_query
                st.rerun()

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
