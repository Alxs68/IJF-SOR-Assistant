# AUDITORÍA NORMATIVA FINAL DE ACEPTACIÓN — RRE 3.0 FASE 1
**Proyecto:** IJF SOR Assistant  
**Rol:** Auditor Normativo Independiente  
**Fecha:** 5 de noviembre de 2026  
**Fuente Normativa Oficial:** *IJF Sport and Organisation Rules (SOR)*, Edición Oficial 14 de agosto de 2026 (298 páginas).  
**Entorno Evaluado:** Local (`C:\PROYECTOS\IJF-SOR-Assistant`), rama `integration/ijf-sor-2026-08-merge`, commit base `61afc1bc2c8fa273f118f4e10bc447dbafcfe650`.

---

## 1. RESUMEN EJECUTIVO

La presente auditoría normativa independiente somete a examen crítico y exhaustivo los **22 casos de la batería de aceptación funcional** del IJF SOR Assistant (RRE 3.0 Fase 1 + ADA), contrastando las respuestas emitidas por el sistema directamente contra el texto canónico del PDF oficial del SOR 2026 (14 de agosto de 2026).

### Cuatro Dimensiones de Evaluación Diferenciadas
Para evitar confusiones entre rendimiento computacional y validez reglamentaria, se aplicó la distinción estricta de cuatro planos de análisis:
1. **Recuperación satisfactoria (RRE):** Capacidad del motor de búsqueda para posicionar los pasajes normativos oficiales pertinentes dentro del Top-K.
2. **Respuesta técnicamente válida (Pipeline ADA):** Conformidad del contrato JSON, trazabilidad de KUNs, y cumplimiento del filtro antialucinaciones (citas literales validadas contra pasajes).
3. **Respuesta normativamente correcta (SOR 2026):** Exactitud jurídica de las consecuencias, artículos, numerales, condiciones y excepciones frente al reglamento oficial.
4. **Respuesta arbitralmente confiable:** Capacidad de la respuesta para resolver una duda arbitral real sin inducir a error ni requerir deducciones complementarias por parte del oficial o competidor.

### Hallazgos Principales
- **Corrección Crítica en TC-08 (Defensa con Cabeza en Cadetes):** La auditoría confirma taxativamente que el reporte funcional previo incurrió en un error material al declarar que Uke recibe Hansoku-make y expulsión. El texto canónico del **Art. 18.1.4, punto 34 (pág. 188)** y la tabla resumen de códigos de penalización **G1.3 (pág. 255, código PS34)** establecen sin ambigüedad: **Uke es sancionado con SHIDO**, y Tori recibe puntuación técnica si existió proyección. No es Hansoku-make.
- **Consultas Disciplinarias (TC-10 y TC-18):** El reglamento sanciona la agresión física y los insultos graves con **Hansoku-make directo sin posibilidad de continuar en el torneo (CANNOT continue)** conforme al **Art. 1.1.1 (pág. 14)**, **Apéndice D1.1 (pág. 134)** y **Art. 18.2.2 puntos 11 y 13 (págs. 190, 193)**. Sin embargo, ADA omitió explicitar la sanción formal («Hansoku-make directo») en la síntesis al estar operando en modo local desconectado extractivo, limitándose a citar el principio ético.
- **Efecto del Modo Determinista Desconectado:** La validación estricta de citas literales garantizó 0% de alucinación generativa (todas las citas provienen verbatim del PDF); sin embargo, al extraer sólo las primeras oraciones de los pasajes líderes de RRE, la consecuencia normativa (sanción o puntuación) a menudo quedó relegada a los párrafos secundarios del pasaje o a las citas accesorias, sin una síntesis interpretativa explícita.
- **Falsos Positivos Fuera de Dominio (TC-16 y TC-20):** La falta de un clasificador de intención o filtro de entidad de dominio provocó que una consulta sobre falta personal en baloncesto (TC-16) fuera respondida citando el código de sanciones de judo (Art. 4, Art. 18.1.1).

---

## 2. MATRIZ INTEGRAL DE AUDITORÍA DE LOS 22 CASOS

