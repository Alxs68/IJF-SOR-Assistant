#!/usr/bin/env bash
# Rotacion de GEMINI_API_KEY y GROQ_API_KEY en el .env de produccion y en el de la experimental.
# Las claves llegan por la entrada estandar (dos lineas) y nunca se imprimen: solo sus 4 ultimos caracteres.
# No llama a Gemini ni a Groq: solo comprueba /_stcore/health de cada instancia.
#
# Transaccional en los dos .env: se respaldan y verifican ambos, se preparan ambos y se sustituyen;
# si algo falla antes de terminar de sustituir los dos, se restauran AMBOS desde .env.bak_rot.
# Produccion: solo cambian esas dos lineas y se recrea el contenedor UNA vez con la misma imagen (sin build).
# Si produccion no responde 200 o no carga la clave nueva, se restauran los dos .env y produccion vuelve
# a levantarse con la configuracion anterior. Los respaldos .env.bak_rot se conservan siempre.
#
# Codigos de salida:
#   0  rotacion aplicada en produccion y experimental
#   1  no llegaron las dos claves (nada cambio)
#   2  respaldo existente o no verificado (nada cambio)
#   3  fallo al preparar o sustituir los .env (ambos restaurados; nada se reinicio)
#   10 produccion no respondio o no cargo la clave: .env restaurados y produccion revertida
#   11 la reversion de produccion tambien fallo (revisar a mano; respaldos conservados)
#   21 produccion OK con la clave nueva; la EXPERIMENTAL fallo al reiniciar, no responde o no cargo la clave
set -Eeuo pipefail
PROD=${PROD:-/home/ubuntu/IJF-SOR-Assistant}; EXPC=${EXPC:-/home/ubuntu/IJF-SOR-Assistant-exp/current}
HEALTH_TRIES=${HEALTH_TRIES:-24}; HEALTH_SLEEP=${HEALTH_SLEEP:-5}
export GIT_OPTIONAL_LOCKS=0
FILES=("$PROD/.env" "$EXPC/.env")
KEYS_RE='^(GEMINI_API_KEY|GROQ_API_KEY)='

