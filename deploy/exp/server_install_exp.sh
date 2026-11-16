#!/usr/bin/env bash
# Instala la instancia EXPERIMENTAL del IJF SOR Assistant (R3 + DIG v2) en OCI SIN tocar produccion.
#   bash server_install_exp.sh /home/ubuntu/ijf_exp_<sha7>.tar.gz
# Que hace:
#   1. Comprobaciones previas (solo lectura): RAM, disco, contenedor de produccion, commit de produccion.
#   2. Extrae el paquete en /home/ubuntu/IJF-SOR-Assistant-exp/releases/<sha7> (directorio NUEVO).
#   3. Copia el .env de produccion (sin modificarlo) a la instancia experimental.
#   4. Arranca un contenedor NUEVO 'ijf-sor-assistant-exp' con la MISMA imagen de produccion (sin builds ni
#      dependencias nuevas), el codigo experimental montado, flags R3 + DIG v2, limite de memoria y el
#      puerto 127.0.0.1:8502 (solo local; acceso por tunel SSH o subdominio opcional).
#   5. Verifica salud de la instancia experimental y que produccion sigue respondiendo igual.
# No modifica: contenedor, directorio, .env, Nginx, DNS ni puertos de produccion.
set -euo pipefail
TAR="${1:?uso: bash server_install_exp.sh ijf_exp_<sha7>.tar.gz}"
PROD_DIR="${PROD_DIR:-/home/ubuntu/IJF-SOR-Assistant}"
PROD_CT="${PROD_CT:-ijf-sor-assistant}"
EXP_ROOT="/home/ubuntu/IJF-SOR-Assistant-exp"
EXP_CT="ijf-sor-assistant-exp"
EXP_PORT="${EXP_PORT:-8510}"
EXP_DIG_V3="${EXP_DIG_V3:-1}"
EXP_LLM_JSON="${EXP_LLM_JSON:-1}"
MEM_LIMIT="${MEM_LIMIT:-2500m}"
LOG="$EXP_ROOT/install_$(date +%Y%m%d_%H%M%S).log"
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi
mkdir -p "$EXP_ROOT/releases"
exec > >(tee -a "$LOG") 2>&1

echo "== 1. Comprobaciones previas (solo lectura)"
[ -f "$TAR.sha256" ] && (cd "$(dirname "$TAR")" && sha256sum -c "$(basename "$TAR").sha256")
free -m
df -h /home /var/lib/docker 2>/dev/null || df -h /
AVAIL=$(free -m | awk '/^Mem:/{print $7}')
echo "RAM disponible: ${AVAIL} MB"
if [ "$AVAIL" -lt 1800 ]; then echo "ABORTO: menos de 1800 MB disponibles; no se arranca la instancia experimental"; exit 2; fi
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
PROD_IMAGE=$(docker inspect -f '{{.Config.Image}}' "$PROD_CT")
PROD_HF=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/root/.cache/huggingface"}}{{.Name}}{{end}}{{end}}' "$PROD_CT")
PROD_COMMIT=$(git -C "$PROD_DIR" rev-parse HEAD 2>/dev/null || echo desconocido)
PROD_DIRTY=$(git -C "$PROD_DIR" status --porcelain 2>/dev/null | wc -l || echo ?)
PROD_HTTP_BEFORE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501/_stcore/health || true)
echo "Produccion: contenedor=$PROD_CT imagen=$PROD_IMAGE commit=$PROD_COMMIT cambios_locales=$PROD_DIRTY hf_volume=$PROD_HF salud=$PROD_HTTP_BEFORE"
if [ -z "$PROD_HF" ]; then echo "ABORTO: no se encontro el volumen de cache HF de produccion (modelo denso)"; exit 3; fi
if docker ps -a --format '{{.Names}}' | grep -qx "$EXP_CT"; then echo "ABORTO: ya existe $EXP_CT; use server_rollback_exp.sh antes de reinstalar"; exit 4; fi
if ss -ltn | grep -q ":$EXP_PORT "; then echo "ABORTO: el puerto $EXP_PORT ya esta en uso"; exit 5; fi

echo "== 2. Extraer paquete"
NAME=$(basename "$TAR" .tar.gz)
SHA7=${NAME#ijf_exp_}
REL="$EXP_ROOT/releases/$SHA7"
mkdir -p "$REL"
tar -xzf "$TAR" -C "$REL" --strip-components=1
ln -sfn "$REL" "$EXP_ROOT/current"

echo "== 3. Configuracion (copia del .env de produccion; produccion no se modifica)"
cp "$PROD_DIR/.env" "$REL/.env"
chmod 600 "$REL/.env"
[ -d "$PROD_DIR/.streamlit" ] && cp -r "$PROD_DIR/.streamlit" "$REL/.streamlit" || true
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
      RRE_ENABLE_SCOPE_PREFERENCE: "1"
      RRE_SCOPE_BETA: "0.2"
      DIG_NUMBER_NORMALIZATION: "v2"
      DIG_V3: "${EXP_DIG_V3}"
      LLM_JSON_MODE: "${EXP_LLM_JSON}"
      IJF_DEPLOY_LABEL: "Instancia EXPERIMENTAL ${SHA7} (R3 + DIG v2 + correcciones v3). No es la version publicada; resultados no certificados."
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

echo "== 4. Arranque de la instancia experimental"
(cd "$REL" && $DC -p ijf-exp -f docker-compose.exp.yml up -d)
for i in $(seq 1 60); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${EXP_PORT}/_stcore/health" || true)
  [ "$code" = "200" ] && break; sleep 5
done
echo "Salud experimental: ${code:-sin respuesta}"
docker logs --tail 40 "$EXP_CT" || true

echo "== 5. Verificacion posterior"
PROD_HTTP_AFTER=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501/_stcore/health || true)
echo "Produccion salud antes=$PROD_HTTP_BEFORE despues=$PROD_HTTP_AFTER commit=$(git -C "$PROD_DIR" rev-parse HEAD 2>/dev/null || echo ?)"
docker exec "$EXP_CT" sh -c 'cd /app && python - <<PY
import hashlib, os
print("corpus_sha256", hashlib.sha256(open("data/processed/rebuild_2026_08_corrected/passages_candidate.json","rb").read()).hexdigest())
print("flags", {k: os.environ.get(k) for k in ("RRE_ENABLE_SCOPE_PREFERENCE","RRE_SCOPE_BETA","DIG_NUMBER_NORMALIZATION","DIG_V3","LLM_JSON_MODE")})
import sys; sys.path.insert(0, "src")
import decision_integrity as d; print("DIG", d.DIG_VERSION)
from src.scope_preference import ScopePreference; print("R3 indicadores", sorted(ScopePreference().indicator))
PY'
docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'
free -m
echo "Commit experimental desplegado: $SHA7   Directorio: $REL"
echo "Acceso: desde su PC ->  ssh -i <clave> -N -L ${EXP_PORT}:127.0.0.1:${EXP_PORT} ubuntu@<IP_OCI>   y abra http://localhost:${EXP_PORT}"
echo "Registro: $LOG"
