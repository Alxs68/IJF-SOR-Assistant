# 🥋 IJF SOR Assistant 2026 — Versión 3.0
> **Asistente Oficial de Consulta Reglamentaria y Decisión Arbitral de la Federación Internacional de Judo (IJF)**  
> **Marco Normativo Vigente:** IJF Sport and Organisation Rules (Edición oficial del 14 de agosto de 2026 — 298 páginas)  
> **Producción:** [https://sor.alxol.com](https://sor.alxol.com)

---

## 📋 Resumen del Proyecto

El **IJF SOR Assistant** es una plataforma judicial y de consulta reglamentaria inteligente diseñada para resolver consultas operativas, normativas y fácticas sobre el judo internacional de alto rendimiento. 

Basado en una arquitectura desacoplada de **Recuperación y Razonamiento Reglamentario (RRE/ADA)** con recuperación híbrida trifásica, gobernanza documental inmutable y verificación criptográfica SHA-256, el asistente garantiza:
1. **Fidelidad Normativa Absoluta:** Respuestas fundamentadas estrictamente en las 298 páginas del SOR 2026-08 oficial, sin alucinación de artículos, tolerancias o códigos de sanción inexistentes.
2. **Presentación Limpia en Dos Niveles:** Separación estricta entre la respuesta directa u operativa (Nivel 1), las evidencias normativas certificadas con citas textuales y acceso interactivo al PDF (Nivel 2), y la auditoría técnica detallada (reservada para diagnóstico y panel de trazabilidad).
3. **Resiliencia Operativa Multi-Proveedor:** Orquestador de modelos de lenguaje con conmutación por error (*fallback*) automático entre Google Gemini, Groq (Llama-3) y un motor determinístico local desconectado.

---

## 📚 Alcance y Cobertura Normativa Certificada (SOR 2026-08)

El corpus activo del asistente cubre íntegramente las materias deportivas y organizativas promulgadas en las **298 páginas del SOR oficial**:

```text
========================================================================================
SECCIÓN / APÉNDICE          MATERIA NORMATIVA CUBIERTA                    PÁGINAS SOR
========================================================================================
Apéndice D (100%)           Reglas de Arbitraje (Artículos 1 al 21)       Págs. 132-200
Apéndice C (100%)           Control de Judogi e Indumentaria (Sokuteiki)  Págs. 114-131
Secciones 2, 3 y 4          Sistemas de Competición, Pesaje y Sorteo      Págs. 34-87
Sección 6 & Apéndice E      Manual Médico y Control Antidopaje            Págs. 94-99, 200-212
Sección 7 & Apéndice F      Educación y Entrenadores (Coaches)            Págs. 88-93, 236-238
Apéndice A                  Regulaciones para Veteranos / Masters         Págs. 100-106
Sección 1                   Régimen Disciplinario, Integridad y Ética     Págs. 12-25
Sección 8                   Protocolo, Premiación y Ceremonias Oficiales   Págs. 107-111
========================================================================================
```

### Detalle de Capítulos Incorporados:

1. **📖 Reglas de Arbitraje (Apéndice D):**
   - Acciones técnicas y puntuaciones (Ippon, Waza-ari, cuatro criterios rectores).
   - Inmovilizaciones (Osaekomi, Toketa), estrangulaciones (Shime-waza) y luxaciones (Kansetsu-waza).
   - Sistema de sanciones leves (Shido) e infracciones graves (Hansoku-make indirecto y directo).
   - Protocolo de seguridad cervical y regla de puente voluntario de Uke (Art. 14.2, págs. 166-167).
   - Acciones de cabeza y zambullida peligrosa (*Head Diving*, Art. 18.2.1, pág. 190).
   - Reglas específicas por edad: restricciones en Cadetes (Art. 18.1.4, págs. 188-189, ej. penalización con Shido para reverse seoi-nage y prohibición de uso defensivo de la cabeza).

2. **🏫 Educación y Entrenadores / Coaches (Sección 7 & Apéndice F):**
   - **Código de Conducta de Entrenadores (Art. 7.1):** Comportamiento en la silla de coach, prohibición de grabaciones o instrucciones inadecuadas durante las acciones de combate.
   - **Código de Vestimenta Oficial (Art. 7.2):** Requisitos obligatorios diferenciados:
     * *Bloque Final (Final Block / Horario TV) y Sorteo (Draw):* Traje formal (chaqueta, pantalón, camisa y corbata para hombres; chaqueta, pantalón/falda/vestido, blusa para mujeres) y zapatos formales de vestir (prohibido calzado deportivo o chanclas).
     * *Rondas Preliminares (Eliminatorias):* Chándal nacional oficial con pantalones largos hasta los zapatos, camisetas oficiales y calzado deportivo.
   - **Régimen de Tarjetas y Suspensión (Art. 7.3 & Formulario F1.3.29, Pág. 236):** Procedimiento disciplinario de amonestación (tarjeta amarilla) y expulsión de la silla de coach (tarjeta roja), con tramitación formal ante la Comisión de Arbitraje de la IJF.

3. **🏥 Manual Médico y Control Antidopaje (Sección 6 & Apéndice E):**
   - **Asistencia Médica en Tatami:** Límite estricto de dos (2) intervenciones médicas para lesiones con sangrado (Art. 20, págs. 196-198); atención fuera de la zona de combate.
   - **Protocolo de Traumatismo Craneoencefálico / Conmoción (Head Trauma):** Evaluación médica obligatoria, registro oficial y suspensión preventiva de combate.
   - **Requisitos de Control Antidopaje (Art. E1.6, Págs. 203-206):** Protocolo oficial de sorteo médico, selección de judokas para control, cadena de custodia de muestras y responsabilidades del Comisionado Médico de la IJF.

4. **👴 Regulaciones para Veteranos / Masters (Apéndice A):**
   - **Divisiones de Edad (Art. A1.4, Pág. 103):** Categorías masculinas (M1 a M11, desde 30 hasta más de 80 años) y femeninas (F1 a F11).
   - **Duración del Combate para Veteranos (Art. A1.6, Pág. 103):** 3 minutos para M7/F7 y categorías superiores; 4 minutos para divisiones jóvenes.
   - **Unificación de Categorías (Category Combining, Art. A1.7, Pág. 104):** Criterios oficiales para fusionar divisiones de peso o edad cuando no se alcanza el quórum mínimo de competidores.
   - **Pesaje y Judogi para Veteranos (Art. A1.10 y A1.11, Pág. 105):** Normas adaptadas de pesaje y dorsales oficiales para torneos de veteranos.

5. **⚖️ Régimen Disciplinario, Integridad y Ética (Sección 1):**
   - **Comité Disciplinario de la IJF (Art. 1.2.1, Pág. 14):** Competencias para juzgar faltas a la ética, conductas antideportivas graves y trampas.
   - **Integridad Deportiva y Apuestas (Art. 1.2.2 y 1.2.3, Págs. 15-16):** Prohibición de manipulación de combates (*match fixing*) y sanciones federativas.
   - **Actos contra el Espíritu del Judo (Art. 18.2.2, Págs. 190-194):** Descalificación directa inmediata (*Hansoku-make*) por insultos, gestos despectivos, agresión deliberada o conductas contrarias a la moral del judo, con expulsión del torneo.

6. **🥋 Control de Judogi e Indumentaria (Apéndice C):**
   - Inspección previa en la mesa de control de Judogi (*Judogi Control Table*).
   - Medidas reglamentarias verificadas con el calibrador oficial **Sokuteiki** (cruce de solapa, holgura de mangas y pantalones).
   - Colores oficiales certificados: Blanco puro (*Snow white*) y Azul Pantone oficial (*Pantone 285M*).
   - Colocación de etiquetas de homologación de la IJF, parches publicitarios y dorsales oficiales (*Backnumbers*).

---

## 🏛️ Arquitectura del Sistema

```text
                     [ Consulta del Usuario (ES / EN) ]
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       Streamlit Frontend (app.py)                │
             │   - Selector de Tema Claro / Oscuro Nativo       │
             │   - Presentación Limpia (Nivel 1: Summary)       │
             │   - Tarjetas de Evidencias (Nivel 2: Citas/PDF)  │
             │   - Visor PDF Interactivo Integrado              │
             │   - Panel Técnico de Auditoría Plegable          │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │   Arbitration Decision Assistant (ADA v2.0)      │
             │   - Traductor Técnico Normativo Bilingüe         │
             │   - Coordinador de Razonamiento en Dos Niveles   │
             │   - Validador Normativo Anti-Alucinaciones       │
             │   - Extractor de Citas Textuales Completas       │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │   Reasoning Retrieval Engine (RRE v3.0)          │
             │   - Sparse BM25 + Dense FAISS/Embeddings         │
             │   - Re-ranker Semántico Topológico               │
             │   - Alineación Tópica (Topological Scoping)      │
             │   - Inmunidad Técnica de Judo                    │
             │   - Anclas de Dominio Negativo (Anti-OOD)        │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │   Multi-Provider LLM Manager                     │
             │   - Primario: Google Gemini Flash / Pro          │
             │   - Fallback: Groq (Llama-3-70B / 8B)            │
             │   - Respaldo: Motor Determinístico Local         │
             └──────────────────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │   Corpus Normativo Oficial IJF SOR 2026-08       │
             │   (298 Páginas Certificadas — SHA-256 Verificado)│
             └──────────────────────────────────────────────────┘
```

---

## 🛠️ Tecnologías y Librerías

- **Lenguaje:** Python 3.12+
- **Frontend Interactivo:** Streamlit 1.35+, HTML5 sanitizado, CSS dinámico con soporte total de modo claro y modo oscuro.
- **Modelos de Lenguaje (LLM):** Google Gemini API (`gemini-flash-lite-latest`, `gemini-1.5-flash`, `gemini-1.5-pro`) y Groq API.
- **Recuperación Vectorial y Búsqueda:** BM25 sparse + FAISS dense embeddings + Re-ranker semántico topológico.
- **Validación Normativa:** Modelos Pydantic v2, validador de integridad documental y verificación criptográfica SHA-256.
- **Infraestructura Cloud:** Oracle Cloud Infrastructure (OCI) — VM ARM64 Ampere A1 (Ubuntu 24.04 LTS), Docker Compose, Cloudflare Tunnel con certificado SSL/TLS inmutable en `https://sor.alxol.com`.

---

## 💡 Ejemplos de Consultas Reales Soportadas

| Dominio Reglamentario | Pregunta de Ejemplo | Fundamento y Cita Oficial |
| :--- | :--- | :--- |
| **Entrenadores (Coaches)** | *¿Cuál es el código de vestimenta de los entrenadores en el bloque final y eliminatorias?* | **Art. 7.2 (Pág. 89):** Traje formal obligatorio para finales/sorteo; chándal nacional oficial para eliminatorias. |
| **Antidopaje** | *¿Cómo es el procedimiento de selección para el control de dopaje en eventos IJF?* | **Art. E1.6.2 (Pág. 203):** Sorteo oficial del Comisionado Médico con el delegado IJF y firma de protocolo. |
| **Veteranos / Masters** | *¿Cuáles son las divisiones de edad y la duración del combate para veteranos?* | **Art. A1.4 y A1.6 (Pág. 103):** Divisiones M1 a M11; tiempos de combate de 3 y 4 minutos según categoría. |
| **Régimen Disciplinario** | *¿Qué facultades y sanciones aplica el Comité Disciplinario de la IJF?* | **Art. 1.2.1 (Pág. 14):** Medidas disciplinarias por trampas, faltas éticas o conductas contrarias a los valores del judo. |
| **Conducta y Respeto** | *¿Si un competidor insulta o agrede a otro, qué procede?* | **Art. 18.2.2 (Págs. 190, 193):** Hansoku-make directo inmediato por actos contra el espíritu del judo; no puede continuar en el torneo. |
| **Cadetes (Técnicas)** | *¿Cómo se sanciona el reverse seoi-nage en cadetes?* | **Art. 18.1.4 (Pág. 189):** Sin puntuación y Shido inmediato a Tori. |
| **Seguridad Cervical** | *¿Se permite defenderse haciendo un puente tras ser proyectado?* | **Art. 14.2 (Pág. 166):** Todo puente voluntario tras proyección se evalúa como Ippon para Tori por seguridad cervical. |
| **Judogi y Medidas** | *¿Cuáles son las medidas y colores reglamentarios del Judogi?* | **Regla C1.1 y C1.9 (Págs. 115, 124):** Dimensiones verificadas con Sokuteiki; colores blanco nieve y azul Pantone 285M. |

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Alxs68/IJF-SOR-Assistant.git
cd IJF-SOR-Assistant
```

### 2. Crear y Activar Entorno Virtual
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno (Opcional para Modo Conectado)
Crear un archivo `.env` en la raíz del proyecto:
```env
GEMINI_API_KEY="tu-api-key-de-gemini"
# Opcional para proveedor de respaldo:
GROQ_API_KEY="tu-api-key-de-groq"
```
*(Si no se configuran claves, el sistema opera automáticamente en **Modo Local Desconectado Certificado**).*

### 5. Iniciar la Interfaz Web
```bash
streamlit run app.py
```
Acceder en el navegador a `http://localhost:8501`.

---

## 🧪 Ejecución de Pruebas Unitarias y Regresión

El proyecto cuenta con una batería de pruebas exhaustiva que valida la gobernanza, la precisión de citas y la respuesta sin alucinaciones:

```bash
# Ejecutar suite de validación completa:
python -m pytest tests/test_citation_highlighting_regression.py \
                 tests/test_citation_highlighting.py \
                 tests/test_response_structurer.py \
                 tests/test_ood_detector.py \
                 tests/test_p1_a_abstention_ood.py -v
```

---

## ☁️ Despliegue en Producción (Oracle Cloud Infrastructure - OCI)

La versión de producción está contenerizada mediante **Docker Compose** en una instancia VM de OCI detrás de un túnel seguro de Cloudflare:

```bash
# Conectar al servidor de producción vía SSH:
ssh ubuntu@149.130.187.132

# Actualizar a la versión más reciente de main:
cd /home/ubuntu/IJF-SOR-Assistant
git pull origin main

# Reiniciar el contenedor de Streamlit:
sudo docker compose restart streamlit
```

Verificar la disponibilidad del servicio:
```bash
curl -I https://sor.alxol.com
```

---

## ⚖️ Gobernanza y Autoridad Documental

- **Autoridad Normativa y Product Owner:** Alexis Oliveros Lozano
- **Norma Primaria Oficial:** International Judo Federation (IJF) Sport and Organisation Rules (SOR), 14 de agosto de 2026.
- **Hash SHA-256 del PDF Oficial:** `9426B10D11C21A4CB9EB23150C2C4FC95BFCD463511E66BA451D2CFF005AE620`
- **Trazabilidad:** Cada respuesta generada enlaza directamente a la página física correspondiente del PDF oficial accesible desde el visor integrado.
