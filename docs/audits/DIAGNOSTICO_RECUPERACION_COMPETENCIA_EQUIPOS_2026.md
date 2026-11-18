# Diagnóstico de recuperación — competición de judo por equipos (SOR 2026)

**Fecha:** 17 de noviembre de 2026
**Tipo:** prueba de recuperación documental de solo lectura. No se llamó a ningún LLM, no se usó la red y no se tocó OCI.
**Resultados:** `experiments/competencia_equipos_2026/`
* `run_prueba_equipos.py`, SHA-256 `17f68fc1…`;
* `resultados_competencia_equipos.json`, SHA-256 `c0a8511a…`;
* `stdout_competencia_equipos.log`.

---

## Resumen ejecutivo

**Respuesta a la pregunta planteada: no.** Con la arquitectura y los recursos experimentales disponibles **no** existe capacidad real de recuperar y organizar toda la información necesaria para explicar una competición por equipos.

Ninguna de las seis configuraciones entrega más de **20 de los 49 fragmentos normativos imprescindibles**, y esa cifra solo la alcanza el RRE actual de producción.

**Lo que se perdió:**
* En ninguna configuración llegan al paquete:
  * el orden de los combates de equipos mixtos;
  * el procedimiento de desempate por sorteo y golden score;
  * la ceremonia y el cierre del encuentro (art. 9).
* Las tablas de categorías de peso solo llegan en las variantes por apartados, y el apartado que las regula (2.7.1) no llega en ninguna configuración.

**Las variantes experimentales empeoran el resultado frente a producción:**

| Configuración | Fragmentos imprescindibles entregados |
|---|---|
| Producción (A-prod) | 20/49 |
| Ventanas sobre páginas (C1) | 8/49 |
| Expansión jerárquica B4 (D) | 8/49 |
| Apartados (B) | 6/49 |
| Ventanas sobre apartados (C2) | 5/49 |

La evidencia sí existe en los índices: los 56 fragmentos de referencia están en el corpus por páginas y en `units.jsonl`, y casi todos aparecen en algún canal. Se pierde **al seleccionar el paquete**, no al extraer el PDF.

**Causa estructural.** El RRE entrega a ADA un paquete de **tamaño fijo**: 5 semillas y hasta 3 relacionados. Lo construye con **una sola consulta** y un **único ranking global**. Ninguna pieza descompone la pregunta en sus facetas, dimensiona el paquete según la cobertura necesaria ni recorre la estructura del documento hacia los subapartados y las referencias cruzadas.

La explicación correcta requiere como mínimo **12 unidades** (unos 22 000 caracteres) o **12 páginas**. Ni con un orden perfecto cabrían en 5 semillas.

Tres señales de ordenación agravan el problema:
* favorecen unidades cortas o vacías, como un encabezado de 47 caracteres o una página que solo contiene la cabecera del PDF;
* la fusión penaliza todo lo que aparece en un solo canal;
* la expansión B4 solo sube al padre y se mueve a los hermanos, nunca baja a los hijos.

Las variantes experimentales cambian la **unidad** que se recupera, pero no el **contrato de selección**. Por eso no resuelven esta consulta.

---

## 1. Recursos utilizados

| Recurso | Identificación |
|---|---|
| Repositorio | `C:\PROYECTOS\IJF-SOR-Assistant`, rama `exp/r3-dig-v2`, HEAD `d126873` (`d1268732c862…`) |
| Árbol de trabajo | Incluye los cambios FIX3 **sin commit**, ya presentes antes de esta prueba y no modificados aquí. `src/rre_engine.py` SHA-256 `a0318e88b4e9…` (contiene R1); `src/ada_assistant.py` `876b6ef50417…`; `app.py` `86c020a0b012…` |
| PDF oficial | `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`, SHA-256 `9426b10d11c2…` (verificado) |
| Corpus por páginas | `data/processed/rebuild_2026_08_corrected/`, 385 pasajes; `passages_candidate.json` `7d4634288997…` |
| Índice de apartados | `experiments/segmentacion_apartados_2026/index/` y `units.jsonl` (`812aa19d1838…`), 342 unidades |
| Ventanas sobre páginas | `experiments/ventanas_2026/windows_emb.npy` y `windows_meta.json`: 1021 ventanas de 220 tokens con solapamiento de 30 |
| Ventanas sobre apartados | `experiments/segmentacion_apartados_2026/index/windows_*`: 730 ventanas |
| Expansión B4 | Mecanismo de `experiments/reglas_rre_expansion_2026/eval_reglas_expansion.py` con nivel 4, S=2, MAX_ADD=8 y sin filtro, los límites fijados a priori en ese experimento. Se copió literalmente porque allí está definido dentro de `main()` y no se puede importar. **Fidelidad verificada:** reproduce exactamente las adiciones registradas en `results.json` (SW+B4) en las **82/82** consultas de DEV |
| Entorno | Python 3.12.10, MiniLM local (`HF_HUB_OFFLINE=1`) y claves de LLM vacías en el proceso |

