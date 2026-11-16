# AUDITORÍA OCI PRE-DEPLOYMENT — IJF SOR ASSISTANT 2026
## Inspección Diagnóstica Integral del Servidor de Producción (`https://sor.alxol.com`)

**Proyecto:** IJF SOR Assistant 2026  
**Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano  
**Planificador y Auditor Metodológico Independiente:** ChatGPT  
**Ejecutor Técnico Local:** Antigravity  
**Fecha:** 08 de noviembre de 2026  
**Entorno Remoto:** Oracle Cloud Infrastructure (OCI) — VM.Standard.A1.Flex  
**Commit Actualmente en Producción:** `61afc1bc2c8fa273f118f4e10bc447dbafcfe650` (`61afc1b`)  
**Release Candidato a Desplegar:** `3e86a0898a233a4357f11a29870780084d816f25` (`3e86a08`)

---

## 1. RESUMEN EJECUTIVO Y DICTAMEN

### 1.1 Resumen de la Auditoría
En cumplimiento estricto del mandato de la **Fase 1: Auditoría OCI Pre-Deployment**, se ejecutó una inspección técnica remota, no invasiva y de solo lectura sobre la instancia de producción en Oracle Cloud Infrastructure (OCI).

Se constataron de forma fehaciente los siguientes aspectos clave:
1. **Infraestructura OCI estable:** VM ARM64 Ampere Altra en Ubuntu 24.04.4 LTS, con carga mínima (`load average: 0.15`), 3.8 GiB de RAM disponible y **20 GiB de espacio libre en disco**, permitiendo respaldos completos holgadamente.
2. **Arquitectura de Runtime Real en Producción:** La aplicación en producción **no está corriendo como servicio Systemd nativo**, sino dentro de un **contenedor Docker** (`ijf-sor-assistant`), gestionado por `docker-compose.yml`, con reinicio automático (`unless-stopped`), montando `/home/ubuntu/IJF-SOR-Assistant` en `/app` mediante bind mount.
3. **Servicio Systemd `ijf-assistant.service`:** Se encuentra inactivo (`inactive (dead)` / `disabled`). Históricamente reportaba `Port 8501 is not available` debido a que el puerto 8501 está ocupado legítimamente por el proxy de Docker del contenedor `ijf-sor-assistant`.
4. **Exposición Web Segura:** El servicio está expuesto al público exclusivamente vía **Cloudflare Tunnel** (`cloudflared.service`), activo y saludable, resolviendo hacia `sor.alxol.com` con HTTP 200 dinámico, sin puertos HTTP/HTTPS expuestos directamente a internet público en la máquina.
5. **Persistencia de Observaciones de Usuario:** Se verificó la existencia del archivo de novedades en producción `data/feedback/user_observations.jsonl` (886 bytes, permisos `root:root`), el cual contiene observaciones reales de usuarios que **deben ser respaldadas y preservadas de forma obligatoria**.
6. **Estado de Git en el Servidor:** La rama activa es `integration/ijf-sor-2026-08-merge`, anclada en el commit `61afc1b`. El working tree está completamente limpio de modificaciones en archivos versionados (`git diff` vacío), con 13 scripts auxiliares no rastreados.
7. **Integridad del Corpus Oficial:** El PDF fuente posee exactamente el hash SHA-256 canónico `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` y los embeddings densos `dense_embeddings_candidate.npy` coinciden idénticamente con el hash local `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617`.

### 1.2 Dictamen Técnico Oficial

$$\mathbf{DICTAMEN:\ AUTORIZABLE\ PARA\ DESPLIEGUE\ (CON\ RESERVAS\ OPERATIVAS)}$$

El entorno de producción se encuentra sano, disponible y en condiciones técnicas óptimas para recibir el release `3e86a08`. Las reservas son de índole exclusivamente operativa:
- **Reserva 1 (Respaldo de Novedades):** Debe realizarse un backup explícito de `data/feedback/user_observations.jsonl` antes de cualquier maniobra para no perder retroalimentación real de usuarios.
- **Reserva 2 (Mecanismo de Despliegue Docker):** El despliegue debe contemplar el reinicio o recreación del contenedor Docker (`docker compose down && docker compose up -d --build` o `docker compose restart`), y no mediante `systemctl restart ijf-assistant`.

