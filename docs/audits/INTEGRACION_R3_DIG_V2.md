# Integración experimental R3 + DIG v2 — informe de pruebas y errores conocidos

Fecha: 2026-11-15 · Base local: `main` @ `bb1d32d` + cambios sin commit de las Fases 9–11 · Estado: **experimental, desactivado por defecto**.
Este informe no declara el asistente correcto, perfecto ni certificado. Todas las cifras son de DEV (41 ítems de benchmark_v2); `test_sealed` y benchmark_v3 no se usaron.

## 1. Qué se integró

| Pieza | Archivo | Activación | Efecto con la variable apagada |
|---|---|---|---|
| R3 — preferencia por ámbito (partes del SOR deducidas de la portada; indicadores `kata`, `veter`, `entri`, `gener`; re-ranking del pool de 25 con β=0,2) | `src/scope_preference.py`, `src/rre_engine.py` | `RRE_ENABLE_SCOPE_PREFERENCE=1` (`RRE_SCOPE_BETA`, por defecto 0,2) | Ninguno: mismo top-k que el original |
| DIG v2 — normalización de cifras de formato (guiones Unicode e IDs SOR, fecha de la edición, numeración de listas, etiqueta de sección + su propio título) | `src/dig_number_normalization.py`, `src/decision_integrity.py` | `DIG_NUMBER_NORMALIZATION=v2` (versión informada `DIG-1.3+NUM-v2`) | Ninguno: `numbers_in_v1` = función original |
| Aviso de instancia experimental en la UI | `app.py` | `IJF_DEPLOY_LABEL` | Ninguno |

No se integraron R2, R4 ni R5. No se añadieron hardcodes por pregunta o artículo (lo verifica `tests/test_r3_dig_v2_integration.py`). Los 31 boosts y 34 detectores temáticos preexistentes del RRE no se tocaron. EXC-006 sigue identificado y pendiente de revisión arbitral; no se creó ninguna excepción artificial. Corpus SOR y SHADOW sin cambios (`corpus_unchanged=True` en todas las corridas; hashes en `data/eval/integracion_r3_dig/logs/corpus_sha_*.txt`).

## 2. Pruebas automáticas (pytest, Windows)

| Modo | Resultado |
|---|---|
| Original (variables apagadas) | 7 failed, 485 passed, 1 skipped |
| Experimental (R3 + DIG v2 activos) | 7 failed, 484 passed, 2 skipped |

* 6 fallos son **preexistentes** e idénticos en ambos modos: golden dataset 75 % (< 80 %), `evaluation_battery` D01 y D04, `response_structurer` test_06, `rre_ada_architecture` test_07 y test_09. Todos reflejan que el DIG abstiene donde los tests antiguos esperaban SUCCESS con un generador simulado; no los introduce esta integración.
* El 7.º fallo (`test_productive_modules_do_not_reference_experimental`) lo causaban docstrings de los dos módulos nuevos que mencionaban `experimental.<módulo>`. **Corregido** reformulando los docstrings, sin tocar el test. Debe confirmarse en la próxima corrida de pytest.
* El skip adicional del modo experimental es el test que verifica los valores por defecto; se salta a propósito cuando las variables están activadas.

## 3. Recuperación DEV (determinista)

| Métrica (31 respondibles) | Original | Experimental |
|---|---|---|
| R@5 | 0,77 | 0,77 |
| MRR | 0,53 | 0,54 |
| Distractor de ámbito entregado | 7 | 5 |
| Distractor entregado sin evidencia | 2 | 1 |
| Errores de rango | 2 | 1 |
| Recall de referencias cruzadas (n=2) | 0,50 | **0,00** |

Cambió el bundle en 8 ítems. Mejoran SCO-013, SCO-024, SCO-025 (salen distractores de otras partes) y CAT-003 (sube el ámbito correcto). **Regresión:** B2-REF-001 ("Which rules must the judogi of veterans conform to?"). El indicador `veter` empuja todo el bundle a la parte de Veteranos y expulsa los pasajes del Apéndice C (judogi), que son justo la referencia cruzada obligatoria. Es un límite estructural de R3: penaliza las remisiones que salen de la parte detectada. En la Fase 11 la mitigación era R4 (carril de referencias cruzadas), que no se autorizó integrar.

