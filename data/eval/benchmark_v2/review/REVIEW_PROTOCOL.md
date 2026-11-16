# benchmark_v2 - Protocolo de revision arbitral

Estado inicial de todos los items: `PENDING_EXPERT_REVIEW`. Las etiquetas `auto_labels` son
propuestas automaticas ancladas a texto literal; NO son verdad de referencia certificada.

1. Copiar `review_template.csv` a `review/reviews/<revisor>_<fecha>.csv` (no editar la plantilla).
2. Por cada fila rellenar `reviewer`, `review_date` (AAAA-MM-DD) y `verdict`:
   * `ACEPTA`  - comportamiento esperado, evidencia minima y distractores correctos.
   * `CORRIGE` - rellenar `human_expected_behavior` (RESPONDER, ABSTENER_INSUFICIENCIA,
     ABSTENER_FUERA_DE_DOMINIO, SOLICITAR_ACLARACION) y/o `human_expected_articles` (separados por `;`)
     y explicar en `notes`.
   * `RECHAZA` - el item no es valido (pregunta mal planteada, regla inexistente...); explicar en `notes`.
   * `DUDA`    - el revisor no puede decidir; queda pendiente.
3. Ejecutar `python scripts/merge_benchmark_v2_review.py review/reviews/<archivo>.csv`.
   El merge escribe `reviewed/benchmark_v2_reviewed.jsonl` y `reviewed/review_log.json`;
   nunca modifica `benchmark_v2.jsonl` ni las `auto_labels`.
4. Un item pasa a `EXPERT_REVIEWED` solo con veredicto ACEPTA o CORRIGE de al menos un revisor;
   con dos revisores discrepantes pasa a `REVIEW_CONFLICT`.
5. Las metricas deben informarse por separado sobre items `PENDING_EXPERT_REVIEW` y `EXPERT_REVIEWED`.
6. Revisar el split `test_sealed` no autoriza a usarlo para ajustar el sistema.