**Configuraciones.** Ninguna es nueva: todas existían y estaban documentadas.

| Id | Qué es | Equivale a |
|---|---|---|
| **A-prod** | RRE tal como lo construye ADA (`ada_assistant.py:124-131`): `semantic_ranker`, desambiguador de órdenes, OOD y anclas negativas. Índice por páginas, R1 apagado, `top_k=5` (`rag_engine.query`, k=5) y `expand_graph=True` | Producción, en lo reproducible localmente |
| A-ref | Páginas, OOD y R1 encendido | «B» de los informes anteriores |
| **B** | Apartados con denso truncado y R1 | «S» |
| **C1** | Ventanas sobre páginas y R1 | «D» de `ventanas_2026` |
| **C2** | Ventanas sobre apartados y R1 | «SW» |
| **D** | C2 más la expansión jerárquica B4 | «SW+B4» |

**Integridad:**
* SHA-256 idéntico antes y después en los **20 archivos protegidos**: corpus, índices, `units.jsonl`, ventanas, `results.json` previo, `src/rre_engine.py`, `src/ada_assistant.py`, `app.py` y el PDF;
* `git status` idéntico antes y después;
* no se modificó ni se borró ningún artefacto previo.

## 2. Consulta ejecutada

Pregunta original, sin dividir ni reformular. Se usa como `domain_query`, igual que en ADA:

> «Explícame cómo se desarrolla una competencia de judo por equipos, desde la organización inicial hasta la finalización de los encuentros. Describe el sistema de competición, la composición de los equipos, el orden de los combates, las categorías de peso, cómo se determina el equipo ganador y qué sucede en caso de empate, de acuerdo con el SOR 2026».

En producción, ADA traduce la pregunta con el LLM antes de recuperar (`ada_assistant.py:410`). Como aquí no se puede usar el LLM, se aplicó el **mismo método de ADA**, `_translate_to_technical_english`, con el LLM no disponible. En esa situación ADA usa su **respaldo determinista por diccionario**, el mismo que se ejecuta si Gemini falla. Consulta de recuperación resultante, idéntica para todas las configuraciones:

```
explicame desarrolla competencia judo team teams encounter organizacion inicial finalizacion encuentros describe
system competition composicion orden combates categories weight determina ganador sucede caso empate acuerdo sor 2026
```

* El pre-chequeo de anclas negativas de ADA da `is_ood = False`.
* Todas las configuraciones devuelven `SUCCESS` en modo `HYBRID`.
* Cada recuperación tarda entre 45 y 54 ms; la carga de los motores, 15 s.

## 3. Disposiciones normativas del SOR (verificadas en el PDF)

Se leyeron directamente las páginas del PDF; la numeración impresa coincide con `pdf_page_index`. La normativa de equipos **está distribuida** entre las secciones 2, 6 y el artículo 9.

