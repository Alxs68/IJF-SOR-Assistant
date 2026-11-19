#!/usr/bin/env bash
# uso: run_eval.sh <etiqueta> <worktree> <perfil> <conjunto.json>
set -u
E=/home/ubuntu/ijf-eval; L=$1; W=$2; P=$3; SET=$4
FL=(-e RRE_ENABLE_SCOPE_PREFERENCE=0 -e RRE_CHANNEL_CHAMPIONS=1 -e DIG_NUMBER_NORMALIZATION=v2 -e DIG_V3=1
    -e DIG_11_SUBORDINATE=1 -e DIG06_REFS=1 -e LLM_JSON_MODE=1 -e LLM_JSON_SCHEMA=1 -e ADA_UNIFIED_ANSWER=1 -e ADA_TRANSLATE_ANY_LANG=1)
EXTRA=()
[ -f "$E/tools/extra_$P.env" ] && EXTRA=(--env-file "$E/tools/extra_$P.env")
docker run --rm --name "ijf-eval-$L" --memory 2g --env-file /home/ubuntu/IJF-SOR-Assistant/.env "${FL[@]}" "${EXTRA[@]}" \
  -e PYTHONIOENCODING=utf-8 -e REPLAY_FILE=/tools/g01_respuesta_grabada.json -v "$W":/app -v "$E/prev/evidence_reassembly.py":/app/src/evidence_reassembly.py:ro -v "$E/tools":/tools:ro -v "$E/out":/out \
  -v ijf-sor-assistant_hf_cache:/root/.cache/huggingface:ro -w /app ijf-sor-assistant-streamlit:latest \
  python /tools/eval_replay.py --consultas "/tools/$SET" --out "/out/$L.jsonl" --etiqueta "$L" --solo G01 \
  > "$E/out/$L.log" 2>&1
echo "FIN $L rc=$?" >> "$E/out/$L.log"
