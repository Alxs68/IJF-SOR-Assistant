# INFORME DE AUDITORÍA DE EXACTITUD NORMATIVA Y TRAZABILIDAD DOCUMENTAL
## IJF Sport and Organisation Rules (Edición Oficial 14 de Agosto de 2026)

**Proyecto:** `IJF-SOR-Assistant`  
**Ubicación local:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama examinada:** `review/ijf-sor-2026-08-rre-ada`  
**Commit base examinado:** `6a4b08de0a9821f4ff83291f111bfdbf78edfa6c`  
**Fecha de ejecución:** 2026-10-18 / 2026-10-19  
**Roles:** Antigravity (Ejecutor técnico y control de calidad) | ChatGPT (Planificador y auditor externo)  

---

## 1. Resumen Ejecutivo

Se realizó una auditoría técnica exhaustiva de exactitud normativa, trazabilidad documental y concordancia física sobre las cinco consultas de evaluación funcional registradas en `scratch/audit_diagram_queries_results.json`.

Todas las afirmaciones sustantivas emitidas en las respuestas generadas fueron desglosadas atómicamente y cotejadas de forma binaria contra el PDF oficial de la Federación Internacional de Judo (`IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`), los textos brutos extraídos (`pages_raw/page_XXX.txt`), los 385 pasajes indexados y las inspecciones visuales renderizadas a 150 DPI.

**Dictamen General:** **`APROBADO CON RESERVAS`**  
- **Justificación:** Las consultas referidas a diagramas y cuadros de competición específicos (Q1 pág. 213, Q2 pág. 222 y Q3 pág. 225) presentan un respaldo normativo directo del 100% en sus reglas sustantivas de combate, orden de desempate, indumentaria y clasificación. Las limitaciones de representación geométrica se declaran con total transparencia. La reserva técnica se circunscribe a las consultas marco y anafóricas (Q4 y Q5), en las cuales la respuesta determinista de respaldo se focaliza en las reglas de competencia y sorteo general (Art. General, Sección 5, pág. 70-71) sin citar expresamente el catálogo de formularios F1.3 (págs. 208-240) como repositorio documental de plantillas oficiales.

---

## 2. Verificación Criptográfica y Autenticidad del PDF y Enlaces

### 2.1 Verificación de Integridad Binaria del PDF Local
Se calculó el hash criptográfico SHA-256 del archivo físico en disco mediante streaming de chunks de 1 MB:
- **Ruta del archivo:** `C:\PROYECTOS\IJF-SOR-Assistant\data\raw\sor_2026_08_rebuild\IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`
- **Tamaño verificado:** `29.664.780` bytes.
- **SHA-256 Calculado:** `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`
- **SHA-256 Esperado:** `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`
- **Resultado:** **COINCIDENCIA BINARIA EXACTA (100% AUTÉNTICO)**.

### 2.2 Verificación de la URL Externa y Anclas de Página
Se realizó una solicitud de cabecera HTTP `HEAD` sobre la URL oficial empleada en los pasajes indexados:
- **URL Base:** `https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf`
- **Código de Estado HTTP:** `200 OK`
- **Content-Length:** `29.664.780` bytes (idéntico byte por byte al archivo local).
- **Content-Type:** `application/pdf`
- **Last-Modified:** `Sat, 22 Aug 2026 20:35:04 GMT`
- **Correspondencia de Anclas `#page=N`:** Las anclas generadas por el asistente (`#page=38`, `#page=39`, `#page=70`, `#page=71`, `#page=213`, `#page=222`, `#page=225`) corresponden estrictamente al índice físico 1-indexed del documento oficial, coincidiendo con la numeración impresa visible en el pie de página de cada hoja del PDF.

---

## 3. Matriz de Auditoría de Exactitud Normativa (Q1 a Q5)

Cada afirmación factual y normativa contenida en las respuestas generadas fue clasificada según la taxonomía requerida:
- **[RD]** Respaldada directamente por el texto del PDF oficial.
- **[RP]** Respaldada parcialmente.
- **[INF]** Inferencia lógica identificada como tal.
- **[NR]** No respaldada o contradictoria.
- **[NV]** No verificable con el material disponible.