| Tema | Disposición | Pág. | Contenido normativo |
|---|---|---|---|
| Sistema de competición | **2.7** Competition System for Mixed Team and Team Events | 42 | IJF mixtos: eliminación con repesca de cuartos (remite a 2.5.2). Otros eventos: doble repesca, repesca completa o eliminación directa. *Match* = enfrentamiento entre dos equipos, formado por *contests* |
| | 2.5.2 Quarter-final Repechage | 38 | Descripción del sistema al que remite 2.7 |
| | 2.5 Competition Systems (tabla) | 37 | Sistema por tipo de evento, incluidos los mundiales y continentales por equipos mixtos |
| | 2.6 / 2.6.1 / 2.6.2 Low Numbers | 41-42 | De 1 a 5 equipos: sistemas para números bajos y medallas |
| | 2.5.5.2 Round Robin Rules for Team Events | 40 | Clasificación en round robin con las reglas 1 a 7 (encuentros ganados, combates ganados, puntos, enfrentamiento directo, shidos, tiempo y combate de decisión) |
| Composición | **2.7.1** Regulations for Mixed Team Events | 42-43 | 6 deportistas (3 mujeres y 3 hombres) más hasta 6 reservas. Máximo 12 inscritos, con 2 por categoría. Mínimo 4 tras lesión; con 3 no compite |
| | **2.7.2** Regulations for Female and Male Team Events | 45 | Hasta 5 deportistas y 5 reservas, mínimo 3. 10 inscritos con 2 por categoría |
| Categorías de peso | **2.2.2** (tablas: sénior y júnior, Juegos Olímpicos, cadetes) | 34 | Categorías de equipos mixtos |
| | **2.2.3** (tabla y nota) | 34 | Equipos mixtos en los Juegos Olímpicos; solo participan deportistas clasificados en las categorías individuales indicadas |
| | **2.2.4** (2 tablas) | 35 | Categorías de equipos femeninos y masculinos (sénior, júnior y cadete) |
| | 2.7.1 / 2.7.2 | 42 / 45 | Se puede competir en la propia categoría o en la inmediatamente superior; los cadetes, no |
| Orden de los combates | **2.7.1** más su tabla de ejemplo | 43 | Sorteo de la categoría inicial y rotación por rondas (ejemplo −73 kg). Selección por el jefe de equipo antes de cada encuentro. Listas 30 minutos antes de la primera ronda y 5 minutos después en las demás |
| | **2.7.2** | 46 | Equipos femeninos y masculinos: de la categoría más ligera a la más pesada |
| | Art. 9 a) | 153 | Entrada «en el orden del sorteo de categorías» |
| Ganador | **2.7.1** | 43-45 | Victorias por categorías vacías (1:0, 1:1, 0:0). Gana el primero que logra la mayoría de combates; en eventos IJF no se disputan los restantes. Incomparecencia, negativa a competir (hansoku-make directo) y resultado en caso de *forfeit* |
| | **2.7.2** | 46-47 | Igual para equipos femeninos y masculinos; el organizador decide si se disputan los combates restantes |
| Empate | **2.7.1** más dos tablas | 44-45 | Sorteo por ordenador de una categoría para un combate de golden score, con cuatro escenarios de exclusión. Reglas para el doble hansoku-make en el golden score, con tres escenarios |
| | 2.7.2 | 46 | «If there are an equal number of wins at the end of the match **see Section 2.7.1**» (remisión) |
| | Art. 9 f) | 154 | Procedimiento en el tatami para el sorteo y el combate extra |
| Desarrollo y finalización | **Art. 9** Start of the Contest (equipos) | 153-154 | Saludo entre equipos, tres árbitros con dos combates cada uno, saludo final en orden inverso y anuncio del ganador |
| | 2.7.1 / 2.7.2 | 43 / 46 | Duración: 4 minutos por combate. Entrenadores y médico en el área de competición, zona delimitada y reservas fuera |
| Organización inicial | 2.7.1 | 42-43 | Confirmación en la acreditación; composición del equipo antes de las 13:00 del día anterior |
| | 2.7.2 | 45 | La lista puede actualizarse antes del pesaje oficial |
| | 6.4 / 6.5 Weigh-in | 80-87 | Pesaje de equipos mixtos y de equipos femeninos y masculinos (remiten a 2.7.1 y 2.7.2) |

**Lo que el SOR no regula expresamente en estas secciones:**
* no hay un apartado único de «organización inicial»: se reparte entre la acreditación, la confirmación, el pesaje y las listas;
* la duración de 4 minutos se fija dentro de 2.7.1 y 2.7.2, no en una tabla propia de equipos.

**Fuente que no debe usarse:** las páginas 259-298 (H1.1 *Document Version History*) repiten versiones antiguas de estas tablas, con texto tachado. No es normativa vigente.

**Conjunto de referencia.** Se definieron **56 fragmentos literales** del PDF, cada uno asociado a una página: 49 imprescindibles y 7 complementarios (números bajos, round robin y pesaje). Están en `resultados_competencia_equipos.json` → `referencia`.
* Los 56 se verificaron en el texto del PDF con PyMuPDF.
* Los 56 están en el corpus por páginas y en alguna unidad de `units.jsonl`.
* La extracción solo presenta un artefacto, el espacio antes del punto («Rule 1 .», «2 .2 .4»), que se neutraliza al normalizar.