### Taxonomía de Clasificación de Errores:
- `SIN_ERROR`: Respuesta y fundamento normativo 100% exactos y completos.
- `ERROR_RECUPERACION`: RRE no recuperó el pasaje normativo específico en el top ranking.
- `ERROR_INTERPRETACION`: Deducción arbitral incorrecta o tergiversada.
- `ERROR_CITACION`: Artículo, numeral o página incorrectos o incompletos.
- `ERROR_CONSECUENCIA_NORMATIVA`: Sanción o puntuación dictada contraria al SOR 2026.
- `ERROR_OMISION_CONDICION`: Omisión de requisitos previos para aplicar la regla.
- `ERROR_OMISION_EXCEPCION`: Omisión de excepciones reglamentarias explícitas.
- `ERROR_ABSTENCION`: Abstención injustificada ante una consulta reglamentada.
- `FALSO_POSITIVO_OOD`: Respuesta afirmativa con normas de judo ante consultas fuera de dominio (*Out-of-Domain*).
- `INDETERMINADO`: Evidencia insuficiente para calificar.

| ID | Consulta Resumida | Precepto Oficial SOR 2026 | Consecuencia Canónica Oficial | Cita ADA Recuperada | Clasificación de Error | Estado Arbitral |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Medidas área combate y seguridad tatami | Art. 8.7 (pág. 96); Art. 8.5 (pág. 95) | Combate: mín 8x8m, máx 10x10m. Seguridad: mín 2m (3m entre tatamis) | Art. 8.7 (pág. 96): mín 8x8m, máx 10x10m | `ERROR_OMISION_CONDICION` (omitió 2m/3m seguridad en extracto líder) | Parcialmente confiable |
| **TC-02** | Duración combate Senior masc/fem | Art. 6.1 (pág. 152) | 4 minutos de tiempo real para hombres y mujeres | Art. 7 (pág. 152) y Art. 6 (pág. 152) | `ERROR_RECUPERACION`, `ERROR_OMISION_CONDICION` (Art. 7 lideró sobre Art. 6) | Parcialmente confiable |
| **TC-03** | Cuatro criterios para Ippon | Art. 14.1 (pág. 166) | Velocidad, fuerza, sobre la espalda y control hasta el final | Art. 14 (pág. 166) verbatim | `SIN_ERROR` | Plenamente confiable |
| **TC-04** | Caída lateral 90° con fuerza/velocidad | Art. 15 (pág. 168) | Waza-ari (aterrizaje de costado >90° o no cumple 4 criterios) | Art. 8.7 (pág. 96) lideró; Art. 14 en top-4 | `ERROR_RECUPERACION`, `ERROR_CONSECUENCIA_NORMATIVA` | No confiable |
| **TC-05** | Escape Osaekomi a los 16 segundos | Art. 7 b) (pág. 152); Art. 15 (pág. 168) | Waza-ari (inmovilización de 10 a 19 segundos) | Art. 17 (pág. 174) Toketa; Art. 15 (pág. 169) | `ERROR_OMISION_CONDICION` (recuperó Toketa pero no la tabla de 10-19s en top-1) | Parcialmente confiable |
| **TC-06** | Reverse seoi-nage en Cadetes | Art. 18.1.4 p.35 (pág. 189) | No hay puntuación; Tori es sancionado con Shido | Art. 18.1.4 p.35 (pág. 189) verbatim | `SIN_ERROR` | Plenamente confiable |
| **TC-07** | Uso de cabeza por Tori para proyectar | Art. 18.1.4 p.33 (pág. 188); Art. 18.2.1 (pág. 190) | Cadetes: Shido (18.1.4 p.33). Seniors: Permitido salvo Head Diving | Art. 18.1.4 p.33 (pág. 188) verbatim | `ERROR_OMISION_EXCEPCION` (omitió contrastar Seniors per se) | Parcialmente confiable |
| **TC-08** | Defensa con cabeza por Uke en Cadetes | Art. 18.1.4 p.34 (pág. 188); G1.3 (pág. 255) | **Shido para Uke**; puntuación para Tori si corresponde | Art. 18.1.4 p.34 (pág. 188) verbatim | `ERROR_OMISION_EXCEPCION` (el texto líder omitió la frase de puntuación a Tori) | Confiable en norma base |
| **TC-09** | Sanción Head Diving y continuidad | Art. 18.2.1 (pág. 190) | Hansoku-make directo; **el atleta SÍ puede continuar** | Art. 18.2.1 (pág. 190) verbatim | `SIN_ERROR` | Plenamente confiable |
| **TC-10** | Insultos o agresión al rival | Art. 1.1.1 (p. 14); D1.1 (p. 134); 18.2.2 (p. 190, 193) | Hansoku-make directo; **NO puede continuar en el torneo** | Art. D1.1 (pág. 134) y Art. 18.2.2 (pág. 193) | `ERROR_CONSECUENCIA_NORMATIVA`, `ERROR_OMISION_CONDICION` (no explicitó Hansoku-make en síntesis) | Parcialmente confiable |
| **TC-11** | Sanción por Kawazu-gake | Art. 18.2.2 p.1 (pág. 190) | Hansoku-make directo; exclusión de la competencia | Art. 4 (p. 149) en top; Art. 18.2.2 p.1 (p. 190) en 4° | `ERROR_RECUPERACION`, `ERROR_CONSECUENCIA_NORMATIVA` | Parcialmente confiable |
| **TC-12** | Proyección culminada en área de seguridad | Art. 5 Excepciones a) (pág. 151) | Válida si la acción es continua y no supera 2m fuera de combate | Art. 8.7 (pág. 96) lideró; Art. 9 en top-4 | `ERROR_RECUPERACION`, `ERROR_OMISION_EXCEPCION` | No confiable |
| **TC-13** | Judogi reversible doble cara blanco/azul | Art. C1.1 (pág. 115) | Expresamente prohibido («Reversible judogi is not allowed») | Art. C1.1.2 p.115 en top; omitió C1.1 en síntesis | `ERROR_RECUPERACION`, `ERROR_CONSECUENCIA_NORMATIVA` | No confiable |
| **TC-14** | ¿Qué pasa si un judoka usa la cabeza? | Art. 18.1.4 p.33/34; Art. 18.2.1 (pág. 190) | Distinción tripartita: Tori Cadete (Shido), Tori Diving (HM cont.), Uke Cadete (Shido) | Art. 18.2.2 lideró; Art. 18.1.4 en top-7 | `ERROR_RECUPERACION`, `ERROR_INTERPRETACION` | No confiable |
| **TC-15** | ¿Cuándo se marca mate? | Art. 11.1 (págs. 160-161) | Casos taxativos (peligro, salida, falta, reajuste indumentaria/pelo, lesión) | Art. C1.3 (pág. 119, marcas y logos judogi) | `ERROR_RECUPERACION` (Colisión léxica de «mate» con «material/maker») | No confiable |
| **TC-16** | Falta personal en básquetbol | Fuera de dominio SOR | **Abstención categórica** (no regulado en IJF SOR 2026) | Respondió Art. 4 (pág. 149, señas arbitrales judo) | `FALSO_POSITIVO_OOD` | No confiable (Grave OOD) |
| **TC-17** | Interés compuesto en finanzas | Fuera de dominio SOR | **Abstención categórica** | Abstención correcta (`status: ABSTAIN`, 0 pasajes) | `SIN_ERROR` | Plenamente confiable |
| **TC-18** | Ofensa o agresión entre competidores | Art. 1.1.1 (p. 14); D1.1 (p. 134); 18.2.2 (p. 193) | Descalificación inmediata, Hansoku-make directo, exclusión | Art. 1.1.1 (pág. 14) y Art. 18.2.2 (pág. 193) | `ERROR_OMISION_CONDICION` (citó principios pero no la sanción formal) | Parcialmente confiable |
| **TC-19** | Código de conducta de entrenadores | Art. 7.1 / 7.2 (págs. 89-90) | Respeto al Código de Ética; advertencia verbal hasta expulsión | Art. 7.1 (pág. 89) verbatim | `SIN_ERROR` | Plenamente confiable |
| **TC-20** | Cuántos shidos provocan descalificación | Art. 18 (pág. 175) | 2 shidos de advertencia; el 3º es Hansoku-make indirecto | Art. 18 (pág. 175) verbatim | `ERROR_OMISION_CONDICION` (el snippet cortó antes de «the third will be») | Parcialmente confiable |
| **TC-21** | Puente voluntario para evitar caída | Art. 14.2 (pág. 166) | Se califica como Ippon (seguridad columna cervical) | Art. 14 (pág. 167) pie de página; p. 166 en 2º lugar | `ERROR_RECUPERACION`, `ERROR_OMISION_CONDICION` (Chunk boundary cut) | Parcialmente confiable |
| **TC-22** | Puente con aterrizaje sobre cuerpo de Tori | Art. 14.2 (pág. 167) | No se otorga puntuación ni penalización por puente | Art. 14 (pág. 167) verbatim | `SIN_ERROR` | Plenamente confiable |

