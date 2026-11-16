# Fase 11A — Reproducción y calibración experimental del DIG (solo dev)

**Estado:** COMPLETADO.
* **DIG de producción:** sin cambios. La variante experimental solo existe dentro del proceso de evaluación offline (`experimental.dig_variants.dig_variant`, que restaura siempre la función original; verificado por test).
* **Ámbito:** dev, sin test_sealed.
* **Evidencia:** `data/eval/fase11/llm_dev_f11_capture.json`, `data/eval/fase11/dig_replay_dev.json` y `data/eval/fase11/logs/b2_*`, `b3_*`.

## 1. Método

1. **Captura exacta** (`eval_llm_shadow.py --capture-dig`). Un envoltorio transparente alrededor del `evaluate` del DIG, que llama al original y devuelve su resultado intacto, guarda las entradas reales de cada llamada:
   * respuesta cruda del modelo y consulta;
   * consulta técnica en inglés;
   * evidencia y relacionados con su texto, tal como los entregó el RRE;
   * textos SHADOW;
   * decisión registrada.

   Se hicieron 2 corridas sobre las 41 consultas de dev.
2. **Reejecución** (`scripts/replay_dig_f11.py`) en dos modos:
   * **CAPTURADO** (exacto): con las entradas guardadas en el paso anterior.
   * **RECONSTRUIDO** (aproximado): corrida previa sin captura; respuesta registrada y textos del corpus, sin SHADOW. Se informa por separado.
3. **Variante:** el mismo DIG con `numbers_in_v2`. Solo cambia la normalización de cifras.
4. **Adversarial:** sobre cada respuesta capturada se inyectan cifras inventadas con 7 estrategias.

## 2. Reproducibilidad

| Modo | Casos | Decisión y reglas fallidas idénticas |
|---|---|---|
| CAPTURADO | 20 | **20 / 20** |
| RECONSTRUIDO | 41 | 34 / 41 (las diferencias vienen de no tener el texto SHADOW ni la evidencia cosida) |

**El DIG es determinista con sus entradas reales.** La reconstrucción sin captura no es fiable para conclusiones finas.

**Limitación de la captura:** el proveedor falló en 48 de 82 evaluaciones (QUOTA ×104 y REQUEST_TOO_LARGE ×31 errores registrados; Groq respondió 13 veces). Solo hubo 20 llamadas al DIG con respuesta del modelo.

## 3. Efecto de la variante DIG‑06

**Cambios de decisión:**
* **Solo en una dirección:** 8 casos cambian de reglas fallidas; **6 pasan de ABSTENER a PERMITIR** (2 capturados y 4 reconstruidos).
* **Ninguno** pasa de PERMITIR a ABSTENER.
* **Recuento de DIG‑06 fallido:** de 19 a 11. El resto de reglas no varía.
* **Los otros 2 casos** pierden el fallo de DIG‑06 pero siguen bloqueados por otras reglas: OOD‑006 por insuficiencia declarada y sin cita, y SCO‑013/0 por pertinencia sin el ancla.

**Revisión individual de los 6 desbloqueos.** En todos la cita es literal y del ancla esperada, y ninguno cita un distractor de ámbito.