**Conjunto mínimo para una explicación correcta:** 12 unidades, con 22 076 caracteres, o 12 páginas, con 29 767.
* **Unidades:** SEC-0053 (2.7), SEC-0054 (2.7.1), SEC-0055 (2.7.2), SEC-0037 (2.2.3), SEC-0041 (2.5), SEC-0043 (2.5.2) y SEC-0183 (art. 9), más las tablas TAB-0006, TAB-0008, TAB-0010, TAB-0011 y TAB-0016.
* **Páginas:** 34, 35, 37, 38, 42-47, 153 y 154.

Solo 2.7.1 y 2.7.2 contienen **33 de los 49** fragmentos imprescindibles.

## 4. Resultados de A, B, C y D

**Paquete** = lo que llega a ADA: evidencia del top-5 más relacionados (`related_passages`, máximo 3) y, en D, las unidades añadidas por B4.

### A-prod: RRE actual, configuración de producción

| # | Pasaje | Contenido | Págs. entregadas |
|---|---|---|---|
| 1 | P042-S053 | 2.7 (página 42 completa, que incluye el inicio de 2.7.1) | 42 |
| 2 | P086-S102, cosido | 6.5 Weigh-in de equipos | 84-87 |
| 3 | P082-S100, cosido | 6.4.2 Weigh-in de equipos mixtos | 81-82 |
| 4 | P045-S055, cosido | **2.7.2 completo** | 45-46 |
| 5 | P105-S133 | A1.13 *Competition System for Veterans* (no pertinente) | 105 |

* No hay relacionados.
* Suplementarios: tres de LA28 (cuota olímpica, equipo mixto olímpico y período de calificación), que son fuentes de nivel no normativo.
* Paquete: 22 840 caracteres.
* **Fragmentos imprescindibles entregados: 20/49.** Es la mejor configuración.

### A-ref: páginas con R1

Primeros puestos iguales a A-prod. **R1 sustituye P105 y P045 (2.7.2)** por P091-S106 y P231-S254:
* **P091 es una página con solo la cabecera del PDF**: 75 caracteres, «Sport and Organisation Rules of the International Judo Federation / page - 91»;
* P231 es un ejemplo de *Winners' List*.

Resultado: 8/49 y 18 693 caracteres.

### B: apartados con denso truncado

| # | Unidad | Contenido |
|---|---|---|
| 1 | SEC-0038 | 2.2.4: **solo el encabezado**, 47 caracteres |
| 2 | SEC-0053 | 2.7 (570 caracteres) |
| 3 | SEC-0036 | 2.2.2: solo el encabezado, 76 caracteres |
| 4 | SEC-0120 | a1.1 Veteranos (no pertinente) |
| 5 | SEC-0255 | f1.3.23, ejemplo de cuadro (campeón R1, no pertinente) |

* Relacionados por `has_table`: TAB-0010, TAB-0011 y TAB-0006.
* **6/49** y 4 891 caracteres.
* Las tablas sí llegan por la relación `has_table`, pero **2.7.1 y 2.7.2 quedan en los puestos 16 y 20 de la fusión**.

### C: ventanas semánticas

**C1, ventanas sobre páginas:** el top-5 es P105 (veteranos), P042, P086, P082 y **P091 (página con solo la cabecera)**. R1 vuelve a sustituir a P045, es decir, 2.7.2. Resultado: 8/49 y 17 885 caracteres.

**Ventanas mejor puntuadas en C1** (`ventanas.C1`): la ventana número 1, con similitud 0,704, es la ventana de 12 tokens de P091, que **solo contiene la cabecera**. Lo mismo ocurre en P087 y en P069, la acreditación. Las demás son, sobre todo, veteranos, formularios del anexo F y glosario.

Solo 3 de las 25 primeras ventanas contienen texto de referencia:
* la número 16, de p42 (2.7), con SIS-7;
* las números 20 y 22, de **H1.1 *Document Version History*** (págs. 281 y 277). Es texto histórico con el mismo contenido que 6.5 y 2.2.2, y el RRE lo atenúa y lo filtra.