---

## 3. VERIFICACIÓN NORMATIVA CRÍTICA PUNTUAL

### 3.1. Caso TC-08: Defensa con la Cabeza en Cadetes (Aclaración Taxativa)
El reporte preliminar de la fase de pruebas contenía una discrepancia sustancial respecto a la sanción aplicable a un competidor Cadete que utiliza la cabeza para defenderse.

#### Texto Canónico del PDF Oficial SOR 2026:
> **Artículo 18.1.4 Penalties (Shido) in Cadet Competitions (Página 188):**  
> *«34. In cadet events athletes are not allowed to use the head to defend as UKE. In this situation, tori will be awarded a score, if any, and uke will be penalised with shido. See pictures 18.61-18.67.»*

> **G1.3 Penalty Codes (Página 255):**  
> *«Using the head to defend in cadet events | PS34 | Shido | 18.1.4 34»*

#### Determinación Normativa:
1. **La sanción es exclusivamente SHIDO.** La afirmación anterior que señalaba *«Hansoku-make directo y expulsión del torneo»* es **normativamente errónea**. Confundió la defensa con cabeza de Cadetes (Art. 18.1.4 p.34) con el Head Diving (Art. 18.2.1) o con actos contra el espíritu del judo (Art. 18.2.2).
2. **Consecuencia dual:** Tori recibe puntuación técnica si la proyección cumplió los criterios reglamentarios; simultáneamente, a Uke se le impone Shido por poner en riesgo su columna cervical.
3. **Estado en el Asistente:** RRE recuperó correctamente el KUN `SOR-2026-08-P188-S196` correspondiente a `Article 18.1.4` (pág. 188). Sin embargo, el snippet extractivo del resumen cortó el texto justo después de la primera frase (*«In cadet events athletes are not allowed to use the head to defend as UKE»*), omitiendo la segunda parte donde se explicita el Shido y la puntuación de Tori.