```
+----+---------------------------------------------------------------+-----------------------+---------+--------+----------------+
| N° | Afirmación Evaluada en la Respuesta                           | Fuente Exacta SOR     | Art.    | Pág.   | Clasificación  |
+----+---------------------------------------------------------------+-----------------------+---------+--------+----------------+
| Q1 | El cuadro de la pág. 213 es Direct Knockout (F1.3.6).         | Texto extraído PDF    | F1.3.6  | p. 213 | [RD] Respaldad.|
| Q1 | El sistema es de eliminación directa sin repesca.             | 2.5.1 Direct Knockout | 2.5.1   | p. 38  | [RD] Respaldad.|
| Q1 | En hoja de sorteo: competidor superior blanco, inferior azul. | 2.5 Competition Syst. | 2.5     | p. 38  | [RD] Respaldad.|
| Q1 | Perdedores de semifinales reciben medalla de bronce.          | 2.5.1 Direct Knockout | 2.5.1   | p. 38  | [RD] Respaldad.|
| Q1 | Ganadores de semifinales compiten por oro y plata.            | 2.5.1 Direct Knockout | 2.5.1   | p. 38  | [RD] Respaldad.|
| Q1 | Los cuatro perdedores de cuartos clasifican igualados 5.º.    | 2.5.1 Direct Knockout | 2.5.1   | p. 38  | [RD] Respaldad.|
| Q1 | La geometría detallada del cuadro no está codificada en texto | Declaración en límite | N/A     | N/A    | [INF] Identif. |
+----+---------------------------------------------------------------+-----------------------+---------+--------+----------------+
| Q2 | El cuadro de la pág. 222 es Double Repechage hasta 8 atletas. | Texto extraído PDF    | F1.3.15 | p. 222 | [RD] Respaldad.|
| Q2 | Se divide a los atletas en dos tablas mediante sorteo.        | 2.5.3 Double Repech.  | 2.5.3   | p. 38  | [RD] Respaldad.|
| Q2 | Eliminación directa para producir dos finalistas (oro/plata). | 2.5.3 Double Repech.  | 2.5.3   | p. 38  | [RD] Respaldad.|
| Q2 | Atletas que perdieron con los semifinalistas van a repesca.   | 2.5.3 Double Repech.  | 2.5.3   | p. 38  | [RD] Respaldad.|
| Q2 | Ganadores de repescas disputan bronce vs perdedor semi opuesta| 2.5.3 Double Repech.  | 2.5.3   | p. 38  | [RD] Respaldad.|
| Q2 | Los dos ganadores de esos combates son terceros (dos bronces).| 2.5.3 Double Repech.  | 2.5.3   | p. 38  | [RD] Respaldad.|
| Q2 | La cuadrícula gráfica requiere inspección visual en PDF p.222 | Declaración en límite | N/A     | N/A    | [INF] Identif. |
+----+---------------------------------------------------------------+-----------------------+---------+--------+----------------+
| Q3 | Pág. 225 corresponde a Five Athletes/Teams - Option 1.        | Texto extraído PDF    | F1.3.18 | p. 225 | [RD] Respaldad.|
| Q3 | Cada competidor se enfrenta contra todos los demás.           | 2.5.5 Round Robin     | 2.5.5   | p. 39  | [RD] Respaldad.|
| Q3 | En grupo de 5 se disputan 10 combates en total.               | C(5,2)=10 combates    | 2.5.5   | p. 39  | [RD] Respaldad.|
| Q3 | Regla 1 desempate: Número de combates ganados.                | 2.5.5.1 Regla 1       | 2.5.5.1 | p. 39  | [RD] Respaldad.|
| Q3 | Regla 2 desempate: Suma total de puntos (Ippon=100, Waza=10). | 2.5.5.1 Regla 2       | 2.5.5.1 | p. 39  | [RD] Respaldad.|
| Q3 | Regla 3 desempate: Comparación directa entre empatados.       | 2.5.5.1 Regla 3       | 2.5.5.1 | p. 39  | [RD] Respaldad.|
| Q3 | Regla 4 desempate: Menor número acumulado de shidos (HM = 3). | 2.5.5.1 Regla 4       | 2.5.5.1 | p. 39  | [RD] Respaldad.|
| Q3 | Regla 5 desempate: Tiempo acumulado de victorias (menor gana).| 2.5.5.1 Regla 5       | 2.5.5.1 | p. 39  | [RD] Respaldad.|
| Q3 | Regla 6 desempate: Concursos de desempate Golden Score / WRL. | 2.5.5.1 Regla 6       | 2.5.5.1 | p. 39  | [RD] Respaldad.|
| Q3 | Se advierte que el diagrama visual gráfico reside en PDF.     | Declaración en límite | N/A     | N/A    | [INF] Identif. |
+----+---------------------------------------------------------------+-----------------------+---------+--------+----------------+
| Q4 | Las Competition Rules son responsabilidad de IJF Sport Comm.  | Portada Sección 2     | General | p. 30  | [RD] Respaldad.|
| Q4 | El sorteo (DRAW) es responsabilidad de IJF Sport Commission.  | Portada Sección 5     | General | p. 70  | [RD] Respaldad.|
| Q4 | El sorteo se rige por Art. 5.1 (momento, lugar, publicación). | 5.1 Draw Regulations  | 5.1     | p. 71  | [RD] Respaldad.|
| Q4 | Respuesta no describe directamente los formatos 2.5.1-2.5.5.  | Brecha contextual     | 2.5     | p. 38  | [RP] Parcial   |
+----+---------------------------------------------------------------+-----------------------+---------+--------+----------------+
| Q5 | El sorteo (DRAW) es responsabilidad de IJF Sport Commission.  | Portada Sección 5     | General | p. 70  | [RD] Respaldad.|
| Q5 | La lista y sorteo se publican en tablón/medios IJF.           | 5.1 Draw Regulations  | 5.1     | p. 71  | [RD] Respaldad.|
| Q5 | Omite citar expresamente que las plantillas están en F1.3.    | Omisión de catálogo   | F1.3    | p. 208 | [RP] Parcial   |
+----+---------------------------------------------------------------+-----------------------+---------+--------+----------------+
```

