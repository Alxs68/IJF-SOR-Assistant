# Traspaso a Claude Code — 17 de noviembre de 2026

**Proyecto:** IJF SOR Assistant 2026
**Responsable:** Alexis Oliveros Lozano (responde en español sencillo)

**Lee este documento entero antes de ejecutar nada.** La sesión anterior se hizo en el chat de Claude. Su historial completo no está disponible aquí, pero sí sus informes en `docs/audits/`.

---

## 1. Restricciones permanentes (no negociables)

1. **Secretos:**
   * nunca leer, mostrar ni registrar los valores de `.env`, `.env.*` ni las claves SSH (`*.key`);
   * de una clave, como mucho, sus **4 últimos caracteres**;
   * el usuario no pegará claves en la conversación.
2. **Producción** (`ijf-sor-assistant`, puerto 8501, `https://sor.alxol.com`) y el **DNS:** no se tocan.
3. **Git:** sin commit, push ni stash, salvo autorización expresa.
4. **Datos protegidos:** no modificar el corpus SOR, SHADOW, los benchmarks ni `test_sealed`; **no abrir** `data/eval/benchmark_v2/splits/test_sealed.jsonl`.
5. **DIG:** no cambiar DIG‑05 ni DIG‑09. Sin reglas o valores escritos a mano para una pregunta o un artículo concretos. No relajar el DIG para ganar cobertura.
6. **Interruptores:** las funciones FIX3 siguen bajo sus interruptores experimentales, desactivados por defecto. Nada se activa de forma global.
7. **Proveedores:**
   * no llamar a Gemini ni a Groq sin autorización de esa ejecución concreta;
   * las evaluaciones, **solo con Gemini**;
   * un 503 se registra como fallo del proveedor, sin pasar a Groq.
8. **Conexiones al servidor:** cualquier `ssh` o `scp` a OCI (`ubuntu@149.130.187.132`) necesita aprobación previa del usuario.
9. **Al terminar cada tarea:** entregar los resultados y **esperar autorización** antes del siguiente paso.
10. **Saldo:** el usuario paga la clave de Gemini (prepago). No hace falta volver a plantear el riesgo de saldo.

---

## 2. Estado actual

* **Repositorio:** `C:\PROYECTOS\IJF-SOR-Assistant`, rama `exp/r3-dig-v2`, HEAD `d126873`. Los cambios de FIX3 están **sin commit**.
* **FIX3** (todo desactivado por defecto):
  * `ADA_UNIFIED_ANSWER`, respuesta única y validada;
  * `RRE_CHANNEL_CHAMPIONS` (R1);
  * `ADA_TRANSLATE_ANY_LANG` (R2);
  * `DIG_11_SUBORDINATE` (R5a);
  * `DIG06_REFS` (R5b).
* **Empaquetado sin commit:**
  * `deploy/exp/build_package_exp.py` arma el paquete con el commit base más los archivos FIX3 autorizados, y genera un manifiesto;
  * `deploy/exp/deploy_fix3_exp.ps1` ya no hace commit y se detiene si pytest devuelve un código distinto de 0.
* **Rotación de claves:** `deploy/exp/rotar_claves_servidor.sh` es transaccional, con respaldos `.env.bak_rot`. **La ejecuta el usuario a mano en PowerShell**, no Claude Code.
* **Servidor:**
  * producción en la carpeta `/home/ubuntu/IJF-SOR-Assistant`;
  * experimental en `ijf-sor-assistant-exp`, `127.0.0.1:8510`, proyecto Docker `ijf-exp`, carpeta `/home/ubuntu/IJF-SOR-Assistant-exp/current`, que apunta a `releases/d126873`;
  * el puerto 8502 es de **NuevaMente**, otro proyecto: no tocarlo.
* **Pruebas locales:**
  * `tests/test_build_package_exp.py` (16), `tests/test_rotar_claves_servidor.py` (9), `tests/test_install_exp_rollback.py` (10) y `tests/test_aislamiento_proveedores.py` (6): todas pasan;
  * `tests/ps/test_deploy_ps1_aborta.ps1`: 5 de 5 en Windows.

---

## 3. Resultados recientes (leer los informes)