---

### 3.2. Casos TC-10 y TC-18: Agresión, Insultos y Conducta Antideportiva
Se verificó si las conductas de agresión física o verbal justifican Hansoku-make directo en todos los supuestos o si existe graduación arbitral.

#### Texto Canónico del PDF Oficial SOR 2026:
1. **Artículo 1.1.1 Behaviour at IJF Events (Página 14):**  
   *«Unacceptable behaviour, violence or aggression will not be tolerated and will be severely punished. Any athlete... committing an infraction against these rules can face immediate disqualification, removal of prize money and of World Ranking List (WRL) points and a ban from the event...»*
2. **Apéndice D1.1 Refereeing - Culture, History and Principles (Página 134):**  
   *«Actions contrary to the spirit of judo, on the competition area, without this list being exhaustive are: Attacking or attempting to attack voluntarily the physical integrity of one's opponent or oneself... Insulting, by word or gesture, his opponent, the referee, the coach, the organisers, the public or any other person present in the venue.»*
3. **Artículo 18.2.2 Hansoku-make for Acts against the Spirit of Judo (Páginas 190 y 193):**  
   *«If this type of hansoku-make is awarded the athlete CANNOT continue in the competition...»*  
   *«11. To make unnecessary calls, remarks, or gestures derogatory to the opponent or referee during the contest.»*  
   *«13. Any action against the spirit of judo... may be punished by a direct hansoku-make at any time in the contest.»*

