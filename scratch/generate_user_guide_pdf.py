import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "IJF SOR Assistant 2026 — Guía Oficial de Usuario")
            self.drawRightString(612 - 54, 750, "Edición Normativa SOR IJF 14-Ago-2026")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Footer
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(612 - 54, 36, page_text)
        self.drawString(54, 36, "Documento Técnico Oficial — Prohibida su alteración normativa.")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 612 - 54, 46)
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1d4ed8")
    dark_neutral = colors.HexColor("#0f172a")
    body_color = colors.HexColor("#334155")
    border_box = colors.HexColor("#e2e8f0")
    bg_box = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        alignment=1, # Center
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=10
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        alignment=1,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=dark_neutral,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=body_color,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )

    table_header = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        'TC',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=dark_neutral
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("GUÍA OFICIAL DE USUARIO", title_style))
    story.append(Paragraph("Asistente Experto en el Reglamento SOR de la IJF (Edición Rebuild 2026)", subtitle_style))
    story.append(Paragraph("Autor: Alexis Oliveros (Árbitro Nacional de Judo - 2° Dan) &bull; Edición Normativa: 14 de Agosto de 2026", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=10))

    # Resumen Ejecutivo / Propósito
    callout_data = [[
        Paragraph(
            "<b>PROPÓSITO Y MARCO DE VALIDEZ:</b> El <i>Asistente SOR IJF</i> es un sistema técnico de apoyo investigativo, "
            "formativo y documental para árbitros, entrenadores, comisionados y competidores. Opera de forma auditable sobre las "
            "<b>Reglas de Organización y Deporte (SOR 2026)</b> oficiales de la Federación Internacional de Judo (edición 14 de agosto de 2026). "
            "El sistema fundamenta cada respuesta en el texto normativo exacto, indicando artículos rectores, identificadores de conocimiento "
            "y páginas oficiales del documento vigente.",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 8))

    # Sección 1: Estructura de la Interfaz
    story.append(Paragraph("1. Arquitectura de Interfaz y Navegación", h1_style))
    story.append(Paragraph(
        "La interfaz del Asistente SOR IJF presenta un diseño limpio, moderno y optimizado para estaciones de trabajo y dispositivos móviles, "
        "eliminando elementos que condicionen la redacción de la consulta:",
        body_style
    ))

    ui_components = [
        [Paragraph("<b>Componente</b>", table_header), Paragraph("<b>Ubicación</b>", table_header), Paragraph("<b>Función Operativa</b>", table_header)],
        [
            Paragraph("<b>Panel Central de Consulta Libre</b>", table_cell),
            Paragraph("Área principal", table_cell),
            Paragraph("Entrada de texto principal sin restricciones ni preguntas predefinidas. Permite formular cualquier consulta fáctica libremente.", table_cell)
        ],
        [
            Paragraph("<b>Selector Opcional de Ejemplos</b>", table_cell),
            Paragraph("Barra lateral", table_cell),
            Paragraph("Menú desplegable opcional con consultas frecuentes representativas. Precarga la pregunta en el panel central para su edición libre antes del envío.", table_cell)
        ],
        [
            Paragraph("<b>Selector Bilingüe Dinámico</b>", table_cell),
            Paragraph("Barra lateral (superior)", table_cell),
            Paragraph("Conmuta de forma inmediata entre <i>Español</i> e <i>English</i>, adaptando la interfaz y la respuesta en terminología técnica oficial IJF.", table_cell)
        ],
        [
            Paragraph("<b>Configuración Multi-LLM</b>", table_cell),
            Paragraph("Barra lateral", table_cell),
            Paragraph("Gestión de proveedores (Gemini primario con fallback a Groq), parámetros RAG y visualización del estado del motor.", table_cell)
        ],
        [
            Paragraph("<b>Visor Documental Integrado</b>", table_cell),
            Paragraph("Área principal (bajo respuesta)", table_cell),
            Paragraph("Visor PDF sincronizado con el documento oficial de 29 MB, apertura en el folio físico exacto y visualización de pasajes.", table_cell)
        ],
    ]
    t_comp = Table(ui_components, colWidths=[130, 110, 264])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, border_box),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_box])
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 8))

    # Sección 2: Política de Razonamiento ADA
    story.append(Paragraph("2. Política Transversal de Razonamiento Reglamentario (ADA)", h1_style))
    story.append(Paragraph(
        "El Asistente de Decisión Arbitral (ADA) opera mediante una política de análisis estructurado para asegurar rigor técnico y evitar generalizaciones indebidas:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Estructura de Respuesta en Dos Niveles:</b><br/>"
                           "<b>Nivel 1 (Respuesta Operativa Directa):</b> Síntesis concisa y proporcional a la consulta que entrega de inmediato la sanción, "
                           "tolerancia o decisión normativa aplicable con su artículo rector, sin preámbulos introductorios ni texto innecesario.<br/>"
                           "<b>Nivel 2 (Análisis Ampliado y Trazabilidad):</b> Desglose pormenorizado con fundamentos normativos textuales, identificadores certificados "
                           "(ej. <code>[SOR-2026-08-P188-S196]</code>), condiciones y excepciones, procedimiento arbitral paso a paso y declaración expresa de limitaciones.", bullet_style))
    story.append(Paragraph("&bull; <b>Diferenciación Estricta por Categoría de Edad:</b><br/>"
                           "- <i>Cadetes e Infantiles:</i> Se aplican exclusivamente las conductas tipificadas en el Art. 18.1.4 (pág. 188): el uso deliberado de la cabeza "
                           "por parte de <b>Tori</b> para proyectar se sanciona con <b>Shido</b> (punto 33); el uso deliberado de la cabeza por parte de <b>Uke</b> para "
                           "defenderse se sanciona con <b>Shido</b> y se concede a Tori la puntuación correspondiente (punto 34); y el <i>reverse seoi-nage</i> no otorga "
                           "puntuación y se penaliza a Tori con <b>Shido</b> (punto 35, pág. 189).<br/>"
                           "- <i>Juniors y Séniors:</i> Las restricciones especiales de cadetes (Art. 18.1.4) <b>no se extrapolan automáticamente</b> a juniors ni séniors. "
                           "Esto no constituye una autorización universal: toda acción técnica en estas categorías permanece sometida al régimen general de técnicas "
                           "prohibidas y peligrosas del SOR (Art. 18.2).", bullet_style))
    story.append(Paragraph("&bull; <b>Diferenciación de Roles (Tori vs. Uke):</b><br/>"
                           "- <i>Tori:</i> El lanzamiento de cabeza en picado (<i>Head Diving</i>) al intentar o ejecutar una técnica conlleva <b>Hansoku-make directo</b> "
                           "por técnica peligrosa (Art. 18.2.1, pág. 190); en este supuesto específico, el competidor <b>sí puede continuar</b> en las siguientes rondas de la "
                           "competición si califica por el sistema de competencia.<br/>"
                           "- <i>Uke:</i> El puente voluntario al caer se computa reglamentariamente como impacto de espaldas y se otorga <b>Ippon</b> a Tori por protección "
                           "de la columna cervical (Art. 14.2, pág. 166), con la salvedad textual de que Uke caiga sobre el cuerpo de Tori sin que la cabeza ni los pies toquen el tatami.", bullet_style))
    story.append(Paragraph("&bull; <b>Evaluación Arbitral de la Jugada y Protocolo Médico:</b><br/>"
                           "Ante un impacto o caída que involucre la cabeza o cause traumatismo, la normativa separa estrictamente dos planos:<br/>"
                           "1. <i>Evaluación Arbitral:</i> El equipo arbitral juzga si el desenlace provino de una técnica lícita, de una infracción antideportiva o de un lance fortuito "
                           "de combate, determinando si corresponde o no sanción deportiva según las circunstancias concretas de la acción.<br/>"
                           "2. <i>Protocolo y Asistencia Médica:</i> Si existe lesión, conmoción o sangrado, el árbitro detiene el combate (<i>Mate!</i>) y se aplica el protocolo "
                           "médico oficial (Art. 20, págs. 196-203, y Apéndice E). La decisión sobre si un competidor lesionado puede o no continuar la lucha o el torneo recae "
                           "en las autoridades médicas acreditadas (Comisionado Médico de la IJF / médicos comisionados de la organización local o de delegación, según el nivel del evento).", bullet_style))
    story.append(Paragraph("&bull; <b>Transparencia sobre Evidencia Insuficiente:</b> Si una consulta es ambigua o los extractos oficiales certificados no contienen la disposición aplicable, "
                           "el asistente declara con total claridad las limitaciones de la evidencia, sin inferir ni fabricar reglas inexistentes.", bullet_style))
    story.append(Spacer(1, 8))

    # Sección 3: Flujo Operativo y Ejemplos de Consulta
    story.append(Paragraph("3. Flujo Operativo y Ejemplos de Consulta", h1_style))
    story.append(Paragraph(
        "Para realizar consultas reglamentarias con máxima precisión técnica, se sugiere el siguiente flujo de trabajo:",
        body_style
    ))
    story.append(Paragraph("<b>Paso 1:</b> Redacte su consulta libre en el panel central (o seleccione un ejemplo lateral y edítelo a conveniencia).<br/>"
                           "<b>Paso 2:</b> Revise el Nivel 1 para obtener la resolución inmediata y el artículo rector aplicable.<br/>"
                           "<b>Paso 3:</b> Examine el Nivel 2 para verificar los escenarios fácticos, salvedades y límites documentales.<br/>"
                           "<b>Paso 4:</b> Haga clic en el identificador normativo para abrir el visor interactivo y cotejar el texto oficial en el PDF original.", body_style))
    story.append(Spacer(1, 4))

    examples = [
        ("Defensa con Cabeza en Cadetes", "Art. 18.1.4 (Pág. 188)", "¿Qué sanción aplica si un cadete usa la cabeza para defender?", "Uke es sancionado con Shido (punto 34) y se concede a Tori la puntuación técnica correspondiente, si la hubo."),
        ("Head Diving de Tori al Proyectar", "Art. 18.2.1 (Pág. 190)", "¿Cuál es la consecuencia del head diving y puede continuar el atleta?", "Hansoku-make directo por técnica peligrosa. El atleta sí puede continuar en la competición si clasifica."),
        ("Puente Voluntario de Uke al Caer", "Art. 14.2 (Pág. 166)", "¿Cómo se juzga si Uke cae en puente voluntario para evitar la espalda?", "Se otorga Ippon a Tori por protección cervical, salvo caída sobre el cuerpo de Tori sin contacto de cabeza/pies en tatami."),
        ("Colores Reglamentarios de Judogi", "Regla C1.9 (Pág. 124)", "¿Cuáles son los colores autorizados para el judogi oficial?", "Blanco (Snow white) y Azul (Pantone textil 18-4051TCX a 18-4039TCX / print 285M a 286M)."),
    ]

    t_ex_data = [
        [Paragraph("<b>Tema Reglamentario</b>", table_header), Paragraph("<b>Artículos SOR</b>", table_header), Paragraph("<b>Consulta y Criterio IJF</b>", table_header)]
    ]
    for cat, art, q, a in examples:
        t_ex_data.append([
            Paragraph(f"<b>{cat}</b>", table_cell),
            Paragraph(art, table_cell),
            Paragraph(f"<i>'{q}'</i><br/><b>Dictamen:</b> {a}", table_cell)
        ])

    t_ex = Table(t_ex_data, colWidths=[120, 110, 274])
    t_ex.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, border_box),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_box])
    ]))
    story.append(t_ex)
    story.append(Spacer(1, 8))

    # Sección 4: Advertencia Oficial y Deber de Cotejo
    story.append(Paragraph("4. Advertencia Oficial y Deber de Cotejo", h1_style))
    warn_data = [[
        Paragraph(
            "<b>ADVERTENCIA DE RESPONSABILIDAD ARBITRAL Y DEBER DE COTEJO:</b><br/>"
            "El <i>IJF SOR Assistant</i> provee fundamentación documental auditable mediante algoritmos de recuperación documental RRE y "
            "generación mediante modelos de lenguaje supervisados por contexto normativo. <b>No emite decisiones infalibles ni ostenta autoridad arbitral "
            "o jurisdiccional alguna.</b><br/><br/>"
            "En cualquier evento deportivo, la autoridad reglamentaria y decisoria reside exclusivamente en los árbitros sobre el tatami, "
            "los Directores de Arbitraje de la IJF y la Comisión de Arbitraje / Jurado de Apelación en vivo. La única fuente con validez vinculante "
            "es el texto oficial del reglamento IJF SOR publicado en su versión original en inglés. Se recomienda cotejar siempre la cita en el visor integrado "
            "o en el documento oficial antes de adoptar decisiones arbitrales o formalizar protestas reglamentarias.",
            callout_style
        )
    ]]
    warn_table = Table(warn_data, colWidths=[504])
    warn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#fef3c7")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(warn_table)
    story.append(Spacer(1, 8))

    # Sección 5: Ficha Técnica
    story.append(Paragraph("5. Ficha Técnica y Control de Versión", h1_style))
    meta_info = [
        [Paragraph("<b>Parámetro</b>", table_header), Paragraph("<b>Especificación Oficial</b>", table_header)],
        [Paragraph("<b>Sistema</b>", table_cell), Paragraph("IJF SOR Assistant (Rebuild Edition 2026)", table_cell)],
        [Paragraph("<b>Reglamento Base</b>", table_cell), Paragraph("IJF Sport and Organisation Rules (14 August 2026)", table_cell)],
        [Paragraph("<b>Arquitectura</b>", table_cell), Paragraph("Recuperación Documental RRE (híbrido denso/disperso/grafo) + Generación LLM Multi-Proveedor", table_cell)],
        [Paragraph("<b>Hash SHA-256 Fuente</b>", table_cell), Paragraph("<code>4fd5d55cb15082b2f6797a7a149f131a316279f6764500902888cf982a7f05b0</code>", table_cell)],
        [Paragraph("<b>Despliegue</b>", table_cell), Paragraph("OCI Ubuntu 24.04 ARM64 &bull; Docker Compose &bull; Puerto 8501", table_cell)],
        [Paragraph("<b>Autor / Desarrollador</b>", table_cell), Paragraph("Alexis Oliveros &bull; Árbitro Nacional de Judo &bull; 2° Dan", table_cell)],
    ]
    t_meta = Table(meta_info, colWidths=[130, 374])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, border_box),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_box])
    ]))
    story.append(t_meta)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generado exitosamente en: {filename}")

if __name__ == "__main__":
    out_path = os.path.join("docs", "guides", "IJF_SOR_Assistant_Guia_Usuario.pdf")
    build_pdf(out_path)
