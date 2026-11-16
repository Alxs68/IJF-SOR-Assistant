# INFORME DE AUDITORÍA — FASE 4.2: VALIDACIÓN DOCKER REPRODUCIBLE
**Proyecto:** IJF SOR Assistant 2026  
**Product Owner y Autoridad Normativa:** Alexis Oliveros Lozano  
**Auditor Metodológico Independiente:** ChatGPT  
**Ejecutor Técnico:** Antigravity  
**Fecha:** 8 de noviembre de 2026  
**Commit Evaluado:** `bcdfe7d6d6960b388803fa5ceff1bcd82f141ef4` (`fix(deps): declare pydantic dependency for OCI runtime`)  
**Entorno de Validación:** OCI Ampere A1 (ARM64 `aarch64`, Ubuntu 24.04 LTS, Docker Engine 28.5.1)  

---

## 1. RESUMEN EJECUTIVO

En cumplimiento estricto del mandato de la **Fase 4.2**, se ejecutó la validación Docker reproducible e integral del commit correctivo `bcdfe7d`. La prueba se realizó directamente en la arquitectura de producción de OCI (ARM64), construyendo una imagen Docker temporal aislada a partir exclusivamente del `Dockerfile` y `requirements.txt` del commit `bcdfe7d`, sin utilizar la caché de la imagen anterior de producción ni tocar el contenedor activo de servicio (`ijf-sor-assistant`).

### Resultados Clave:
1. **Construcción e Instalación Limpia:** La dependencia `pydantic>=2.0.0` se resolvió e instaló de manera 100% reproducible: `pydantic==2.14.3` y `pydantic-core==2.50.4` (wheels binarios oficiales `manylinux2014_aarch64`).
2. **Eliminación Definitiva del Error:** Se ejecutaron pruebas focalizadas de `test_negative_domain_anchor_scoring.py` dentro del contenedor Docker ARM64: **25/25 PASS**.
3. **Suite Completa de Pruebas en Contenedor:** **270/270 PASS** en `pytest tests/ -q` dentro del contenedor Docker ARM64.
4. **Batería Soberana VF01 (11 Casos Ratificados por Alexis):** **11/11 PASS (100% OK)** ejecutados dentro del contenedor Docker ARM64.
5. **Auditoría Focal CGPT-06 (10 Casos Kumi-Kata):** **10/10 PASS (100% OK)** ejecutados dentro del contenedor Docker ARM64.
6. **Consultas Funcionales Canónicas y OOD:** 
   - Consulta canónica (Tatami): Estado `SUCCESS`, 8 evidencias recuperadas ($\ge 5$, cumpliendo $K=5$), Top evidencia: `SOR-2026-08-P096-S114`.
   - Consulta OOD (Baloncesto FIBA): Estado `ABSTAIN`, 0 evidencias recuperadas, abstención estricta garantizada.
7. **Integridad de Corpus y Embeddings:** Los hashes SHA-256 de PDF oficial, embeddings densos `.npy` y pasajes `.json` dentro de la imagen coinciden de forma exacta con la línea base certificada.
8. **Aislamiento y Producción Intacta:** El contenedor de producción (`ijf-sor-assistant`, commit `61afc1b`) se mantuvo en ejecución continua sin perturbación alguna (HTTP 200 en `https://sor.alxol.com`).
9. **Limpieza Completa:** La imagen temporal `test-val-arm64:bcdfe7d` y el directorio temporal `/home/ubuntu/tmp_docker_val` fueron eliminados de OCI tras la validación.

---

## 2. ESPECIFICACIÓN DEL ENTORNO DE VALIDACIÓN

| Parámetro | Detalle en OCI |
| :--- | :--- |
| **Host** | `149.130.187.132` (Oracle Cloud Infrastructure) |
| **Arquitectura** | ARM64 (`aarch64` Ampere Altra) |
| **Sistema Operativo Base** | Ubuntu 24.04 LTS (Kernel 6.8.0-1018-oracle) |
| **Docker Engine** | 28.5.1 |
| **Imagen Base** | `python:3.11-slim` (oficial ARM64) |
| **Imagen Temporal de Test** | `test-val-arm64:bcdfe7d` (ID: `f55906654cd0`) |
| **Volumen Caché HuggingFace** | `ijf-sor-assistant_hf_cache` montado en `/root/.cache/huggingface` |