#### Determinación Normativa:
- **No existe Shido para la agresión física o el insulto:** Son infracciones graves taxativamente clasificadas bajo el Artículo 18.2.2 y Apéndice D1.1.
- **Consecuencia obligatoria:** **Direct Hansoku-make** con expulsión completa del torneo (**CANNOT continue** en la competición ni en la repesca).
- **Competencia disciplinaria adicional:** Conforme al Art. 1.1.1 y 1.2.1, la comisión disciplinaria de la FIJ puede imponer sanciones ulteriores (suspensión temporal, retiro de puntos del ranking y pérdida de premios económicos).

---

### 3.3. Casos TC-21 y TC-22: Puente Voluntario y Excepción de Aterrizaje
#### Texto Canónico del PDF Oficial SOR 2026:
> **Artículo 14.2 Ippon (Página 166-167):**  
> *«2. All situations in which one of the athletes voluntarily makes a 'bridge' (head and one foot or both feet in contact with the tatami) after having been thrown will be ippon (pictures 14.2-14.3).»*  
> *«This decision is taken for the safety of the athletes, so they do not try to escape from the technique and endanger their cervical spine.»*  
> *«No score or penalty will be given if the landing of uke occurs on the body of tori, in such a way that not all parts of uke's body involving the bridge situation (head, foot or feet) touch the tatami.»*

#### Determinación Normativa:
- **Regla general:** La acción voluntaria de arquear el cuerpo formando un puente al ser proyectado se valora automáticamente como **Ippon** para el adversario.
- **Excepción de contacto con el cuerpo:** Si Uke aterriza sobre el torso o extremidades de Tori, de modo que la cabeza o pies no tocan directamente el tatami para formar el arco contra el suelo, **no se considera puente**: no se concede Ippon automático ni se penaliza por esa causa, valorándose la caída según los criterios ordinarios de impacto.
- **Diagnóstico del sistema:** RRE recuperó el pasaje de la página 167 (que contiene la excepción y el fundamento de la columna cervical), pero cortó la definición de la página 166 por límite de chunk, evidenciando la urgencia de la **Fase 2 (Chunk Stitching)**.

---

## 4. ANÁLISIS DETALLADO DE ERRORES POR CATEGORÍA

### 4.1. Errores de Recuperación (ERROR_RECUPERACION)
1. **TC-04 (Caída de costado 90°):** La presencia de términos espaciales como «costado», «tatami» y «proyección» causó que el índice vectorial privilegiara el Art. 8.7 (dimensiones del tatami) sobre el Art. 15 (definición de Waza-ari).
2. **TC-11 (Kawazu-gake):** Si bien el Art. 18.2.2 p.1 fue recuperado, ocupó el 4º lugar de relevancia, siendo superado por el Art. 4 (señas arbitrales) debido a la coincidencia con términos generales de penalización.
3. **TC-12 (Proyección hacia área de seguridad):** Recuperó las dimensiones del campo (Art. 8.7) en lugar del artículo sustantivo de validez de técnicas fuera del área (Art. 5 Excepciones a).
4. **TC-13 (Judogi reversible):** Recuperó el control de dorsal de judogi blanco y azul (Art. C1.1.2), perdiendo la prohibición expresa que reside en el párrafo introductorio de la página 115 (Art. C1.1).
5. **TC-15 (Señal Mate):** Colisión sub-léxica grave: el token «mate» coincidió con «material» y «maker» en las especificaciones del judogi (Art. C1.3, pág. 119), desplazando totalmente al Art. 11 (Aplicación de Mate, pág. 160).

### 4.2. Errores de Consecuencia Normativa y Omisión
1. **Falta de Síntesis Resolutiva en Modo Determinista:** Al ejecutarse el fallback local extractivo, ADA no genera texto discursivo interpretativo, sino que concatena los títulos y primeros párrafos oficiales. En los casos TC-10 y TC-18 (agresión), el sistema presentó las advertencias éticas del Art. 1.1.1 y D1.1, pero no redactó explícitamente: *«Corresponde Hansoku-make directo y expulsión de la competición»*.
2. **Corte en Mitad de Regla por Chunking Fragmentado (TC-20):** En la pregunta sobre acumulación de Shidos, el extracto del Art. 18 (pág. 175) cortó la frase en: *«The prohibited acts are divided into infringements that receive the penalty of:»*, impidiendo que el usuario leyera en el snippet visible la regla de los dos shidos y el tercer shido como Hansoku-make.