**C2, ventanas sobre apartados:** el top-5 es SEC-0038 (encabezado de 2.2.4), SEC-0102 (6.5), SEC-0053 (2.7), SEC-0036 (encabezado de 2.2.2) y SEC-0258 (f1.3.26, formulario de alineación, campeón R1). Resultado: **5/49** y 9 375 caracteres.

**Ventanas mejor puntuadas en C2:** formularios f1.3.x, el encabezado 2.2.4, glosario y el historial H1.1. Solo 1 de las 25 primeras contiene texto de referencia: la número 19, de 2.7. Ninguna es de 2.7.1, de 2.7.2 ni del art. 9.

**¿Encuentran las ventanas algo que el índice actual pierde?** **No en esta consulta.**
* La similitud de 2.7.1 mejora frente al denso truncado (de 0,443 a 0,482), pero solo sube del puesto 85 al 63 del canal denso. Sigue fuera del corte de 25 que usa el RRE.
* Sobre páginas, las ventanas empeoran a P042-S054 (2.7.1), que pasa del puesto 12 al 28.

### D: expansión jerárquica B4 sobre C2

**Unidades que incorpora** (8, el máximo):

| Unidad | Origen |
|---|---|
| 2.2 (padre de 2.2.4) | expansión desde 2.2.4 |
| 2.2.3 (hermano) | expansión desde 2.2.4 |
| TAB-0009 | tabla contenida en 2.2.3 |
| TAB-0006, TAB-0007, TAB-0008 | tablas de 2.2.2, el hermano ya presente |
| PORTADA *weigh-in* (padre de 6.5) | expansión desde 6.5 |
| 6.4 (hermano de 6.5) | expansión desde 6.5 |

**Unidades que descarta** (`configs.D.descartadas`):
* por alcanzar MAX_ADD=8: 2.2.1 con sus tablas, 6.3, TAB-0035 (tabla de 6.5), TAB-0030, la PORTADA *competition rules*, y **2.6 y 2.8** (hermanos de 2.7);
* por el límite S=2 de hermanos: 2.5, 2.4, 2.3 y 2.1, y treinta formularios f1.3.x.

**Lo que B4 no puede añadir aunque no hubiera límites: 2.7.1 y 2.7.2.** Son **hijos** de la semilla 2.7 (SEC-0053), y el mecanismo solo sube al padre y recorre a los hermanos y sus tablas.

Resultado: **8/49** y 11 686 caracteres. Mejora las categorías de peso (5/7) y no recupera nada de composición, orden, ganador, empate ni desarrollo.

## 5. Comparación de cobertura y pertinencia

Fragmentos imprescindibles entregados, por faceta:

| Faceta (n) | A-prod | A-ref | B | C1 | C2 | D |
|---|---|---|---|---|---|---|
| Sistema (5) | 3 | 3 | 3 | 3 | 3 | 3 |
| Composición (6) | **6** | 3 | 0 | 3 | 0 | 0 |
| Orden de combates (8) | 2 | 0 | 0 | 0 | 0 | 0 |
| Categorías de peso (7) | 2 | 1 | 3 | 1 | 2 | **5** |
| Ganador (5) | 1 | 0 | 0 | 0 | 0 | 0 |
| Empate (6) | 2 | 0 | 0 | 0 | 0 | 0 |
| Desarrollo y finalización (9) | 2 | 0 | 0 | 0 | 0 | 0 |
| Organización inicial (3) | 2 | 1 | 0 | 1 | 0 | 0 |
| **Total imprescindibles (49)** | **20** | 8 | 6 | 8 | 5 | 8 |
| Total con complementarios (56) | 22 | 10 | 6 | 10 | 6 | 10 |
| Caracteres del paquete | 22 840 | 18 693 | 4 891 | 17 885 | 9 375 | 11 686 |

Clasificación de los 56 fragmentos:

| Estado | A-prod | A-ref | B | C1 | C2 | D |
|---|---|---|---|---|---|---|
| Entregada | 22 | 10 | 6 | 10 | 6 | 10 |
| Desplazada: en el ranking fusionado (top-40), fuera del paquete | 11 | 18 | 37 | 18 | 36 | 34 |
| En un canal, eliminada en la fusión | 1 | 1 | 0 | 1 | 0 | 0 |
| Fuera del corte de canal (puestos 26 a 60) | 18 | 23 | 10 | 21 | 10 | 10 |
| Nunca recuperada (fuera del top-60 de ambos canales) | 4 | 4 | 3 | 6 | 4 | 2 |

