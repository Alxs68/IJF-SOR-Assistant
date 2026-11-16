#!/usr/bin/env bash
# Retira la instancia EXPERIMENTAL. No toca produccion. Conserva los releases (borrado opcional con --purge).
set -uo pipefail
EXP_ROOT="/home/ubuntu/IJF-SOR-Assistant-exp"
if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi
(cd "$EXP_ROOT/current" 2>/dev/null && $DC -p ijf-exp -f docker-compose.exp.yml down) || docker rm -f ijf-sor-assistant-exp
if [ "${1:-}" = "--purge" ]; then rm -rf "$EXP_ROOT"; echo "Directorio experimental eliminado"; fi
echo "Produccion:"; docker ps --filter name=ijf-sor-assistant --format '{{.Names}}\t{{.Status}}'
curl -s -o /dev/null -w 'salud produccion %{http_code}\n' http://127.0.0.1:8501/_stcore/health