---

## 3. CONSTRUCCIÓN DE LA IMAGEN DOCKER Y RESOLUCIÓN DE DEPENDENCIAS

La imagen temporal se construyó a partir del commit `bcdfe7d` con `requirements.txt` actualizado:

```text
pydantic>=2.0.0
```

### Evidencia de Instalación:
```text
Collecting pydantic>=2.0.0 (from -r requirements.txt (line 12))
  Downloading pydantic-2.14.3-py3-none-any.whl.metadata (103 kB)
Collecting pydantic_core==2.50.4 (from pydantic>=2.0.0->-r requirements.txt (line 12))
  Downloading pydantic_core-2.50.4-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl.metadata (6.7 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.0.0->-r requirements.txt (line 12))
  Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
...
Successfully installed annotated-types-0.7.0 pydantic-2.14.3 pydantic_core-2.50.4
```

### Inspección de Módulos Críticos en Contenedor:
```text
Pydantic version: 2.14.3
pydantic_core version: 2.50.4
NegativeDomainAnchorScoring loaded successfully!
```

---

## 4. RESULTADOS DE LAS PRUEBAS EN CONTENEDOR DOCKER ARM64

### 4.1 Pruebas Focales de Negative Domain Anchor Scoring
```bash
python -m pytest tests/test_negative_domain_anchor_scoring.py -v
```
**Resultado:** **25 passed in 0.94s (100% PASS)**

### 4.2 Suite Completa de Pruebas
```bash
python -m pytest tests/ -q
```
**Resultado:** **270 passed, 44 warnings in 28.52s (100% PASS)**

### 4.3 Batería Soberana VF01 (11 Casos Ratificados por Alexis)
Ejecutada con `scratch/test_regression_11_cases.py` dentro del contenedor:
- `VF01-01` (Medidas del tatami): `SOR-2026-08-P096-S114` **[PASS]**
- `VF01-07` (Acciones con cabeza Cadetes vs Senior): `SOR-2026-08-P188-S196`, `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-09` (Continuación tras head diving): `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-14` (Consecuencia técnica/disciplinaria cabeza): `SOR-2026-08-P166-S187`, `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-23` (Reverse seoi-nage en senior): `SOR-2026-08-P189-S196` **[PASS]**
- `VF01-24` (Shido por no combatividad y segundos): `SOR-2026-08-P177-S193` **[PASS]**
- `VF01-25` (Congelación reglas LA28 - OOD): Estado `ABSTAIN` **[PASS]**
- `VF01-29` (No combatividad tachi-waza vs ne-waza): `SOR-2026-08-P177-S193` **[PASS]**
- `VF01-30` (Contraataque involuntario con cabeza): `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-42` (Defending attack head-first - hansoku-make): `SOR-2026-08-P190-S197` **[PASS]**
- `VF01-48` (Kumikata, agarres no convencionales y sanciones): `SOR-2026-08-P182-S194`, `SOR-2026-08-P178-S194` **[PASS]**

**Dictamen VF01:** `TODOS LOS 11 CASOS RATIFICADOS PASARON LA REGRESIÓN EXITOSAMENTE (100% OK)`