---

## 4. Evidencia de Verificación Visual de los Diagramas (Páginas 213, 222 y 225)

Las páginas físicas fueron inspeccionadas a partir de sus mapas vectoriales nativos y renderizados a 150 DPI archivados en `docs/audit_appendix_e/evidencias_visuales/`:

1. **Página Física 213 (`page_213.png`):**
   - **Elementos:** 288 trazos vectoriales, 68 imágenes ráster (marcas/logos IJF), 100 caracteres de texto (`F1.3.6 Direct Knockout`).
   - **Estructura Gráfica:** Representa un árbol binario completo de eliminación directa con cajas vacías distribuidas jerárquicamente de izquierda a derecha. No contiene nombres de competidores ni asignaciones de cabezas de serie predefinidas.
   - **Conclusión de Integridad:** La deducción del asistente de que se trata de un árbol eliminatorio sin repesca concuerda 100% con la geometría visible y el Artículo 2.5.1.
2. **Página Física 222 (`page_222.png`):**
   - **Elementos:** 82 trazos vectoriales, 0 imágenes ráster, 128 caracteres de texto (`F1.3.15 Double Repechage up to 8 Athletes or Teams`).
   - **Estructura Gráfica:** Muestra dos bloques principales de 4 atletas cada uno (Tablas A y B), con ramas conectoras hacia semifinales y final, y en la zona inferior dos bloques de repesca independientes que conectan con los encuentros por medalla de bronce.
   - **Conclusión de Integridad:** La descripción funcional del asistente (dos tablas de 4, repesca para los perdedores ante semifinalistas y duelos cruzados por bronce) representa fielmente el flujo geométrico del diagrama.
3. **Página Física 225 (`page_225.png`):**
   - **Elementos:** 136 trazos vectoriales, 0 imágenes ráster, 177 caracteres de texto (`F1.3.18 Five (5) Athletes or Teams - Option 1`).
   - **Estructura Gráfica:** Representa una matriz tabular de cuadrícula para 5 atletas con números de emparejamiento (1 al 10) organizados por rondas de combate.
   - **Conclusión de Integridad:** El texto extraído contiene únicamente números sueltos (`1, 3, 4, 2, 6, 5...`); la respuesta del asistente no alucinó la posición de las casillas, sino que explicó con absoluta precisión el sistema matemático y normativo de todos contra todos conforme al Artículo 2.5.5.1.

