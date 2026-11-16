# INFORME DE CIERRE — PASO 2: EXPANSIÓN LÉXICA DE TÉRMINOS COLOQUIALES DE JUDO
**Proyecto:** IJF SOR Assistant  
**Fase:** Reorientación Funcional Lean (Post-Diagnóstico)  
**Autoridad y Aprobación:** Alexis Oliveros Lozano  
**Ejecutor:** Antigravity  
**Fecha:** 2026-11-06  

---

## 1. RESUMEN EJECUTIVO

Siguiendo la instrucción directa de Alexis Oliveros Lozano (*"paso 2 primero"*) y las precisiones técnicas sobre la jerga del judo (*"al hablar de pretina quiere decir cinturon"* y *"faldon de la chaqueta o del gi"*), se ha implementado la expansión léxica dirigida en el motor de búsqueda `src/rre_engine.py`.

### Resultados Clave:
1. **Precisión Coloquial Inmediata (Top 1):** Las 4 consultas representativas que antes se degradaban a páginas irrelevantes ahora recuperan con exactitud milimétrica la norma y el artículo sancionatorio aplicable en el Top 1.
2. **Cero Regresiones (100% PASS):** Se ejecutó la batería completa de regresión del sistema. Pasaron las 267 pruebas existentes previas más 4 pruebas automatizadas nuevas de regresión dedicadas, totalizando **271 pruebas aprobadas (271 passed, 0 failed)** en 53 segundos.
3. **Corpus y Embeddings Intactos:** No se tocó ningún índice, embedding ni archivo del corpus canónico.

---

## 2. RESULTADOS COMPARATIVOS ANTES VS. DESPUÉS

| Consulta de Usuario (Coloquial / Real) | Antes del Paso 2 | Después del Paso 2 (Top 1) | Resultado Normativo |
| :--- | :--- | :--- | :--- |
| *"rodilla palanca en ne-waza"* | Página 159 (Conceptos generales / Waza) | **Artículo 18.2.2 (Página 191)** | **Hansoku-make directo** (armlocks fuera del codo) |
| *"estrangular con la pretina o faldon desatado"* | Página 124 (Fabricación de judogis) | **Artículo 18.1.2 (Página 184)** | **Shido** (acción prohibida con faldón o cinturón) |
| *"meter el pie en la solapa o cinturon"* | Página 186 (Salida de tatami) | **Artículo 18.1.2 (Página 184)** | **Shido** (introducir extremidad en prendas) |
| *"tirarse de cabeza voluntario"* | Página 191 (Otras faltas) | **Artículo 18.2.1 (Página 190)** | **Hansoku-make directo** (Diving / caída sobre la cabeza) |

---

## 3. VOCABULARIO INCORPORADO EN `src/rre_engine.py`

En estricta conformidad con las directrices de Alexis, se agregaron y calibraron las siguientes entradas en `SPANISH_TO_ENGLISH_SYNONYMS`:

- **Faldón:** `skirt bottom shime-waza` *(conecta con el faldón de la chaqueta/gi y las técnicas de estrangulación prohibidas)*.
- **Cinturón / Cinturones:** `belt shime-waza encircle` *(conecta con el uso indebido del cinturón para rodear o estrangular)*.
- **Pretina:** `belt shime-waza encircle` *(interpreta coloquialismos de practicantes redirigiéndolos al cinturón)*.
- **Rodilla / Rodillas / Tobillo / Tobillos:** `joint knee/ankle ashi-garami kansetsu-waza elbow` *(conecta articulaciones anatómicas de miembros inferiores con las prohibiciones de palancas)*.
- **Palanca / Palancas:** `kansetsu-waza joint lock armlock` *(conecta el término coloquial "palanca" con las técnicas oficiales de luxación)*.
- **Desatado / Desatada:** `unfastened untied shime-waza` *(identifica la condición de prenda suelta para las infracciones del Art. 18)*.
- **Tirarse / Zambullirse:** `diving head` *(identifica el salto o clavado voluntario sobre la cabeza)*.
- **Meter / Pie:** `insert foot leg belt lapel` *(identifica la inserción de dedos/pies en solapas o cinturón)*.

---

## 4. SUITE DE PRUEBAS AUTOMATIZADA

Se creó el archivo de pruebas `tests/test_colloquial_judo_synonyms.py` para garantizar que en cualquier versión futura estas consultas mantengan su precisión canónica sin riesgo de degradación.

```bash
collected 271 items
tests/test_colloquial_judo_synonyms.py ....                              [100%]
============================== 271 passed in 53.06s ==============================
```
