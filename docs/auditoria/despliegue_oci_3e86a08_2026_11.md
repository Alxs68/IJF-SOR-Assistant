# INFORME DE DESPLIEGUE OCI Y PROTOCOLO DE ROLLBACK — IJF SOR ASSISTANT 2026
## Fase 3: Activación del Release `3e86a08`, Detección de Anomalía de Dependencia y Restauración Inmediata a `61afc1b`

**Proyecto:** IJF SOR Assistant 2026  
**Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano  
**Planificador y Auditor Metodológico Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha:** 08 de noviembre de 2026  
**Entorno Remoto:** Oracle Cloud Infrastructure (OCI) — VM ARM64  
**Release Evaluado:** `3e86a0898a233a4357f11a29870780084d816f25` (`3e86a08`)  
**Línea Base Restaurada (Rollback):** `61afc1bc2c8fa273f118f4e10bc447dbafcfe650` (`61afc1b`)  
**URL de Producción:** `https://sor.alxol.com`

---

## 1. RESUMEN EJECUTIVO Y DICTAMEN FINAL

### 1.1 Resumen de la Operación
En cumplimiento estricto del mandato de la **Fase 3: Despliegue Autorizado en OCI**:
1. **Validación Previa Satisfactoria:** Se verificó la existencia del respaldo de Fase 2 (`/home/ubuntu/backups/pre_deploy_3e86a08_20261108_061328`), la preservación de `.env` (permisos 600), la persistencia de observaciones reales de usuario (`data/feedback/user_observations.jsonl`, 886 bytes) y la salud de Cloudflare Tunnel (`cloudflared`, HTTP 200).
2. **Activación Controlada:** Se ejecutó `git checkout 3e86a0898a233a4357f11a29870780084d816f25` en `/home/ubuntu/IJF-SOR-Assistant` y se reinició en caliente el contenedor Docker de producción mediante `sudo docker compose restart streamlit`.
3. **Detección de Anomalía Crítica en Validación Post-Despliegue:**
   Durante la ejecución de las pruebas funcionales directas en el contenedor de producción, se detectó una excepción bloqueante en tiempo de ejecución:
   ```text
   ModuleNotFoundError: No module named 'pydantic'
   ```
   originada en `src/negative_domain_anchor_scoring.py` (componente incorporado en la fase P1-A de calibración OOD).
   - **Causa Raíz:** El archivo `requirements.txt` no declaraba explícitamente `pydantic`. En los entornos locales de desarrollo, `pydantic` se encontraba disponible por paquetes globales preexistentes, pero la imagen Docker de producción en OCI carece de dicha librería.
4. **Activación Inmediata del Protocolo de Rollback:**  
   Siguiendo rigurosamente la instrucción soberana de no improvisar parches no autorizados en caliente, se procedió de inmediato al rollback automático:
   - Retorno al commit estable `61afc1bc2c8fa273f118f4e10bc447dbafcfe650`.
   - Reinicio del contenedor Docker.
   - Validación funcional en vivo, verificando que el motor RRE/ADA responde con `Estado: SUCCESS` y recupera evidencias válidas.
   - Comprobación de salud HTTP pública: `https://sor.alxol.com` operando en `HTTP/2 200 OK`.

### 1.2 Dictamen Final de la Fase 3

$$\mathbf{DICTAMEN:\ ROLLBACK\ EJECUTADO\ —\ PRODUCCIÓN\ RESTAURADA}$$

La instancia de producción se encuentra 100% operativa, estable y segura bajo el commit `61afc1b`. Los datos de feedback de usuarios, corpus oficial y configuración permanecen íntegros e intactos. Se documenta la causa raíz y la solución técnica requerida para la posterior activación definitiva.

---

## 2. CRONOLOGÍA DETALLADA Y COMANDOS EJECUTADOS

| Hora (UTC) | Fase / Acción | Comando Ejecutado | Resultado Técnico |
| :---: | :--- | :--- | :--- |
| **06:32:14** | Pre-Check | `git rev-parse HEAD; ls -la /home/ubuntu/backups/...` | Confirmado commit `61afc1b` y backup íntegro. |
| **06:32:34** | Activación Release | `git checkout 3e86a0898a233a4357f11a29870780084d816f25` | `HEAD is now at 3e86a08...` (Éxito). |
| **06:32:36** | Reinicio Docker | `sudo docker compose restart streamlit` | Contenedor `ijf-sor-assistant` reiniciado (Éxito). |
| **06:32:48** | Healthcheck Web | `curl -I https://sor.alxol.com` | `HTTP/2 200 OK` (Cloudflare DYNAMIC). |
| **06:33:37** | Validación Funcional | `docker exec ijf-sor-assistant python -` (consulta RRE/ADA) | **FALLO:** `ModuleNotFoundError: No module named 'pydantic'`. |
| **06:34:10** | **ROLLBACK INMEDIATO** | `git checkout 61afc1bc2c8fa273f118f4e10bc447dbafcfe650` | `HEAD is now at 61afc1b...` (Éxito). |
| **06:34:12** | Reinicio Rollback | `sudo docker compose restart streamlit` | Contenedor reiniciado en versión previa (Éxito). |
| **06:34:34** | Verificación Web Post-Rollback | `curl -I https://sor.alxol.com` | `HTTP/2 200 OK` (Estable). |
| **06:35:43** | Prueba Funcional Post-Rollback | `docker exec ijf-sor-assistant python -` (consulta tatami) | **PASS:** `Estado: SUCCESS \| Evidencias RRE: ['SOR-2026-08-P096-S114', ...]`. |