| Caso | Modo | «Cifras» que bloqueaban | Origen | Revisión de lo afirmado frente a lo citado |
|---|---|---|---|---|
| SCO‑009 / 0 | CAPTURADO | 6.3 | «6.3 Random Weigh‑in», etiqueta con su título | «No hay pesaje aleatorio en equipos mixtos»: literal en la cita. **Respaldada.** |
| DIR‑017 / 1 | CAPTURADO | 8.1 | «8.10 Awarding Ceremonies», que `numbers_in` normaliza a 8.1 | «20 % del premio al entrenador»: literal en la cita. **Respaldada.** |
| DIR‑011 / 1 | RECONSTRUIDO | 2026, 8, 93 | ID SOR con guion U+2011 | «30 minutos o 6 combates antes del primer combate»: literal. **Respaldada.** |
| EXC‑005 / 1 | RECONSTRUIDO | 14, 2026 | fecha de edición | «Cabeza cubierta solo con vendaje médico; si no, se niega el derecho a competir y el rival gana por fusen‑gachi o kiken‑gachi»: literal en las dos citas. **Respaldada.** |
| EXC‑006 / 1 | RECONSTRUIDO | 1, 2, 3, 4, 2026 | numeración de lista y «SOR 2026» | Las condiciones 1, 2, 4 y 5 están en las citas. La condición 3 («el +5 % solo se aplica a las categorías de menos») es cierta en el SOR (p. 81), pero **no está en ninguna cita**: el DIG no verifica afirmaciones sin cifra. **Requiere revisión arbitral.** |
| MLG‑003 / 1 | RECONSTRUIDO | 6.3 | «6.3 Random Weigh‑in» | «Los veteranos no tienen pesaje aleatorio; se pesan el día anterior»: literal. **Respaldada.** |

**Sobre los casos reconstruidos:** los 4 se confirmaron con datos aproximados. Su desbloqueo en el flujo real queda **pendiente de una captura exacta**.

## 4. Pruebas adversariales (20 respuestas capturadas, 130 ataques)

Criterio de detección: la cifra inyectada aparece en la lista de cifras sin respaldo de DIG‑06.

| Ataque | Base detecta | Variante detecta |
|---|---|---|
| A1: sustituir una cifra respaldada por otra inventada | 10 / 10 | 10 / 10 |
| A2: cifra nueva («The applicable limit is N kg.») | 20 / 20 | 20 / 20 |
| A3: cifra dentro de una lista numerada 1., 2. | 20 / 20 | 20 / 20 |
| A4: decimal seguido de palabra en mayúscula («N.5 Kilograms…») | 20 / 20 | 20 / 20 |
| A4b: etiqueta real con otro título («6.3 Kilograms…») | 20 / 20 | 20 / 20 |
| A5: fecha distinta de la edición («20 August 2026») | 20 / 20 | 20 / 20 |
| A6: ID SOR con guiones Unicode más una cifra inventada | 20 / 20 | 20 / 20 |

* **La variante no deja pasar ninguna cifra inventada** de las probadas: 0 pérdidas de detección respecto al DIG base.
* **Puntos ciegos conocidos, aceptados y documentados.** La variante no puede distinguir una afirmación inventada que coincida exactamente con:
  * la fecha de edición («14 August 2026»);
  * una etiqueta de sección seguida de su propio título;
  * la numeración 1..k de una lista.

  En esos tres casos el número no expresa una cifra normativa.
* **Pendiente:** la estrategia adversarial S2 de la Fase 9, que usa el flujo completo con stubs, no se reejecutó con la variante. Queda para la siguiente fase.

## 5. Conclusiones y recomendación

1. **La variante corrige un falso negativo real y concreto** del DIG‑06: cuenta como cifras el formato de las citas. Lo hace sin pérdida de detección en 130 ataques y sin afectar a ninguna otra regla.
2. **Desbloquear no es lo mismo que acertar.** EXC‑006 muestra que el DIG sigue sin verificar afirmaciones sin cifra. Esa limitación (nivel D, NO_VERIFICADO) no cambia con la variante.
3. **No se recomienda llevarla a producción todavía.** Antes hacen falta:
   * una captura exacta con más casos, porque solo hay 20 (cuota);
   * la reejecución de la batería adversarial S2 de la Fase 9;
   * la revisión arbitral de los 6 desbloqueos (columna en el CSV de abstenciones);
   * la validación en un benchmark_v3 sellado.
4. **Las demás causas de falso negativo** (M2–M6 del diagnóstico: cifra de la consulta, encabezado, idioma SHADOW, DIG‑11, excepción cercana) **no se tocaron**, a la espera de decisión arbitral.