### 4.4 Auditoría Focal CGPT-06 (10 Casos Kumi-Kata)
Ejecutada con `scratch/test_focal_cgpt06_queries.py` dentro del contenedor:
- `1. Cross grip con preparación positiva`: `SOR-2026-08-P178-S194` **[PASS]**
- `2. Pocket/pistol grip con progresión`: `SOR-2026-08-P178-S194`, `SOR-2026-08-P182-S194` **[PASS]**
- `3. Inside jacket sleeve en tachi-waza`: `SOR-2026-08-P180-S194` **[PASS]**
- `4. Agarre bajo cinturón hasta muslo interno`: `SOR-2026-08-P179-S194` **[PASS]**
- `5. Agarre por debajo del límite (leg grabbing)`: `SOR-2026-08-P180-S194` **[PASS]**
- `6. Ruptura con dos manos conservando agarre`: `SOR-2026-08-P180-S194` **[PASS]**
- `7. Ruptura con dos manos liberando completamente`: `SOR-2026-08-P180-S194` **[PASS]**
- `8. Agarre por dentro del pantalón`: `SOR-2026-08-P180-S194` **[PASS]**
- `9. Dedos entrelazados (interlocking fingers)`: `SOR-2026-08-P180-S194` **[PASS]**
- `10. Bloqueo defensivo rígido`: `SOR-2026-08-P178-S194` **[PASS]**

**Dictamen CGPT-06:** `10/10 CASOS RECUPERADOS CON PRECISIÓN NORMATIVA (100% PASS)`

---

## 5. VALIDACIÓN FUNCIONAL, $K=5$ CANÓNICO Y ABSTENCIÓN OOD

Se ejecutó un script Python de validación directa instanciando `RagEngine(".")` dentro del contenedor Docker:

```python
# Consulta Canónica Tatami
res = engine.query("¿Cuáles son las medidas oficiales del área de combate del tatami?", language="es")
# Estado: SUCCESS | Evidencias RRE: 8 pasajes (>= 5 requeridos por K=5 canónico)
# Top Evidencia: SOR-2026-08-P096-S114

# Consulta Fuera de Dominio (OOD)
res_ood = engine.query("¿Cuál es el tiempo de posesión en baloncesto FIBA?", language="es")
# Estado: ABSTAIN | Evidencias RRE: 0 (Abstención certificada)
```
**Resultado:** Ambos contratos funcionales ratificados al 100%.

---

## 6. INTEGRIDAD CRIPTOGRÁFICA DE CORPUS Y EMBEDDINGS

Verificación mediante `sha256sum` dentro de la imagen de contenedor:

| Archivo | SHA-256 en Contenedor | Hash Canónico Esperado | Estado |
| :--- | :--- | :--- | :--- |
| `data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | `9426b10d...` | **IDÉNTICO** |
| `data/processed/rebuild_2026_08_corrected/dense_embeddings_candidate.npy` | `124ced95fb9e152ce586dec9f30a1eb98dc14ee385c0bc335a2055357f73a617` | `124ced95...` | **IDÉNTICO** |
| `data/processed/rebuild_2026_08_corrected/passages_candidate.json` | `7d4634288997404278e26a5885e5eeedfa707742072b9fa4178e3f56ccc1167b` | `7d463428...` | **IDÉNTICO** |

---

## 7. AISLAMIENTO DE PRODUCCIÓN Y LIMPIEZA

1. **Estado del Contenedor de Producción:**
   - Contenedor: `ijf-sor-assistant` (en commit `61afc1b`).
   - Estado: `Up 33 minutes` (sin reinicios ni afectación durante toda la prueba).
   - Servicio Web: `https://sor.alxol.com` respondiendo `HTTP 200 OK`.
2. **Limpieza de Recursos Temporales en OCI:**
   - Imagen temporal `test-val-arm64:bcdfe7d` eliminada (`Deleted: sha256:f55906654cd0...`).
   - Directorio `/home/ubuntu/tmp_docker_val` purgado completamente.
   - Archivo bundle `/home/ubuntu/docker_val_bundle.tar.gz` eliminado.

---

## 8. CONCLUSIÓN Y DICTAMEN

El commit `bcdfe7d6d6960b388803fa5ceff1bcd82f141ef4` ha demostrado ser **100% reproducible y operativo en el entorno real de OCI ARM64**. La inclusión de `pydantic>=2.0.0` en `requirements.txt` resuelve total y limpiamente el incidente previo sin introducir efectos secundarios, conservando intacta la paridad algorítmica, los hashes normativos, la configuración canónica ($K=5$) y la inmunidad OOD.

```
FASE 4.2 COMPLETADA — DOCKER REPRODUCIBLE VALIDADO
```