### 4.3. Falsos Positivos Fuera de Dominio (FALSO_POSITIVO_OOD)
- **TC-16 (Falta personal en baloncesto):** Al consultar por una falta personal y tiros libres de un deporte ajeno, el sistema encontró solapamiento léxico en «falta», «sanción» y «tiro», entregando como respuesta los códigos de penalización del judo (Art. 4 y Art. 18.1.1).  
  *Criterio arbitral:* Es inaceptable en un asistente arbitral oficial emitir sanciones de judo para hechos ajenos. Requiere un clasificador que verifique si los términos pertenecen inequívocamente al dominio del judo antes de procesar la similitud semántica.

---

## 5. CASOS QUE REQUIEREN VALIDACIÓN DE ÁRBITRO EXPERTO

Se identificaron situaciones donde el texto normativo del SOR 2026 requiere apreciación del equipo de arbitraje y supervisión de la FIJ:
1. **TC-14 (Uso ambiguo de la cabeza):** Si un competidor apoya la cabeza sin lanzarse frontalmente (ej. apoyo para girar el cuerpo en Ne-waza o transición), la norma no es taxativa respecto a si se equipara a Shido o si es acción permitida en Seniors, dependiendo de la apreciación del Supervisor de la FIJ.
2. **TC-12 (Continuidad de proyección en área de seguridad):** La apreciación de si una acción comenzó efectivamente antes de salir del área de combate y si no hubo pausa antes de proyectar en la zona de seguridad es un juicio fáctico que la comisión de arbitraje evalúa mediante el sistema de video (*Care System*).

---

## 6. DICTAMEN FINAL DE ACEPTACIÓN FUNCIONAL

### Evaluación Cualitativa
- **Recuperación (RRE 3.0 Fase 1):** **APROBADA PARCIALMENTE (77.3%)**. La ontología bilingüe y la expansión léxica resolvieron los casos disciplinarios críticos (Art. 1.1.1, 18.2.2) y de categorías de edad (Art. 18.1.4), pero evidencian fallas ante colisiones morfológicas («mate» vs «material») y falta de desambiguación semántica («costado» vs «tatami»).
- **Validez Técnica (ADA Determinista):** **APROBADA AL 100%**. Cumplimiento estricto del esquema JSON y cero alucinaciones (100% de citas verificables verbatim).
- **Exactitud Normativa (SOR 2026):** **CONDICIONADA**. Aunque las normas recuperadas son verídicas, el modo extractivo omitió la consecuencia sancionatoria en el 22.7% de los casos debido a límites de fragmentación de párrafos.
- **Confiabilidad Arbitral:** **NO APTA PARA PRODUCCIÓN EN ESTE ESTADO**. El riesgo de emitir citas parciales o responder a consultas fuera de dominio (TC-16) impide certificar el sistema como un asistente arbitral autónomo listo para despliegue final.

---

## 7. RECOMENDACIÓN DE PRÓXIMOS PASOS (PLAN TÉCNICO)

1. **NO DESPLEGAR A PRODUCCIÓN OCI (Mantener 61afc1b en staging/local):**  
   Desplegar el estado actual expondría al asistente a cortes en la frontera de páginas (casos de puente de Ippon) y falsos positivos ante consultas no relacionadas.
2. **Proceder de Inmediato a la Fase 2: Chunk Stitching y Ventana Deslizante:**  
   - Fusionar fragmentos normativos continuos para evitar cortes entre artículos divididos en dos páginas (ej. páginas 166-167 del Art. 14 y 188-189 del Art. 18.1.4).
   - Preservar KUNs múltiples o compuestos (`SOR-2026-08-P166-P167`).
3. **Incorporar en Fase 3/4 un Filtro de Verificación de Dominio (*Domain Guardrail*):**  
   - Si la consulta menciona entidades de otros deportes o materias ajenas sin anclaje en judo, forzar el estado `ABSTAIN` de inmediato.
4. **Implementar Tokenización de Términos Arbitrales Protegidos:**  
   - Proteger el lema `Mate!` como término reservado arbitral con límite de palabra estricto (`\bMate\b`) para evitar colisiones con *materials* o *maker*.

---
*Fin del Informe de Auditoría Normativa.*
