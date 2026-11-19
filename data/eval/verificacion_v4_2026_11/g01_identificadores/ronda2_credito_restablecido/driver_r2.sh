#!/usr/bin/env bash
E=/home/ubuntu/ijf-eval; W=$E/candv4
$E/tools/run_replay.sh rep2_g01 $W v4 consultas_funcionales_v1.json
$E/tools/run_solo.sh r2f $W v4 consultas_funcionales_v1.json D01,D02
$E/tools/run_solo.sh r2v $W v4 consultas_validacion_v1.json V16,V17,V18,V19,V20,V21,V22,V23
echo "FIN driver_r2" >> $E/out/driver_r2.log
