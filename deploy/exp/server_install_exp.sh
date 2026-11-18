#!/usr/bin/env bash
# Instala (o sustituye) la instancia EXPERIMENTAL del IJF SOR Assistant en OCI SIN tocar produccion, con
# REVERSION AUTOMATICA a la version experimental anterior si algo falla.
#   bash server_install_exp.sh /home/ubuntu/ijf_exp_<sha7>.tar.gz
# Que hace:
#   1. Comprobaciones previas (solo lectura de produccion): paquete, imagen y cache del modelo de produccion.
#   2. Extrae el paquete en un directorio NUEVO de releases/ (nunca sobrescribe una version existente).
#   3. Copia el .env de produccion (solo lectura del original) y genera el compose experimental.
#   4. Retira el contenedor experimental anterior (solo proyecto ijf-exp; su directorio se conserva intacto).
#   5. Comprueba RAM y puerto, apunta 'current' a la nueva version, la arranca y verifica su salud.
#   Si falla cualquier paso posterior al 4: retira la nueva, restaura 'current' a la version anterior, levanta
#   su contenedor y comprueba su salud; registra el error original y el resultado de la reversion.
# Nunca: borra versiones anteriores, toca el contenedor/directorio/.env/puerto de produccion, Nginx ni DNS.
# Codigos de salida: 0 instalada | 2-6 abortada antes de retirar la anterior (nada cambia) |
#   10 fallo y reversion correcta | 11 fallo y reversion fallida | 12 fallo sin version anterior que restaurar.
set -Eeuo pipefail   # -E: el control de errores (trap ERR) tambien actua dentro de las funciones
TAR="${1:?uso: bash server_install_exp.sh ijf_exp_<sha7>.tar.gz}"
PROD_DIR="${PROD_DIR:-/home/ubuntu/IJF-SOR-Assistant}"
PROD_CT="${PROD_CT:-ijf-sor-assistant}"
PROD_PORT="${PROD_PORT:-8501}"
EXP_ROOT="${EXP_ROOT:-/home/ubuntu/IJF-SOR-Assistant-exp}"
EXP_CT="ijf-sor-assistant-exp"
EXP_PROJECT="ijf-exp"
EXP_PORT="${EXP_PORT:-8510}"
EXP_DIG_V3="${EXP_DIG_V3:-1}"
EXP_LLM_JSON="${EXP_LLM_JSON:-1}"
# Esquema JSON y correcciones de la auditoria de trazabilidad (respuesta unica, R1, R2, R5a, R5b): SOLO aqui.
EXP_LLM_SCHEMA="${EXP_LLM_SCHEMA:-1}"
EXP_FIX3="${EXP_FIX3:-1}"
MEM_LIMIT="${MEM_LIMIT:-2500m}"
MIN_RAM_MB="${MIN_RAM_MB:-1800}"
HEALTH_TRIES="${HEALTH_TRIES:-60}"
HEALTH_SLEEP="${HEALTH_SLEEP:-5}"
# --- Barreras (ANTES de crear o escribir nada): la experimental nunca puede coincidir con produccion -----------
real() { readlink -m "$1" 2>/dev/null || echo "$1"; }
case "$(real "$EXP_ROOT")/" in "$(real "$PROD_DIR")/"*) echo "ABORTO: EXP_ROOT dentro de produccion"; exit 6;; esac
[ "$EXP_CT" != "$PROD_CT" ] || { echo "ABORTO: contenedor experimental = produccion"; exit 6; }
[ "$EXP_PORT" != "$PROD_PORT" ] || { echo "ABORTO: puerto experimental = produccion"; exit 6; }
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi
mkdir -p "$EXP_ROOT/releases"
LOG="$EXP_ROOT/install_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1

# Unicas formas de parar/arrancar contenedores en este script: proyecto ijf-exp o contenedor experimental.
exp_down() { (cd "$1" && $DC -p "$EXP_PROJECT" -f docker-compose.exp.yml down) || docker rm -f "$EXP_CT" || true; }
exp_up()   { (cd "$1" && $DC -p "$EXP_PROJECT" -f docker-compose.exp.yml up -d); }
exp_health() {
  local code=""
  for _ in $(seq 1 "$HEALTH_TRIES"); do
    code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${EXP_PORT}/_stcore/health" || true)
    [ "$code" = "200" ] && { echo 200; return 0; }
    sleep "$HEALTH_SLEEP"
  done
  echo "${code:-sin_respuesta}"; return 1
}