---

## 5. Resultados de las Pruebas de Ejecución en Limpio

Durante esta auditoría no se reutilizaron resultados históricos. Se ejecutaron en tiempo real los tests relevantes y las 5 consultas funcionales:

### 5.1 Ejecución en Tiempo Real de las 5 Consultas Funcionales
- Script ejecutado: `python scratch/run_diagram_queries.py`.
- Resultado: **5 / 5 consultas respondidas con estado `SUCCESS`**.
- Metadatos guardados en: `scratch/audit_diagram_queries_results.json`.

### 5.2 Suite de Proveedor y Fallback (`tests/test_llm_provider.py`)
- Comando: `python -m pytest tests/test_llm_provider.py -v`
- Total pruebas ejecutadas: **16 pruebas**.
- Aprobadas: **16 passed (100%)**.
- Duración: **12.79 segundos**.
- Componentes validados: Fallback automático, control estricto de cuota 429, redacción de secretos, modo determinista fuera de línea y abstención estricta OOD en baloncesto/F1 sin llamar al LLM.

### 5.3 Suite de Prevención de Alucinaciones, Estructura y Arquitectura
- Comando: `python -m pytest tests/test_normative_hallucinations.py tests/test_response_structurer.py tests/test_rre_ada_architecture.py tests/test_rebuild_integration.py -q`
- Total pruebas ejecutadas: **36 pruebas**.
- Aprobadas: **36 passed (100%)**.
- Duración: **19.11 segundos**.
- Componentes validados: Prevención de sanciones inexistentes (PS34 en cadetes), control de firmas de supervisores, verificación SHA-256 de PDF oficial y contrato de dos niveles.

---

## 6. Defectos Confirmados y Limitaciones Pendientes

### Defectos Confirmados:
- **D-AUD-01 (Bajo — Cobertura contextual en consulta anafórica Q4):** Ante la pregunta aislada *"¿Qué reglas determinan el sistema de competición aplicable a esos cuadros?"*, la recuperación RRE se ancla a las portadas generales de Competencia (pág. 30) y Sorteo (pág. 70-71). Aunque esto es técnicamente verídico (el sorteo y las reglas generales de competencia rigen los cuadros), no se recuperó el Artículo 2.5 (*Competition Systems*, pág. 37-38) que define los criterios específicos de asignación de sistemas (knockout vs repechaje según número de participantes).
- **D-AUD-02 (Bajo — Remisión a catálogo de plantillas en Q5):** Ante la pregunta general *"¿Dónde puedo consultar el diagrama oficial correspondiente?"*, la respuesta orienta a la Sección de Sorteo (pág. 70-71) y a los canales oficiales de la IJF, omitiendo mencionar explícitamente el Apéndice F (Sección F1.3, págs. 208-240) donde residen las plantillas maestras en blanco.

### Limitaciones Pendientes:
- **L-AUD-01 (Naturaleza no vectorial del LLM):** El sistema opera como asistente de texto estructurado; no renderiza llaves interactivas ni diagramas SVG. Cumple rigurosamente el protocolo de advertir al usuario en `limitations` que para la representación gráfica debe consultar el PDF oficial en los anclajes provistos.

---

## 7. Dictamen Final

### **DICTAMEN: APROBADO CON RESERVAS**

**Fundamentos del Dictamen:**
1. **Autenticidad y Trazabilidad Verificada:** El PDF analizado es 100% auténtico (SHA-256 coincidente), la URL remota está activa y las anclas `#page=N` conducen exactamente a las páginas físicas normativas correspondientes.
2. **Cero Alucinaciones en Consultas de Diagramas:** Las respuestas sobre las páginas 213, 222 y 225 presentan una concordancia perfecta con los Artículos 2.5.1, 2.5.3 y 2.5.5.1 del SOR 2026 oficial, diferenciando las reglas escritas de la geometría gráfica no codificada.
3. **Reserva Formal:** Se emite dictamen con reservas debido a que en consultas descontextualizadas (Q4 y Q5), el sistema entrega reglas marco válidas (sorteo y competencia general), pero no amplía la referencia hacia el catálogo documental de plantillas F1.3 ni a los umbrales de participación de la Sección 2.5/2.6.