* **`docs/audits/AUDITORIA_INTEGRAL_PROCESAMIENTO_DOCUMENTAL_2026.md`:**
  * la extracción del PDF está bien: 99,6 % de las palabras frente a `pdftotext`;
  * los problemas están en el ordenamiento: la fusión RRF (H‑04), las reglas fijas como la de cadetes y la p. 188 (H‑05), y el truncamiento del canal denso (H‑03);
  * en el corpus, la unidad es la página y no el apartado (H‑02), y falta la página 9 (H‑01, crítico).
* **`docs/audits/RESULTADOS_T1_T2_EMBEDDINGS_RRE_2026.md`:**
  * **T1:** truncamiento **confirmado**. `all-MiniLM-L6-v2` corta en 256 tokens; 294 de 385 pasajes (76,4 %) lo superan y queda fuera el 49,8 % de los tokens. Los 9 fallos del canal denso tienen la regla fuera de la ventana; dentro, el canal encuentra 17 de 17.
  * **T2:** R1 sube R@5 de 0,774 a 0,871 (LLM) y a 0,806 (DICT), sin pérdidas. Recupera SCO‑019 (LLM), SCO‑020 (las dos formas) y SCO‑022 (LLM).
* **Informes anteriores:**
  * `AUDITORIA_TRAZABILIDAD_RRE_GEMINI_DIG.md`;
  * `INFORME_INTERVENCION_RECUPERACION_GENERACION_DIG11.md`;
  * `VERIFICACION_BILLING_CUOTAS_GEMINI.md`;
  * `FASE_11_RECUPERACION_EXPERIMENTAL.md`.

---

## 4. Pendiente, en orden (cada paso con autorización propia)

1. **Fase 1, rotación de claves de Gemini y Groq:** la hace el usuario en PowerShell.
   * El primer intento se detuvo bien, porque el `.env` local todavía tenía las claves antiguas, terminadas en `ro_g` y `WD2T`.
   * Comprobación previa: bloques A1 y A2.
   * Rotación: bloque B, con `rotar_claves_servidor.sh`.
   * Búsqueda de claves antiguas: bloque C.
   * Facturación: bloque D, solo mirar la pantalla.
   * **No ejecutar `check_llm_quota`** en esta fase.
2. **Fase 4, despliegue experimental FIX3:** `powershell -ExecutionPolicy Bypass -File deploy\exp\deploy_fix3_exp.ps1`. Pide SI antes de subir; producción no se toca.
3. **Fase 5, verificación posterior** (solo lectura):
   * salud de 8501 y 8510;
   * interruptores activos solo en la experimental;
   * Gemini como proveedor;
   * reversión disponible.
4. **Primera corrida A/B solo con Gemini:** `scripts/run_eval_fix3.ps1 -Corrida 1`. **Autorización aparte.**
   * Incluye R1.
   * Falta medir su efecto en las preguntas no respondibles y en las respuestas validadas por el DIG.
5. **Experimento contra el truncamiento** (diseño, no implementado):
   * codificar cada página en ventanas de hasta 256 tokens dentro del mismo pasaje y tomar la mayor similitud;
   * en una caché experimental, con el mismo modelo, los mismos pasajes y la misma fusión;
   * medir el recall del canal denso y R@5 en SCO‑013, SCO‑014, EXC‑003, MLG‑002, SCO‑021, SCO‑022, DIR‑017, EXC‑009 y MUL‑004.
6. **Otras recomendaciones de la auditoría integral**, todas pendientes de decisión:
   * incorporar la p. 9;
   * ablación de la regla de cadetes;
   * continuidad de los apartados entre páginas;
   * versionar los scripts de construcción;
   * unificar el tokenizador léxico.

---

## 5. Herramientas útiles ya creadas

* `deploy/exp/out/t1t2_diag.py`: diagnóstico de T1 y T2, de solo lectura y sin red. Su resultado está en `deploy/exp/out/t1t2_result.json`.
* `scripts/eval_r1_channel_champions.py`: evaluación de R1 sin LLM.
* `scripts/eval_ab_dev.py --set fix3 --gemini-only`: corrida A/B solo con Gemini.
* La carpeta `deploy/exp/out/` queda fuera del paquete de despliegue y contiene archivos auxiliares de la sesión anterior que pueden borrarse.

---

## 6. Forma de trabajar con el usuario

* Explicar en español sencillo qué hace cada comando y qué significa su salida.
* Antes de cualquier acción remota, de escritura o con coste, decir qué se va a hacer y esperar su confirmación.
* Entregar los informes en `docs/audits/` con datos verificables y separar los hechos confirmados de las hipótesis.
