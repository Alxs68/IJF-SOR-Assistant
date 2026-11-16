# Matriz de Benchmark Ampliado — Fase 4.2.5 (40 Consultas)
**Proyecto:** IJF SOR Assistant  
**Fase:** 4.2.5 — Calibración y Endurecimiento del Retrieval Multifuente  
**Supervisor:** Alexis Oliveros Lozano  
**Arquitectura y Auditoría:** ChatGPT  
**Ejecutor:** Antigravity  
**Fecha:** 2026-11-05  
**Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Estado:** **DISEÑO DE BENCHMARK AMPLIADO — SIN EJECUCIÓN NI CAMBIOS DE CÓDIGO**

---

## 1. Estructura y Distribución del Dataset

El benchmark ampliado para la Fase 4.2.5 incrementa la cobertura de 20 a **40 consultas representativas y adversariales**, distribuidas en 8 categorías funcionales rigurosas:

```
Categoría 1: Enmiendas Oficiales Directas (Tier 2) ----------------- 6 consultas
Categoría 2: Interpretaciones Técnicas Arbitrales (Tier 3) ---------- 6 consultas
Categoría 3: Consultas Normativas Puras SOR (Sin Sidecar) ---------- 6 consultas
Categoría 4: Consultas Fuera de Dominio (OOD / Otros Deportes) ------ 5 consultas
Categoría 5: Consultas Ambiguas / Término Aislado ------------------- 5 consultas
Categoría 6: Consultas Negativas / Falsas Premisas ----------------- 4 consultas
Categoría 7: Consultas Adversariales / Conflicto Potencial ---------- 4 consultas
Categoría 8: Consultas Bilingües y Transfronterizas (EN/ES) --------- 4 consultas
TOTAL: 40 consultas etiquetadas
```

---

## 2. Matriz Completa de Casos Etiquetados (BM425-01 a BM425-40)

