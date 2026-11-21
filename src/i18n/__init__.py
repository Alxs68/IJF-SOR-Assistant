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
        "app_subtitle": "Official IJF Sport and Organisation Rules (SOR 2026) consultant. Certified responses, normative reasoning, and complete document traceability.",
        "welcome_title": "Welcome",
        "header_tooltip": "International Judo Federation Rules (SOR 2026)",
        
        # Sidebar sections
        "sidebar_info_title": "ℹ️ Information",
        # How to use the assistant (sidebar audit 2026-11-21)
        "sidebar_howto_title": "📘 How to use the assistant",
        "sidebar_howto_ask_title": "How to ask",
        "sidebar_howto_ask_content": (
            "Type your question in natural language, in Spanish or English, and press <b>Submit</b>. "
            "Specific questions (a situation, a category or an article) get more precise answers. "
            "If your question has several parts, ask them separately. "
            "You can also press <b>🎤 Dictate</b> and speak: the text is added to the field so you can review it before submitting. "
            "Speech recognition is done by your browser (depending on the browser, through an online service of its provider); "
            "the application does not record or store audio."
        ),
        "sidebar_howto_read_title": "How to read the answer",
        "sidebar_howto_read_content": (
            "The answer is based only on the official IJF SOR rules and is checked against the official text before "
            "it is shown. It gives the answer, the applicable rule and, where relevant, the conditions and exceptions. "
            "Click a citation <b>📍 Art. · Page</b> or a <b>📄 Page</b> link to open the official PDF on that page."
        ),
        "sidebar_howto_abstain_title": "When it does not answer",
        "sidebar_howto_abstain_content": (
            "If the rules do not contain enough information or the answer cannot be checked against the official text, "
            "the assistant <b>abstains</b> and says so instead of guessing. When available, the passages it consulted "
            "remain available for reference."
        ),
        "sidebar_howto_history_title": "History and reports",
        "sidebar_howto_history_content": (
            "In <b>Query history</b> you can return to the questions of this session. If you spot an error, use "
            "<b>Help us improve</b>, below the answer."
        ),
        "sidebar_howto_notice_title": "Important",
        "sidebar_howto_notice_content": (
            "The assistant is a study and reference aid. In a refereeing decision or a dispute, the official SOR text "
            "and the decisions of the competent IJF bodies always prevail."
        ),
        # About the assistant
        "sidebar_about_title": "ℹ️ About the assistant",
        "sidebar_about_project_title": "Project and purpose",
        "sidebar_about_project_content": (
            "<b>IJF SOR Assistant</b> helps referees, coaches, athletes and the wider judo community consult the "
            "<i>Sport and Organisation Rules</i> (SOR) of the International Judo Federation, with answers grounded in "
            "the official text and linked to its page."
        ),
        "sidebar_rules_edition": "official edition of 14 August 2026",
        "sidebar_sources_title": "Official sources",
        "sidebar_sources_content": (
            "Answers are based exclusively on the IJF SOR, {edition}. Some answers include complementary links to "
            "official IJF resources (rules portal, refereeing videos, news releases). They are reference material and "
            "do not replace the SOR."
        ),
        "sidebar_author_title": "Author",
        "sidebar_author_content": (
            "**Alexis Oliveros**\n\n"
            "National Judo Referee – Colombia\n\n"
            "2nd Dan\n\n"
            "Lead Developer of the **IJF SOR Assistant** project.\n\n"
            "© 2026 Alexis Oliveros. All rights reserved."
        ),
        "sidebar_version_title": "Version",
        "sidebar_version_rules": "Rules: IJF SOR, {edition}",
        "sidebar_source_hash": "Official PDF fingerprint (SHA-256):",
        "sidebar_version_label": "Version {version} · updated on 2026-11-21",
        "sidebar_guide_btn": "📥 User guide (PDF, in Spanish)",
        "sidebar_guide_help": "Download the user guide for version {version}: how to ask, dictate, read the answer and check it in the official PDF.",
        # Voice input (browser Web Speech API)
        "voice_btn_start": "🎤 Dictate",
        "voice_btn_stop": "Stop",
        "voice_btn_title": "Dictate your question with the microphone. The text is added to the query field so you can review it before submitting.",
        "voice_state_requesting": "Requesting microphone access…",
        "voice_state_listening": "Listening…",
        "voice_state_processing": "Processing the transcription…",
        "voice_state_ready": "Text added to your question. Review it and press Submit.",
        "voice_state_nospeech": "No speech detected. Press 🎤 Dictate to try again.",
        "voice_state_lang_changed": "Dictation stopped by a language or theme change. Press 🎤 Dictate to continue.",
        "voice_err_denied": "Microphone permission denied. Allow it in your browser or type your question.",
        "voice_err_nomic": "No microphone available. You can type your question.",
        "voice_err_unsupported": "This browser does not support dictation. You can type your question.",
        "voice_err_insecure": "Dictation requires a secure connection (HTTPS). You can type your question.",
        "voice_err_network": "The browser's speech service is unavailable. Try again later or type your question.",
        "voice_err_generic": "Dictation could not be completed. Try again or type your question.",
        "voice_err_noinput": "The query field was not found. Reload the page.",
        # Service availability (replaces the quota card)
        "availability_title": "🛡️ Service availability",
        "availability_desc": (
            "The assistant drafts and checks answers with an AI service. If that service is temporarily unavailable, "
            "the assistant does not produce unchecked answers: it will say so and you can try again later."
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
        "chat_input_placeholder": "Type your IJF SOR rules inquiry here...",
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
        "evidences_section_title": "Certified Normative Evidence",
        "evidences_section_subtitle": "Primary regulatory provisions and verified official citations from the IJF SOR",
        "evidence_article_label": "Article / Rule",
        "evidence_page_label": "Page",
        "evidence_edition_label": "Edition",
        "evidence_verified_badge": "Official (SHA-256 Verified)",
        "evidence_quote_label": "Official Textual Citation:",
        "evidence_context_label": "Contextual Regulatory Excerpt:",
        "evidence_view_pdf_btn": "Inspect in PDF (P. {page})",
        "evidence_more_expander": "View additional complementary evidence ({count})",
        "expander_audit_metadata": "🛠️ Technical Traceability & Engine Audit",
        "audit_rre_title": "Retrieval Engine (RRE)",
        "audit_sha_title": "Cryptographic Hash Validation",
        "audit_provider_title": "Generative Provider",
        "audit_chunks_title": "Retrieved Canonical Chunks",
        "normative_rigor_warning": "⚠️ **Normative Rigor Notice:** Discrepancies or evidentiary limitations detected regarding secondary aspects. Inspect Evidence Limitations section.",
        "view_details_expander": "🔍 Expand answer with detailed analysis and article relationships",
        "sec_graph_relations": "🕸️ Regulatory Article Relationships & Graph",
        "graph_caption_relations": "Map of normative dependencies and relationships between applicable articles:",
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
        "feedback_type_label": "Type of observation or feedback",
        "feedback_type_options": [
            "Posible error o inconsistencia normativa",
            "Consulta no resuelta satisfactoriamente",
            "Aclaración o comentario",
            "Sugerencia de mejora",
            "Solicitud de nueva funcionalidad",
            "Observación de funcionamiento",
            "Otro"
        ],
        "feedback_comment_label": "Description, comments, or details",
        "feedback_comment_placeholder": "Share any observations, suggestions, or issues (free text)...",
        "feedback_attachment_label": "Attach evidence (optional: PNG, JPG, PDF - max 5 MB)",
        "feedback_submit_btn": "Submit Report 📨",
        "feedback_success": "✓ {message} *(Identifier: `{obs_id}`)*",
        "feedback_error": "⚠️ {message}",
        
        # Administrative management
        "sidebar_admin_title": "🔒 Administration (restricted access)",
        "admin_auth_header": "🔐 Restricted Access - Observations Admin",
        "admin_auth_caption": "Authorized administration module to review, track, and update user observations.",
        "admin_token_label": "Administrative Access Token",
        "admin_login_btn": "Authenticate",
        "admin_logout_btn": "Sign Out",
        "admin_not_configured": "Administrative access is currently disabled (no token configured on server).",
        "admin_auth_failed": "Authentication failed: invalid administrative token.",
        "admin_filter_status": "Filter by status:",
        "admin_filter_type": "Filter by type:",
        "admin_search_label": "Search by ID, query, or comment:",
        "admin_refresh_btn": "Refresh",
        "admin_no_records": "No observations found matching the criteria.",
        "admin_metrics_title": "Participation Metrics",
        "admin_total_feedback": "Total Observations",
        "admin_recent_feedback": "Last 7 Days",
        "admin_export_csv_btn": "📥 Export observations (CSV)",
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
        "scope_expander_title": "📋 View topics included in assistant scope and coverage",
        "local_fallback_banner_title": "⚡ Local Alternative Mode Active",
        "local_fallback_banner_desc": "The free-tier AI quota limit was reached (15 queries/min on Gemini or 30/min on Groq). The assistant continues operating normally via Local Alternative Mode (certified algorithmic extraction from official SOR 2026).",
        "sidebar_llm_expander_title": "⚙️ Assistant AI Configuration",
        "sidebar_kg_expander_title": "🕸️ Knowledge Graph (KG)",
        "sidebar_history_expander_title": "🕒 Query History",
        "scope_certified_kuns": "The assistant features **{count} Certified Knowledge Units** extracted directly from official IJF sources.",
        "scope_covered_title": "#### ✅ In-Scope Certified Topics",
        "scope_covered_body": (
            "*   **📖 Refereeing Rules (Appendix D - 100%):** All articles (1 to 21), official gestures, scoring (Ippon, Waza-ari), Osaekomi, Mate, Kansetsu-waza, direct Hansoku-make, head diving, and concussion protocols.\n"
            "*   **🥋 Judogi Control (Appendix C - 100%):** Control procedure, approved dimensions, Sokuteiki tool, label placement, certified colors (Snow white & Pantone blue), and belt requirements.\n"
            "*   **⏱️ Competition Systems & Weigh-in (Sections 2, 3, 4):** Official weigh-in and random weigh-in, weight tolerances, repechage brackets, seeding, and draw procedures.\n"
            "*   **🏥 Medical & Anti-Doping Handbook (Section 6 & Appendix E):** On-tatami medical assistance, bleeding limits (2 treatments), head trauma, anti-doping requirements, and athlete selection procedures.\n"
            "*   **🏫 Coach Education & Dress Code (Section 7 & Appendix F):** Coaches' code of conduct, chair dress codes (preliminaries vs. final block), coach penalty cards, and review forms.\n"
            "*   **👴 Veterans / Masters Regulations (Appendix A):** Age divisions (M1-M11, F1-F11), weight categories, contest duration, category combining, and veterans weigh-in.\n"
            "*   **⚖️ Disciplinary Code & Ethics (Section 1):** IJF Disciplinary Committee, betting rules, competition manipulation, ethical infringements, and sanctions.\n"
            "*   **🎖️ Protocol & Ceremonies (Section 8):** Medal ceremonies, flag raising, national anthems, and official dress codes."
        ),
        "scope_uncovered_title": "#### ❌ Out-of-Scope (Not Covered)",
        "scope_uncovered_body": (
            "*   **📢 Commercial Marketing & Broadcast:** Private corporate sponsorship agreements and commercial television broadcast distribution contracts.\n"
            "*   **🏟️ Venue Engineering & Facilities:** Civil engineering architectural layout, VIP hospitality lounges, and stadium HVAC specifications.\n"
            "*   **📋 Internal Political Governance:** General Assembly elections and non-sporting corporate bylaws."
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
        ],

        # Token metrics & API Key viability
        "usage_metrics_expander_title": "📊 API Usage & Token Metrics",
        "usage_metrics_card_title": "API Consumption & Viability Monitor",
        "usage_total_queries": "Total Inquiries",
        "usage_llm_queries": "Queries with LLM",
        "usage_local_queries": "Local / Deterministic",
        "usage_last_tokens": "Last Query Tokens",
        "usage_avg_tokens": "Average Tokens / Query",
        "usage_prompt_tokens": "Prompt (Input)",
        "usage_completion_tokens": "Response (Output)",
        "usage_total_accumulated": "Accumulated Tokens",
        "usage_est_cost": "Estimated API Cost",
        "usage_avg_cost_query": "Avg Cost / Query",
        "usage_queries_per_usd": "Estimated Queries per $1 USD",
        "usage_viability_title": "💡 API Key Rental & Cost Viability",
        "usage_viability_verdict": "Highly viable: Official Gemini rates make high-volume operational use exceptionally affordable.",
        "usage_reset_btn": "🔄 Reset Metrics",
        "usage_reset_success": "Metrics reset successfully.",
        "usage_response_badge": "📊 Tokens: {tokens} (Input: {prompt} | Output: {completion}) • Running Avg: {avg} tokens/query",
        "usage_response_badge_nd": "📊 Tokens: N/A (the provider did not report usage) • Running Avg: {avg} tokens/query",
        "usage_response_badge_local": "📊 Tokens: 0 (no model call) • Running Avg: {avg} tokens/query",
        "usage_avg_basis": "Average over {n} queries with tokens reported by the provider (real figures, not estimates).",
        "tab_current_query": "📝 Current query",
        "tab_query_history": "🗂️ Query history ({n})",
        "history_empty": "No previous queries in this session yet. Each new query moves the current one into this history.",
        "history_record_title": "Query #{n}",
        "history_question_label": "QUERY",
        "history_answer_label": "ANSWER",
        "history_norms_label": "SUPPORTING RULES",
        "history_show_record": "Show answer and supporting rules",
        "history_make_current": "Open as current query",
        "history_no_norms": "No supporting rules were recorded for this query.",
        "history_tokens_nd": "tokens N/A",
        "pdf_doc_search_placeholder": "Search a word or phrase in the whole SOR PDF...",
        "pdf_doc_search_btn": "🔍 Search",
        "pdf_doc_search_clear": "✕ Clear",
        "pdf_doc_search_results": "{total} match(es) on {pages} page(s) · result {cur} of {total} · page {page}",
        "pdf_doc_search_none": "No matches for “{q}” in the document.",
        "pdf_doc_search_short": "Type at least 2 characters.",
        "pdf_doc_search_prev": "◀ Previous match",
        "pdf_doc_search_next": "Next match ▶",
        "pdf_doc_search_unavailable": "Document search is unavailable: the local SOR PDF was not found.",
        "pdf_nav_prev_page": "◀ Previous page",
        "pdf_nav_next_page": "Next page ▶",
        "pdf_nav_page_label": "Go to page",
        "pdf_badge_no_matches": "No matches on this page",
        "audit_tokens_title": "Token Usage & Running Avg",
        "header_queries_badge": "📊 Processed Queries: {total} ({llm} AI • {local} Local)",
        "admin_usage_management_title": "⚙️ Usage Statistics Management",
        "admin_reset_metrics_warning": "⚠️ Danger Zone: This action will permanently reset the query counter and all token usage history to zero.",
        "admin_reset_metrics_btn": "🗑️ Reset Usage Statistics to Zero",
        "admin_reset_metrics_confirm": "Usage statistics have been successfully reset to zero.",
    },
    "es": {
        # App metadata & headers
        "app_title": "Asistente SOR IJF",
        "app_subtitle": "Consultor oficial del Reglamento de Organización y Deporte (IJF SOR 2026). Respuestas certificadas, fundamentación normativa y trazabilidad documental completa.",
        "welcome_title": "Bienvenido",
        "header_tooltip": "Reglamento de la Federación Internacional de Judo (SOR 2026)",
        
        # Sidebar sections
        "sidebar_info_title": "ℹ️ Información",
        # Como usar el asistente (auditoria de la barra lateral 2026-11-21)
        "sidebar_howto_title": "📘 Cómo usar el asistente",
        "sidebar_howto_ask_title": "Cómo consultar",
        "sidebar_howto_ask_content": (
            "Escriba su pregunta en lenguaje natural, en español o en inglés, y pulse <b>Enviar</b>. "
            "Las preguntas concretas (una situación, una categoría o un artículo) obtienen respuestas más precisas. "
            "Si su duda tiene varias partes, hágalas por separado. "
            "También puede pulsar <b>🎤 Dictar</b> y hablar: el texto se añade al campo para que lo revise antes de enviarlo. "
            "El reconocimiento de voz lo realiza su navegador (según el navegador, con un servicio en línea de su proveedor); "
            "la aplicación no graba ni guarda audio."
        ),
        "sidebar_howto_read_title": "Cómo leer la respuesta",
        "sidebar_howto_read_content": (
            "La respuesta se basa únicamente en el reglamento oficial SOR de la IJF y se comprueba contra el texto "
            "oficial antes de mostrarse. Indica la respuesta, la regla aplicable y, cuando corresponde, las condiciones "
            "y excepciones. Pulse una cita <b>📍 Art. · Pág.</b> o un enlace <b>📄 Pág.</b> para abrir el PDF oficial "
            "en esa página."
        ),
        "sidebar_howto_abstain_title": "Cuándo no responde",
        "sidebar_howto_abstain_content": (
            "Si el reglamento no contiene información suficiente o la respuesta no puede comprobarse con el texto "
            "oficial, el asistente <b>se abstiene</b> y lo indica, en lugar de suponer. Cuando los hay, los pasajes "
            "consultados quedan disponibles como referencia."
        ),
        "sidebar_howto_history_title": "Historial y reportes",
        "sidebar_howto_history_content": (
            "En <b>Historial de consultas</b> puede volver a las preguntas de esta sesión. Si detecta un error, use "
            "<b>Ayúdanos a mejorar</b>, bajo la respuesta."
        ),
        "sidebar_howto_notice_title": "Importante",
        "sidebar_howto_notice_content": (
            "El asistente es una ayuda de estudio y consulta. Ante una decisión arbitral o una controversia, prevalecen "
            "siempre el texto oficial del SOR y las decisiones de los órganos competentes de la IJF."
        ),
        # Acerca del asistente
        "sidebar_about_title": "ℹ️ Acerca del asistente",
        "sidebar_about_project_title": "Proyecto y propósito",
        "sidebar_about_project_content": (
            "<b>IJF SOR Assistant</b> facilita la consulta del <i>Sport and Organisation Rules</i> (SOR) de la "
            "Federación Internacional de Judo a árbitros, entrenadores, deportistas y demás miembros de la comunidad "
            "del judo, con respuestas fundamentadas en el texto oficial y enlazadas a su página."
        ),
        "sidebar_rules_edition": "edición oficial del 14 de agosto de 2026",
        "sidebar_sources_title": "Fuentes oficiales",
        "sidebar_sources_content": (
            "Las respuestas se basan exclusivamente en el SOR de la IJF, {edition}. Algunas respuestas incluyen "
            "enlaces complementarios a recursos oficiales de la IJF (portal de reglas, vídeos de arbitraje, "
            "comunicados). Son material de consulta y no sustituyen al SOR."
        ),
        "sidebar_author_title": "Autor",
        "sidebar_author_content": (
            "**Alexis Oliveros**\n\n"
            "Árbitro Nacional de Judo – Colombia\n\n"
            "2° Dan\n\n"
            "Desarrollador del proyecto **IJF SOR Assistant**.\n\n"
            "© 2026 Alexis Oliveros. Todos los derechos reservados."
        ),
        "sidebar_version_title": "Versión",
        "sidebar_version_rules": "Reglamento: SOR IJF, {edition}",
        "sidebar_source_hash": "Huella del PDF oficial (SHA-256):",
        "sidebar_version_label": "Versión {version} · actualizada el 21-11-2026",
        "sidebar_guide_btn": "📥 Guía de uso (PDF)",
        "sidebar_guide_help": "Descargue la guía de uso de la versión {version}: cómo consultar, dictar, leer la respuesta y comprobarla en el PDF oficial.",
        # Consulta por voz (Web Speech API del navegador)
        "voice_btn_start": "🎤 Dictar",
        "voice_btn_stop": "Detener",
        "voice_btn_title": "Dictar la consulta con el micrófono. El texto se añade al campo de consulta para revisarlo antes de enviarlo.",
        "voice_state_requesting": "Solicitando acceso al micrófono…",
        "voice_state_listening": "Escuchando…",
        "voice_state_processing": "Procesando la transcripción…",
        "voice_state_ready": "Texto añadido a la consulta. Revíselo y pulse Enviar.",
        "voice_state_nospeech": "No se detectó voz. Pulse 🎤 Dictar para intentarlo de nuevo.",
        "voice_state_lang_changed": "Dictado detenido por un cambio de idioma o de tema. Pulse 🎤 Dictar para continuar.",
        "voice_err_denied": "Permiso de micrófono denegado. Actívelo en el navegador o escriba su consulta.",
        "voice_err_nomic": "No se encontró un micrófono disponible. Puede escribir su consulta.",
        "voice_err_unsupported": "Este navegador no permite dictar. Puede escribir su consulta.",
        "voice_err_insecure": "El dictado requiere una conexión segura (HTTPS). Puede escribir su consulta.",
        "voice_err_network": "El servicio de voz del navegador no está disponible. Inténtelo más tarde o escriba su consulta.",
        "voice_err_generic": "No se pudo completar el dictado. Inténtelo de nuevo o escriba su consulta.",
        "voice_err_noinput": "No se encontró el campo de consulta. Recargue la página.",
        # Disponibilidad del servicio (sustituye a la tarjeta de cuotas)
        "availability_title": "🛡️ Disponibilidad del servicio",
        "availability_desc": (
            "El asistente redacta y comprueba las respuestas con un servicio de IA. Si ese servicio no está disponible "
            "temporalmente, el asistente no genera respuestas sin comprobar: lo indicará y podrá intentarlo de nuevo "
            "más tarde."
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
        "chat_input_placeholder": "Escriba aquí su consulta sobre el reglamento IJF SOR...",
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
        "evidences_section_title": "Evidencias Normativas Certificadas",
        "evidences_section_subtitle": "Disposiciones reglamentarias primarias y citas oficiales verificadas del IJF SOR",
        "evidence_article_label": "Artículo / Regla",
        "evidence_page_label": "Pág.",
        "evidence_edition_label": "Edición",
        "evidence_verified_badge": "Oficial (SHA-256 Verificado)",
        "evidence_quote_label": "Cita Textual Oficial:",
        "evidence_context_label": "Extracto Normativo Contextual:",
        "evidence_view_pdf_btn": "Consultar en PDF (Pág. {page})",
        "evidence_more_expander": "Ver evidencias complementarias adicionales ({count})",
        "expander_audit_metadata": "🛠️ Trazabilidad Técnica y Auditoría del Motor",
        "audit_rre_title": "Motor de Recuperación (RRE)",
        "audit_sha_title": "Validación Criptográfica de Fuente",
        "audit_provider_title": "Proveedor Generativo",
        "audit_chunks_title": "Pasajes Canónicos Recuperados",
        "normative_rigor_warning": "⚠️ **Aviso de Rigor Normativo:** Se han detectado discrepancias probatorias o limitaciones en la evidencia que afectan aspectos complementarios de esta consulta. Consulte la sección de Límites de la Evidencia.",
        "view_details_expander": "🔍 Ampliar respuesta con análisis detallado y relaciones entre artículos",
        "sec_graph_relations": "🕸️ Diagrama y Relaciones entre Artículos",
        "graph_caption_relations": "Mapa de dependencias y relaciones normativas entre los artículos aplicables:",
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
        "feedback_type_label": "Tipo de novedad u observación",
        "feedback_type_options": [
            "Posible error o inconsistencia normativa",
            "Consulta no resuelta satisfactoriamente",
            "Aclaración o comentario",
            "Sugerencia de mejora",
            "Solicitud de nueva funcionalidad",
            "Observación de funcionamiento",
            "Otro"
        ],
        "feedback_comment_label": "Descripción, comentario u observación",
        "feedback_comment_placeholder": "Comparte cualquier detalle, sugerencia o inconveniente (texto libre)...",
        "feedback_attachment_label": "Adjuntar evidencia (opcional: PNG, JPG, PDF - máx 5 MB)",
        "feedback_submit_btn": "Enviar reporte 📨",
        "feedback_success": "✓ {message} *(Identificador: `{obs_id}`)*",
        "feedback_error": "⚠️ {message}",
        
        # Administrative management
        "sidebar_admin_title": "🔒 Administración (acceso restringido)",
        "admin_auth_header": "🔐 Acceso Restringido — Administración de Novedades",
        "admin_auth_caption": "Módulo administrativo autorizado para revisar, dar seguimiento y gestionar observaciones técnicas.",
        "admin_token_label": "Token de Acceso Administrativo",
        "admin_login_btn": "Autenticar",
        "admin_logout_btn": "Cerrar sesión",
        "admin_not_configured": "El acceso administrativo se encuentra deshabilitado (no hay token configurado en el servidor).",
        "admin_auth_failed": "Autenticación fallida: el token administrativo no es válido.",
        "admin_filter_status": "Filtrar por estado:",
        "admin_filter_type": "Filtrar por tipo:",
        "admin_search_label": "Buscar por ID, consulta o comentario:",
        "admin_refresh_btn": "Actualizar lista",
        "admin_no_records": "No se encontraron novedades con los criterios seleccionados.",
        "admin_metrics_title": "Métricas de Participación",
        "admin_total_feedback": "Total de novedades",
        "admin_recent_feedback": "Últimos 7 días",
        "admin_export_csv_btn": "📥 Exportar novedades (CSV)",
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
        "scope_expander_title": "📋 Ver temas incluidos en alcance y cobertura del asistente",
        "local_fallback_banner_title": "⚡ Modo Alternativo Local Activo",
        "local_fallback_banner_desc": "Se ha alcanzado la cuota de consultas del modelo de IA gratuito o el servicio externo está temporalmente no disponible. El asistente está respondiendo mediante extracción directa certificada del SOR 2026 oficial, asegurando continuidad y fidelidad reglamentaria.",
        "sidebar_llm_expander_title": "⚙️ Configuración del Asistente (IA)",
        "sidebar_kg_expander_title": "🕸️ Grafo de Conocimiento (KG)",
        "sidebar_history_expander_title": "🕒 Historial de Consultas",
        "scope_certified_kuns": "El asistente cuenta con **{count} Unidades de Conocimiento certificadas** extraídas de las fuentes oficiales de la IJF.",
        "scope_covered_title": "#### ✅ Temas Cubiertos",
        "scope_covered_body": (
            "*   **📖 Reglas de Arbitraje (Apéndice D - 100%):** Todos los artículos (1 al 21), gestos oficiales, puntuaciones, Osaekomi, Mate, luxaciones, descalificaciones directas (Hansoku-make) y conmoción cerebral.\n"
            "*   **🥋 Control de Judogi (Apéndice C - 100%):** Proceso de control, medidas permitidas, Sokuteiki, colocación de logotipos, colores (blanco/azul) e indumentaria.\n"
            "*   **⏱️ Sistemas y Pesaje (Secciones 2, 3, 4):** Pesaje oficial y sorteo aleatorio, tolerancias, llaves de competencia con repechaje, siembra de cabezas de serie y gestión de categorías.\n"
            "*   **🏥 Manual Médico y Antidopaje (Sección 6 & Apéndice E):** Asistencia médica en tatami, límite de 2 atenciones para sangrado, conmociones, requisitos de control antidopaje y selección de atletas.\n"
            "*   **🏫 Educación y Coaches (Sección 7 & Apéndice F):** Código de conducta y vestimenta de entrenadores en la silla (eliminatorias y bloque final), tarjetas de sanción a coaches y formularios oficiales.\n"
            "*   **👴 Regulaciones para Veteranos / Masters (Apéndice A):** Divisiones de edad (M1-M11, F1-F11), categorías de peso, duración de combates, unificación de divisiones y pesaje para veteranos.\n"
            "*   **⚖️ Régimen Disciplinario y Ética (Sección 1):** Comité Disciplinario de la IJF, violaciones éticas, manipulación de combates y sanciones aplicables.\n"
            "*   **🎖️ Protocolos de Premiación (Sección 8):** Ceremonias de medallas, izado de banderas, himnos nacionales y código de vestimenta oficial."
        ),
        "scope_uncovered_title": "#### ❌ Fuera de Alcance (No Cubiertos)",
        "scope_uncovered_body": (
            "*   **📢 Marketing y Difusión Comercial:** Contratos corporativos de patrocinio privado de la IJF y derechos de transmisión televisiva externa.\n"
            "*   **🏟️ Infraestructura del Recinto:** Planos arquitectónicos de ingeniería civil del pabellón, áreas VIP y climatización de la arena.\n"
            "*   **📋 Gobernanza Política Interna:** Elecciones de la asamblea general de la IJF y estatutos políticos federativos no deportivos."
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
        ],

        # Token metrics & API Key viability
        "usage_metrics_expander_title": "📊 Consumo de Tokens y Métricas API",
        "usage_metrics_card_title": "Monitor de Consumo y Viabilidad API",
        "usage_total_queries": "Consultas Totales",
        "usage_llm_queries": "Consultas con IA",
        "usage_local_queries": "Modo Local / Determinista",
        "usage_last_tokens": "Tokens Última Consulta",
        "usage_avg_tokens": "Promedio Tokens / Consulta",
        "usage_prompt_tokens": "Entrada (Prompt)",
        "usage_completion_tokens": "Salida (Respuesta)",
        "usage_total_accumulated": "Tokens Acumulados",
        "usage_est_cost": "Costo Estimado Acumulado",
        "usage_avg_cost_query": "Costo Promedio / Consulta",
        "usage_queries_per_usd": "Consultas Estimadas por $1 USD",
        "usage_viability_title": "💡 Viabilidad Económica de Renta de API Key",
        "usage_viability_verdict": "Altamente viable: Las tarifas oficiales de Gemini hacen que el asistente resulte extraordinariamente económico para uso intensivo.",
        "usage_reset_btn": "🔄 Reiniciar Estadísticas",
        "usage_reset_success": "Contadores de métricas reiniciados exitosamente.",
        "usage_response_badge": "📊 Consumo: {tokens} tokens (Entrada: {prompt} | Salida: {completion}) • Promedio acumulado: {avg} tokens/consulta",
        "usage_response_badge_nd": "📊 Consumo: N/D (el proveedor no informó tokens) • Promedio acumulado: {avg} tokens/consulta",
        "usage_response_badge_local": "📊 Consumo: 0 tokens (sin llamada al modelo) • Promedio acumulado: {avg} tokens/consulta",
        "usage_avg_basis": "Promedio sobre {n} consultas con tokens informados por el proveedor (cifras reales, no estimadas).",
        "tab_current_query": "📝 Consulta actual",
        "tab_query_history": "🗂️ Historial de consultas ({n})",
        "history_empty": "Aún no hay consultas anteriores en esta sesión. Cada nueva consulta traslada la actual a este historial.",
        "history_record_title": "Consulta #{n}",
        "history_question_label": "CONSULTA",
        "history_answer_label": "RESPUESTA",
        "history_norms_label": "NORMAS DE SOPORTE",
        "history_show_record": "Mostrar respuesta y normas de soporte",
        "history_make_current": "Abrir como consulta actual",
        "history_no_norms": "Esta consulta no registró normas de soporte.",
        "history_tokens_nd": "tokens N/D",
        "pdf_doc_search_placeholder": "Buscar una palabra o frase en todo el PDF del SOR...",
        "pdf_doc_search_btn": "🔍 Buscar",
        "pdf_doc_search_clear": "✕ Limpiar",
        "pdf_doc_search_results": "{total} coincidencia(s) en {pages} página(s) · resultado {cur} de {total} · página {page}",
        "pdf_doc_search_none": "No hay coincidencias para «{q}» en el documento.",
        "pdf_doc_search_short": "Escriba al menos 2 caracteres.",
        "pdf_doc_search_prev": "◀ Coincidencia anterior",
        "pdf_doc_search_next": "Coincidencia siguiente ▶",
        "pdf_doc_search_unavailable": "La búsqueda en el documento no está disponible: no se encontró el PDF local del SOR.",
        "pdf_nav_prev_page": "◀ Página anterior",
        "pdf_nav_next_page": "Página siguiente ▶",
        "pdf_nav_page_label": "Ir a la página",
        "pdf_badge_no_matches": "Sin coincidencias en esta página",
        "audit_tokens_title": "Consumo de Tokens y Promedio",
        "header_queries_badge": "📊 Consultas Atendidas: {total} ({llm} IA • {local} Local)",
        "admin_usage_management_title": "⚙️ Gestión de Estadísticas de Uso",
        "admin_reset_metrics_warning": "⚠️ Zona de Peligro: Esta acción reiniciará permanentemente a cero el contador de consultas y todo el historial de consumo de tokens.",
        "admin_reset_metrics_btn": "🗑️ Reiniciar Estadísticas a Cero",
        "admin_reset_metrics_confirm": "Las estadísticas de uso han sido reiniciadas a cero exitosamente.",
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
