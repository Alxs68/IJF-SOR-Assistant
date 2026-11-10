# Interfaz Gráfica Streamlit (app.py) — Versión 3.0

Este módulo implementa el frontend interactivo del **IJF SOR Assistant 2026** utilizando **Streamlit**, desacoplado mediante una arquitectura de presentación limpia en dos niveles, trazabilidad verificable y soporte bilingüe completo (Español e Inglés).

---

## 🎨 Características de Diseño y UX

### 1. Presentación Limpia en Dos Niveles
* **Nivel 1 (Respuesta Normativa Principal):** Texto fluido, natural y riguroso que expone de inmediato la solución reglamentaria sin códigos internos (`SOR-...`), identificadores crudos ni scores matemáticos en el texto ordinario.
* **Nivel 2 (Tarjetas de Evidencia Certificada):** Bloque visual independiente de tarjetas con la disposición oficial (`Art. X.Y`), número de página en el SOR, insignia de verificación de integridad documental (sello SHA-256 verificado), cita textual completa y botón de acceso al visor PDF.

### 2. Visor PDF Oficial Integrado con Salto a Página
* Incorpora un visor PDF interactivo integrado en la propia aplicación web.
* Al hacer clic en el botón de navegación de cualquier evidencia, el visor se abre automáticamente posicionado en la página exacta del PDF oficial del SOR 2026 (págs. 1 a 298), destacando la cita pertinente.

### 3. Selector de Tema Claro / Oscuro Nativo
* Soporta tres modalidades de tema seleccionables en la barra lateral:
  - 🖥️ **Automático:** Detecta dinámicamente la preferencia de color del sistema operativo o navegador (`prefers-color-scheme`).
  - ☀️ **Modo Claro:** Esquema con fondos blancos y contraste optimizado para lectura diurna.
  - 🌙 **Modo Oscuro:** Esquema con fondo oscuro (*tatami night*) y tipografía de alto contraste para baja fatiga visual.

### 4. Panel Técnico de Auditoría Plegable
* Ubicado debajo de las evidencias en un acordeón plegable para no saturar la lectura ordinaria:
  - Identificador de conocimiento y ancla documental.
  - Scores de recuperación híbrida (BM25 + Dense + RRF + Re-ranking).
  - Tiempos de ejecución, modelo utilizado y estado de contingencia (*fallback*).
  - Verificación criptográfica del PDF oficial (`SHA-256`).

### 5. Barra Lateral e Internacionalización Bilingüe (ES / EN)
* **Selector de Idioma:** Conmutador instantáneo entre Español e Inglés que traduce todos los componentes visuales, mensajes del sistema, ejemplos y sugerencias.
* **Desplegable de Alcance y Cobertura:** Detalla formalmente los temas cubiertos del SOR:
  - 📖 Reglas de Arbitraje (Apéndice D)
  - 🥋 Control de Judogi (Apéndice C)
  - ⏱️ Sistemas de Competición y Pesaje (Secciones 2, 3, 4)
  - 🏥 Manual Médico y Antidopaje (Sección 6 & Apéndice E)
  - 🏫 Educación y Entrenadores / Coaches (Sección 7 & Apéndice F)
  - 👴 Regulaciones para Veteranos / Masters (Apéndice A)
  - ⚖️ Régimen Disciplinario y Ética (Sección 1)
  - 🎖️ Protocolo y Premiación (Sección 8)
* **Chips de Sugerencia Rápida:** Botones de consulta rápida con un solo clic.

---

## 🚀 Ejecución de la Interfaz
Para iniciar el servidor local de Streamlit:
```bash
streamlit run app.py
```
La aplicación se abrirá automáticamente en `http://localhost:8501`.