---

## 2. INVENTARIO DEL ENTORNO OCI

| Parámetro | Valor Inspeccionado en Producción | Observación Técnica |
| :--- | :--- | :--- |
| **Hostname** | `ijf-sor-assistant` | VM estándar en OCI |
| **Dirección IP Pública** | `149.130.187.132` | Región Colombia Central (Bogotá) |
| **Usuario SSH** | `ubuntu` | Autenticación con llave RSA 4096 bits |
| **Sistema Operativo** | Ubuntu 24.04.4 LTS (Noble Numbat) | Kernel `6.17.0-1018-oracle` |
| **Arquitectura de CPU** | ARM64 (`aarch64`) — Neoverse-N1 (1 OCPU) | Soporte completo Python 3.12 y Docker |
| **Memoria RAM** | 5.8 GiB Total / 1.9 GiB Usado / **3.8 GiB Disponible** | Memoria suficiente para recarga de modelos |
| **Espacio en Disco (`/`)** | 45 GiB Total / 25 GiB Usado / **20 GiB Disponible (57%)** | Holgura amplia para backups y logs |
| **Uptime del Sistema** | 110 días, 7 horas | Sistema con alta estabilidad |
| **Carga Promedio (`load`)** | `0.15, 0.08, 0.02` | Servidor desahogado |
| **Fecha / Hora del Servidor** | Sun 2026-11-08 05:50:06 UTC | Sincronizado vía NTP (`systemd-timesyncd`) |

---

## 3. ESTADO DE LA APLICACIÓN Y REPOSITORIO

- **Directorio de la Aplicación:** `/home/ubuntu/IJF-SOR-Assistant`
- **Rama Git Activa:** `integration/ijf-sor-2026-08-merge`
- **Commit HEAD en Producción:** `61afc1bc2c8fa273f118f4e10bc447dbafcfe650` (`61afc1b`)
- **Mensaje del Commit en Producción:** `fix(rre,ada): integrate general bridge ippon and head defense distinctions across categories`
- **Estado de Git (`git status`):**
  - Working tree versionado: **100% LIMPIO** (`git diff` reporta 0 diferencias).
  - Archivos no rastreados (`untracked`): 13 scripts scratch/diagnósticos previos (`check_ada_conn.py`, `eval_remote.py`, `verify_remote_auth.py`, etc.).
- **Entorno Virtual Python del Host:** `/home/ubuntu/IJF-SOR-Assistant/.venv`
  - Intérprete: Python 3.12.3
  - Streamlit Host: 1.59.2
- **Entorno del Contenedor de Producción:**
  - Contenedor Docker: `ijf-sor-assistant`
  - Python interno: Python 3.12
  - Streamlit interno: 1.59.2

---

## 4. ESTADO DE SERVICIOS Y RUNTIME

### 4.1 Servicio Systemd (`ijf-assistant.service`)
- **Estado:** `inactive (dead)` / `disabled`.
- **Causa:** El puerto `8501` está ocupado por el contenedor Docker `ijf-sor-assistant`. Intentar arrancar este servicio provocaba colisión de puertos (`Port 8501 is not available`).
- **Conclusión:** Este servicio no debe ser activado mientras Docker esté gestionando el asistente en el puerto 8501.

### 4.2 Contenedor Docker (`ijf-sor-assistant`) — Runtime Efectivo
- **Container ID:** `9328522b5d3f`
- **Imagen:** `ijf-sor-assistant-streamlit`
- **Estado:** `Up 3 days` (desde el 4 de noviembre de 2026).
- **Puertos:** `0.0.0.0:8501->8501/tcp`, `[::]:8501->8501/tcp`.
- **Comando:** `/usr/local/bin/python3.12 /usr/local/bin/streamlit run app.py --server.address=0.0.0.0 --server.port=8501`.
- **Montajes (`Mounts`):**
  - Bind Mount: `/home/ubuntu/IJF-SOR-Assistant` montado en `/app` (`rw`).
  - Volumen anónimo: `/app/.venv`
  - Volumen anónimo: `/app/__pycache__`
  - Volumen nombrado: `hf_cache` montado en `/root/.cache/huggingface`.

