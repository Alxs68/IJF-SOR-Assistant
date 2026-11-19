#!/usr/bin/env bash
E=/home/ubuntu/ijf-eval; W=$E/candv4
$E/tools/run_eval.sh g01f $W v4 consultas_funcionales_v1.json
$E/tools/run_eval.sh g01v $W v4 consultas_validacion_v1.json
docker run --rm --name ijf-eval-mut --memory 2g --env-file /home/ubuntu/IJF-SOR-Assistant/.env -e PYTHONIOENCODING=utf-8 -e IJF_SOR_EDITION=2026-08 \
  -v $W:/app -v $E/out:/out -w /app ijf-sor-assistant-streamlit:latest \
  python scripts/eval_mutaciones_v4.py /out/g01f.jsonl /out/g01v.jsonl --out /out/mut_g01.jsonl > $E/out/mut_g01.log 2>&1
echo "FIN driver rc=$?" >> $E/out/mut_g01.log
