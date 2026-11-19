# Informe — Verificación V4 y revisión humana (2026-11-19)

## 1. Contexto

Asistente de consulta normativa sobre las Sport and Organisation Rules (SOR 2026) de la IJF. Se preparó una nueva versión candidata con verificación de respuestas "V4" que sustituye al DIG bloqueante. Todo el trabajo está en la rama local `exp/verificacion-v4`, **sin commit, sin push y sin despliegue**. Producción no se tocó.

## 2. Cambios de la versión candidata

1. **Contador de consultas**: cuenta solo consultas reales.
2. **Contrato de respuesta**: respuestas directas, únicas, completas y proporcionales a la pregunta.
3. **Continuidad**: solo se señalan vacíos reales de información.
4. **Verificación V4** (flag `ADA_VERIFICATION_V4=1`), en dos capas:
   - Capa 1, determinista: citas literales, cifras y controles del DIG.
   - Capa 2: verificación de entailment con un modelo verificador (`gemini-3.8-flash`).
   - **Modo reducido**: si el verificador no está disponible, se ejecuta la capa 1 y decide el DIG completo.
5. **Reparación de páginas cosidas** (dentro de `ADA_CITATION_REPAIR`): un identificador de una página incluida en un pasaje cosido se atribuye al pasaje entregado solo si todas sus citas son literales en él.

Restricciones respetadas: DIG-05, DIG-09, K=5 (DEC-009), corpus, embeddings e índices sin cambios. R3 Scope Preference desactivado. No se usó el conjunto sellado de prueba. No hay parches específicos por consulta.

## 3. Pruebas automáticas

| Configuración | Pasadas | Omitidas |
|---|---|---|
| Por defecto | 632 | 21 |
| Candidata sin V4 | 631 | 22 |
| Candidata con V4 | 631 | 22 |

## 4. Evaluación con los conjuntos existentes (sin benchmarks nuevos)

- Preguntas respondibles contestadas: 26/27 (funcional) y 16/16 (validación).
- Fallo pendiente: G01, por un identificador de pasaje inventado por el modelo (`P055-S055`).
- Mutaciones adversariales detectadas por V4: 19/19.
- Latencia p90: 13–14 s.
- Tokens: unos 11.290 por consulta en promedio.
  - Por etapa: traducción ~475, análisis ~8.410 (flash-lite), verificación ~2.410.
  - Por dirección: entrada ~9.900, salida ~1.380.

## 5. Revisión humana (54 respuestas)

- Se revisaron 53 respuestas del archivo `REVISION_HUMANA.md`, más 1 consulta añadida por el revisor (U01: prohibiciones de los entrenadores en competencia).
- **Resultado: 54/54 CORRECTA.** Ninguna se validó como incorrecta, incompleta, no sustentada, fallo de recuperación u otra observación.

| Tipo de consulta | Cantidad |
|---|---|
| SI | 42 |
| NO (fuera del reglamento) | 5 |
| PARCIAL | 4 |
| AMBIGUA | 2 |
| Sin clasificar (U01) | 1 |

- Clasificación de errores: 0 en las seis categorías.
- Registro persistente: `revision_humana_registro.jsonl`, con una línea por decisión y el hash del archivo fuente.
- El archivo fuente no se modificó (sha256 `1e45bdbe…bd9f`).

### Discrepancias de referencia en el conjunto de evaluación

En dos respuestas el pasaje citado no coincide con el esperado por el conjunto. El revisor comprobó el texto del SOR y **la cita de la respuesta es correcta en ambos casos**:

| ID | Pregunta | Cita de la respuesta | Esperado por el conjunto | Texto verificado |
|---|---|---|---|---|
| V21 | Uñas del atleta / marca de cortaúñas | P202-S218 (Art. E1.3, pág. 202) | P118-S157 | "The nails of the feet and hands shall be cut short." |
| V22 | ¿Cuándo es el pesaje? | P077-S090 (Art. 6.2.3, pág. 77) | P077-S091, P079-S093 | "For IJF events, the official weigh-in is scheduled one day before the competition at 16:00 local time" |

Las métricas automáticas que comparan identificadores contarían estos dos casos como fallo, aunque las respuestas son correctas. No se ha verificado qué contienen los pasajes esperados.

## 6. Limitaciones

- La revisión humana la hizo un solo revisor.
- Los conjuntos son pequeños: 31 + 22 + 1.
- No se usó el conjunto sellado de prueba.
- La versión no se ha probado en producción.

## 7. Decisiones pendientes

1. ¿Hacer commit de la rama `exp/verificacion-v4` y promoverla a producción?
2. Corrección de G01 (identificador inventado): propuesta ofrecida, sin decidir.
3. ¿Corregir las referencias esperadas de V21 y V22 en el conjunto de evaluación? Requiere aprobación, porque altera el benchmark.
4. GitHub `main` está en 76a0eed: elegir entre un commit de revert y un force-push. No se hará force-push sin autorización explícita.
5. Push de las ramas locales y reglas de palabras clave del RRE.

## 8. Preguntas para la revisión externa

- ¿Es suficiente la evidencia (pruebas, mutaciones, 54/54 en revisión humana) para promover V4, o falta alguna verificación?
- ¿Cómo tratar las discrepancias de referencia del conjunto sin alterar la trazabilidad del benchmark?
- ¿Qué priorizar entre las decisiones pendientes?

## 9. Nota de corrección (2026-11-19, posterior a la entrega)

- **Alcance real de la revisión humana.** Las 54 validaciones cubren las respuestas **emitidas**. Las 6 no respuestas (G01, J01, J03, L02, L03, V23) **no** se revisaron por una persona; la sección 5 no debe leerse como 60/60.
- **Corrección G01 (identificadores inexistentes) aplicada y verificada en OCI.** Tras ella, G01, L02 y V23 pasan a SUCCESS. Esas tres respuestas nuevas **no** tienen revisión humana. Siguen sin revisar J01, J03 y L03 (no respuestas).
- **Defecto menor corregido.** `_strip_ids` (src/answer_verification.py) dejaba «, ,» al retirar un identificador intermedio de un grupo de citas. Se corrigió con una prueba (`test_strip_ids_leaves_no_empty_separators`). Solo afecta a la presentación de los identificadores, no a qué se emite.
- **Decisiones pendientes actualizadas.** El punto 2 de la sección 7 ya está aplicado. Queda pendiente la revisión humana de G01, L02 y V23, y de las tres no respuestas restantes.