### 4.3 Cloudflare Tunnel (`cloudflared.service`)
- **Estado:** `active (running)` desde el 11 de agosto de 2026 (PID: 1342321).
- **Configuración:** Invocación con `--token-file /etc/cloudflared/token`.
- **Conectividad:** Enrutamiento directo y saludable hacia `https://sor.alxol.com` (protocolo QUIC).
- **Respuesta Pública HTTP:** Código `200 OK` (HTTP/2, Cloudflare DYNAMIC).

---

## 5. CONFIGURACIÓN Y SEGURIDAD

1. **Archivo de Entorno (`.env`):**
   - Ruta: `/home/ubuntu/IJF-SOR-Assistant/.env`
   - Permisos: `-rw------- (600)` — Propietario: `ubuntu:ubuntu`.
   - Variables requeridas presentes:
     - `GEMINI_API_KEY`: [PRESENTE Y CONFIGURADA]
     - `GROQ_API_KEY`: [PRESENTE Y CONFIGURADA]
     - `GROQ_MODEL`: [PRESENTE Y CONFIGURADA]
     - `LLM_PROVIDER`: [PRESENTE Y CONFIGURADA]
     - `FEEDBACK_ADMIN_TOKEN`: [PRESENTE Y CONFIGURADA]
   - *Nota de auditoría: Ningún valor de credencial fue divulgado ni comprometido durante la inspección.*
2. **Directorio y Datos de Feedback:**
   - Ruta: `/home/ubuntu/IJF-SOR-Assistant/data/feedback/`
   - Archivo: `user_observations.jsonl` (886 bytes, permisos `root:root`, generado por el contenedor).
   - Contiene telemetría de observaciones de usuario remitidas desde producción.
3. **Firewall del Sistema Operativo:**
   - Los puertos 80 y 443 no están abiertos hacia internet en iptables del host. Todo el tráfico web seguro ingresa exclusivamente a través del túnel de Cloudflare hacia `127.0.0.1:8501`.

---

## 6. INTEGRIDAD DEL CORPUS Y DIFERENCIAS RESPECTO AL RELEASE `3e86a08`

### 6.1 Hashes Criptográficos en Producción
| Archivo | Hash SHA-256 en Producción OCI | Estado frente al Manifiesto Canónico |
| :--- | :--- | :--- |
| `IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | **COINCIDENCIA TOTAL** |
| `dense_embeddings_candidate.npy` | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` | **COINCIDENCIA TOTAL** |

### 6.2 Diferencias Funcionales: Producción (`61afc1b`) vs Release (`3e86a08`)
| Característica | Estado Actual en Producción (`61afc1b`) | Estado en Release (`3e86a08`) |
| :--- | :--- | :--- |
| **Configuración $K$** | Sliders manuales en UI (`k_param` línea 1046, `min_score_param` línea 1051) | Sliders retirados. $K=5$ canónico fijado en backend (`DEC-009`). |
| **Invocación del Engine** | `engine.query(query, k=k_param, min_score=min_score_param)` | `engine.query(query, language=lang)` |
| **Mecanismo de Novedades** | Formulario genérico preliminar | 7 tipos normativos oficiales, auto-captura y exportación CSV admin. |
| **Detección OOD** | Sin calibración de anclas negativas | Puntuación calibrada de anclas negativas (100% abstención no judo). |
| **Selección y Síntesis** | Heurística básica de selección | 7 perfiles normativos, desempates y citas Tier 1 (`P0-C`). |
| **Kumi-kata** | Parcial (omisión explícita en dedos entrelazados continuos) | Shido reglamentario incorporado y evaluado 10/10 PASS (`P0-B`). |

---

## 7. ANÁLISIS DE RIESGOS

