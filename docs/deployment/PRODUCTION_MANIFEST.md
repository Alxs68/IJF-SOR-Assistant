# MANIFIESTO DE PRODUCCIÓN Y ESTADO DE DESPLIEGUE
## IJF SOR Assistant 2026

**Fecha de emisión:** 07 de noviembre de 2026  
**Product Owner y Autoridad Normativa (Autoridad Soberana):** Alexis Oliveros Lozano  
**Planificador, Supervisor Metodológico y Auditor Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Estado:** VIGENTE — INFORMATIVO Y DE CONTROL DE CONFIGURACIÓN

---

## 1. IDENTIFICACIÓN DEL ENTORNO DE PRODUCCIÓN ACTIVO

| Parámetro | Detalle Conocido de Producción | Evidencia y Estado de Verificación |
| :--- | :--- | :--- |
| **URL Pública Activa** | `https://sor.alxol.com` | Operativa (HTTP 200, certificado TLS activo) |
| **Infraestructura Cloud** | Oracle Cloud Infrastructure (OCI) — Free Tier / Compute Instance | Bogotá (Colombia Central), `VM.Standard.A1.Flex` |
| **Arquitectura de Servidor** | ARM64 (Ampere Altra), Canonical Ubuntu 24.04 LTS | Especificada en `docs/deployment/oci_deployment.md` |
| **Servicio del Sistema** | `systemd` (`ijf-assistant.service`) | Configurado para reinicio automático en servidor |
| **Reverse Proxy / TLS** | **Pendiente de verificación remota** | Responde en puerto 443 HTTPS. Tecnología específica (Caddy, Nginx, Traefik o Load Balancer OCI) no documentada en el repositorio. |
| **Puerto Interno de la App** | `8501` (Streamlit standard) | Tráfico interno enlazado a `127.0.0.1:8501` |
| **Commit Desplegado en Producción** | `61afc1b` (`61afc1b8ebec886d3e38c9febe5fbddb53c15555`) | Desplegado el 04 de noviembre de 2026 en estado limpio |
| **Corpus Activo en Producción** | IJF Sport and Organisation Rules (SOR) — Edición Agosto 2026 (`385 pasajes`) | Hash canónico SHA-256 verificado en respuestas remotas |
| **Verificación Externa Realizada** | Playwright E2E sobre `https://sor.alxol.com` (06/11/2026) | Verificación sintética externa funcional (español e inglés) |

---

## 2. ADVERTENCIA CRÍTICA: DISCREPANCIA ENTRE DESARROLLO Y PRODUCCIÓN

> [!WARNING]
> **NO EXISTE EQUIVALENCIA FUNCIONAL ENTRE DESARROLLO LOCAL Y PRODUCCIÓN:**  
> Aunque ambos entornos tienen como ancestro común el commit `61afc1b`, el servidor de producción corre dicho commit en estado limpio tal como fue desplegado el 04/11/2026.  
> Por tanto, **producción carece de todas las fases correctivas P0-B, P0-C, P1-A, P1-B, de los ajustes de interfaz y de la configuración canónica ratificada en DEC-009**.  
> Por instrucción expresa del Product Owner, **no se realiza despliegue a producción en esta fase**, manteniéndose congelada hasta la autorización formal de publicación y release.

### Matriz Comparativa Detallada
| Característica / Componente | Desarrollo Local (`integration/ijf-sor-2026-08-merge`) | Producción OCI (`https://sor.alxol.com`) | Brecha / Diferencia Funcional |
| :--- | :--- | :--- | :--- |
| **Base de Commit** | `61afc1b` + árbol de trabajo local con modificaciones | `61afc1b` (árbol limpio al 04/11/2026) | Local posee cambios no comprometidos de P0/P1 y gobernanza |
| **Corpus SOR Canónico** | SOR Agosto 2026 (385 pasajes indexados) | SOR Agosto 2026 (385 pasajes indexados) | **Idéntico** |
| **Configuración Canónica RRE** | **$K=5$, `min_score=None` ratificado formalmente (DEC-009)** | **No ratificado ni aplicado en producción** | Producción corre en estado previo a DEC-009 con sliders manuales en UI |
| **Fase P0-B (Kumi-kata)** | Implementada (10/10 PASS focal CGPT-06, ESC-09 Shido corregido) | Parcial / Sin la corrección focal ESC-09 | Producción omite la sanción explícita en dedos entrelazados continuos |
| **Fase P0-C (Selección / Síntesis)** | Implementada (7 perfiles normativos, desempates, citas Tier 1) | Sin contrato rector de selección de 7 perfiles | Producción usa heurística previa sin desempates de P0-C |
| **Fase P1-A (Calibración OOD)** | Calibrada (100% exactitud en benchmark de 40 casos) | Detección preliminar no calibrada | Producción vulnerable a falsas aceptaciones OOD |
| **Fase P1-B (E2E Configuración)** | Verificada (propagación determinista, 9/9 PASS) | Sin validación formal de propagación E2E | Local verificado |
| **Interfaz: Controles Técnicos** | **Retirados** (sliders de $K$ y `min_score` eliminados en UI) | **Presentes** (sliders de $K$ y `min_score` visibles en sidebar) | En producción el usuario aún puede alterar manualmente $K$ y `min_score` |
| **Interfaz: Mecanismo Novedades** | **Simplificado** (7 tipos normativos oficiales, auto-captura, exportación CSV) | Formulario previo de feedback estándar | Local cuenta con reporte de baja fricción y CSV en admin |
| **Suites Automatizadas** | 86 pruebas automáticas reportadas PASS | No ejecuta pruebas automáticas locales | Regresiones cubiertas localmente |

