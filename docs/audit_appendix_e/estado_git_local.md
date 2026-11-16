# Estado de Git y Entorno Local — Auditoría Apéndice E

**Fecha y hora:** 2026-10-17 17:00:00 (America/Bogota / UTC-5)  
**Ruta absoluta del repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`  
**Rama activa comprobada:** `review/ijf-sor-2026-08-rre-ada`  

---

## 1. Identidad e Integridad de Referencias Git

### 1.1 Identificadores Criptográficos (SHA)
- **HEAD Local:** `6a4b08de0a9821f4ff83291f111bfdbf78edfa6c`
- **Remoto `origin/review/ijf-sor-2026-08-rre-ada`:** `626a42f53eff6c2522efe297ccfbf9754debb1a2`
- **Rama Base `origin/main`:** `afb5b1108cea21efddf29f302bea36bd03da03df`
- **Rama Local `main`:** `afb5b1108cea21efddf29f302bea36bd03da03df`

### 1.2 Registro de Estado (`git status --short --branch`)
```text
## review/ijf-sor-2026-08-rre-ada...origin/review/ijf-sor-2026-08-rre-ada [behind 11]
?? .github/workflows/
?? data/processed/rebuild_2026_08/pages_raw/
?? data/raw/sor_2026_08_rebuild/IJF_Sport_and_Organisation_Rules_2026_08_14.pdf
?? docs/audit_appendix_e/
?? scratch/
```

### 1.3 `git log -5 --oneline --decorate`
```text
6a4b08d (HEAD -> review/ijf-sor-2026-08-rre-ada) ci(validation): add github actions workflow, strict allow_degraded control, and complete test suite
23c24f5 fix(rre-ada): enforce mathematical dense matrix validation and explicit hybrid operating mode
fdadbc4 fix(reproducibility): declare direct dependencies, track dense matrix and clarify offline ADA evidence
fc2ec65 docs(rre-ada): update architecture implementation report with RRE and ADA specifications
7abb20b test(rre-ada): add unit and integration test suite for RRE and ADA architecture
```

### 1.4 Inspección de Diferencias Locales en Seguimiento
- `git diff`: Vacío (sin modificaciones no deseadas en archivos rastreados).
- `git diff --cached`: Vacío (sin archivos en stage pendientes).

---

## 2. Análisis de Divergencia con el Remoto de Referencia

El commit remoto de referencia indicado en la directiva es `626a42f53eff6c2522efe297ccfbf9754debb1a2`.

Tras ejecutar `git fetch origin`, se constata que `origin/review/ijf-sor-2026-08-rre-ada` se encuentra exactamente en dicho commit `626a42f`, mientras que el `HEAD` local se encuentra en `6a4b08d`.
La rama local está retrasada en 11 commits lineales respecto al remoto:
1. `a260598` — `fix(rre-ada): enforce offline startup and validate all hybrid resources`
2. `d725d31` — `ci(rre-ada): run corpus quality and lexical retrieval gates`
3. `0173154` — `fix(ada): validate citations and preserve RRE abstention metadata`
4. `2957fc7` — `test(rre-ada): verify text hashes and retrieval quality`
5. `5db77b7` — `fix(rre): prefer operative articles over version history matches`
6. `22c333f` — `fix(rre): apply primary-article ranking regex correctly`
7. `fa3472f` — `fix(rag): align retrieved IDs and evidence records`
8. `4e17f84` — `fix(rag): log retrieved evidence after adapting result contract`
9. `09e8ea0` — `test(rre): accept continuation page for Article 18.1.4`
10. `770d90f` — `fix(rre): rank by relevance without global article boost`
11. `626a42f` — `ci(rre-ada): verify source PDF bytes against official SHA-256`

### Archivos Afectados por la Divergencia Remota
```text
M	.github/workflows/rre-ada-validation.yml
M	app.py
M	data/processed/rebuild_2026_08/test_normative_retrieval.py
M	data/processed/rebuild_2026_08/test_quality_gates.py
M	scripts/setup_model.py
A	scripts/verify_source_pdf.py
M	src/ada_assistant.py
M	src/rag_engine.py
M	src/rre_engine.py
M	tests/test_rebuild_integration.py
M	tests/test_rre_ada_architecture.py
```

### Determinación Técnica y Preservación
En estricto cumplimiento de la restricción de Fase A (*"Si hay divergencia, identifica los commits y archivos afectados sin intentar resolverla automáticamente"* y *"No cambies de rama ni hagas reset, checkout destructivo, limpieza forzada o sobrescritura de archivos"*), no se aplicó ningún `git reset`, `git merge` ni `git pull` automático.
Todos los artefactos no rastreados (`data/raw/...`, `data/processed/...`, `scratch/`) y la integridad del árbol local se preservan intactos.