PREV_REL=""; REL=""; PREV_STOPPED=0; PREV_RUNNING=0; FAIL_STEP="(ninguno)"
rollback() {
  local why="$1"
  trap - ERR; set +e
  echo "!! ERROR en el paso: $FAIL_STEP -- $why"
  echo "== REVERSION AUTOMATICA (solo instancia experimental; produccion no se toca)"
  [ -n "$REL" ] && [ -f "$REL/docker-compose.exp.yml" ] && exp_down "$REL"
  if [ -z "$PREV_REL" ] || [ ! -f "$PREV_REL/docker-compose.exp.yml" ]; then
    echo "REVERSION: no hay version experimental anterior que restaurar (current queda como estaba: ${PREV_REL:-ninguna})"
    [ -n "$PREV_REL" ] && ln -sfn "$PREV_REL" "$EXP_ROOT/current"
    echo "RESULTADO: FALLO SIN VERSION ANTERIOR"; exit 12
  fi
  ln -sfn "$PREV_REL" "$EXP_ROOT/current"
  echo "current restaurado -> $(readlink "$EXP_ROOT/current")"
  if [ "$PREV_RUNNING" != "1" ]; then
    echo "La version anterior no estaba en ejecucion: solo se restaura 'current' (no se arranca nada)."
    echo "RESULTADO: REVERSION CORRECTA a $PREV_REL (sin contenedor, como estaba)"; exit 10
  fi
  exp_up "$PREV_REL"
  h=$(exp_health); hrc=$?
  echo "Salud de la version restaurada: $h"
  echo "Produccion salud: $(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PROD_PORT}/_stcore/health" || true)"
  if [ $hrc -eq 0 ]; then echo "RESULTADO: REVERSION CORRECTA a $PREV_REL"; exit 10; fi
  echo "RESULTADO: REVERSION FALLIDA (la version anterior no responde)"; exit 11
}
on_err() { [ "$PREV_STOPPED" = "1" ] && rollback "comando fallido (linea $1)"; echo "ABORTO en $FAIL_STEP (linea $1): nada cambio en la experimental en ejecucion"; exit 2; }
trap 'on_err $LINENO' ERR

echo "== 1. Comprobaciones previas (solo lectura)"
FAIL_STEP="1-comprobaciones"
[ -f "$TAR.sha256" ] && (cd "$(dirname "$TAR")" && sha256sum -c "$(basename "$TAR").sha256")
free -m
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
PROD_IMAGE=$(docker inspect -f '{{.Config.Image}}' "$PROD_CT")
PROD_HF=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/root/.cache/huggingface"}}{{.Name}}{{end}}{{end}}' "$PROD_CT")
PROD_COMMIT=$(git -C "$PROD_DIR" rev-parse HEAD 2>/dev/null || echo desconocido)
PROD_HTTP_BEFORE=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PROD_PORT}/_stcore/health" || true)
echo "Produccion: contenedor=$PROD_CT imagen=$PROD_IMAGE commit=$PROD_COMMIT hf_volume=$PROD_HF salud=$PROD_HTTP_BEFORE"
if [ -z "$PROD_HF" ]; then echo "ABORTO: no se encontro el volumen de cache HF de produccion"; exit 3; fi
[ -L "$EXP_ROOT/current" ] && PREV_REL=$(readlink -f "$EXP_ROOT/current") || true
echo "Version experimental anterior: ${PREV_REL:-ninguna}"

