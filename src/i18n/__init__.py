"""
Internationalization (i18n) Module for IJF SOR Assistant
=========================================================
Provides seamless bilingual support (Spanish and English) with Spanish as the default.
Decouples visual UI labels, headers, buttons, placeholders, system status messages,
and tooltips from core business logic while preserving official IJF judo terminology.
"""

from typing import Dict, Any, List

DEFAULT_LANGUAGE = "es"

TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "en": {
        # App metadata & headers
        "app_title": "IJF SOR Assistant",
        "app_subtitle": "Your Official IJF Sport and Organisation Rules (SOR 2026) Advisory Assistant. Inquire about refereeing, contest rules, judogi control, weigh-in, medical protocols, and organization.",
        "welcome_title": "Welcome",
        "header_tooltip": "International Judo Federation Rules (SOR 2026)",
        
        # Sidebar sections
        "sidebar_info_title": "ℹ️ Information",
        "sidebar_project_title": "1. Project",
        "sidebar_project_content": (
            "**IJF SOR Assistant**\n\n"
            "The IJF SOR Assistant is a dedicated expert system engineered to facilitate the inquiry, "
            "interpretation, and understanding of the *Sport and Organisation Rules (SOR)* of the International Judo Federation (IJF).\n\n"
            "Its mission is to provide authoritative answers grounded strictly in certified official documentation, "
            "delivering rapid, precise, and structured access to the regulatory framework governing international judo refereeing and competition."
        ),
        "sidebar_purpose_title": "2. Purpose",
        "sidebar_purpose_content": (
            "This application was developed to support study, preparation, and authoritative reference "
            "for the official IJF regulations.\n\n"
            "The assistant structures and presents official provisions clearly, facilitating regulatory access for referees, coaches, "
            "athletes, and all members of the international judo community.\n\n"
            "All generated answers serve as technical and educational guidance. In any event of discrepancy, the official "
            "regulations published by the International Judo Federation and the decisions of its competent commissions always prevail."
        ),
        "sidebar_sources_title": "3. Official Sources",
        "sidebar_sources_content": (
            "This assistant operates exclusively on official publications of the International Judo Federation (IJF), "
            "including the Sport and Organisation Rules (SOR), refereeing guidelines, technical circulars, and official appendices."
        ),
        "sidebar_author_title": "4. Author",
        "sidebar_author_content": (
            "**Alexis Oliveros**\n\n"
            "National Judo Referee – Colombia\n\n"
            "2nd Dan\n\n"
            "Lead Developer of the **IJF SOR Assistant** project.\n\n"
            "© 2026 Alexis Oliveros. All rights reserved."
        ),
        "sidebar_version_title": "5. Version",
        "sidebar_version_label": "Version **1.2.0 (Rebuild Edition)**",
        "sidebar_based_on": "Based on:",
        "sidebar_source_hash": "Source SHA-256 hash:",
        
        # User Guide
        "sidebar_guide_title": "6. User Guide",
        "sidebar_guide_summary": (
            "**Official User Guide (SOR 2026 Edition)**\n\n"
            "Comprehensive manual covering interface navigation, query formulation, citation interpretation, "
            "PDF viewer interaction, and regulatory compliance guidelines for referees, coaches, and athletes."
        ),
        "sidebar_guide_download_btn": "📥 Download User Guide (PDF)",
        "sidebar_guide_quick_title": "📋 Quick Reference Guide",
        "sidebar_guide_quick_content": (
            "1. **Language:** Select *Español* or *English* at the top of the sidebar.\n"
            "2. **Querying:** Type your question or click one of the quick suggestions.\n"
            "3. **Citations:** Click blue citation badges to open the official PDF on the exact certified page.\n"
            "4. **Disclaimer:** The assistant provides technical guidance. Always contrast critical rulings with the official IJF SOR."
        ),
        
        # Regulatory Edition
        "edition_title": "📚 SOR Rule Edition",
        "edition_info": "**{version_label}**\n\nSole active and certified official edition authorized for international refereeing and competition.",
        
        # Model Configuration
        "model_config_title": "🤖 Model Configuration",
        "primary_provider_label": "Primary Provider:",
        "primary_provider_help": "Select the primary LLM provider to formulate analytical syntheses and arbitration briefs.",
        "model_label": "Model ({provider}):",
        "model_help": "Active inference model for provider {provider}.",
        "fallback_policy_label": "Fallback Policy:",
        "fallback_policy_help": "Automatic: switches transparently to alternate provider upon quota exhaustion (429) or connection failure. Manual: reports error without silent switch.",
        "fallback_opt_auto": "Automatic",
        "fallback_opt_manual": "Manual",
        "key_active": "🔑 {provider} Key: `{masked_key}` (Active)",
        "key_missing": "⚠️ Missing Key: Set `{env_var}` in `.env` or container environment.",
        
        # Search Settings
        "search_settings_title": "🧭 Search Settings",
        "k_slider_label": "Number of Rules to Inspect",
        "k_slider_help": "Defines how many certified official passages the assistant analyzes before formulating the response.",
        "min_score_label": "Relevance Gate Filter",
        "min_score_help": "Controls semantic and lexical relevance threshold. Higher values retain only strictly top-matching passages.",
        
        # Quick Suggestions & Example Questions
        "quick_suggestions_title": "💡 Quick Suggestions",
        "example_select_placeholder": "Choose an example query...",
        "example_select_help": "Select a representative scenario to inspect the assistant's normative reasoning.",
        "sample_queries_prompt": "Try one of these official queries",
        
        # History
        "history_title": "📚 Session History",
        "history_select_label": "Review query:",
        "history_select_help": "Instantly review prior inquiries and verified evidence from this session.",
        
        # Graph Governance
        "kg_title": "🥋 Knowledge Graph Governance",
        "badge_connected": "🟢 Connected Mode ({provider})",
        "badge_offline": "🟡 Offline Mode (Local)",
        "kg_modules_title": "📈 Knowledge Modules",
        "kg_total_kuns": "Total KUNs",
        "kg_relations": "Relationships",
        "kg_avg_degree": "Average Degree",
        "kg_hubs_title": "🕸️ Hub Nodes",
        "kg_links_suffix": "links",
        
        # Language Selector
        "lang_selector_label": "🌐 Language / Idioma:",
        
        # Chat input & actions
        "chat_input_placeholder": "Type your regulatory inquiry here...",
        "send_btn": "Submit 📤",
        
        # Query Status messages
        "status_querying": "Consulting official IJF SOR 2026...",
        "status_rre_hybrid": "🧠 Reasoning Retrieval Engine (RRE): Hybrid neural (384d) + lexical + RRF retrieval (SOR 2026-08)...",
        "status_rre_degraded": "⚠️ Reasoning Retrieval Engine (RRE): Operating in degraded lexical mode ({reason})...",
        "status_sha_verified": "🔐 Physical official SOR PDF SHA-256 cryptographically verified in this environment.",
        "status_sha_unverified": "ℹ️ Physical PDF not present for byte verification; declared cryptographic hash validated.",
        "status_ada_analyzing": "⚖️ Arbitration Decision Assistant (ADA): Analyzing {count} certified official evidence passage(s)...",
        "status_llm_synthesizing": "✍️ Formulating AI-assisted judicial synthesis...",
        "status_local_compiling": "📋 Compiling grounded normative brief with anchored PDF citations...",
        "status_done": "✅ Response generated",
        
        # Response Presentation (Tier 1 & 2)
        "tier1_box_header": "Official Direct Ruling:",
        "fallback_badge_notice": "🔄 *Automatic fallback activated: {primary} unavailable, response generated via {secondary}.*",
        "fallback_all_failed_notice": "ℹ️ *External generative providers unavailable. Displaying certified official normative evidence.*",
        "rre_mode_caption": "RRE Mode: {mode}",
        "pdf_source_caption": "Official PDF source: SHA-256 verified.",
        "pdf_source_unverified_caption": "Official PDF source: verified against declared canonical hash.",
        
        # Citation pills & interactive viewer
        "citations_title_label": "📌 Certified Official Citations (click to inspect in PDF viewer):",
        "normative_rigor_warning": "⚠️ **Normative Rigor Notice:** Discrepancies or evidentiary limitations detected regarding secondary aspects. Inspect Evidence Limitations section.",
        "view_details_expander": "📖 View full normative foundation and extended analysis",
        "sec_normative_basis": "📜 Applicable Articles and Regulatory Provisions",
        "sec_conditions": "⚖️ Conditions, Exceptions, and Restrictions",
        "sec_extended": "🔍 Extended Arbitration Analysis & Procedures",
        "sec_limitations": "⚠️ Evidence Boundaries and Limitations",
        
        # PDF Viewer
        "btn_hide_pdf": "📖 Hide PDF Viewer",
        "btn_show_pdf": "📖 Show PDF Viewer",
        "pdf_viewer_title": "📄 Official Viewer: {article} (Page {page})",
        "pdf_edition_badge": "IJF 14 Aug 2026",
        "pdf_prev_btn": "◀ Prev",
        "pdf_prev_title": "Previous page",
        "pdf_page_prefix": "Page",
        "pdf_next_btn": "Next ▶",
        "pdf_next_title": "Next page",
        "pdf_zoom_out_title": "Zoom out",
        "pdf_zoom_in_title": "Zoom in",
        "pdf_zoom_fit_btn": "Fit",
        "pdf_zoom_fit_title": "Fit width",
        "pdf_search_placeholder": "Search page text...",
        "pdf_highlight_btn": "🔍 Highlight",
        "pdf_badge_highlighted": "Citation highlighted",
        "pdf_badge_matches": "✓ {matches} match(es) highlighted",
        "pdf_open_tab_btn": "↗ Official tab",
        "pdf_open_tab_title": "Open in new browser tab with native viewer",
        "pdf_loading_text": "Loading official IJF SOR PDF (Streaming 29MB)...",
        "pdf_rendering_page": "Rendering page {num}...",
        "pdf_load_error": "⚠️ Error loading PDF in interactive viewer.<br><a href=\"{url}#page={num}\" target=\"_blank\" style=\"color: #60a5fa; text-decoration: underline;\">Click here to open directly in a new tab</a>",
        
        # Traceability & Graph tabs
        "expander_traceability": "🔍 Show Traceability & Knowledge Graph",
        "tab_traceability": "📚 Traceability & Citations",
        "tab_graph": "🕸️ Relational Subgraph",
        "source_availability_notice": (
            '<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">'
            'Visualization and links to external videos and documents depend on origin platform availability (e.g., YouTube or official IJF servers).<br><br>'
            'The Reference Resolution Manager (RRM) provides operational status and alternative references where applicable.<br><br>'
            '<strong>Legend:</strong> &nbsp; 🟢 <em>Available</em> &nbsp;&nbsp; 🟡 <em>Migrated</em> &nbsp;&nbsp; 🔵 <em>General Portal</em> &nbsp;&nbsp; 🔴 <em>Unavailable</em>'
            '</div>'
        ),
        "source_label": "Source:",
        "original_text_label": "Original:",
        "interpretation_label": "Interpretation:",
        "no_graph_msg": "No graph relationships available for this query.",
        "no_traceability_msg": "No legal traceability available for this query.",
        
        # Feedback channel
        "feedback_expander": "💬 Help us improve",
        "feedback_caption": "Did you spot an error, have a suggestion, or find an issue? Your report directly improves the assistant.",
        "feedback_comment_label": "Description, comments, or details",
        "feedback_comment_placeholder": "Share any observations, suggestions, or issues (free text)...",
        "feedback_attachment_label": "Attach evidence (optional: PNG, JPG, PDF - max 5 MB)",
        "feedback_submit_btn": "Submit Report 📨",
        "feedback_success": "✓ {message} *(Identifier: `{obs_id}`)*",
        "feedback_error": "⚠️ {message}",
        
        # Administrative management
        "sidebar_admin_title": "7. Observations Management",
        "admin_auth_header": "🔐 Restricted Access - Observations Admin",
        "admin_auth_caption": "Authorized administration module to review, track, and update user observations.",
        "admin_token_label": "Administrative Access Token",
        "admin_login_btn": "Authenticate",
        "admin_logout_btn": "Sign Out",
        "admin_not_configured": "Administrative access is currently disabled (no token configured on server).",
        "admin_auth_failed": "Authentication failed: invalid administrative token.",
        "admin_filter_status": "Filter by status:",
        "admin_search_label": "Search by ID, query, or comment:",
        "admin_refresh_btn": "Refresh",
        "admin_no_records": "No observations found matching the criteria.",
        "admin_table_id": "ID",
        "admin_table_date": "Date",
        "admin_table_status": "Status",
        "admin_table_query": "User Query",
        "admin_table_comment": "Description",
        "admin_detail_header": "Report Details: {obs_id}",
        "admin_status_update_label": "Change Status:",
        "admin_note_label": "Internal Tracking Note:",
        "admin_save_btn": "Update Report",
        "admin_update_success": "Report {obs_id} updated successfully.",
        "admin_attachment_available": "📎 Attachment: {filename} ({size_kb} KB)",
        "admin_download_attachment_btn": "Download Attachment",
        
        # Scope and coverage expander
        "scope_expander_title": "📝 Assistant Scope & Topic Coverage",
        "scope_certified_kuns": "The assistant features **{count} Certified Knowledge Units** extracted directly from official IJF sources.",
        "scope_covered_title": "#### ✅ In-Scope Certified Topics",
        "scope_covered_body": (
            "*   **📖 Refereeing Rules (Appendix D - 100%):** All articles (1 to 21), official gestures, scoring (Ippon, Waza-ari), Osaekomi, Mate, Kansetsu-waza, direct Hansoku-make, head diving, and concussion protocols.\n"
            "*   **🥋 Judogi Control (Appendix C - 100%):** Control procedure, approved dimensions, Sokuteiki tool, label placement, certified colors (Snow white & Pantone blue), and belt requirements.\n"
            "*   **⏱️ Competition Systems & Weigh-in (Sections 2, 3, 4):** Official weigh-in and random weigh-in, weight tolerances, repechage brackets, seeding, and draw procedures.\n"
            "*   **🏥 Medical Guidelines (Section 6):** On-tatami medical assistance, bleeding limits (2 treatments), head trauma, and mandatory suspension periods.\n"
            "*   **🎖️ Protocol & Ceremonies (Section 8):** Medal ceremonies, flag raising, national anthems, and official dress codes."
        ),
        "scope_uncovered_title": "#### ❌ Out-of-Scope (Not Covered)",
        "scope_uncovered_body": (
            "*   **🏫 Coach Education (Section 5):** Coach chair dress codes, technical accreditations, and yellow/red coach card disciplinary processes.\n"
            "*   **📢 Marketing & Broadcast (Section 10):** Commercial sponsorship contracts, broadcast rights, and arena banner specifications.\n"
            "*   **🏟️ Venue Infrastructure (Section 11):** Arena layout, VIP lounges, warm-up room lighting, and stadium air conditioning standards.\n"
            "*   **📋 Statutes & Ethics (Appendices A, B):** Internal IJF governance, executive elections, Disciplinary Code, and Court of Arbitration appeals.\n"
            "*   **🧬 Special Categories (Appendices E, F, G, H):** Gender transition rules, laboratory anti-doping protocols, Veterans/Masters modified rules, and Kata competition refereeing."
        ),
        
        # Predefined examples (bilingual list)
        "example_queries": [
            "Choose an example query...",
            "What is the penalty for head diving in the cadet category?",
            "What are the official dimensions of the tatami contest area?",
            "How many medical interventions are permitted per contest for bleeding?",
            "What is Smart Judogi NFC chip technology?",
            "How is a bear hug penalised under IJF rules?",
            "How is reverse seoi-nage penalised in the cadet category?",
            "What happens if an athlete loses consciousness from shime-waza?",
            "What is the Sokuteiki and how is it used?",
            "What are the official Judogi colour rules (white and blue)?",
            "How does the head trauma / concussion protocol work and how many days of suspension apply?",
            "What is the tolerance time to present on the tatami before disqualification (Kiken-gachi)?",
            "What are the weight tolerance differences between official and random weigh-in?",
            "How do repechage competition brackets divide athletes in the official system?",
            "What is the official dress code for team doctors on the field of play?",
            "Is finger taping allowed and how must it be approved?"
        ],
        
        # Chip suggestions
        "chips": [
            ("Head diving rule", "What is the penalty for head diving in the cadet category?"),
            ("Tatami dimensions", "What are the official dimensions of the tatami contest area?"),
            ("Medical interventions", "How many medical interventions are permitted per contest?"),
            ("Sokuteiki usage", "What is the Sokuteiki and how is it used?"),
            ("Reverse seoi-nage", "How is reverse seoi-nage penalised in the cadet category?"),
            ("Judogi colour rules", "What are the official Judogi colour rules?"),
        ]
    },
    "es": {
        # App metadata & headers
        "app_title": "Asistente SOR IJF",
        "app_subtitle": "Tu consultor del Reglamento de Organización y Deporte (SOR 2026). Pregúntame sobre arbitraje, uniformes, pesaje o asistencia médica.",
        "welcome_title": "Bienvenido",
        "header_tooltip": "Reglamento de la Federación Internacional de Judo (SOR 2026)",
        
        # Sidebar sections
        "sidebar_info_title": "ℹ️ Información",
        "sidebar_project_title": "1. Proyecto",
        "sidebar_project_content": (
            "**IJF SOR Assistant**\n\n"
            "El IJF SOR Assistant es un asistente especializado diseñado para facilitar la consulta y comprensión del *Sport and Organisation Rules (SOR)* de la Federación Internacional de Judo (IJF).\n\n"
            "Su propósito es ofrecer respuestas fundamentadas exclusivamente en documentación oficial, permitiendo acceder de manera rápida y organizada a la información normativa utilizada en el arbitraje y la competición internacional."
        ),
        "sidebar_purpose_title": "2. Propósito",
        "sidebar_purpose_content": (
            "Esta aplicación fue desarrollada con el objetivo de apoyar el estudio, la preparación y la consulta del reglamento oficial de la IJF.\n\n"
            "El asistente organiza y presenta la información oficial de forma clara, facilitando el acceso al contenido normativo para árbitros, entrenadores, deportistas y demás miembros de la comunidad del judo.\n\n"
            "Las respuestas generadas constituyen una ayuda documental y educativa. En caso de discrepancia o interpretación, siempre prevalecen los documentos oficiales publicados por la Federación Internacional de Judo y las decisiones adoptadas por sus órganos competentes."
        ),
        "sidebar_sources_title": "3. Fuentes Oficiales",
        "sidebar_sources_content": (
            "Este asistente utiliza exclusivamente fuentes oficiales publicadas por la Federación Internacional de Judo (IJF), incluyendo reglamentos, documentos técnicos, comunicados y otros recursos oficiales."
        ),
        "sidebar_author_title": "4. Autor",
        "sidebar_author_content": (
            "**Alexis Oliveros**\n\n"
            "National Judo Referee – Colombia\n\n"
            "2nd Dan\n\n"
            "Desarrollador del proyecto **IJF SOR Assistant**.\n\n"
            "© 2026 Alexis Oliveros. Todos los derechos reservados."
        ),
        "sidebar_version_title": "5. Versión",
        "sidebar_version_label": "Versión **1.2.0 (Rebuild Edition)**",
        "sidebar_based_on": "Basado en:",
        "sidebar_source_hash": "Hash SHA-256 de fuente:",
        
        # User Guide
        "sidebar_guide_title": "6. Guía de Usuario",
        "sidebar_guide_summary": (
            "**Guía Oficial de Usuario (Edición SOR 2026)**\n\n"
            "Manual técnico integral sobre navegación de la interfaz, formulación de consultas normativas, "
            "interpretación de citas y trazabilidad, interacción con el visor PDF y pautas de cotejo reglamentario para árbitros, entrenadores y competidores."
        ),
        "sidebar_guide_download_btn": "📥 Descargar Guía de Usuario (PDF)",
        "sidebar_guide_quick_title": "📋 Guía Rápida de Referencia",
        "sidebar_guide_quick_content": (
            "1. **Idioma:** Seleccione *Español* o *English* en la parte superior de la barra lateral.\n"
            "2. **Consulta:** Escriba su consulta técnica o seleccione una de las sugerencias predefinidas.\n"
            "3. **Citas y Visor:** Haga clic en las píldoras de cita para abrir el visor interactivo en la página exacta oficial.\n"
            "4. **Cotejo Obligatorio:** El asistente ofrece orientación técnica. Ante fallos arbitrales o controversias, contraste siempre la decisión con el texto oficial del IJF SOR."
        ),
        
        # Regulatory Edition
        "edition_title": "📚 Edición del Reglamento SOR",
        "edition_info": "**{version_label}**\n\nEdición oficial única y vigente autorizada para arbitraje y competición.",
        
        # Model Configuration
        "model_config_title": "🤖 Configuración del modelo",
        "primary_provider_label": "Proveedor Principal:",
        "primary_provider_help": "Selecciona el proveedor de LLM principal para generar las respuestas analíticas y síntesis arbitrales.",
        "model_label": "Modelo ({provider}):",
        "model_help": "Modelo de inferencia activo para el proveedor {provider}.",
        "fallback_policy_label": "Política de Respaldo:",
        "fallback_policy_help": "Automático: conmuta al proveedor alternativo ante agotamiento de cuota (429) o fallos de conexión. Manual: informa del error sin cambio silencioso.",
        "fallback_opt_auto": "Automático",
        "fallback_opt_manual": "Manual",
        "key_active": "🔑 Clave {provider}: `{masked_key}` (Activa)",
        "key_missing": "⚠️ Clave ausente: Defina `{env_var}` en `.env` o en el entorno.",
        
        # Search Settings
        "search_settings_title": "🧭 Ajustes de Búsqueda",
        "k_slider_label": "Cantidad de Reglas a Consultar",
        "k_slider_help": "Define cuántas reglas oficiales revisará el asistente antes de elaborar la respuesta.",
        "min_score_label": "Filtro Anti-Distracciones",
        "min_score_help": "Controla qué tan relacionadas deben estar las reglas encontradas con tu consulta.",
        
        # Quick Suggestions & Example Questions
        "quick_suggestions_title": "💡 Sugerencias Rápidas",
        "example_select_placeholder": "Elige una pregunta para consultar...",
        "example_select_help": "Elige una pregunta predefinida para ver cómo responde el asistente.",
        "sample_queries_prompt": "Prueba con alguna de estas consultas",
        
        # History
        "history_title": "📚 Historial",
        "history_select_label": "Revisar consulta:",
        "history_select_help": "Te permite volver a ver cualquiera de las consultas realizadas anteriormente en esta sesión de forma instantánea.",
        
        # Graph Governance
        "kg_title": "🥋 Gobernanza del Grafo",
        "badge_connected": "🟢 Modo Conectado ({provider})",
        "badge_offline": "🟡 Modo Offline (Local)",
        "kg_modules_title": "📈 Módulos de Conocimiento",
        "kg_total_kuns": "Total KUNs",
        "kg_relations": "Relaciones",
        "kg_avg_degree": "Grado Promedio",
        "kg_hubs_title": "🕸️ Nodos Hub",
        "kg_links_suffix": "enlaces",
        
        # Language Selector
        "lang_selector_label": "🌐 Idioma / Language:",
        
        # Chat input & actions
        "chat_input_placeholder": "Escribe tu pregunta aquí...",
        "send_btn": "Enviar 📤",
        
        # Query Status messages
        "status_querying": "Consultando el Reglamento SOR 2026...",
        "status_rre_hybrid": "🧠 Reasoning Retrieval Engine (RRE): Recuperación híbrida neuronal (384d) + léxica + RRF (SOR 2026-08)...",
        "status_rre_degraded": "⚠️ Reasoning Retrieval Engine (RRE): Operando en modo degradado léxico ({reason})...",
        "status_sha_verified": "🔐 SHA-256 del PDF oficial físico verificado en este entorno.",
        "status_sha_unverified": "ℹ️ El PDF físico no está disponible para verificar sus bytes en este entorno; solo se validó el hash declarado.",
        "status_ada_analyzing": "⚖️ Arbitration Decision Assistant (ADA): {count} evidencia(s) oficial(es) analizada(s)...",
        "status_llm_synthesizing": "✍️ Formulando síntesis analítica asistida por IA...",
        "status_local_compiling": "📋 Compilando resumen de evidencias normativas con enlaces anclados...",
        "status_done": "✅ Respuesta generada",
        
        # Response Presentation (Tier 1 & 2)
        "tier1_box_header": "Respuesta Directa Oficial:",
        "fallback_badge_notice": "🔄 *Respaldo automático activado: {primary} no disponible, respuesta generada con {secondary}.*",
        "fallback_all_failed_notice": "ℹ️ *No se pudo conectar con los proveedores generativos externos. Mostrando evidencias normativas oficiales recuperadas.*",
        "rre_mode_caption": "Modo RRE: {mode}",
        "pdf_source_caption": "Fuente física PDF: SHA-256 verificado.",
        "pdf_source_unverified_caption": "Fuente física PDF: no verificada en este entorno; no se presume comprobación de sus bytes.",
        
        # Citation pills & interactive viewer
        "citations_title_label": "📌 Citas Oficiales Verificadas (clic para examinar en visor PDF):",
        "normative_rigor_warning": "⚠️ **Aviso de Rigor Normativo:** Se han detectado discrepancias probatorias o limitaciones en la evidencia que afectan aspectos complementarios de esta consulta. Consulte la sección de Límites de la Evidencia.",
        "view_details_expander": "📖 Ver fundamentación normativa y análisis completo",
        "sec_normative_basis": "📜 Preceptos y Artículos Aplicables",
        "sec_conditions": "⚖️ Condiciones, Excepciones y Restricciones",
        "sec_extended": "🔍 Análisis Arbitral Ampliado",
        "sec_limitations": "⚠️ Límites de la Evidencia",
        
        # PDF Viewer
        "btn_hide_pdf": "📖 Ocultar Visor PDF",
        "btn_show_pdf": "📖 Mostrar Visor PDF",
        "pdf_viewer_title": "📄 Visor Oficial: {article} (Pág. {page})",
        "pdf_edition_badge": "IJF 14 Ago 2026",
        "pdf_prev_btn": "◀ Ant",
        "pdf_prev_title": "Página anterior",
        "pdf_page_prefix": "Pág.",
        "pdf_next_btn": "Sig ▶",
        "pdf_next_title": "Página siguiente",
        "pdf_zoom_out_title": "Reducir zoom",
        "pdf_zoom_in_title": "Aumentar zoom",
        "pdf_zoom_fit_btn": "Ajustar",
        "pdf_zoom_fit_title": "Ajustar ancho",
        "pdf_search_placeholder": "Buscar texto en pág...",
        "pdf_highlight_btn": "🔍 Resaltar",
        "pdf_badge_highlighted": "Cita resaltada",
        "pdf_badge_matches": "✓ {matches} fragmento(s) resaltado(s)",
        "pdf_open_tab_btn": "↗ Pestaña oficial",
        "pdf_open_tab_title": "Abrir en pestaña nueva con visor nativo",
        "pdf_loading_text": "Cargando PDF oficial IJF SOR (Streaming 29MB)...",
        "pdf_rendering_page": "Renderizando página {num}...",
        "pdf_load_error": "⚠️ Error al cargar PDF en el visor interactivo.<br><a href=\"{url}#page={num}\" target=\"_blank\" style=\"color: #60a5fa; text-decoration: underline;\">Haga clic aquí para abrirlo directamente en nueva pestaña</a>",
        
        # Traceability & Graph tabs
        "expander_traceability": "🔍 Mostrar Trazabilidad y Grafo",
        "tab_traceability": "📚 Trazabilidad y Citas",
        "tab_graph": "🕸️ Subgrafo Relacional",
        "source_availability_notice": (
            '<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">'
            'La visualización y navegación hacia videos, documentos y otros recursos oficiales depende de las características técnicas y de la disponibilidad de las plataformas de origen (por ejemplo, YouTube o los portales oficiales de la IJF).<br><br>'
            'Cuando esto ocurra, el Reference Resolution Manager (RRM) informará el estado de la referencia y presentará una alternativa cuando exista.<br><br>'
            '<strong>Leyenda:</strong> &nbsp; 🟢 <em>Disponible</em> &nbsp;&nbsp; 🟡 <em>Migrada</em> &nbsp;&nbsp; 🔵 <em>Portal General</em> &nbsp;&nbsp; 🔴 <em>No Disponible</em>'
            '</div>'
        ),
        "source_label": "Fuente:",
        "original_text_label": "Original:",
        "interpretation_label": "Interpretación:",
        "no_graph_msg": "No hay relaciones de grafo disponibles para esta consulta.",
        "no_traceability_msg": "No hay trazabilidad legal disponible para esta consulta.",
        
        # Feedback channel
        "feedback_expander": "💬 Ayúdanos a mejorar",
        "feedback_caption": "¿Has identificado algo que debamos revisar, una sugerencia o un inconveniente? Tu reporte nos ayuda a perfeccionar el asistente.",
        "feedback_comment_label": "Descripción, comentario u observación",
        "feedback_comment_placeholder": "Comparte cualquier detalle, sugerencia o inconveniente (texto libre)...",
        "feedback_attachment_label": "Adjuntar evidencia (opcional: PNG, JPG, PDF - máx 5 MB)",
        "feedback_submit_btn": "Enviar reporte 📨",
        "feedback_success": "✓ {message} *(Identificador: `{obs_id}`)*",
        "feedback_error": "⚠️ {message}",
        
        # Administrative management
        "sidebar_admin_title": "7. Administración de Novedades",
        "admin_auth_header": "🔐 Acceso Restringido — Administración de Novedades",
        "admin_auth_caption": "Módulo administrativo autorizado para revisar, dar seguimiento y gestionar observaciones técnicas.",
        "admin_token_label": "Token de Acceso Administrativo",
        "admin_login_btn": "Autenticar",
        "admin_logout_btn": "Cerrar sesión",
        "admin_not_configured": "El acceso administrativo se encuentra deshabilitado (no hay token configurado en el servidor).",
        "admin_auth_failed": "Autenticación fallida: el token administrativo no es válido.",
        "admin_filter_status": "Filtrar por estado:",
        "admin_search_label": "Buscar por ID, consulta o comentario:",
        "admin_refresh_btn": "Actualizar lista",
        "admin_no_records": "No se encontraron novedades con los criterios seleccionados.",
        "admin_table_id": "ID",
        "admin_table_date": "Fecha",
        "admin_table_status": "Estado",
        "admin_table_query": "Consulta del usuario",
        "admin_table_comment": "Descripción",
        "admin_detail_header": "Detalle del Reporte: {obs_id}",
        "admin_status_update_label": "Cambiar Estado:",
        "admin_note_label": "Nota Interna de Seguimiento:",
        "admin_save_btn": "Actualizar Reporte",
        "admin_update_success": "Reporte {obs_id} actualizado con éxito.",
        "admin_attachment_available": "📎 Evidencia adjunta: {filename} ({size_kb} KB)",
        "admin_download_attachment_btn": "Descargar Adjunto",
        
        # Scope and coverage expander
        "scope_expander_title": "📝 Alcance del Asistente & Cobertura de Temas",
        "scope_certified_kuns": "El asistente cuenta con **{count} Unidades de Conocimiento certificadas** extraídas de las fuentes oficiales de la IJF.",
        "scope_covered_title": "#### ✅ Temas Cubiertos",
        "scope_covered_body": (
            "*   **📖 Reglas de Arbitraje (Apéndice D - 100%):** Todos los artículos (1 al 21), gestos oficiales, puntuaciones, Osaekomi, Mate, luxaciones, descalificaciones directas (Hansoku-make) y conmoción cerebral.\n"
            "*   **🥋 Control de Judogi (Apéndice C - 100%):** Proceso de control, medidas permitidas, Sokuteiki, colocación de logotipos, colores (blanco/azul) e indumentaria.\n"
            "*   **⏱️ Sistemas y Pesaje (Secciones 2, 3, 4):** Pesaje oficial y sorteo aleatorio, tolerancias, llaves de competencia con repechaje, siembra de cabezas de serie y gestión de categorías.\n"
            "*   **🏥 Manual Médico (Sección 6):** Asistencia médica en tatami, límite de 2 atenciones para lesiones con sangrado, conmociones y días de inhabilitación.\n"
            "*   **🎖️ Protocolos de Premiación (Sección 8):** Ceremonias de medallas, izado de banderas, himnos nacionales y código de vestimenta oficial."
        ),
        "scope_uncovered_title": "#### ❌ Fuera de Alcance (No Cubiertos)",
        "scope_uncovered_body": (
            "*   **🏫 Educación y Coaches (Sección 5):** Códigos de vestimenta para entrenadores en la silla, acreditaciones técnicas y penalización de tarjetas en la silla de coach.\n"
            "*   **📢 Marketing y Difusión (Sección 10):** Contratos de patrocinadores oficiales de la IJF, derechos de transmisión de televisión y publicidad permitida en los banners.\n"
            "*   **🏟️ Infraestructura del Recinto (Sección 11):** Disposición física del pabellón, áreas VIP, vestuarios, requisitos de iluminación y climatización de la arena.\n"
            "*   **📋 Estatutos y Apelaciones (Apéndices A, B):** Normas internas de la IJF, elecciones directivas, el Código Disciplinario y procesos de apelación federativos.\n"
            "*   **🧬 Transición y Categorías Especiales (Apéndices E, F, G, H):** Reglamentos de transición de género, control antidopaje de laboratorio, reglas modificadas para veteranos/masters y arbitraje de competencias de Kata."
        ),
        
        # Predefined examples (bilingual list)
        "example_queries": [
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
        ],
        
        # Chip suggestions
        "chips": [
            ("Defensa con la cabeza", "¿Se permite la defensa con la cabeza?"),
            ("Dimensiones del tatami", "¿Cuáles son las dimensiones del tatami?"),
            ("Intervenciones médicas", "¿Cuántas intervenciones médicas se permiten por combate?"),
            ("Sokuteiki y su uso", "¿Qué es el Sokuteiki y cómo se usa?"),
            ("Reverse seoi-nage", "¿Cómo se sanciona el reverse seoi-nage en cadetes?"),
            ("Color de Judogi", "¿Cuáles son las reglas de color de Judogi?"),
        ]
    }
}


def t(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> Any:
    """
    Returns the localized string or object for the requested key.
    Defaults to English ('en') if key or language is not found.
    Interpolates kwargs if value is a string.
    """
    catalog = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    val = catalog.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    if isinstance(val, str) and kwargs:
        return val.format(**kwargs)
    return val