> [!NOTE]
> **ESTADO DE LA DECISIÓN DEC-009 FRENTE A PRODUCCIÓN:**  
> La ratificación soberana de **$K=5$** como configuración canónica oficial (DEC-009) aplica a la línea base rectora del proyecto IJF SOR Assistant 2026. **Dicha configuración NO se encuentra actualmente desplegada ni activa en el entorno de producción `https://sor.alxol.com`**, el cual continuará operando en su estado previo hasta que el Product Owner autorice un despliegue formal tras las fases de release correspondientes.

---

## 3. CONFIGURACIÓN TÉCNICA DEL SERVICIO EN OCI

### A. Unidad `systemd` Referencial (`/etc/systemd/system/ijf-assistant.service`)
```ini
[Unit]
Description=IJF SOR Assistant 2026 Streamlit Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/IJF-SOR-Assistant
ExecStart=/home/ubuntu/IJF-SOR-Assistant/venv/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/home/ubuntu/IJF-SOR-Assistant/.env

[Install]
WantedBy=multi-user.target
```

### B. Enrutamiento HTTPS y Terminación TLS
- **Dominio Público:** `sor.alxol.com`
- **Protocolo Externo:** HTTPS (puerto 443 estándar).
- **Tecnología de Reverse Proxy:** **Pendiente de verificación remota**. No se asume Caddy ni Nginx sin inspección directa del servidor.
- **Destino Interno:** `http://127.0.0.1:8501` con soporte para WebSockets de Streamlit.

---

## 4. ASPECTOS TÉCNICOS PENDIENTES DE AUDITORÍA REMOTA EN OCI

Previo a cualquier futuro despliegue de la versión integrada (P0/P1 y DEC-009), se deben auditar y validar los siguientes aspectos en el servidor de OCI:

1. **Persistencia Remota del Archivo de Novedades:**  
   - En el código local, la ruta establecida es `data/feedback/user_observations.jsonl`.  
   - En el servidor OCI, el estado queda registrado como: **"Persistencia remota pendiente de verificación"**. Se debe verificar si el directorio `data/feedback/` cuenta con permisos de escritura para el usuario `ubuntu` del servicio y si está excluido de sobrescrituras accidentales ante futuros `git checkout` o `git pull`.
2. **Políticas de Copias de Respaldo Remotas:**  
   - Establecer un cron de respaldo periódico para las observaciones y telemetría de usuario reportadas desde producción.
3. **Consumo de Memoria en Arquitectura ARM64:**  
   - La instancia opera bajo el shape `VM.Standard.A1.Flex` (6 GB RAM). Se debe vigilar que la concurrencia no comprometa la memoria ante consultas simultáneas.
4. **Variables de Entorno y Claves de API:**  
   - Verificar la vigencia de credenciales en `/home/ubuntu/IJF-SOR-Assistant/.env`.

---

## 5. PROTOCOLO REQUERIDO PARA FUTURO DESPLIEGUE

Cualquier actualización de producción deberá cumplir obligatoriamente con el siguiente flujo soberano:

```
[Árbol Local Verificado (86 pruebas PASS)]
                │
                ▼
   [Aprobación Formal PO + Dictamen ChatGPT]
                │
                ▼
   [Commit en rama integration]
                │
                ▼
     [Push a GitHub origin]
                │
                ▼
  [Merge formal a main + Tag de Release]
                │
                ▼
  [Despliegue a OCI (pull, sync venv, restart service)]
                │
                ▼
 [Verificación Humana y Playwright E2E en sor.alxol.com]
```

> **NOTA DE GOBERNANZA:**  
> Por orden del Product Owner, **no se ejecutará despliegue alguno ni conexión SSH a producción** durante la presente actividad de formalización documental.