## 4. Corridas LLM DEV (1 corrida por modo)

| | Original | Experimental |
|---|---|---|
| SUCCESS con evidencia esperada | 0/31 | 3/31 (DIR-007, MLG-003, SCO-010) |
| Falsos positivos de control (ámbito, cifras, sin evidencia, debía abstener) | 0 | 0 |
| Abstenciones legítimas (no respondibles) | 10/10 | 10/10 |
| Sin generación por API (cuota / petición demasiado grande) | 22 | 25 |
| Llamadas con error | 34 | 41 |

**Estas corridas no permiten afirmar una mejora.** Más del 50 % de los ítems no llegó a generarse por cuota de Gemini/Groq. La reejecución offline del DIG sobre las entradas capturadas (`scripts/replay_dig_f11.py`) muestra que:
* las decisiones se reproducen exactamente (12/12 original, 7/7 experimental);
* los 3 SUCCESS del modo experimental **también pasan con el DIG original v1**: se deben a que el generador respondió (Groq) en esa corrida, no a DIG v2;
* sobre las respuestas del modo original, DIG v2 desbloquea solo B2-DIR-011 (cifras `14` y `2026` = fecha de la edición), con cita en la evidencia esperada y sin distractor. Es el mismo caso que en la Fase 11;
* ataques adversariales con cifras inventadas: v2 no pierde ninguna detección respecto a v1.

## 5. Errores conocidos

1. **Regresión de referencias cruzadas con R3** (B2-REF-001, §3). Es el motivo principal para no llevar R3 a producción sin R4 o sin un ajuste revisado.
2. **Punto ciego del DIG (v1 y v2 por igual):** en B2-MLG-003, una cifra decimal inventada tras una etiqueta de capítulo (`37.5`) o una etiqueta real con otro título (`6.3`) no se detecta. Es preexistente y no lo introduce v2.
3. B2-MLG-003 (experimental) acepta una cita adicional fuera de la evidencia esperada (P079-S093, pesaje aleatorio general). Es pertinente, pero el benchmark no la anticipa.
4. Abstenciones por API (cuota Gemini/Groq, `REQUEST_TOO_LARGE`) dominan cualquier comparación LLM; hacen falta más corridas o cuota antes de sacar conclusiones.
5. Los 6 fallos de pytest preexistentes (§2).
6. EXC-006 pendiente de revisión arbitral. Benchmark_v2 sigue con etiquetas `PENDING_EXPERT_REVIEW`.
7. Los indicadores de R3 se derivan solo de la portada. Una pregunta que mezcla partes (p. ej. veteranos + judogi) se sesga hacia una sola.

## 6. Diferencia con la producción

La instancia experimental contiene **todo el estado local sin commit de las Fases 9–11** (DIG-1.3, contrato JSON con citas literales, módulos experimentales inactivos, evaluaciones), más R3 y DIG v2. Si producción corre `bb1d32d` o un commit anterior, la diferencia funcional es mucho mayor que R3 + DIG v2. El commit exacto de producción lo registra `server_install_exp.sh` en `install_*.log`. Con ese valor:

```powershell
git diff --stat <commit_produccion> exp/r3-dig-v2 -- src app.py requirements.txt Dockerfile
```

## 7. Reversión

* Funcional: apagar `RRE_ENABLE_SCOPE_PREFERENCE` y poner `DIG_NUMBER_NORMALIZATION=v1` (o quitarlas). El código vuelve a comportarse como el original.
* Instancia OCI: `bash ~/server_rollback_exp.sh` (solo baja `ijf-sor-assistant-exp`; `--purge` borra también la carpeta experimental). Producción, su contenedor, su volumen HF, Nginx y DNS no se tocan.
* Código local: la rama `exp/r3-dig-v2` es local (sin push). `git switch main` devuelve al estado anterior.

