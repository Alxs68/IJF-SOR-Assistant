#!/usr/bin/env bash
# Estado de produccion y de la instancia experimental (solo lectura).
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker stats --no-stream --format '{{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}'
free -m
for p in 8501 8502; do curl -s -o /dev/null -w "puerto $p salud %{http_code}\n" http://127.0.0.1:$p/_stcore/health; done
readlink -f /home/ubuntu/IJF-SOR-Assistant-exp/current 2>/dev/null
git -C /home/ubuntu/IJF-SOR-Assistant rev-parse HEAD 2>/dev/null | sed 's/^/commit produccion /'