| ID | Consulta Exacta | Categoría | Fuente Esperada | Fragmento Esperado | Relevancia | Autoridad | Vigencia | Elegibilidad | Resultado Esperado | Justificación de Evaluación |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BM425-01** | ¿Está permitido el reverse seoi-nage en la categoría Senior? | TIER_2_DIRECT | `KUN-NEW-001` | `CHK-KUN-NEW-001-002` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Consulta directa sobre enmienda oficial de Seoi-nage inverso. |
| **BM425-02** | ¿Cuál es el límite máximo de disputa de kumi-kata sin ataque? | TIER_2_DIRECT | `KUN-NEW-001` | `CHK-KUN-NEW-001-003` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Límite estricto de 30 segundos en agarre. |
| **BM425-03** | ¿Desde qué torneo se bloquean las reglas arbitrales para LA28? | TIER_2_DIRECT | `KUN-NEW-001` | `CHK-KUN-NEW-001-001` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Cierre de reglas desde GS Ulaanbaatar. |
| **BM425-04** | ¿Cuántos segundos de inmovilización otorgan Yuko en las nuevas reglas? | TIER_2_DIRECT | `KUN-NEW-003` | `CHK-KUN-NEW-003-001` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Puntuación de Yuko para 5 a 9 segundos. |
| **BM425-05** | ¿Cómo se valora la combatividad combinada entre pie y suelo? | TIER_2_DIRECT | `KUN-NEW-003` | `CHK-KUN-NEW-003-002` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Evaluación integrada de pasividad tachi/ne-waza. |
| **BM425-06** | ¿Se sanciona el contacto de cabeza si es producto de la inercia de caída? | TIER_2_DIRECT | `KUN-NEW-003` | `CHK-KUN-NEW-003-003` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Excepción de contacto cefálico involuntario. |
| **BM425-07** | ¿Cuándo debe el árbitro permitir la continuidad hacia el suelo? | TIER_3_DIRECT | `KUN-PPT-002` | `CHK-KUN-PPT-002-001` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Criterio de continuidad en transición inmediata. |
| **BM425-08** | ¿Qué sanción recibe quien hala al oponente al suelo sin desequilibrio? | TIER_3_DIRECT | `KUN-PPT-002` | `CHK-KUN-PPT-002-002` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Sanción Shido por tirarse directamente sin técnica. |
| **BM425-09** | ¿Puede continuarse la acción en ne-waza si el ataque inició en tachi-waza? | TIER_3_DIRECT | `KUN-PPT-002` | `CHK-KUN-PPT-002-001` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Principio de transición inmediata y control. |
| **BM425-10** | ¿Constituye infracción tirarse a la guardia sin técnica previa de judo? | TIER_3_DIRECT | `KUN-PPT-002` | `CHK-KUN-PPT-002-002` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Equivalencia a arrastre directo a suelo. |
| **BM425-11** | Criterio de aplicación de Shido por jalar a ne-waza | TIER_3_DIRECT | `KUN-PPT-002` | `CHK-KUN-PPT-002-002` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Formulación compacta de la infracción de arrastre. |
| **BM425-12** | Instrucción arbitral sobre la fluidez en el paso de pie a suelo | TIER_3_DIRECT | `KUN-PPT-002` | `CHK-KUN-PPT-002-001` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Interpretación técnica operativa. |
| **BM425-13** | ¿Cuáles son las medidas reglamentarias del área de combate y seguridad? | SOR_PUR_CANONICAL | SOR 2026 | *Ninguno (SOR)* | NULA | Tier 1 | VIGENTE | CANONICAL | ABSTAIN_SIDECAR | Art. 1 SOR. El Sidecar debe abstenerse (score < umbral). |
| **BM425-14** | ¿Cuál es la tolerancia milimétrica de las mangas con el Sokuteiki? | SOR_PUR_CANONICAL | SOR 2026 | *Ninguno (SOR)* | NULA | Tier 1 | VIGENTE | CANONICAL | ABSTAIN_SIDECAR | Apéndice C SOR. Sin evidencia complementaria. |
| **BM425-15** | ¿Cuáles son los límites de peso en la categoría femenina de -52 kg? | SOR_PUR_CANONICAL | SOR 2026 | *Ninguno (SOR)* | NULA | Tier 1 | VIGENTE | CANONICAL | ABSTAIN_SIDECAR | Art. 3 SOR. El Sidecar no debe hacer match por la palabra "peso". |
| **BM425-16** | ¿En qué circunstancias se declara la descalificación por Hansoku-make directo? | SOR_PUR_CANONICAL | SOR 2026 | *Ninguno (SOR)* | NULA | Tier 1 | VIGENTE | CANONICAL | ABSTAIN_SIDECAR | Art. 18.2 SOR. Norma canónica de penalizaciones graves. |
| **BM425-17** | ¿Cuánto dura el descanso reglamentario entre combates consecutivos? | SOR_PUR_CANONICAL | SOR 2026 | *Ninguno (SOR)* | NULA | Tier 1 | VIGENTE | CANONICAL | ABSTAIN_SIDECAR | Art. 6 SOR. Tiempo de recuperación de 10 minutos. |
| **BM425-18** | ¿Cuál es el procedimiento oficial para el pesaje aleatorio? | SOR_PUR_CANONICAL | SOR 2026 | *Ninguno (SOR)* | NULA | Tier 1 | VIGENTE | CANONICAL | ABSTAIN_SIDECAR | Art. 4 SOR. Control del 5% de tolerancia de peso. |
| **BM425-19** | En fútbol, ¿cuándo se sanciona un fuera de juego posicional? | OUT_OF_DOMAIN | Ninguna | *Ninguno* | NULA | N/A | N/A | INELIGIBLE | ABSTAIN_ALL | Fuera de dominio (Fútbol). Debe abstenerse completamente. |
| **BM425-20** | ¿Cuántos puntos vale un tiro libre encestado en baloncesto? | OUT_OF_DOMAIN | Ninguna | *Ninguno* | NULA | N/A | N/A | INELIGIBLE | ABSTAIN_ALL | Fuera de dominio (Baloncesto). |
| **BM425-21** | En tenis de mesa, ¿cómo se efectúa un servicio reglamentario? | OUT_OF_DOMAIN | Ninguna | *Ninguno* | NULA | N/A | N/A | INELIGIBLE | ABSTAIN_ALL | Fuera de dominio (Tenis de mesa). |
| **BM425-22** | En natación, ¿cuál es la penalización por salida en falso en 100m mariposa? | OUT_OF_DOMAIN | Ninguna | *Ninguno* | NULA | N/A | N/A | INELIGIBLE | ABSTAIN_ALL | Dominio negativo explícito. No debe matchear "penalización". |
| **BM425-23** | ¿Cómo se anota un touchdown en fútbol americano? | OUT_OF_DOMAIN | Ninguna | *Ninguno* | NULA | N/A | N/A | INELIGIBLE | ABSTAIN_ALL | Fuera de dominio (NFL). |
| **BM425-24** | Penalización | AMBIGUOUS_TERM | *Indeterminada* | *Ninguno* | NULA | N/A | N/A | INELIGIBLE | ABSTAIN_SIDECAR | Término único aislado. Ambigüedad extrema. |
| **BM425-25** | Combate | AMBIGUOUS_TERM | *Indeterminada* | *Ninguno* | NULA | N/A | N/A | INELIGIBLE | ABSTAIN_SIDECAR | Término único aislado. Coincide con todo el corpus. |
| **BM425-26** | Tiempo de agarre | AMBIGUOUS_TERM | `KUN-NEW-001` | `CHK-KUN-NEW-001-003` | MEDIA | Tier 2 | VIGENTE | ELIGIBLE | RESOLVE_OR_ABSTAIN | Si no especifica judo/30s, evaluar margen de score. |
| **BM425-27** | Cabeza en tatami | AMBIGUOUS_TERM | `KUN-NEW-003` | `CHK-KUN-NEW-003-003` | MEDIA | Tier 2 | VIGENTE | ELIGIBLE | RESOLVE_OR_ABSTAIN | Ambigua entre head dive (SOR Art.18) y excepción (Sidecar). |
| **BM425-28** | Transición | AMBIGUOUS_TERM | `KUN-PPT-002` | `CHK-KUN-PPT-002-001` | BAJA | Tier 3 | VIGENTE | ELIGIBLE | ABSTAIN_SIDECAR | Término genérico. El umbral debe suprimir match espurio. |
| **BM425-29** | ¿Por qué se permite el reverse seoi-nage en competidores Cadetes? | NEGATIVE_PREMISE | `KUN-NEW-001` | `CHK-KUN-NEW-001-002` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | REFUTE_PREMISE | Premisa falsa: está prohibido en Cadetes; solo en Senior. |
| **BM425-30** | ¿Es verdad que una inmovilización de 5 segundos otorga Waza-ari? | NEGATIVE_PREMISE | `KUN-NEW-003` | `CHK-KUN-NEW-003-001` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | REFUTE_PREMISE | Premisa falsa: 5 a 9s otorga Yuko, no Waza-ari. |
| **BM425-31** | ¿Se eliminó la sanción por tirar al oponente al suelo sin técnica? | NEGATIVE_PREMISE | `KUN-PPT-002` | `CHK-KUN-PPT-002-002` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | REFUTE_PREMISE | Premisa falsa: sigue sancionándose con Shido estricto. |
| **BM425-32** | ¿Las reglas de arbitraje de Los Ángeles 2028 cambian en cada Grand Slam? | NEGATIVE_PREMISE | `KUN-NEW-001` | `CHK-KUN-NEW-001-001` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | REFUTE_PREMISE | Premisa falsa: están formalmente bloqueadas y congeladas. |
| **BM425-33** | En Cadetes, ¿un atleta puede hacer reverse seoi-nage si tiene agarre cruzado? | ADVERSARIAL_CROSS | `KUN-NEW-001` | `CHK-KUN-NEW-001-002` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Desafía el límite entre categoría y técnica permitida. |
| **BM425-34** | Si uke hace puente voluntario de cuello, ¿es excepción por contacto involuntario? | ADVERSARIAL_CROSS | SOR 2026 | *Ninguno (SOR Art.14)* | ALTA (SOR) | Tier 1 | VIGENTE | CANONICAL | PRIORITY_SOR | Intenta confundir la excepción de cabeza con puente voluntario. |
| **BM425-35** | ¿Se acumulan dos puntuaciones de Yuko para formar un Waza-ari en el ciclo LA28? | ADVERSARIAL_CROSS | `KUN-NEW-003` | `CHK-KUN-NEW-003-001` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Aclara que Yuko no se acumula para Waza-ari. |
| **BM425-36** | ¿Puede el entrenador pedir revisión de video durante una acción continua de ne-waza? | ADVERSARIAL_CROSS | SOR 2026 | *Ninguno (SOR)* | NULA | Tier 1 | VIGENTE | CANONICAL | ABSTAIN_SIDECAR | Art. 8 SOR. Solo la mesa de arbitraje usa CARE; no entrenador. |
| **BM425-37** | Can senior competitors execute reverse seoi-nage in World Tour events? | BILINGUAL_EN_ES | `KUN-NEW-001` | `CHK-KUN-NEW-001-002` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Consulta formal en inglés. |
| **BM425-38** | What is the maximum time allowed for kumi-kata dispute before shido? | BILINGUAL_EN_ES | `KUN-NEW-001` | `CHK-KUN-NEW-001-003` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Consulta bilingüe sobre tiempo de agarre. |
| **BM425-39** | How many seconds of osaekomi are required to score yuko under current rules? | BILINGUAL_EN_ES | `KUN-NEW-003` | `CHK-KUN-NEW-003-001` | ALTA | Tier 2 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Consulta bilingüe sobre puntuación Yuko. |
| **BM425-40** | Is pulling down the opponent into ne-waza without throwing attempt penalized? | BILINGUAL_EN_ES | `KUN-PPT-002` | `CHK-KUN-PPT-002-002` | ALTA | Tier 3 | VIGENTE | ELIGIBLE | MATCH_SIDECAR | Consulta bilingüe sobre penalización de arrastre. |