## 8. Correcciones v3 (2026-11-16, autorizadas por el responsable; desactivadas por defecto)

Origen: diagnóstico en la instancia experimental (`deploy/exp/diag_consultas_exp.py`). Con cuota disponible, 5 de 7 preguntas respondibles produjeron una respuesta correcta con citas literales; solo 1 se emitió.

| Corrección | Variable | Falso positivo que corrige | Qué NO cambia |
|---|---|---|---|
| Modo JSON del proveedor (solo la llamada de análisis) | `LLM_JSON_MODE=1` | DIG-00: respuestas correctas con JSON mal formado (ippon, duración del combate) | El DIG completo sigue evaluando la respuesta |
| DIG-05: título de la unidad derivada que contiene la cita literal | `DIG_V3=1` | Cita correcta del art. A1.11 "Judogi Rules for Veterans" sin la palabra *veteran* en la frase | Requiere cita literal localizada; no cuenta títulos de otras unidades |
| DIG-07: partes de términos con guion citados | `DIG_V3=1` | "waza" en la respuesta con "osaekomi-waza" en la cita | No al revés: un término con guion no citado sigue sin respaldo |
| DIG-08: vocabulario del texto de instrucciones | `DIG_V3=1` | "reglas" marcada como influencia SHADOW: la palabra figura en las instrucciones del prompt ("Reglas Generales y Reglas Especiales") | Solo se excluyen palabras del texto de instrucciones (prompt sin evidencia SOR ni bloques SHADOW); cifras, nombres y demás términos de SHADOW siguen detectándose |

| Guion de corte de línea del PDF | `DIG_V3=1` | DIG-03: "kansetsu-⏎waza" en el PDF frente a "kansetsu-waza" en la cita literal (ippon, ne-waza) | Se aplica igual a cita y pasaje; cualquier otra diferencia de texto sigue rechazada |

**Resultado en la instancia experimental (commit 4d83db9, 2026-11-16):** de 7 preguntas respondibles, 3 aceptadas con citas literales correctas (pesaje de veteranos, judogi de veteranos —antes bloqueada—, sanción por usar la cabeza en cadetes); la pregunta fuera de dominio, abstención correcta. Bloqueadas: ippon y ne-waza (guion de corte de línea, corregido después; en ippon además DIG-07/DIG-09 correctos: la respuesta afirma la excepción del puente sin citarla), tatami (JSON no válido pese al modo JSON; en diagnóstico) y duración del combate (proveedor: Gemini 503, Groq 413).

**Reejecución offline** (`scripts/replay_dig_v3.py`, 39 entradas capturadas de Fase 11 e integración; resultado en `data/eval/dig_v3/replay_dig_v3.json`): cambia 1 decisión (B2-REF-005 pasa a PERMITIR, con la cita en la evidencia esperada y sin distractor); ninguna pasa a bloquearse. **Ataques adversariales:** 9 tipos (cifras inventadas A1–A6, término distintivo inventado, cifra solo en SHADOW); v3 detecta exactamente lo mismo que el DIG actual y no hay ninguna regresión. El punto ciego conocido A4/A4b (1 caso) sigue igual en ambos.

Primera versión de la corrección DIG-08 (excluir palabras ordinarias en respuestas no inglesas) **descartada**: los tests `test_shadow_terms_in_analysis_abstain` y `test_shadow_title_words_count_as_shadow_footprint` mostraron que dejaba pasar fugas reales ("locked", "Ulaanbaatar", "Congelación"). La reejecución offline no mide la corrección DIG-08, porque las entradas capturadas no incluyen el texto de instrucciones.

**No resuelto por v3:** tatami (DIG-05: *tatami* no es término distintivo, aparece en > 15 % de páginas; DIG-06 detectó correctamente "50 cm" sin cita), sanción por cabeza en cadetes y ne-waza (límites del proveedor).
