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
from feedback_manager import (
    record_observation,
    is_admin_configured,
    verify_admin_token,
    list_observations_protected,
    get_observation_attachment_bytes,
    update_observation_status_protected,
    export_observations_csv,
    get_feedback_metrics,
    VALID_STATUSES,
    TIPOS_NOVEDAD
)
from i18n import t
from response_structurer import clean_presentation_text, sanitize_presentation_html

def render_custom_html(html_content: str):
    """Inserta HTML en la UI evitando la interpretacion CommonMark como bloque de codigo."""
    if hasattr(st, "html"):
        st.html(html_content)
    else:
        st.markdown(html_content, unsafe_allow_html=True)


logo_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
logo_path = os.path.join(logo_dir, 'logo.svg')

st.set_page_config(
    page_title="IJF SOR Assistant",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "app_theme" not in st.session_state:
    st.session_state.app_theme = "auto"

theme_mode = st.session_state.get("app_theme", "auto")

light_theme_vars = """
        --ijf-text-color: #0f172a;
        --ijf-blue: #003399;
        --ijf-blue-light: #1d4ed8;
        --ijf-blue-accent: #2563eb;
        --ijf-red: #ED1C24;
        --kun-bg: #F8FAFC;
        --kun-border: #E2E8F0;
        --ijf-metric-val: #003399;
        --ijf-metric-lbl: #4B5563;
        --ijf-cit-label: #1e3a8a;
        --ijf-btn-border: rgba(128, 128, 128, 0.25);
        --ijf-btn-hover-border: #003399;
        --ijf-btn-hover-color: #003399;
        --ijf-btn-hover-bg: rgba(0, 51, 153, 0.08);
        --ijf-tier1-bg: rgba(37, 99, 235, 0.06);
        --ijf-tier1-border: #2563eb;
        --ijf-tier1-outline: rgba(37, 99, 235, 0.15);
        --ijf-title-color: #1d4ed8;
        --ijf-subtitle-color: #475569;
        --ijf-caption-color: #475569;
        --ijf-tooltip-bg: #1e293b;
        --ijf-tooltip-color: #f8fafc;
        --ijf-tooltip-border: #334155;
        --ijf-help-bg: rgba(29, 78, 216, 0.10);
        --status-conn-bg: #D1FAE5;
        --status-conn-color: #065F46;
        --status-conn-border: #A7F3D0;
        --status-off-bg: #FEF3C7;
        --status-off-color: #92400E;
        --status-off-border: #FDE68A;
        --surface-main-bg: #ffffff;
        --surface-sidebar-bg: #F8FAFC;
        --surface-header-bg: rgba(255, 255, 255, 0.95);
        --surface-card-bg: #F8FAFC;
        --surface-card-border: #E2E8F0;
        --surface-input-bg: #ffffff;
        --surface-input-color: #0f172a;
        --surface-input-border: #cbd5e1;
        --surface-expander-bg: #F8FAFC;
        --surface-expander-border: #E2E8F0;
        --background-color: #ffffff;
        --secondary-background-color: #F8FAFC;
        --text-color: #0f172a;
"""

dark_theme_vars = """
        --ijf-text-color: #f8fafc;
        --ijf-blue: #60a5fa;
        --ijf-blue-light: #3b82f6;
        --ijf-blue-accent: #60a5fa;
        --ijf-red: #f87171;
        --kun-bg: #1e293b;
        --kun-border: #334155;
        --ijf-metric-val: #60a5fa;
        --ijf-metric-lbl: #9ca3af;
        --ijf-cit-label: #93c5fd;
        --ijf-btn-border: rgba(255, 255, 255, 0.20);
        --ijf-btn-hover-border: #60a5fa;
        --ijf-btn-hover-color: #93c5fd;
        --ijf-btn-hover-bg: rgba(59, 130, 246, 0.16);
        --ijf-tier1-bg: rgba(59, 130, 246, 0.14);
        --ijf-tier1-border: #3b82f6;
        --ijf-tier1-outline: rgba(59, 130, 246, 0.25);
        --ijf-title-color: #60a5fa;
        --ijf-subtitle-color: #94a3b8;
        --ijf-caption-color: #f1f5f9;
        --ijf-tooltip-bg: #0f172a;
        --ijf-tooltip-color: #f8fafc;
        --ijf-tooltip-border: #475569;
        --ijf-help-bg: rgba(59, 130, 246, 0.15);
        --status-conn-bg: rgba(16, 185, 129, 0.18);
        --status-conn-color: #34d399;
        --status-conn-border: rgba(52, 211, 153, 0.35);
        --status-off-bg: rgba(245, 158, 11, 0.18);
        --status-off-color: #fbbf24;
        --status-off-border: rgba(251, 191, 36, 0.35);
        --surface-main-bg: #0e1117;
        --surface-sidebar-bg: #1e293b;
        --surface-header-bg: rgba(14, 17, 23, 0.95);
        --surface-card-bg: #1e293b;
        --surface-card-border: #334155;
        --surface-input-bg: #1e293b;
        --surface-input-color: #f8fafc;
        --surface-input-border: #475569;
        --surface-expander-bg: #1e293b;
        --surface-expander-border: #334155;
        --background-color: #0e1117;
        --secondary-background-color: #1e293b;
        --text-color: #f8fafc;
"""

if theme_mode == "dark":
    active_theme_tokens = f":root {{\n{dark_theme_vars}\n}}"
elif theme_mode == "light":
    active_theme_tokens = f":root {{\n{light_theme_vars}\n}}"
else:  # "auto"
    active_theme_tokens = f"""
    :root {{
        {light_theme_vars}
    }}
    @media (prefers-color-scheme: dark) {{
        :root {{
            {dark_theme_vars}
        }}
    }}
    """

# Custom Styling for modern premium UI
st.markdown(f"""
<style>
    .block-container {{
        padding-top: 0.8rem !important;
        padding-bottom: 1.5rem !important;
    }}

    {active_theme_tokens}

    /* Dynamic Theme Surface Overrides */
    .stApp {{
        background-color: var(--surface-main-bg) !important;
        color: var(--ijf-text-color) !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: var(--surface-sidebar-bg) !important;
        color: var(--ijf-text-color) !important;
    }}
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {{
        color: var(--ijf-text-color);
    }}
    [data-testid="stHeader"] {{
        background-color: var(--surface-header-bg) !important;
    }}
    .stTextInput input, .stTextArea textarea {{
        background-color: var(--surface-input-bg) !important;
        color: var(--surface-input-color) !important;
        border: 1px solid var(--surface-input-border) !important;
    }}
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    input::placeholder,
    textarea::placeholder {{
        color: var(--ijf-subtitle-color) !important;
        opacity: 0.75 !important;
        font-style: italic !important;
        font-size: 0.93rem !important;
    }}

    /* Apertura del Menú Lateral (Sidebar Toggle Button) con alto contraste e indicador visible */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {{
        display: inline-flex !important;
        align-items: center !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 99999 !important;
        top: 0.55rem !important;
        left: 0.75rem !important;
    }}
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button {{
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.45rem !important;
        background-color: var(--surface-card-bg) !important;
        color: var(--ijf-title-color) !important;
        border: 2px solid var(--ijf-title-color) !important;
        border-radius: 20px !important;
        padding: 0.35rem 0.95rem !important;
        min-height: 2.3rem !important;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.25s ease-in-out !important;
        cursor: pointer !important;
    }}
    [data-testid="stSidebarCollapsedControl"] button:hover,
    [data-testid="collapsedControl"] button:hover {{
        background-color: var(--ijf-tier1-bg) !important;
        border-color: var(--ijf-blue-accent) !important;
        color: var(--ijf-blue-accent) !important;
        transform: scale(1.05) !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.45) !important;
    }}
    [data-testid="stSidebarCollapsedControl"] button svg,
    [data-testid="collapsedControl"] button svg {{
        color: var(--ijf-title-color) !important;
        fill: currentColor !important;
        stroke: currentColor !important;
        width: 1.25rem !important;
        height: 1.25rem !important;
        flex-shrink: 0 !important;
    }}
    [data-testid="stSidebarCollapsedControl"] button::after,
    [data-testid="collapsedControl"] button::after {{
        content: "☰ Menú lateral";
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        color: var(--ijf-title-color) !important;
        white-space: nowrap !important;
    }}
    [data-testid="stSidebarCollapseButton"] button {{
        background-color: var(--surface-card-bg) !important;
        color: var(--ijf-text-color) !important;
        border: 1.5px solid var(--surface-card-border) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
    }}
    [data-testid="stSidebarCollapseButton"] button:hover {{
        border-color: var(--ijf-blue-accent) !important;
        color: var(--ijf-blue-accent) !important;
    }}
    .stSelectbox div[data-baseweb="select"] > div {{
        background-color: var(--surface-input-bg) !important;
        color: var(--surface-input-color) !important;
        border-color: var(--surface-input-border) !important;
    }}
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {{
        background-color: var(--surface-card-bg) !important;
        color: var(--ijf-text-color) !important;
        border: 1px solid var(--surface-card-border) !important;
    }}
    li[role="option"] {{
        background-color: var(--surface-card-bg) !important;
        color: var(--ijf-text-color) !important;
    }}
    li[role="option"]:hover, li[aria-selected="true"] {{
        background-color: var(--ijf-tier1-bg) !important;
        color: var(--ijf-blue-accent) !important;
    }}
    [data-testid="stExpander"] {{
        background-color: var(--surface-expander-bg) !important;
        border: 1px solid var(--surface-expander-border) !important;
        border-radius: 6px !important;
    }}
    [data-testid="stExpander"] summary {{
        color: var(--ijf-text-color) !important;
    }}
    [data-testid="stChatMessage"] {{
        background-color: transparent !important;
        color: var(--ijf-text-color) !important;
    }}
    [data-testid="stChatMessageContent"] {{
        color: var(--ijf-text-color) !important;
    }}
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {{
        color: var(--ijf-text-color) !important;
        font-weight: 500 !important;
    }}
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] li,
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown li {{
        color: var(--ijf-text-color) !important;
    }}
    [data-testid="stCaptionContainer"] {{
        opacity: 1 !important;
    }}
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p,
    .stCaption,
    small {{
        color: var(--ijf-caption-color) !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }}
    button[data-baseweb="tab"] {{
        color: var(--ijf-caption-color) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--ijf-blue-accent) !important;
    }}
    [data-testid="stStatusWidget"] {{
        background-color: var(--surface-card-bg) !important;
        border: 1px solid var(--surface-card-border) !important;
        color: var(--ijf-text-color) !important;
    }}
    [data-testid="stStatusWidget"] summary {{
        color: var(--ijf-text-color) !important;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .status-badge-connected {
        background-color: var(--status-conn-bg);
        color: var(--status-conn-color) !important;
        border: 1px solid var(--status-conn-border);
        padding: 0.2rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-offline {
        background-color: var(--status-off-bg);
        color: var(--status-off-color) !important;
        border: 1px solid var(--status-off-border);
        padding: 0.2rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .kun-card {
        border-left: 3px solid var(--ijf-blue-accent);
        border-top: 1px solid var(--kun-border);
        border-right: 1px solid var(--kun-border);
        border-bottom: 1px solid var(--kun-border);
        background-color: var(--kun-bg);
        padding: 0.6rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
        color: var(--text-color);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: var(--ijf-metric-val) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: var(--ijf-metric-lbl) !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        padding-top: 0.15rem !important;
        padding-bottom: 0.15rem !important;
    }
    .element-container {
        margin-bottom: 0.4rem !important;
    }
    /* Banner y Contenedor Resaltado para Ayúdanos a Mejorar (Feedback) */
    .feedback-highlight-banner {
        margin-top: 1.15rem;
        margin-bottom: 0.45rem;
        padding: 0.85rem 1.1rem;
        border-radius: 8px;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(245, 158, 11, 0.09) 100%);
        border: 1.5px dashed var(--ijf-blue-accent);
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    .feedback-highlight-badge {
        font-family: 'Outfit', sans-serif;
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--ijf-blue-accent);
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .feedback-highlight-text {
        font-size: 0.82rem;
        color: var(--ijf-text-color);
        line-height: 1.45;
        opacity: 0.92;
    }
    .quota-info-card {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.06) 0%, rgba(245, 158, 11, 0.08) 100%);
        border: 1px solid var(--surface-card-border);
        border-left: 3px solid var(--ijf-blue-accent);
        padding: 0.65rem 0.8rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        margin-bottom: 0.6rem;
        font-size: 0.78rem;
        line-height: 1.45;
    }
    .quota-info-title {
        font-weight: 700;
        color: var(--ijf-title-color);
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .quota-info-body {
        color: var(--ijf-subtitle-color);
        font-size: 0.75rem;
    }
    .local-fallback-banner {
        background-color: var(--status-off-bg);
        border: 1px solid var(--status-off-border);
        border-left: 4px solid var(--status-off-color);
        border-radius: 6px;
        padding: 0.65rem 0.9rem;
        margin-bottom: 0.75rem;
        font-size: 0.82rem;
        line-height: 1.45;
    }
    .local-fallback-header {
        font-weight: 700;
        color: var(--status-off-color);
        display: flex;
        align-items: center;
        gap: 0.35rem;
        margin-bottom: 0.2rem;
    }
    .local-fallback-desc {
        color: var(--ijf-text-color);
        font-size: 0.8rem;
        opacity: 0.95;
    }

    .tier1-box {
        background-color: var(--ijf-tier1-bg);
        border-left: 4px solid var(--ijf-tier1-border);
        border-top: 1px solid var(--ijf-tier1-outline);
        border-right: 1px solid var(--ijf-tier1-outline);
        border-bottom: 1px solid var(--ijf-tier1-outline);
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 14px;
        font-size: 1.05rem;
        line-height: 1.55;
        color: var(--ijf-text-color) !important;
    }
        /* Bloque Independiente de Evidencias Normativas */
    .normative-evidence-container {
        margin-top: 1.1rem;
        margin-bottom: 1.2rem;
    }
    .evidence-section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 0.8rem;
        margin-bottom: 0.25rem;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid var(--surface-card-border);
    }
    .evidence-section-title {
        font-family: 'Outfit', sans-serif;
        font-size: 0.96rem;
        font-weight: 700;
        color: var(--ijf-text-color);
        letter-spacing: -0.01em;
    }
    .evidence-section-subtitle {
        font-size: 0.78rem;
        color: var(--ijf-subtitle-color);
        margin-bottom: 0.7rem;
    }
    .normative-evidence-card {
        background-color: var(--surface-card-bg);
        border: 1px solid var(--surface-card-border);
        border-left: 4px solid var(--ijf-blue-accent);
        border-radius: 8px;
        padding: 0.75rem 0.95rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .evidence-card-header {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 0.35rem;
    }
    .evidence-badge-art {
        background-color: var(--ijf-tier1-bg);
        color: var(--ijf-blue-accent) !important;
        border: 1px solid var(--ijf-tier1-outline);
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .evidence-badge-page {
        background-color: var(--surface-expander-bg);
        color: var(--ijf-text-color) !important;
        border: 1px solid var(--surface-card-border);
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .evidence-badge-edition {
        background-color: var(--surface-expander-bg);
        color: var(--ijf-subtitle-color) !important;
        border: 1px solid var(--surface-card-border);
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .evidence-badge-verified {
        background-color: var(--status-conn-bg);
        color: var(--status-conn-color) !important;
        border: 1px solid var(--status-conn-border);
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        font-size: 0.74rem;
        font-weight: 600;
    }
    .tier1-title {
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
        color: var(--ijf-text-color) !important;
    }
    .evidence-card-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--ijf-text-color);
        margin-bottom: 0.3rem;
    }
    .normative-quote-box {
        background-color: var(--ijf-tier1-bg);
        border-left: 3px solid var(--ijf-blue-accent);
        padding: 0.45rem 0.75rem;
        border-radius: 0 5px 5px 0;
        font-size: 0.84rem;
        line-height: 1.45;
        color: var(--ijf-text-color) !important;
        margin-top: 0.3rem;
        margin-bottom: 0.2rem;
        font-style: italic;
    }
    .normative-context-box {
        background-color: var(--surface-expander-bg);
        border-left: 3px solid var(--surface-card-border);
        padding: 0.45rem 0.75rem;
        border-radius: 0 5px 5px 0;
        font-size: 0.84rem;
        line-height: 1.45;
        color: var(--ijf-text-color) !important;
        margin-top: 0.3rem;
        margin-bottom: 0.2rem;
    }
    .quote-type-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: var(--ijf-subtitle-color) !important;
        margin-bottom: 0.25rem;
        font-style: normal;
    }
    .audit-panel-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 0.6rem;
        margin-bottom: 0.75rem;
        font-size: 0.82rem;
    }
    .audit-panel-item {
        background-color: var(--surface-card-bg);
        border: 1px solid var(--surface-card-border);
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
    }
    .audit-panel-label {
        font-size: 0.70rem;
        font-weight: 600;
        color: var(--ijf-subtitle-color);
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 0.2rem;
    }
    .audit-panel-value {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--ijf-text-color);
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
        color: var(--ijf-text-color) !important;
    }
    div[data-testid="stButton"] button {
        background-color: transparent;
        border: 1px solid var(--ijf-btn-border);
        border-radius: 9999px;
        padding: 0.4rem 0.85rem !important;
        text-align: center !important;
        color: var(--ijf-text-color) !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        line-height: 1.3;
        white-space: nowrap;
        display: block;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease;
        opacity: 0.85;
    }
    div[data-testid="stButton"] button p {
        margin: 0;
        text-align: center !important;
    }
    div[data-testid="stButton"] button:hover {
        border-color: var(--ijf-btn-hover-border) !important;
        color: var(--ijf-btn-hover-color) !important;
        background-color: var(--ijf-btn-hover-bg) !important;
        opacity: 1;
    }
    div[data-testid="stButton"] button:active {
        background-color: rgba(37, 99, 235, 0.20) !important;
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
        color: var(--ijf-cit-label);
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

def render_pdf_viewer(pdf_url: str, initial_page: int = 1, search_quote: str = "", zoom_level: float = 1.0, height: int = 820, page_b64: str = "", lang: str = "es"):
    """
    Renders an interactive embedded PDF viewer using PDF.js CDN with range streaming,
    canvas rendering, text layer selection, and automated citation query highlighting.
    Uses base64-encoded page data when available to bypass CDN CORS limitations.
    Fully localized according to active UI language.
    """
    safe_quote = html.escape(search_quote).replace("'", "\\'")
    viewer_title = "IJF SOR PDF Viewer" if lang == "en" else "Visor PDF SOR IJF"
    prev_btn_label = t("pdf_prev_btn", lang)
    prev_btn_title = t("pdf_prev_title", lang)
    page_prefix = t("pdf_page_prefix", lang)
    next_btn_label = t("pdf_next_btn", lang)
    next_btn_title = t("pdf_next_title", lang)
    zoom_out_title = t("pdf_zoom_out_title", lang)
    zoom_in_title = t("pdf_zoom_in_title", lang)
    zoom_fit_btn = t("pdf_zoom_fit_btn", lang)
    zoom_fit_title = t("pdf_zoom_fit_title", lang)
    search_placeholder = t("pdf_search_placeholder", lang)
    highlight_btn = t("pdf_highlight_btn", lang)
    badge_highlighted = t("pdf_badge_highlighted", lang)
    open_tab_btn = t("pdf_open_tab_btn", lang)
    open_tab_title = t("pdf_open_tab_title", lang)
    loading_text = t("pdf_loading_text", lang)
    load_error_template = t("pdf_load_error", lang, url=pdf_url, num="'+pageNum+'").replace("'", "\\'")

    cur_theme = st.session_state.get("app_theme", "auto")
    pdf_light_vars = """
          --pdf-bg: #f8fafc;
          --pdf-color: #0f172a;
          --pdf-toolbar-bg: #ffffff;
          --pdf-toolbar-border: #e2e8f0;
          --pdf-btn-bg: #f1f5f9;
          --pdf-btn-color: #1e293b;
          --pdf-btn-border: #cbd5e1;
          --pdf-btn-hover-bg: #e2e8f0;
          --pdf-btn-hover-border: #94a3b8;
          --pdf-input-bg: #ffffff;
          --pdf-input-color: #0f172a;
          --pdf-input-border: #cbd5e1;
          --pdf-status-color: #64748b;
          --pdf-badge-bg: rgba(202, 138, 4, 0.15);
          --pdf-badge-color: #854d0e;
          --pdf-badge-border: #ca8a04;
          --pdf-container-bg: #e2e8f0;
    """
    pdf_dark_vars = """
          --pdf-bg: #0f172a;
          --pdf-color: #f8fafc;
          --pdf-toolbar-bg: #1e293b;
          --pdf-toolbar-border: #334155;
          --pdf-btn-bg: #334155;
          --pdf-btn-color: #f8fafc;
          --pdf-btn-border: #475569;
          --pdf-btn-hover-bg: #475569;
          --pdf-btn-hover-border: #64748b;
          --pdf-input-bg: #0f172a;
          --pdf-input-color: #f8fafc;
          --pdf-input-border: #475569;
          --pdf-status-color: #94a3b8;
          --pdf-badge-bg: rgba(234, 179, 8, 0.2);
          --pdf-badge-color: #fde047;
          --pdf-badge-border: #ca8a04;
          --pdf-container-bg: #0b0f19;
    """
    if cur_theme == "dark":
        pdf_theme_tokens = f":root {{\n{pdf_dark_vars}\n}}"
    elif cur_theme == "light":
        pdf_theme_tokens = f":root {{\n{pdf_light_vars}\n}}"
    else:
        pdf_theme_tokens = f"""
        :root {{
          {pdf_light_vars}
        }}
        @media (prefers-color-scheme: dark) {{
          :root {{
            {pdf_dark_vars}
          }}
        }}
        """

    viewer_html = f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
      <meta charset="utf-8">
      <title>{viewer_title}</title>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.css">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        {pdf_theme_tokens}
        body {{
          background-color: var(--pdf-bg);
          color: var(--pdf-color);
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          height: 100vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }}
        #toolbar {{
          background: var(--pdf-toolbar-bg);
          border-bottom: 1px solid var(--pdf-toolbar-border);
          padding: 8px 12px;
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
          font-size: 0.85rem;
          user-select: none;
        }}
        .btn {{
          background: var(--pdf-btn-bg);
          color: var(--pdf-btn-color);
          border: 1px solid var(--pdf-btn-border);
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
          background: var(--pdf-btn-hover-bg);
          border-color: var(--pdf-btn-hover-border);
        }}
        .btn-primary {{
          background: #2563eb;
          border-color: #3b82f6;
          color: #ffffff;
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
          background: var(--pdf-input-bg);
          color: var(--pdf-input-color);
          border: 1px solid var(--pdf-input-border);
          border-radius: 4px;
          padding: 3px 6px;
          width: 52px;
          text-align: center;
          font-size: 0.85rem;
        }}
        #search-box {{
          background: var(--pdf-input-bg);
          color: var(--pdf-input-color);
          border: 1px solid var(--pdf-input-border);
          border-radius: 4px;
          padding: 3px 8px;
          font-size: 0.82rem;
          min-width: 140px;
          max-width: 220px;
        }}
        #status-bar {{
          font-size: 0.78rem;
          color: var(--pdf-status-color);
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 8px;
        }}
        #highlight-badge {{
          background: var(--pdf-badge-bg);
          color: var(--pdf-badge-color);
          border: 1px solid var(--pdf-badge-border);
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
          background-color: var(--pdf-container-bg);
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
        <button class="btn" id="prev-btn" title="{prev_btn_title}">{prev_btn_label}</button>
        <span>{page_prefix}</span>
        <input type="number" id="page-num" class="input-page" value="{initial_page}" min="1">
        <span id="page-count">/ ...</span>
        <button class="btn" id="next-btn" title="{next_btn_title}">{next_btn_label}</button>
        <div style="border-left: 1px solid #334155; height: 18px; margin: 0 4px;"></div>
        <button class="btn" id="zoom-out-btn" title="{zoom_out_title}">-</button>
        <span id="zoom-label" style="font-size: 0.78rem; min-width: 44px; text-align: center;">100%</span>
        <button class="btn" id="zoom-in-btn" title="{zoom_in_title}">+</button>
        <button class="btn" id="zoom-fit-btn" title="{zoom_fit_title}">{zoom_fit_btn}</button>
        <div style="border-left: 1px solid #334155; height: 18px; margin: 0 4px;"></div>
        <input type="text" id="search-box" placeholder="{search_placeholder}" value="{safe_quote}">
        <button class="btn btn-primary" id="search-btn">{highlight_btn}</button>
        <span id="highlight-badge">{badge_highlighted}</span>
        <div id="status-bar">
          <a class="btn" href="{pdf_url}#page={initial_page}" target="_blank" rel="noopener noreferrer" style="text-decoration: none;" title="{open_tab_title}">{open_tab_btn}</a>
        </div>
      </div>
      <div id="viewer-container">
        <div id="loading-overlay">
          <div class="spinner"></div>
          <div id="loading-text">{loading_text}</div>
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
            highlightBadge.textContent = '{t("pdf_badge_matches", lang, matches="").strip()}' + ' ' + matchesFound;
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
          loadingText.innerHTML = '{load_error_template}';
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

def load_example():
    sel = st.session_state.get("example_select_widget")
    if sel and sel not in ("Elige una pregunta para consultar...", "Choose an example query..."):
        st.session_state.auto_run_query = sel

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

    # Theme Selection Widget (Automático / Claro / Oscuro)
    theme_options = [
        ("Automático (Sistema)", "auto") if lang == "es" else ("Automatic (System)", "auto"),
        ("Claro", "light") if lang == "es" else ("Light", "light"),
        ("Oscuro", "dark") if lang == "es" else ("Dark", "dark")
    ]
    cur_theme_code = st.session_state.get("app_theme", "auto")
    theme_indices = {"auto": 0, "light": 1, "dark": 2}
    cur_theme_idx = theme_indices.get(cur_theme_code, 0)
    selected_theme_tuple = st.selectbox(
        "🎨 " + ("Tema / Theme:" if lang == "es" else "Theme / Tema:"),
        options=theme_options,
        index=cur_theme_idx,
        format_func=lambda x: x[0],
        help="Selecciona la apariencia visual: Automático (Sistema), Claro u Oscuro." if lang == "es" else "Select visual theme: Automatic (System), Light or Dark."
    )
    if selected_theme_tuple[1] != st.session_state.get("app_theme", "auto"):
        st.session_state.app_theme = selected_theme_tuple[1]
        st.rerun()

    # 3. Preguntas Sugeridas (Visible por defecto en la parte superior)
    st.markdown(f"**💡 {t('quick_suggestions_title', lang)}**")
    example_list = t("example_queries", lang)
    st.selectbox(
        t("example_select_placeholder", lang),
        example_list,
        key="example_select_widget",
        on_change=load_example,
        label_visibility="collapsed",
        help=t("example_select_help", lang)
    )

    # 4. Nota Informativa de Cuotas de IA y Continuidad
    st.markdown(f"""<div class="quota-info-card">
<div class="quota-info-title">{t('quota_info_title', lang)}</div>
<div class="quota-info-body">{t('quota_info_desc', lang)}</div>
</div>""", unsafe_allow_html=True)

    st.write("---")

    # 5. EXPANDER: Información y Documentación del Proyecto (Colapsado)
    with st.expander(t("sidebar_docs_expander_title", lang), expanded=False):
        st.markdown(f"**{t('sidebar_project_title', lang)}**")
        st.markdown(t("sidebar_project_content", lang))
        st.write("---")
        st.markdown(f"**{t('sidebar_purpose_title', lang)}**")
        st.markdown(t("sidebar_purpose_content", lang))
        st.write("---")
        st.markdown(f"**{t('sidebar_sources_title', lang)}**")
        st.markdown(t("sidebar_sources_content", lang))
        st.write("---")
        st.markdown(f"**{t('sidebar_author_title', lang)}**")
        st.markdown(t("sidebar_author_content", lang))
        st.write("---")
        st.markdown(f"**{t('sidebar_version_title', lang)}**")
        st.markdown(f"""
**IJF SOR Assistant**

{t("sidebar_version_label", lang)}

{t("sidebar_based_on", lang)} **{engine.config['version_label']}**

{t("sidebar_source_hash", lang)} `{engine.config['source_sha256'][:16]}...`
        """)
        st.write("---")
        st.markdown(f"**{t('sidebar_guide_title', lang)}**")
        st.markdown(t("sidebar_guide_summary", lang))
        guide_pdf_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "docs", "guides", "IJF_SOR_Assistant_Guia_Usuario.pdf"
        )
        if os.path.exists(guide_pdf_path):
            try:
                with open(guide_pdf_path, "rb") as f_guide:
                    guide_bytes = f_guide.read()
                st.download_button(
                    label=t("sidebar_guide_download_btn", lang),
                    data=guide_bytes,
                    file_name="IJF_SOR_Assistant_Guia_Usuario.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e_guide:
                st.caption(f"Error cargando guía PDF: {e_guide}")
        st.markdown(f"**{t('sidebar_guide_quick_title', lang)}**")
        st.info(t("sidebar_guide_quick_content", lang))

    # 6. EXPANDER: Configuración del Asistente (IA) (Colapsado)
    with st.expander(t("sidebar_llm_expander_title", lang), expanded=False):
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

        p_info = provider_status["providers"].get(selected_prov, {})
        if p_info.get("available"):
            st.caption(t("key_active", lang, provider=selected_prov, masked_key=p_info.get('masked_key')))
        else:
            env_var_name = MultiProviderLLMManager.SUPPORTED_PROVIDERS[selected_prov]["env_key"]
            st.caption(t("key_missing", lang, env_var=env_var_name))

    # 7. EXPANDER: Historial de Consultas (Colapsado)
    if len(st.session_state.history) > 0:
        with st.expander(t("sidebar_history_expander_title", lang), expanded=False):
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

    # 8. EXPANDER: Grafo de Conocimiento (KG) (Colapsado)
    with st.expander(t("sidebar_kg_expander_title", lang), expanded=False):
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

    # 9. EXPANDER: Administración y Novedades (Colapsado)
    with st.expander(t("sidebar_admin_title", lang), expanded=False):
        if not is_admin_configured():
            st.warning(t("admin_not_configured", lang))
        else:
            if "admin_authenticated" not in st.session_state:
                st.session_state.admin_authenticated = False
            if "admin_token" not in st.session_state:
                st.session_state.admin_token = ""

            if not st.session_state.admin_authenticated:
                st.caption(t("admin_auth_caption", lang))
                with st.form(key="admin_login_form", clear_on_submit=False):
                    input_tok = st.text_input(
                        t("admin_token_label", lang),
                        type="password",
                        key="admin_token_input"
                    )
                    submit_tok = st.form_submit_button(t("admin_login_btn", lang), use_container_width=True)
                    if submit_tok:
                        if verify_admin_token(input_tok):
                            st.session_state.admin_authenticated = True
                            st.session_state.admin_token = input_tok.strip()
                            st.rerun()
                        else:
                            st.error(t("admin_auth_failed", lang))
            else:
                st.success("✓ Administrador autenticado")
                if st.button(t("admin_logout_btn", lang), key="admin_logout_btn_sidebar", use_container_width=True):
                    st.session_state.admin_authenticated = False
                    st.session_state.admin_token = ""
                    st.rerun()

                st.write("---")
                metrics = get_feedback_metrics(st.session_state.admin_token)
                if metrics.get("success"):
                    st.markdown(f"**{t('admin_metrics_title', lang)}**")
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric(t("admin_total_feedback", lang), metrics.get("total", 0))
                    with col_m2:
                        st.metric(t("admin_recent_feedback", lang), metrics.get("recent_7d", 0))

                csv_ok, csv_str, csv_err = export_observations_csv(st.session_state.admin_token)
                if csv_ok and csv_str:
                    st.download_button(
                        label=t("admin_export_csv_btn", lang),
                        data=csv_str.encode("utf-8-sig"),
                        file_name="ijf_sor_novedades_registro.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                st.write("---")
                tipo_choices = ["TODOS"] + TIPOS_NOVEDAD
                filter_tp = st.selectbox(
                    t("admin_filter_type", lang),
                    tipo_choices,
                    key="admin_filter_tipo_select"
                )
                search_kw = st.text_input(
                    t("admin_search_label", lang),
                    key="admin_search_input"
                )

                obs_resp = list_observations_protected(
                    admin_token=st.session_state.admin_token,
                    tipo_filter=filter_tp if filter_tp != "TODOS" else None,
                    search_term=search_kw.strip() if search_kw else None
                )

                if not obs_resp.get("success"):
                    st.error(obs_resp.get("message", "Error de acceso"))
                else:
                    items = obs_resp.get("data", [])
                    st.caption(f"{t('admin_total_feedback', lang)}: {len(items)}")
                    if not items:
                        st.info(t("admin_no_records", lang))
                    else:
                        for rec in items:
                            r_id = rec.get("observation_id", "")
                            r_tp = rec.get("reason", "General")
                            r_ts = rec.get("timestamp", "")[:10]
                            with st.expander(f"📌 {r_id} — [{r_tp}] ({r_ts})", expanded=False):
                                st.markdown(f"**{t('admin_table_date', lang)}:** {rec.get('timestamp')}")
                                st.markdown(f"**{t('admin_filter_type', lang)}** `{r_tp}`")
                                st.markdown(f"**{t('admin_table_query', lang)}:** {rec.get('context', {}).get('query', 'N/A')}")
                                st.markdown(f"**{t('admin_table_comment', lang)}:**\n> {rec.get('user_comment', 'N/A')}")
                                if rec.get('context', {}).get('response_summary'):
                                    st.markdown(f"**Respuesta:** {rec.get('context', {}).get('response_summary')[:300]}...")

                                att = rec.get("attachment")
                                if att and isinstance(att, dict) and att.get("relative_path"):
                                    fn = att.get("original_filename", "adjunto")
                                    sz_kb = round(att.get("size_bytes", 0) / 1024, 1)
                                    st.markdown(t("admin_attachment_available", lang, filename=fn, size_kb=sz_kb))
                                    ok_att, att_data, err_att = get_observation_attachment_bytes(
                                        admin_token=st.session_state.admin_token,
                                        relative_path=att["relative_path"]
                                    )
                                    if ok_att and att_data:
                                        st.download_button(
                                            label=t("admin_download_attachment_btn", lang),
                                            data=att_data,
                                            file_name=fn,
                                            key=f"dl_att_{r_id}",
                                            use_container_width=True
                                        )
                                    elif err_att:
                                        st.caption(f"⚠️ {err_att}")

    st.write("---")
    # Client-side Exclusive Accordion for Sidebar Expanders
    components.html("""
    <script>
    const doc = window.parent.document;
    function setupSidebarAccordion() {
        const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;
        const expanders = sidebar.querySelectorAll('details');
        expanders.forEach((targetExp) => {
            if (targetExp.dataset.hasAccordionListener) return;
            targetExp.dataset.hasAccordionListener = "true";
            targetExp.addEventListener('toggle', () => {
                if (targetExp.open) {
                    expanders.forEach((otherExp) => {
                        if (otherExp !== targetExp && otherExp.open) {
                            otherExp.removeAttribute('open');
                        }
                    });
                }
            });
        });
    }
    setupSidebarAccordion();
    setInterval(setupSidebarAccordion, 300);
    </script>
    """, height=0, width=0)



# Header
base64_logo = get_base64_logo(logo_path)
if base64_logo:
    render_custom_html(f"""<style>
.ijf-tooltip {{
    position: relative;
    display: inline-flex;
    align-items: center;
    cursor: default;
}}
.ijf-tooltip .ijf-tooltiptext {{
    visibility: hidden;
    background-color: var(--ijf-tooltip-bg);
    color: var(--ijf-tooltip-color);
    border: 1px solid var(--ijf-tooltip-border);
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
    background: var(--ijf-help-bg);
    border: 1px solid var(--ijf-title-color);
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    color: var(--ijf-title-color);
    font-weight: 700;
    margin-left: 0.5rem;
    font-family: 'Inter', sans-serif;
    flex-shrink: 0;
}}
</style>
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: var(--secondary-background-color); border-bottom: 2px solid var(--ijf-title-color); padding: 1.5rem 1rem; margin-top: 1.2rem; margin-bottom: 1.2rem; width: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-radius: 6px; position: relative; z-index: 99; text-align: center; gap: 0.8rem;">
    <div style="display: flex; align-items: center; justify-content: center;">
        <img src="data:image/svg+xml;base64,{base64_logo}" style="width: 80px; height: 80px; object-fit: contain; display: block;" />
    </div>
    <div style="position: relative; display: inline-block;">
        <h2 style="font-family: 'Outfit', sans-serif; color: var(--ijf-title-color); font-size: 2.8rem; margin: 0; font-weight: 700; line-height: 1.1;">{t('app_title', lang)}</h2>
        <div class="ijf-tooltip" style="position: absolute; right: -28px; top: 50%; transform: translateY(-50%);">
            <div class="ijf-help-icon" style="margin-left: 0;">?</div>
            <div class="ijf-tooltiptext" style="left: 50%; transform: translateX(-50%); top: 130%;">{t('header_tooltip', lang)}</div>
        </div>
    </div>
</div>""")
else:
    render_custom_html(f"""<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: var(--secondary-background-color); border-bottom: 2px solid var(--ijf-title-color); padding: 1.5rem 1rem; margin-top: 1.2rem; margin-bottom: 1.2rem; width: 100%; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); border-radius: 6px; text-align: center;">
    <h2 style="font-family: 'Outfit', sans-serif; color: var(--ijf-title-color); font-size: 2.8rem; margin: 0; font-weight: 700; line-height: 1.1;">{t('app_title', lang)}</h2>
</div>""")

# Handle user input
query_to_run = None

# Automatic execution from suggested query selection
if st.session_state.get("auto_run_query"):
    query_to_run = st.session_state.pop("auto_run_query").strip()

# Check if a suggestion was selected to prefill or run
default_input_val = ""
if st.session_state.get("prefill_query"):
    default_input_val = st.session_state.pop("prefill_query")

# Chat input for manual queries (any free inquiry permitted)
with st.container():
    with st.form(key="chat_form", clear_on_submit=True, border=False):
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            user_input = st.text_input(
                "Query input",
                value=default_input_val,
                placeholder=t("chat_input_placeholder", lang),
                label_visibility="collapsed"
            )
        with col2:
            submit_button = st.form_submit_button(t("send_btn", lang), use_container_width=True)

        if submit_button and user_input and not query_to_run:
            query_to_run = user_input.strip()


if query_to_run:
    with st.status(t("status_querying", lang), expanded=True) as status:
        rre_mode = getattr(engine.rre, 'operating_mode', 'HYBRID')
        if rre_mode == "HYBRID":
            status.write(t("status_rre_hybrid", lang))
        else:
            status.write(t("status_rre_degraded", lang, reason=getattr(engine.rre, 'degradation_reason', 'Model unavailable')))

        res = engine.query(query_to_run, language=lang)
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
                item_llm_meta = item.get("llm_meta", {})
                succ_prov = item_llm_meta.get("successful_provider")
                prim_prov = item_llm_meta.get("primary_provider", "")

                # 1. PREPARACIÓN DE DATOS (Estructura, Citas y Evidencias)
                struct = item.get("structured_answer")
                citations_list = []
                if struct and isinstance(struct, dict):
                    citations_list = struct.get("citations", [])

                clean_summary = ""
                if struct and isinstance(struct, dict) and struct.get("summary"):
                    raw_summary = struct["summary"]
                    clean_summary = struct.get("clean_summary") or clean_presentation_text(raw_summary)

                # Construir catálogo de evidencias normativas certificadas
                evidence_entries = []
                seen_evidence_keys = set()
                is_source_verified = bool(item.get("source_sha256_verified", False))

                if citations_list:
                    for c in citations_list:
                        if isinstance(c, dict):
                            pid = c.get("passage_id") or c.get("article_id")
                            if pid and pid in seen_evidence_keys:
                                continue
                            if pid:
                                seen_evidence_keys.add(pid)

                            raw_art = str(c.get("article_id") or c.get("title") or "Norma Oficial").strip()
                            clean_art = re.sub(r"^(?:art\.?\s*)+article\s*", "Art. ", raw_art, flags=re.IGNORECASE)
                            clean_art = re.sub(r"^article\s+", "Art. ", clean_art, flags=re.IGNORECASE)
                            art_label = clean_art
                            title = c.get("title") or art_label

                            raw_page = c.get("page_number") if c.get("page_number") is not None else c.get("page")
                            page_num = None
                            if raw_page is not None:
                                try:
                                    val = int(raw_page)
                                    if val > 0:
                                        page_num = val
                                except (ValueError, TypeError):
                                    page_num = None

                            exact_q = (c.get("exact_quote") or "").strip()
                            text_snip = (c.get("text_snippet") or "").strip()
                            has_exact = bool(exact_q)
                            raw_q = (c.get("quote") or "").strip()
                            if text_snip:
                                quote_str = text_snip
                                has_exact = True
                            elif exact_q:
                                quote_str = exact_q
                                has_exact = True
                            elif raw_q:
                                quote_str = raw_q
                                has_exact = False
                            else:
                                quote_str = ""
                                has_exact = False

                            source_url = c.get("source_url") or official_pdf_url
                            is_cit_verified = is_source_verified and bool(c.get("verified", True if is_source_verified else False))

                            evidence_entries.append({
                                "passage_id": pid or "",
                                "article_label": art_label,
                                "title": title,
                                "page_number": page_num,
                                "edition": "IJF SOR 2026-08",
                                "verified": is_cit_verified,
                                "quote": quote_str,
                                "has_exact_quote": has_exact,
                                "source_url": source_url,
                                "exact_quote": exact_q
                            })

                if len(evidence_entries) < 2 and item.get("trazabilidad"):
                    for kun in item["trazabilidad"]:
                        kid = kun.get("id_conocimiento")
                        if kid and kid in seen_evidence_keys:
                            continue
                        if kid:
                            seen_evidence_keys.add(kid)

                        art_num = kun.get("article_id") or kun.get("referencia_especifica", "").split("(")[0].strip()
                        raw_art = f"Art. {art_num}" if art_num and not str(art_num).lower().startswith("art") else (art_num or "Norma")
                        art_label = re.sub(r"^(?:art\.?\s*)+article\s*", "Art. ", raw_art, flags=re.IGNORECASE)
                        art_label = re.sub(r"^article\s+", "Art. ", art_label, flags=re.IGNORECASE)
                        title = kun.get("titulo") or "Disposición Oficial"

                        raw_page = kun.get("pdf_page_index") if kun.get("pdf_page_index") is not None else kun.get("page")
                        page_num = None
                        if raw_page is not None:
                            try:
                                val = int(raw_page)
                                if val > 0:
                                    page_num = val
                            except (ValueError, TypeError):
                                page_num = None

                        raw_quote = kun.get("contenido_traduccion") or kun.get("contenido_original") or ""
                        if len(raw_quote) > 280:
                            raw_quote = raw_quote[:277].rsplit(" ", 1)[0] + "..."

                        is_kun_verified = is_source_verified and bool(kun.get("verified", True if is_source_verified else False))
                        exact_q = (kun.get("exact_quote") or "").strip()
                        has_exact = bool(exact_q)
                        quote_str = exact_q if has_exact else raw_quote.strip()

                        evidence_entries.append({
                            "passage_id": kid or "",
                            "article_label": art_label,
                            "title": title,
                            "page_number": page_num,
                            "edition": "IJF SOR 2026-08",
                            "verified": is_kun_verified,
                            "quote": quote_str,
                            "has_exact_quote": has_exact,
                            "source_url": kun.get("source_url") or official_pdf_url,
                            "exact_quote": exact_q
                        })

                # Helper para renderizar cada tarjeta de evidencia con badges y enlace a visor PDF
                def _render_evidence_card(ev_item, orig_idx, card_idx):
                    badge_ver = f'<span class="evidence-badge-verified">✓ {t("evidence_verified_badge", lang)}</span>' if ev_item["verified"] else ''
                    p_label = t("evidence_page_label", lang)
                    badge_page = f'<span class="evidence-badge-page">📄 {p_label} {ev_item["page_number"]}</span>' if ev_item["page_number"] is not None else ''

                    quote_html = ''
                    if ev_item["quote"]:
                        escaped_q = html.escape(ev_item["quote"])
                        if ev_item.get("has_exact_quote"):
                            q_label = t("evidence_quote_label", lang)
                            quote_html = f'<div class="normative-quote-box"><div class="quote-type-label">📌 {q_label}</div>“{escaped_q}”</div>'
                        else:
                            ctx_label = t("evidence_context_label", lang)
                            quote_html = f'<div class="normative-context-box"><div class="quote-type-label">📖 {ctx_label}</div>{escaped_q}</div>'

                    st.markdown(f"""
<div class="normative-evidence-card">
    <div class="evidence-card-header">
        <span class="evidence-badge-art">📌 {html.escape(str(ev_item["article_label"]))}</span>
        {badge_page}
        {badge_ver}
    </div>
    <div class="evidence-card-title">{html.escape(str(ev_item["title"]))}</div>
    {quote_html}
</div>
""", unsafe_allow_html=True)

                    if ev_item["page_number"] is not None:
                        btn_col, _ = st.columns([0.48, 0.52])
                        with btn_col:
                            btn_label = t("evidence_view_pdf_btn", lang, page=ev_item["page_number"])
                            if st.button(f"🔍 {btn_label}", key=f"ev_pdf_{orig_idx}_{card_idx}", use_container_width=True):
                                st.session_state.pdf_page = int(ev_item["page_number"])
                                if ev_item.get("exact_quote"):
                                    st.session_state.pdf_quote = ev_item["exact_quote"]
                                st.session_state.pdf_article = str(ev_item["article_label"])
                                st.session_state.pdf_visible = True
                                st.rerun()

                # Aviso de Modo Alternativo Local o Conmutación de Cuota IA
                if not succ_prov:
                    st.markdown(f"""
<div class="local-fallback-banner">
    <div class="local-fallback-header">
        <span>{t('local_fallback_banner_title', lang)}</span>
    </div>
    <div class="local-fallback-desc">
        {t('local_fallback_banner_desc', lang)}
    </div>
</div>
""", unsafe_allow_html=True)
                elif item_llm_meta.get("fallback_triggered"):
                    st.caption(f"ℹ️ Cuota de {prim_prov} alcanzada. Respuesta generada automáticamente mediante {succ_prov}.")

                # 2. RESPUESTA DIRECTA (Nivel 1 - Visible por defecto)
                if clean_summary:
                    safe_summary = sanitize_presentation_html(clean_summary)
                    box_title = t("tier1_box_header", lang)
                    safe_title = html.escape(box_title)
                    st.markdown(
                        f"""<div class="tier1-box">
<div class="tier1-title"><strong>{safe_title}</strong></div>
{safe_summary}
</div>""",
                        unsafe_allow_html=True
                    )

                    if "Control de Rigor Normativo" in str(struct.get("limitations", "")) or "Normative Rigor Control" in str(struct.get("limitations", "")):
                        st.warning(t("normative_rigor_warning", lang))

                else:
                    # Compatibilidad con entradas planas
                    raw_ans = item.get('answer', '')
                    clean_ans = clean_presentation_text(raw_ans)
                    box_title = t("tier1_box_header", lang)
                    safe_title = html.escape(box_title)
                    if "\n\n---\n\n" in clean_ans:
                        parts = clean_ans.split("\n\n---\n\n", 1)
                        safe_part0 = sanitize_presentation_html(parts[0])
                        st.markdown(
                            f"""<div class="tier1-box">
<div class="tier1-title"><strong>{safe_title}</strong></div>
{safe_part0}
</div>""",
                            unsafe_allow_html=True
                        )
                        clean_summary = safe_part0
                    else:
                        safe_ans = sanitize_presentation_html(clean_ans)
                        st.markdown(
                            f"""<div class="tier1-box">
<div class="tier1-title"><strong>{safe_title}</strong></div>
{safe_ans}
</div>""",
                            unsafe_allow_html=True
                        )
                        clean_summary = safe_ans

                # 3. VER FUNDAMENTACIÓN NORMATIVA Y ANÁLISIS COMPLETO (Colapsado por defecto)
                has_details = False
                if struct and isinstance(struct, dict):
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
                elif "\n\n---\n\n" in item.get('answer', ''):
                    parts = item.get('answer', '').split("\n\n---\n\n", 1)
                    with st.expander(t("view_details_expander", lang), expanded=False):
                        st.markdown(parts[1])

                # 4. EVIDENCIAS NORMATIVAS CERTIFICADAS (Colapsado por defecto)
                if evidence_entries:
                    with st.expander(f"⚖️ {t('evidences_section_title', lang)}", expanded=False):
                        st.markdown(f"""
<div class="evidence-section-header">
    <span class="evidence-section-title">⚖️ {t('evidences_section_title', lang)}</span>
    <span class="evidence-badge-edition">IJF SOR 2026-08</span>
</div>
<div class="evidence-section-subtitle">{t('evidences_section_subtitle', lang)}</div>
""", unsafe_allow_html=True)
                        for ev_idx, ev in enumerate(evidence_entries):
                            _render_evidence_card(ev, original_i, ev_idx)

                # 5. PANEL DE AUDITORÍA TÉCNICA Y TRAZABILIDAD (Colapsado por defecto)
                is_fallback = "lo siento" in item.get('answer', '').lower() or "sorry" in item.get('answer', '').lower()
                with st.expander(t("expander_audit_metadata", lang), expanded=False):
                    audit_mode = item.get("rre_operating_mode", getattr(engine.rre, "operating_mode", "HYBRID"))
                    deg_reason = f" ({item.get('degradation_reason')})" if item.get('degradation_reason') else ""
                    audit_sha = t("pdf_source_caption", lang) if item.get("source_sha256_verified", False) else t("pdf_source_unverified_caption", lang)

                    prov_name = item_llm_meta.get("successful_provider") or ("Gemini" if is_connected else "Modo Local Desconectado")
                    model_name = item_llm_meta.get("successful_model") or ("gemini-2.5-flash" if is_connected else "Deterministic Brief")

                    st.markdown(f"""
<div class="audit-panel-grid">
    <div class="audit-panel-item">
        <div class="audit-panel-label">{t('audit_rre_title', lang)}</div>
        <div class="audit-panel-value">⚙️ {audit_mode}{deg_reason}</div>
    </div>
    <div class="audit-panel-item">
        <div class="audit-panel-label">{t('audit_sha_title', lang)}</div>
        <div class="audit-panel-value">🔒 {audit_sha}</div>
    </div>
    <div class="audit-panel-item">
        <div class="audit-panel-label">{t('audit_provider_title', lang)}</div>
        <div class="audit-panel-value">🤖 {prov_name} ({model_name})</div>
    </div>
</div>
""", unsafe_allow_html=True)

                    if item_llm_meta.get("fallback_triggered") and succ_prov:
                        st.info(t("fallback_badge_notice", lang, primary=prim_prov, secondary=succ_prov))
                    elif item_llm_meta.get("fallback_attempted") and not succ_prov:
                        st.warning(t("fallback_all_failed_notice", lang))

                    tab_cite, tab_graph = st.tabs([t("tab_traceability", lang), t("tab_graph", lang)])

                    with tab_cite:
                        with st.expander(t("sidebar_sources_title", lang), expanded=False):
                            st.markdown(t("source_availability_notice", lang), unsafe_allow_html=True)

                        if not is_fallback and item.get('trazabilidad'):
                            for kun in item['trazabilidad']:
                                res_rrm = _rrm_manager.resolve_reference(kun['id_conocimiento'], kun)
                                url = res_rrm.get("url")
                                is_clickable = res_rrm.get("is_clickable", True)
                                op_status = res_rrm.get("operational_status", "AVAILABLE")

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

                                st.markdown(f"**{kun['id_conocimiento']}: {kun['titulo']}** &nbsp; {badge_emoji} *{res_rrm.get('ux_message', '')}*")
                                st.markdown(f"* **{t('source_label', lang)}** {source_link}")
                                st.write(f"* {t('original_text_label', lang)} *\"{kun.get('contenido_original', kun['contenido_traduccion'])}\"*")
                                st.write(f"* {t('interpretation_label', lang)} {kun['interpretacion']}")
                                st.write("---")
                        else:
                            st.info(t("no_traceability_msg", lang))

                    with tab_graph:
                        if item.get('dot_code'):
                            st.graphviz_chart(item['dot_code'])
                        else:
                            st.info(t("no_graph_msg", lang))

                # 6. CANAL DE OBSERVACIONES Y FEEDBACK (RESALTADO DESTACADO)
                st.markdown(f"""
<div class="feedback-highlight-banner">
    <div class="feedback-highlight-badge">💬 {t('feedback_expander', lang)}</div>
    <div class="feedback-highlight-text">{t('feedback_caption', lang)}</div>
</div>
""", unsafe_allow_html=True)

                with st.expander(f"{t('feedback_expander', lang)} — Reportar novedad o sugerencia", expanded=False):
                    with st.form(key=f"feedback_form_{original_i}", clear_on_submit=True):
                        tipo_novedad_sel = st.selectbox(
                            t("feedback_type_label", lang),
                            options=TIPOS_NOVEDAD,
                            key=f"feedback_type_{original_i}"
                        )
                        comentario_user = st.text_area(
                            t("feedback_comment_label", lang),
                            placeholder=t("feedback_comment_placeholder", lang),
                            height=90,
                            key=f"feedback_comment_{original_i}"
                        )
                        uploaded_evidence = st.file_uploader(
                            t("feedback_attachment_label", lang),
                            type=["png", "jpg", "jpeg", "pdf"],
                            key=f"feedback_file_{original_i}"
                        )
                        submit_obs = st.form_submit_button(t("feedback_submit_btn", lang), use_container_width=True)

                        if submit_obs:
                            att_bytes = None
                            att_name = None
                            att_mime = None
                            if uploaded_evidence is not None:
                                att_bytes = uploaded_evidence.getvalue()
                                att_name = uploaded_evidence.name
                                att_mime = uploaded_evidence.type

                            res_obs = record_observation(
                                tipo_novedad=tipo_novedad_sel,
                                comentario=comentario_user,
                                query=item.get("query"),
                                response_summary=clean_summary or item.get("answer"),
                                citations=citations_list,
                                edition="2026-08 (Official)" if engine.is_2026_08 else "2026-01 (Historical)",
                                session_id=st.session_state.get("session_id", "session_anonymous"),
                                extra_metadata={
                                    "lang": lang,
                                    "ui_section": "response_card",
                                    "app_version": "1.2.0"
                                },
                                attachment_bytes=att_bytes,
                                attachment_filename=att_name,
                                attachment_mime=att_mime
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
                page_b64=page_b64_data,
                lang=lang
            )
else:
    render_custom_html(f"""<div style="text-align: center; margin-top: 1.6rem; margin-bottom: 1.2rem;">
    <h1 style="font-family: 'Outfit', sans-serif; color: var(--ijf-title-color); font-size: 2.05rem; font-weight: 700; line-height: 1.05; margin-bottom: 0.4rem; max-width: 28rem; margin-left: auto; margin-right: auto;">{t('welcome_title', lang)}</h1>
    <p style="font-size: 0.88rem; color: var(--ijf-subtitle-color); max-width: 640px; margin: 0 auto; line-height: 1.5; margin-bottom: 1rem; font-weight: 400;">{t('app_subtitle', lang)}</p>
</div>""")

st.write("---")
with st.expander(t("scope_expander_title", lang)):
    st.markdown(t("scope_certified_kuns", lang, count=kg_metrics['nodes_count']))
    col_cov, col_uncov = st.columns(2)
    with col_cov:
        st.markdown(f"{t('scope_covered_title', lang)}\n{t('scope_covered_body', lang)}")
    with col_uncov:
        st.markdown(f"{t('scope_uncovered_title', lang)}\n{t('scope_uncovered_body', lang)}")