---

## 3. ANÁLISIS DE LA ANOMALÍA Y CAUSA RAÍZ

### 3.1 Identificación del Error
Al invocar `engine.query()` en el release `3e86a08`, la traza de importación fue:
```text
File "/app/src/rag_engine.py", line 22, in <module>
    from ada_assistant import ArbitrationDecisionAssistant
File "/app/src/ada_assistant.py", line 22, in <module>
    from rre_engine import ReasoningRetrievalEngine
File "/app/src/rre_engine.py", line 28, in <module>
    from src.negative_domain_anchor_scoring import NegativeDomainAnchorScorer, NegativeDomainResult
File "/app/src/negative_domain_anchor_scoring.py", line 14, in <module>
    from pydantic import BaseModel, Field
ModuleNotFoundError: No module named 'pydantic'
```

### 3.2 Causa Raíz
1. El archivo `src/negative_domain_anchor_scoring.py` fue diseñado utilizando `pydantic.BaseModel` para estructurar los resultados de las anclas de dominio negativo.
2. Sin embargo, `pydantic` no fue incluido en el archivo `requirements.txt` del repositorio:
   ```text
   streamlit>=1.35.0
   python-dotenv>=1.0.1
   numpy>=1.26.0
   torch>=2.0.0
   sentence-transformers>=3.0.0
   pypdf>=4.0.0
   pytest>=8.0.0
   ```
3. En el entorno de desarrollo local (Windows), `pydantic` ya estaba instalado en el Python del sistema, por lo que las suites de prueba ejecutaron 306/306 PASS sin alertar la omisión de la dependencia.
4. En el contenedor Docker de OCI, la imagen base contiene únicamente las dependencias estrictas instaladas en el build inicial, careciendo de `pydantic`.

---

## 4. ESTADO DE INTEGRIDAD DE PRODUCCIÓN RESTAURADA

Tras la ejecución del rollback:
- **Commit HEAD en OCI:** `61afc1bc2c8fa273f118f4e10bc447dbafcfe650` (Idéntico al estado de partida).
- **Contenedor Docker:** `ijf-sor-assistant` activo y saludable (`Up 20+ seconds`).
- **Disponibilidad Pública:** `https://sor.alxol.com` responde `200 OK` (HTTP/2).
- **Datos de Feedback:** `/home/ubuntu/IJF-SOR-Assistant/data/feedback/user_observations.jsonl` (886 bytes) intacto.
- **Corpus Oficial SOR 2026-08:** Hashes SHA-256 verificados:
  - PDF: `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`
  - Embeddings: `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617`
  - Pasajes: `a6d4671ceba041105fc3d2ed45c6a864a95146b611eac6ad0dccf0597cb2a0f3`
- **Prueba Funcional:** Verificada con éxito (`Estado: SUCCESS`, recuperación de evidencias `SOR-2026-08-P096-S114` y pasajes normativos del tatami).

---

## 5. RECOMENDACIÓN TÉCNICA Y PLAN DE ACCIÓN PARA EL PRÓXIMO RELEASE

Para subsanar definitivamente este hallazgo y permitir el despliegue limpio de la versión canónica:

### Opción A (Recomendada — Máximo Apego a la Arquitectura Lean):
Eliminar la dependencia de `pydantic` en `src/negative_domain_anchor_scoring.py`, reemplazándola por `@dataclass` de la biblioteca estándar de Python (`dataclasses`), que es nativa, no requiere paquetes externos, no consume memoria adicional y ofrece exactamente la misma tipificación e inmutabilidad requerida:
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class NegativeDomainResult:
    is_negative: bool
    domain: Optional[str] = None
    confidence: float = 0.0
    matched_anchors: List[str] = field(default_factory=list)
```
*Ventaja:* Cero nuevas dependencias, compatibilidad 100% inmediata con cualquier imagen Docker y estricto apego al principio Lean.

### Opción B:
Agregar `pydantic>=2.0.0` a `requirements.txt` y reconstruir la imagen Docker en OCI (`sudo docker compose build streamlit`).

---
*Informe elaborado por Antigravity (Ejecutor Técnico Local) para Alexis Oliveros Lozano (Product Owner) y ChatGPT (Auditor Metodológico).*