**Respuesta a las preguntas de la sección 5 de la instrucción:**

| Pregunta | A-prod | B | C1 / C2 | D |
|---|---|---|---|---|
| ¿Todos los apartados necesarios? | No: faltan 2.7.1 (págs. 43-44), 2.2.x, 2.5.2 y el art. 9 | No: faltan 2.7.1, 2.7.2, 2.5.2 y el art. 9 | No | No: faltan 2.7.1, 2.7.2, 2.5.2 y el art. 9 |
| ¿Tablas pertinentes? | No (ni las tablas de peso ni las de golden score de la pág. 44) | Parcial: 2.2.4 y una de 2.2.2 | C2: solo 2.2.4 | 2.2.2-2.2.4 sí; TAB-0016 (rotación) no |
| ¿Referencias cruzadas? | No: 2.7.2 remite a 2.7.1 para el empate y 2.7.1 no está | No: 2.7 remite a 2.5.2 y 2.5.2 no está | No | No |
| ¿Continuidad entre apartados? | Sí dentro de 2.7.2 y de 6.5 (cosido). **No** de 2.7 a 2.7.1 | Las unidades son completas, pero falta la que importa | No | No (no baja a los hijos) |
| ¿Información irrelevante? | Veteranos A1.13 y unos 12 000 caracteres de pesaje (pertinencia periférica) | Veteranos a1.1 y formulario f1.3.23 | Página con solo la cabecera, veteranos y formularios | PORTADA *weigh-in* y 2.2 (sin contenido operativo) |
| ¿Pérdida en fusión o expansión? | Sí: pág. 44 en el puesto 7, pág. 41 en el 6 y 2.5.2 eliminada por el umbral | Sí: 2.7.1 en el 16 y 2.7.2 en el 20 | Sí, además de lo que desplaza R1 | Sí: MAX_ADD se agota en tablas de peso y pesaje |
| ¿Permite una explicación completa? | **No.** Permite explicar la composición y las reglas de 2.7.2; no el orden de los equipos mixtos, el desempate, las categorías ni el art. 9 | **No** | **No** | **No** |

## 6. Evidencia perdida y causas demostradas

| Evidencia | Dónde se pierde | Causa demostrada (en `resultados_competencia_equipos.json`) |
|---|---|---|
| **2.7.1, págs. 43-44** (orden, ganador y empate de equipos mixtos) | A: p44 en el puesto 7 de la fusión y p43 en el 27 de TF-IDF, sin aparecer en el denso. B y C2: SEC-0054 en el puesto 16 de la fusión | **Paquete fijo de 5.** Además, por la **bonificación de concordancia**, `(rrf + 0,035) × 1,35` para lo que está en ambos canales (`rre_engine.py:1012-1017`), lo que aparece en un solo canal queda alrededor de 0,016 frente a 0,09: es un escalón, no una gradación. En apartados, 2.7.1 es una unidad de 7849 caracteres: el denso truncado solo ve sus primeros 256 tokens (puesto 85, similitud 0,443) y TF-IDF la sitúa en el 15 |
| **Continuación de 2.7 a 2.7.1** en páginas | A-prod: se entrega la pág. 42 como «2.7» y no se cose con la 43 | **Contrato de los pasajes por página:** cada apartado de una página es un pasaje con el **mismo texto de página completa** (P042-S052, S053 y S054), y la deduplicación por texto conserva solo uno. El cosido sigue al apartado de la semilla (S053, que termina en la pág. 42), no al apartado que continúa (S054) |
| **2.7.2** en A-ref y C1 | Estaba en el top-5 y **R1 lo sustituyó** | El canal denso sitúa en el **primer puesto la pág. 91, que solo contiene la cabecera** (similitud 0,704, la mayor del corpus). R1 la reserva como campeona y expulsa a 2.7.2. **369 de los 385 pasajes** contienen esa misma cabecera, que no se eliminó en el procesamiento |
| **2.5.2** (repesca de cuartos, a la que remite 2.7) | A: puesto 13 del denso, eliminada en la fusión. B y C2: no aparece en el top-60 | **Umbral `min_confidence=0,015`:** un acierto solo denso tiene una puntuación de 1/(60+r), que no supera 0,015 por debajo del puesto 6. La remisión «refer to Section 2.5.2» **no está modelada**: los grafos solo tienen `references_article` (68 aristas en el índice de páginas) y `has_table`, `table_of`, `references_article` y `references_table` en el de apartados. **No existe ninguna arista de referencia a apartados** |
| **Art. 9** (ceremonia, árbitros, desempate en el tatami y cierre) | Todas: puesto 37 de TF-IDF en páginas y 40 en apartados; puesto 27 del denso en C2 | La consulta proyectada solo comparte con el art. 9 términos genéricos (*team*, *encounter*), y ninguno de los propios del artículo (*bow*, *referee*, *Rei*, *golden score*). La dispersión normativa entre la sección 2 y las reglas de arbitraje no tiene ningún enlace estructural |
| **Tablas de peso 2.2.2-2.2.4** en A | Págs. 34 y 35 fuera del corte de canal (puestos 28 y 59 del denso) | En páginas compiten con todo; en apartados sí llegan, por `has_table` (B y C2) o por B4 (D) |
| Encabezados vacíos en primera posición (B, C2) | SEC-0038, 2.2.4 con 47 caracteres: puesto 1 de TF-IDF y del denso | **Representación:** el apartado contiene solo el título; su contenido está en las tablas hijas. Un título que coincide con la consulta gana a unidades con contenido |
| Formularios y veteranos | Todas | Coinciden por léxico genérico (*competition system*, *team*, *weight*) en una consulta que es una bolsa de palabras |