| Riesgo Identificado | Nivel | Estrategia de Mitigación Obligatoria |
| :--- | :---: | :--- |
| **Pérdida de datos de feedback de usuarios** | **ALTO** | Respaldar `data/feedback/user_observations.jsonl` previo a cualquier comando Git. |
| **Colisión de permisos en `data/feedback/`** | **MEDIO** | Como el contenedor corre como `root`, `user_observations.jsonl` tiene dueño `root`. Si un `git pull` intenta sobreescribir este archivo, podría fallar si no se excluye o respalda. |
| **Fallo al reiniciar servicio equivocado** | **MEDIO** | No reiniciar `systemctl restart ijf-assistant`. Se debe gestionar el despliegue vía Docker Compose (`docker compose restart` o `docker compose up -d`). |
| **Downtime prolongado durante build** | **BAJO** | El release `3e86a08` no introduce dependencias de sistema nuevas. Un reinicio del contenedor tarda menos de 10 segundos. |

---

## 8. PLAN DE RESPALDO PRE-DEPLOYMENT

Antes de iniciar la Fase 2 (Despliegue), se debe ejecutar en el servidor el siguiente respaldo estructurado:

1. **Creación de Directorio de Respaldo:**
   ```bash
   mkdir -p /home/ubuntu/backups/pre_deploy_3e86a08_$(date +%Y%m%d_%H%M%S)
   ```
2. **Copia de Seguridad de Archivos Críticos:**
   - Respaldo de `.env`
   - Respaldo de `data/feedback/user_observations.jsonl`
   - Respaldo de `docker-compose.yml`
   - Respaldo empaquetado del código fuente actual (`tar --exclude='.venv' --exclude='__pycache__' ...`)

---

## 9. PLAN DE ROLLBACK

En caso de detectarse alguna anomalía crítica tras el despliegue del release `3e86a08`:

1. **Reversión Git Inmediata:**
   ```bash
   cd /home/ubuntu/IJF-SOR-Assistant
   git checkout 61afc1bc2c8fa273f118f4e10bc447dbafcfe650
   ```
2. **Reinicio del Contenedor Docker:**
   ```bash
   sudo docker compose restart streamlit
   ```
3. **Verificación de Restauración:**
   - Comprobar que `https://sor.alxol.com` responde `200 OK` y exhibe el commit `61afc1b`.

---

## 10. RECOMENDACIÓN DE DESPLIEGUE

Se recomienda **PROCEDER CON LA FASE DE DESPLIEGUE CONTROLADO**, aplicando el siguiente flujo técnico:
1. Respaldar datos de usuario (`data/feedback/user_observations.jsonl`) y configuración `.env`.
2. Ejecutar `git fetch origin` y `git checkout 3e86a0898a233a4357f11a29870780084d816f25`.
3. Reiniciar el contenedor Docker mediante `sudo docker compose restart streamlit` (o recrear con `sudo docker compose up -d`).
4. Ejecutar pruebas de humo post-despliegue (`smoke tests`) sobre `https://sor.alxol.com`.

---

## 11. COMANDOS PROPUESTOS PARA LA FASE 2 (DESPLIEGUE)

```bash
# ==========================================
# 1. RESPALDO PRE-DESPLIEGUE
# ==========================================
BACKUP_DIR=/home/ubuntu/backups/pre_deploy_3e86a08_$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
cp /home/ubuntu/IJF-SOR-Assistant/.env "$BACKUP_DIR/.env.backup"
cp -r /home/ubuntu/IJF-SOR-Assistant/data/feedback "$BACKUP_DIR/feedback_backup" 2>/dev/null || true
cp /home/ubuntu/IJF-SOR-Assistant/docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"

# ==========================================
# 2. ACTUALIZACIÓN DE CÓDIGO FUENTE
# ==========================================
cd /home/ubuntu/IJF-SOR-Assistant
git fetch origin integration/ijf-sor-2026-08-merge
git checkout 3e86a0898a233a4357f11a29870780084d816f25

# ==========================================
# 3. REINICIO DEL CONTENEDOR DOCKER
# ==========================================
sudo docker compose restart streamlit

# ==========================================
# 4. MONITOREO DE INICIO Y HEALTHCHECK
# ==========================================
sudo docker logs --tail 30 -f ijf-sor-assistant
curl -I https://sor.alxol.com
```

---
*Informe elaborado por Antigravity (Ejecutor Técnico Local) para Alexis Oliveros Lozano (Product Owner) y ChatGPT (Auditor Metodológico).*
