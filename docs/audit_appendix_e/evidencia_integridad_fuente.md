# Evidencia de Integridad y Autenticidad de la Fuente Oficial IJF SOR 2026-08

**Fecha de verificación:** 2026-10-17 17:05:00 UTC-5  
**Documento auditado:** *IJF Sport and Organisation Rules* (Reglamento Oficial de Deportes y Organización de la Federación Internacional de Judo).  
**Edición normativa:** 14 de agosto de 2026.  
**Ruta local auditada:** `C:\PROYECTOS\IJF-SOR-Assistant\data\raw\sor_2026_08_rebuild\IJF_Sport_and_Organisation_Rules_2026_08_14.pdf`  
**Manifiesto asociado:** `C:\PROYECTOS\IJF-SOR-Assistant\data\raw\sor_2026_08_rebuild\source_manifest.json`  

---

## 1. Parámetros Criptográficos y de Tamaño

| Parámetro | Valor Esperado (Oficial) | Valor Observado (Físico en Disco) | Estado |
| :--- | :--- | :--- | :--- |
| **Algoritmo de Hash** | SHA-256 | SHA-256 | Conforme |
| **Digest SHA-256** | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | `9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620` | **VERIFICADO (MATCH EXACTO)** |
| **Tamaño en Bytes** | `29.664.780` bytes | `29.664.780` bytes | **VERIFICADO (MATCH EXACTO)** |
| **Número de Páginas Físicas** | 298 páginas | 298 páginas | **VERIFICADO** |
| **URL Oficial Fijada** | `https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf` | Idéntica en manifiesto | **VERIFICADO** |

---

## 2. Procedimiento Técnico de Verificación

La verificación se ejecutó directamente sobre los bytes binarios brutos del archivo en disco (evitando cualquier decodificación de texto, lectura lógica u optimización de visor):

```python
import hashlib, os
from pathlib import Path

pdf_path = Path(r"C:\PROYECTOS\IJF-SOR-Assistant\data\raw\sor_2026_08_rebuild\IJF_Sport_and_Organisation_Rules_2026_08_14.pdf")
size_bytes = os.path.getsize(pdf_path)

h = hashlib.sha256()
with open(pdf_path, "rb") as f:
    while chunk := f.read(1024 * 1024):
        h.update(chunk)
digest = h.hexdigest().lower()

assert size_bytes == 29664780
assert digest == "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
```

**Resultado:**
- Salida del comando: `SIZE: 29664780`, `SHA256: 9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620`, `MATCH: True`.
- Verificación automática en el motor `ReasoningRetrievalEngine`: `self.source_sha256_verified = True`.

---

## 3. Identificación de la Edición

1. **Encabezado en páginas físicas 1 a 298:** *"Sport and Organisation Rules of the International Judo Federation"*.
2. **Pie de página impreso:** Indicadores de versión concordantes con la publicación oficial de agosto de 2026.
3. **Sección H1.1 (Páginas físicas 258–298):** Control de versiones que confirma la vigencia a partir del 14 de agosto de 2026 y la incorporación de las modificaciones aprobadas por el Comité Ejecutivo de la IJF.