**Pérdidas que no se deben al procesamiento documental:** el texto de los 56 fragmentos está íntegro en el corpus y en las unidades. Las cuatro pérdidas «nunca recuperadas» de A-prod (DES-3 y EMP-7, art. 9, p. 154; DES-9, p. 47; ORG-4, 6.4, p. 80) se deben a que esas páginas no puntúan en ningún canal, no a que el texto falte.

## 7. Relaciones entre componentes

| Relación | Estado | Evidencia |
|---|---|---|
| PDF → corpus por páginas | Correcta en el texto. **Defecto:** la cabecera repetida en cada página no se elimina, y una página que solo contiene la cabecera puede ganar el canal denso | P091: 75 caracteres, puesto 1 del denso; 369/385 pasajes con la cabecera |
| PDF → unidades por apartado | Correcta en el texto y en la paginación (`pdf_page_index`, `page_end`). **Defectos:** unidades que solo contienen el título (2.2.2 y 2.2.4) y unidades muy largas (2.7.1 con 7849 caracteres, que el modelo denso trunca). 6.5 no se divide en 6.5.1 y 6.5.2, mientras que 6.4 sí | `units.jsonl`; perfil denso |
| Apartado ↔ tabla | **Funciona:** la relación `has_table` del grafo de apartados hace llegar las tablas de 2.2.4 y 2.2.2 a `related_passages` | B y C2, relacionados |
| Apartado ↔ subapartado | Existe en los metadatos (`parent_unit_id`), pero **el RRE no lo usa y B4 solo lo recorre hacia arriba** | D: 2.7.1 y 2.7.2 no son candidatos |
| Apartado ↔ apartado referido («see Section 2.7.1», «refer to Section 2.5.2», «Weigh-in rules can be found in Section 6») | **No existe** en ningún grafo | Tipos de relación de los dos grafos |
| Ventana ↔ apartado o página | **Correcta y trazable:** cada ventana conserva `passage_id` y su rango de tokens, y se reconstruye su texto exacto (`ventanas.*.chars`). La agregación por máximo recompensa a la ventana más parecida aunque sea solo la cabecera | Ventanas mejor puntuadas en C1 y C2 |
| Página ↔ apartado | **Ambigua en el corpus por páginas:** un pasaje por apartado con el texto de toda la página. La identidad del apartado decide el cosido, pero el texto no se corresponde con el apartado | P042-S052, S053 y S054 |
| Fusión → paquete | Tamaño fijo, `top_k=5` más ≤3 relacionados, sin relación con la amplitud de la pregunta. R1 puede sustituir evidencia pertinente por una campeona vacía | A-ref y C1 |
| RRE → ADA | ADA recibe solo `evidence` más `related_passages[:3]` (`rre_engine.py:1479`) y suplementarios. No hay ningún campo que indique cobertura incompleta ni las remisiones pendientes | `ada_assistant.py:410-419` |