last4() { local v; v=$(grep -E "^$2=" "$1" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '\r' || true); echo "${v: -4}"; }
ct_last4() { local v; v=$(docker exec "$1" printenv "$2" 2>/dev/null || true); echo "${v: -4}"; }
health() { curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$1/_stcore/health" 2>/dev/null || true; }
wait_health() { local i; for i in $(seq 1 "$HEALTH_TRIES"); do [ "$(health "$1")" = "200" ] && return 0; sleep "$HEALTH_SLEEP"; done; return 1; }
code_state() { git -C "$PROD" status --porcelain 2>/dev/null | grep -v -E '\.env' | sha256sum | cut -c1-16 || true; }

read -r G || true; read -r Q || true
G=$(printf '%s' "$G" | tr -d '\r'); Q=$(printf '%s' "$Q" | tr -d '\r')
if [ ${#G} -lt 30 ] || [ ${#Q} -lt 30 ]; then echo "ABORTO: no llegaron las dos claves; nada cambio"; exit 1; fi
NEW_G4=${G: -4}; NEW_Q4=${Q: -4}

echo "== 1. Estado previo (solo lectura)"
IMG0=$(docker inspect -f '{{.Image}}' ijf-sor-assistant); HEAD0=$(git -C "$PROD" rev-parse --short HEAD); ST0=$(code_state)
echo "produccion: commit=$HEAD0 imagen=${IMG0:7:12} salud=$(health 8501) | experimental salud=$(health 8510)"
for f in "${FILES[@]}"; do echo "  $f: Gemini ...$(last4 "$f" GEMINI_API_KEY) Groq ...$(last4 "$f" GROQ_API_KEY)"; done

echo "== 2. Respaldo y comprobacion del respaldo"
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "ABORTO: no existe $f; nada cambio"; exit 2; }
  [ -e "$f.bak_rot" ] && { echo "ABORTO: ya existe $f.bak_rot (no se sobrescribe un respaldo); nada cambio"; exit 2; }
done
for f in "${FILES[@]}"; do
  cp -p "$f" "$f.bak_rot"; chmod 600 "$f.bak_rot"
  if ! cmp -s "$f" "$f.bak_rot" || [ ! -s "$f.bak_rot" ]; then echo "ABORTO: respaldo de $f no verificado; nada cambio"; exit 2; fi
  echo "  respaldo verificado: $f.bak_rot ($(wc -l < "$f.bak_rot") lineas, identico al original)"
done

restore_envs() {   # devuelve los dos .env a su contenido anterior y lo comprueba
  local f ok=1
  for f in "${FILES[@]}"; do
    rm -f "$f.tmp" 2>/dev/null || true
    if cp -p "$f.bak_rot" "$f" && cmp -s "$f" "$f.bak_rot"; then echo "  restaurado: $f"; else echo "  !! NO se pudo restaurar $f (respaldo en $f.bak_rot)"; ok=0; fi
  done
  [ "$ok" = 1 ]
}
on_update_err() {
  trap - ERR
  echo "!! Fallo al actualizar los .env (linea $1): se restauran los dos archivos"
  if restore_envs; then echo "RESULTADO: SIN CAMBIOS (los dos .env restaurados; no se reinicio nada)"; exit 3; fi
  echo "RESULTADO: RESTAURACION INCOMPLETA (revisar a mano; no se reinicio nada)"; exit 11
}

echo "== 3. Preparacion y sustitucion de las dos lineas en ambos archivos"
trap 'on_update_err $LINENO' ERR
for f in "${FILES[@]}"; do   # 3a. preparar los dos archivos nuevos sin tocar los actuales
  grep -v -E "$KEYS_RE" "$f.bak_rot" > "$f.tmp" || true
  printf 'GEMINI_API_KEY=%s\nGROQ_API_KEY=%s\n' "$G" "$Q" >> "$f.tmp"
  chmod 600 "$f.tmp"
  # el resto del archivo debe quedar exactamente igual y las claves nuevas deben estar
  diff -q <(grep -v -E "$KEYS_RE" "$f.bak_rot" || true) <(grep -v -E "$KEYS_RE" "$f.tmp" || true) >/dev/null
  [ "$(last4 "$f.tmp" GEMINI_API_KEY)" = "$NEW_G4" ] && [ "$(last4 "$f.tmp" GROQ_API_KEY)" = "$NEW_Q4" ]
done
for f in "${FILES[@]}"; do   # 3b. sustituir
  mv -f "$f.tmp" "$f"
  [ "$(last4 "$f" GEMINI_API_KEY)" = "$NEW_G4" ]
  echo "  $f: Gemini ...$(last4 "$f" GEMINI_API_KEY) Groq ...$(last4 "$f" GROQ_API_KEY)"
done
trap - ERR
unset G Q

restore_prod() {
  trap - ERR
  echo "!! Produccion: $1. Se restauran los dos .env y se vuelve a levantar produccion con la configuracion anterior"
  restore_envs || true
  (cd "$PROD" && docker compose up -d --no-build --force-recreate streamlit) >/dev/null 2>&1 || true
  if wait_health 8501 && [ "$(ct_last4 ijf-sor-assistant GEMINI_API_KEY)" = "$(last4 "$PROD/.env.bak_rot" GEMINI_API_KEY)" ]; then
    echo "RESULTADO: REVERTIDO. Produccion salud=$(health 8501) con la clave anterior ...$(ct_last4 ijf-sor-assistant GEMINI_API_KEY)"; exit 10
  fi
  echo "RESULTADO: REVERSION FALLIDA. Produccion salud=$(health 8501); respaldos en *.env.bak_rot"; exit 11
}
trap 'restore_prod "error inesperado (linea $LINENO)"' ERR

echo "== 4. Reinicio de produccion (una vez, misma imagen, sin build)"
(cd "$PROD" && docker compose up -d --no-build --force-recreate streamlit) || restore_prod "fallo docker compose"
wait_health 8501 || restore_prod "no responde 200"
[ "$(ct_last4 ijf-sor-assistant GEMINI_API_KEY)" = "$NEW_G4" ] && [ "$(ct_last4 ijf-sor-assistant GROQ_API_KEY)" = "$NEW_Q4" ] \
  || restore_prod "el contenedor no cargo las claves nuevas"
trap - ERR

echo "== 5. Reinicio de la experimental"
EXP_FAIL=""
if ! (cd "$EXPC" && docker compose -p ijf-exp -f docker-compose.exp.yml up -d --no-build --force-recreate); then
  EXP_FAIL="fallo docker compose"
elif ! wait_health 8510; then
  EXP_FAIL="no responde 200 en 8510"
elif [ "$(ct_last4 ijf-sor-assistant-exp GEMINI_API_KEY)" != "$NEW_G4" ] || [ "$(ct_last4 ijf-sor-assistant-exp GROQ_API_KEY)" != "$NEW_Q4" ]; then
  EXP_FAIL="el contenedor no cargo las claves nuevas"
fi

echo "== 6. Verificacion"
IMG1=$(docker inspect -f '{{.Image}}' ijf-sor-assistant || echo desconocida); HEAD1=$(git -C "$PROD" rev-parse --short HEAD || echo desconocido); ST1=$(code_state)
echo "produccion: commit $HEAD0 -> $HEAD1 | imagen ${IMG0:7:12} -> ${IMG1:7:12} | archivos de codigo: $([ "$ST0" = "$ST1" ] && echo sin cambios || echo CAMBIARON)"
for c in ijf-sor-assistant ijf-sor-assistant-exp; do
  echo "  contenedor $c: Gemini ...$(ct_last4 $c GEMINI_API_KEY) | Groq ...$(ct_last4 $c GROQ_API_KEY)"
done
echo "Produccion HTTP: $(health 8501) | Experimental HTTP: $(health 8510)"
echo "Respaldos conservados: $PROD/.env.bak_rot y $EXPC/.env.bak_rot"
if [ -n "$EXP_FAIL" ]; then
  echo "RESULTADO: PRODUCCION ROTADA Y SANA; FALLO DE LA EXPERIMENTAL: $EXP_FAIL"; exit 21
fi
echo "RESULTADO: ROTACION APLICADA"