echo "== 2. Extraer paquete en un directorio nuevo"
FAIL_STEP="2-extraer"
NAME=$(basename "$TAR" .tar.gz); SHA7=${NAME#ijf_exp_}
REL="$EXP_ROOT/releases/$SHA7"
[ -e "$REL" ] && REL="$EXP_ROOT/releases/${SHA7}_$(date +%Y%m%d%H%M%S)"   # nunca sobrescribe una version
mkdir -p "$REL"
tar -xzf "$TAR" -C "$REL" --strip-components=1

echo "== 3. Configuracion (copia del .env de produccion; el original solo se lee)"
FAIL_STEP="3-configuracion"
cp "$PROD_DIR/.env" "$REL/.env"; chmod 600 "$REL/.env"
if [ -d "$PROD_DIR/.streamlit" ]; then cp -r "$PROD_DIR/.streamlit" "$REL/.streamlit"; fi
grep -c '=' "$REL/.env" | xargs echo "variables en .env:"
cat > "$REL/docker-compose.exp.yml" <<YML
services:
  streamlit-exp:
    image: ${PROD_IMAGE}
    container_name: ${EXP_CT}
    ports:
      - "127.0.0.1:${EXP_PORT}:8501"
    env_file:
      - .env
    environment:
      RRE_ENABLE_SCOPE_PREFERENCE: "0"
      RRE_SCOPE_BETA: "0.2"
      DIG_NUMBER_NORMALIZATION: "v2"
      DIG_V3: "${EXP_DIG_V3}"
      LLM_JSON_MODE: "${EXP_LLM_JSON}"
      LLM_JSON_SCHEMA: "${EXP_LLM_SCHEMA}"
      ADA_UNIFIED_ANSWER: "${EXP_FIX3}"
      RRE_CHANNEL_CHAMPIONS: "${EXP_FIX3}"
      ADA_TRANSLATE_ANY_LANG: "${EXP_FIX3}"
      DIG_11_SUBORDINATE: "${EXP_FIX3}"
      DIG06_REFS: "${EXP_FIX3}"
      IJF_DEPLOY_LABEL: "Instancia EXPERIMENTAL ${SHA7} (R3 + DIG v2 + correcciones v3 + respuesta única y correcciones de trazabilidad). No es la version publicada; resultados no certificados."
    mem_limit: ${MEM_LIMIT}
    restart: unless-stopped
    volumes:
      - ./:/app
      - hf_cache_prod:/root/.cache/huggingface:ro
    command: ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
volumes:
  hf_cache_prod:
    external: true
    name: ${PROD_HF}
YML

echo "== 4. Retirar el contenedor experimental anterior (su directorio se conserva)"
FAIL_STEP="4-retirar-anterior"
if docker ps -a --format '{{.Names}}' | grep -qx "$EXP_CT"; then
  PREV_STOPPED=1
  if docker ps --format '{{.Names}}' | grep -qx "$EXP_CT"; then PREV_RUNNING=1; fi
  echo "Contenedor experimental anterior: existe (en ejecucion: $([ "$PREV_RUNNING" = 1 ] && echo si || echo no))"
  if [ -n "$PREV_REL" ] && [ -f "$PREV_REL/docker-compose.exp.yml" ]; then exp_down "$PREV_REL"; else docker rm -f "$EXP_CT"; fi
fi

echo "== 5. Comprobar recursos y arrancar la nueva version"
FAIL_STEP="5-ram"
AVAIL=$(free -m | awk '/^Mem:/{print $7}')
echo "RAM disponible: ${AVAIL} MB"
[ "$AVAIL" -ge "$MIN_RAM_MB" ] || { [ "$PREV_STOPPED" = "1" ] && rollback "RAM insuficiente (${AVAIL} MB < ${MIN_RAM_MB})"; echo "ABORTO: RAM insuficiente"; exit 2; }
FAIL_STEP="5-puerto"
if ss -ltn | grep -q ":$EXP_PORT "; then [ "$PREV_STOPPED" = "1" ] && rollback "puerto $EXP_PORT ocupado"; echo "ABORTO: puerto ocupado"; exit 5; fi
FAIL_STEP="5-arranque"
ln -sfn "$REL" "$EXP_ROOT/current"
PREV_STOPPED=1   # a partir de aqui, cualquier fallo restaura la version anterior (si existe)
exp_up "$REL"
FAIL_STEP="5-salud"
if ! code=$(exp_health); then rollback "la nueva version no responde en /_stcore/health (ultimo codigo $code)"; fi
echo "Salud experimental: $code"

echo "== 6. Verificacion posterior (informativa)"
trap - ERR; set +e
PROD_HTTP_AFTER=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PROD_PORT}/_stcore/health" || true)
echo "Produccion salud antes=$PROD_HTTP_BEFORE despues=$PROD_HTTP_AFTER commit=$(git -C "$PROD_DIR" rev-parse HEAD 2>/dev/null || echo ?)"
docker exec "$EXP_CT" sh -c 'cd /app && python - <<PY
import hashlib, os
print("corpus_sha256", hashlib.sha256(open("data/processed/rebuild_2026_08_corrected/passages_candidate.json","rb").read()).hexdigest())
print("flags", {k: os.environ.get(k) for k in ("RRE_ENABLE_SCOPE_PREFERENCE","RRE_SCOPE_BETA","DIG_NUMBER_NORMALIZATION","DIG_V3","LLM_JSON_MODE","LLM_JSON_SCHEMA","ADA_UNIFIED_ANSWER","RRE_CHANNEL_CHAMPIONS","ADA_TRANSLATE_ANY_LANG","DIG_11_SUBORDINATE","DIG06_REFS")})
import sys; sys.path.insert(0, "src")
import decision_integrity as d; print("DIG", d.DIG_VERSION)
PY'
docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'
echo "RESULTADO: INSTALADA $SHA7 en $REL (anterior conservada: ${PREV_REL:-ninguna})"
echo "Volver a la anterior si hiciera falta: bash server_rollback_exp.sh && ln -sfn ${PREV_REL:-<anterior>} $EXP_ROOT/current && cd $EXP_ROOT/current && $DC -p $EXP_PROJECT -f docker-compose.exp.yml up -d"
echo "Registro: $LOG"
exit 0