## 8. Diferencias entre la arquitectura actual y las variantes experimentales

| Aspecto | Actual (páginas) | Apartados (B) | Ventanas (C1 y C2) | B4 (D) |
|---|---|---|---|---|
| Unidad entregada | Página completa; el cosido sigue al apartado de la semilla | Apartado exacto | La de su índice | Apartado más padre, hermanos y tablas |
| Ventaja observada | Cosido multipágina: aporta 2.7.2 completo, 6.5 y 6.4.2 | Tablas por `has_table` | Ninguna en esta consulta | Completa las tablas de categorías |
| Desventaja observada | Páginas vacías o solo con cabecera; texto de página duplicado por apartado | Los títulos cortos ganan; 2.7.1 (larga) se debilita | La ventana con solo la cabecera es la número 1; formularios | No baja a los hijos; los límites se agotan en ramas periféricas |
| Imprescindibles entregados | **20/49** | 6/49 | 8/49 / 5/49 | 8/49 |

La versión actual gana aquí por una coincidencia estructural: el pasaje de la página 45 pertenece a 2.7.2 y el cosido lo continúa hasta la página 46. Las variantes recuperan unidades más limpias, pero **más pequeñas**, y con el mismo límite de 5 semillas eso reduce la cobertura.

## 9. ¿Qué configuración recupera mejor la evidencia?

**A-prod**, la configuración actual de producción en lo reproducible: 20 de 49 fragmentos imprescindibles. Aun así es **insuficiente**:
* pierde casi todo el orden de los combates (2/8), el ganador (1/5), el empate (2/6), el desarrollo y la finalización (2/9) y las categorías de peso (2/7);
* entrega una remisión pendiente: 2.7.2 dice «see Section 2.7.1» para el empate, y 2.7.1 no está en el paquete.

Ninguna variante experimental la supera en cobertura. D solo es mejor en las tablas de peso, con 5/7 frente a 2/7.

## 10. Límites que impiden afirmar si el asistente completo respondería correctamente

1. **Traducción con el LLM no reproducida.** En producción, ADA traduce con Gemini. Aquí se usó su respaldo determinista, que deja términos en español (*organizacion, combates, ganador, empate…*). Con una traducción del LLM cambiarían los canales. Lo que no cambiaría es el límite de 5 semillas frente a 12 unidades necesarias, que no depende de la consulta.
2. **No se ejecutó la generación ni el DIG.** No se sabe qué haría el generador con un paquete incompleto (¿abstenerse parcialmente, completar con conocimiento propio?) ni si el DIG lo detectaría. La instrucción excluye el LLM.
3. **Configuración parcial de producción.** No se reproduce la composición que hace `rag_engine` para la interfaz ni el despliegue real (OCI, puerto 8501). Los suplementarios se registraron, pero no se evaluaron.
4. **Un solo caso.** El conjunto de referencia (56 fragmentos) lo definió el auditor a partir del PDF. Cualquier otra lectura razonable mantiene el núcleo en 2.7, 2.7.1, 2.7.2, 2.2.2-2.2.4 y el art. 9.
5. **Copia del mecanismo B4.** Es literal y está verificada en 82/82 consultas, pero sigue siendo una copia, no una importación.

---

**Conclusión.** La pregunta exige reunir unas 12 unidades repartidas en tres zonas del SOR (sección 2, sección 6 y art. 9), enlazadas por remisiones explícitas. La arquitectura actual y las experimentales recuperan los **puntos de entrada** correctos (2.7, y 2.7.2 en producción). Lo que no tienen es un mecanismo general que, a partir de esos puntos:
* baje a los subapartados;
* siga las remisiones entre apartados;
* adapte el tamaño del paquete a la amplitud de la pregunta.

A eso se suman tres sesgos del ordenamiento:
* el canal denso premia el texto vacío o solo con cabecera;
* la fusión aplasta lo que está en un solo canal;
* R1 puede expulsar evidencia pertinente.

La deficiencia es **estructural, en el contrato de selección entre RRE y ADA y en la ausencia de relaciones apartado-subapartado y apartado-apartado utilizables**, no en la extracción del PDF.
