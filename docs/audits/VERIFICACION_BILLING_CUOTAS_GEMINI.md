# Verificación de facturación, cuotas y disponibilidad de Gemini

Fecha: 2026-11-16 · Intervención **exclusivamente diagnóstica**.
* Sin leer ni modificar `.env`, sin cambiar claves, proveedores, modelos ni el respaldo.
* Sin llamadas a ningún proveedor, sin evaluaciones, sin despliegues y sin commit.
* Las claves solo se identifican por sus 4 últimos caracteres.

**Fuentes de este informe:**
* el código (`src/llm_provider.py`, `app.py`, `scripts/check_llm_quota.py`, `deploy/`);
* los registros de las 8 corridas (`api_errors` y `provider_status` de cada ejecución);
* las salidas que el responsable ejecutó y pegó en esta sesión (comprobación de cuota, variables de Windows y contenedores de OCI);
* la documentación oficial de Google, consultada hoy.

## 1. Configuración local (Windows)

| Elemento | Estado comprobado | Fuente |
|---|---|---|
| Clave de Gemini en `.env` del proyecto | Termina en **`ro_g`**, 53 caracteres, formato `AQ.` (clave de autenticación nueva de AI Studio) | Comprobación del responsable (2026-11-16 21:05) |
| Variable de Windows `GEMINI_API_KEY` a nivel de usuario | Contenía la clave **antigua `PYoA`**; el responsable la **eliminó**. El proceso de PowerShell de entonces también la tenía | Comprobación del responsable (21:09) |
| Cómo se carga la clave | La aplicación (`app.py`) usa `load_dotenv()` sin `override`: **una variable de Windows tiene prioridad sobre el `.env`**. Los scripts (`check_llm_quota.py`, `eval_ab_dev.py`) **no leen el `.env`**: usan el entorno del proceso | Código |
| Proveedor principal | `LLM_PROVIDER`, o Gemini por defecto. En la interfaz se puede cambiar por sesión (en una captura anterior aparecía Groq como principal) | Código; `check_llm_quota` muestra «proveedor_principal: Gemini» |
| Modelo configurado | `gemini-flash-lite-latest` (`GEMINI_MODEL` en el entorno; es también el valor por defecto) | `check_llm_quota`; `provider_status` de las 8 corridas |
| **Modelo efectivo** | **`gemini-3.5-flash-lite`** (el alias resuelve a esta versión) | `check_llm_quota` («version_que_responde») y los mensajes 429 de Google |
| Clave de Groq | Termina en `D2T`. Disponible en el entorno de los scripts. El modelo del entorno (`llama-3.3-70b-versatile`) no está admitido y se usa `openai/gpt-oss-120b` | `provider_status`; `check_llm_quota` |
| Disponibilidad actual | Gemini `ok: true`, HTTP 200, con la clave nueva en la sesión | `check_llm_quota` (21:11) |

## 2. Configuración OCI

* **Cómo se configura:** producción (`ijf-sor-assistant`, puerto 8501) y la instancia experimental (`ijf-sor-assistant-exp`, 127.0.0.1:8510) son **contenedores Docker**. Leen sus variables con `env_file: .env` (`docker-compose.yml`; `docker-compose.exp.yml`, proyecto `ijf-exp`). **No hay servicio systemd** para la aplicación: el comentario de `src/rag_engine.py` que habla de systemd está desactualizado.
* **Clave en los contenedores:** el 2026-11-17 a las 02:13 UTC se actualizaron los dos `.env`, se recrearon ambos contenedores y se comprobó dentro de ellos que la clave termina en **`ro_g`**. Los dos respondían HTTP 200.
* **No verificado:** el valor de `LLM_PROVIDER` y `GEMINI_MODEL` en los `.env` del servidor.
* **Proceso del puerto 8502 (identificado el 2026-11-16):** es el frontend de **NuevaMente** (`/home/ubuntu/NuevaMente`, servicio systemd `nuevamente-frontend.service`, activo desde el 2026-11-13). **No pertenece al IJF SOR Assistant** y no tiene `GEMINI_API_KEY` en su entorno; según el responsable, es otro proyecto con **su propia clave gratuita**, independiente de la de este asistente. No requiere ninguna acción.

## 3. Proyecto de Google asociado

* **No es verificable desde la configuración local.** Ni la clave ni el código contienen el identificador del proyecto, y no se hicieron llamadas.
* **Cómo comprobarlo:** en **Google AI Studio → «API keys»** (`https://aistudio.google.com/apikey`) cada clave aparece junto a su proyecto. Busque la terminada en `ro_g`, anote el **nombre y el ID del proyecto** y compruebe que es el proyecto en el que registró la tarjeta.

## 4. Estado de facturación

* **No es verificable desde la configuración local.**
* **Registrar una tarjeta no equivale a estar en el plan de pago.** Según la documentación oficial, pasar del plan gratuito al de pago significa vincular una cuenta de facturación y prepagar un mínimo de 5 dólares (o su equivalente) en créditos. Además, los usuarios nuevos empiezan por defecto en el plan de prepago, y cuando el saldo prepago de la cuenta de facturación llega a 0, todas las claves de todos los proyectos vinculados dejan de funcionar a la vez.

Qué revisar:

| Qué | Dónde | Campo |
|---|---|---|
| Plan y nivel del proyecto | AI Studio → **Projects** | Columnas **«Billing Tier»** y **«Status»**. En la página Projects se ve el nivel y el plan de facturación del proyecto en la columna Billing Tier; «Set up billing» indica que **no** tiene facturación |
| Saldo prepago | AI Studio → **Billing** | Plan (Prepay o Postpay) y **saldo de créditos** (debe ser mayor que 0) |
| Límite de gasto efectivo de Gemini | AI Studio → **Spend** → «Monthly spend cap» | Según la documentación, los roles de editor, propietario o administrador del proyecto pueden fijarlo en la página Spend, en Monthly spend cap > Edit spend cap |
| Facturación vinculada | Google Cloud Console → **Billing → Account management** del proyecto | Cuenta de facturación activa |
| Presupuestos de Cloud | Cloud Console → **Billing → Budgets & alerts** | Un presupuesto de alertas **no limita el gasto**: no limita el uso; solo envía alertas según los costes. Solo un *spend cap budget*, o el límite de gasto de AI Studio, corta el servicio |

## 5. Estado del plan de pago

* **No comprobado.**
* **Los registros no lo demuestran:** la corrida con la clave nueva (`ro_g`, evaluación de respuesta única) hizo 82 generaciones sin ningún error. Eso es compatible tanto con el plan gratuito como con el de pago, porque no superó las 500 solicitudes diarias que se observaron como límite gratuito (§7).

## 6. Modelo efectivo

* **Gemini:** `gemini-flash-lite-latest` resuelve a **`gemini-3.5-flash-lite`**. Así aparece en las 149 respuestas 429 y en la comprobación de cuota.
* **Groq:** `openai/gpt-oss-120b`.
* **Mezcla de proveedores:** en las 8 corridas hubo 160 generaciones con Gemini y 38 con Groq.

## 7. Análisis de las 130 ejecuciones sin generación

> **Corrección al informe de trazabilidad:** atribuía estas 130 ejecuciones a «cuota del proveedor o abstención previa al LLM». Los registros muestran que **en las 130 se llamó al LLM** y **fallaron los dos proveedores**. Ninguna fue una abstención previa.

| Gemini | Groq | Ejecuciones |
|---|---|---|
| **HTTP 429**: cuota diaria del plan gratuito | HTTP 413: petición mayor que el límite de tokens por minuto | 62 |
| **HTTP 429**: cuota diaria del plan gratuito | HTTP 429: límite de tokens por minuto | 61 |
| HTTP 503: modelo sobrecargado | HTTP 429: límite de tokens por minuto | 4 |
| HTTP 503: modelo sobrecargado | HTTP 413 | 3 |
| **Total** | | **130** |

Sin casos de HTTP 403, de autenticación ni de tiempo de espera o conectividad.

* **Mensaje de los 429 de Gemini:** en las 149 respuestas 429 registradas (123 en estas 130 ejecuciones y 26 en ejecuciones que luego respondió Groq) el mensaje es el mismo: `Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 500, model: gemini-3.5-flash-lite … per day … on Free Tier`. **Son, sin excepción, la cuota diaria gratuita: 500 solicitudes al día.**
* **Clave de las corridas:** todas las corridas con estos errores (Fase 11, integración R3, A/B anterior) usaron la clave **antigua `…YoA`**. La corrida de respuesta única usó la nueva (`…o_g`) y no tuvo ningún error.
* **Corridas afectadas:**
  * F11 ×2 e integración R3 ×2: 123 fallos, todos por la cuota gratuita de Gemini.
  * A/B anterior: 7 fallos, todos por el error 503 de sobrecarga de Gemini.
* **Errores de Groq:** sí hay errores atribuibles a Groq, que impidieron que el respaldo compensara los fallos de Gemini. En sus 130 fallos:
  * 65 HTTP 413: el prompt de análisis, de unos 10 000 tokens, supera su límite de **8000 tokens por minuto**;
  * 65 HTTP 429 por ese mismo límite.

## 8. Límites efectivos conocidos

| Límite | Gemini (`gemini-3.5-flash-lite`) | Groq (`openai/gpt-oss-120b`) |
|---|---|---|
| Solicitudes por día | **500 en el plan gratuito** (observado en los errores, clave antigua). En el plan de pago: **no verificado** | 1000 (encabezado `x-ratelimit-limit-requests`) |
| Tokens por minuto | No publicado | **8000**: no admite un análisis completo de unos 10 000 tokens |
| Solicitudes por minuto | No publicado | No registrado |
| Concurrencia | No publicada | No registrada |
| Nivel 1 de pago | Requisito: configurar y vincular una cuenta de facturación activa; límite de facturación: 250 dólares; límite de gasto de 10 dólares por cada 10 minutos | — |
| Límites por modelo | Google no los publica: la página dice que los límites dependen del modelo y remite a AI Studio. Están en **AI Studio → Rate limit** (`aistudio.google.com/rate-limit`) | Consola de Groq → Settings → Limits |

**No se deben confundir límites publicados y cuota real.** La cuota real del proyecto solo se ve en **AI Studio → Rate limit**. Google advierte que los límites indicados no están garantizados y la capacidad real puede variar.

## 9. Estado del respaldo

* **Proveedores:** Gemini es el principal y Groq el secundario.
* **Política:** `fallback_policy = "automatic"` (valor por defecto; los scripts de evaluación no lo cambian y no hay variable de entorno para hacerlo).
* **Cuándo se activa:** con **cualquier error** de Gemini (429, 503, autenticación u otros), y también si falta la clave. Si Groq también falla, la consulta termina en abstención sin generación.
* **¿Es silencioso?**
  * **No del todo.** El cambio queda registrado (`successful_provider`, `fallback_triggered`) y la interfaz muestra «Cuota de … alcanzada. Respuesta generada automáticamente mediante …».
  * **En una evaluación sí puede mezclar proveedores sin detenerse:** el A/B anterior tuvo 12 generaciones de Groq después de errores 503 de Gemini, y Fase 11 e integración R3 tuvieron 26 después de errores 429.
* **Evaluación de respuesta única:** fue **íntegramente con Gemini** (82/82), sin activar el respaldo.
* **¿Puede una evaluación A/B ejecutarse solo con Gemini?**
  * **Hoy no se puede garantizar por configuración:** si Gemini falla, se usa Groq automáticamente.
  * **Opción sin tocar código ni `.env`**, para cuando se autorice: ejecutar la evaluación en una sesión de PowerShell sin `GROQ_API_KEY` (`Remove-Item Env:GROQ_API_KEY`). Así un fallo de Gemini termina en abstención registrada en lugar de pasar a Groq. El script ya se detiene tras 3 preguntas seguidas sin generación.
  * Con la verificación del §4 hecha y saldo prepago disponible, es viable.

## 10. Diagnóstico y acciones recomendadas

**Diagnóstico.**
* Las limitaciones históricas son **las del plan gratuito de la clave antigua**: 500 solicitudes diarias, más los 503 por alta demanda.
* El respaldo con Groq **no las compensaba**, por su límite de 8000 tokens por minuto.
* Con la clave nueva no ha habido errores, pero **no está demostrado que esté en un proyecto de pago**.

**Acciones**, en este orden y solo en AI Studio o Cloud Console, sin tocar el proyecto:
1. **AI Studio → API keys:** anotar el proyecto de la clave `ro_g`.
2. **AI Studio → Projects:** comprobar que **«Billing Tier»** dice *Tier 1* (o superior) y no «Set up billing».
3. **AI Studio → Billing:** comprobar el plan (Prepay o Postpay) y que el **saldo de créditos sea mayor que 0**. Si es Prepay sin saldo, hay que comprar créditos (mínimo 5 dólares).
4. **AI Studio → Spend:** revisar el **«Monthly spend cap»**, que es el límite efectivo. Un presupuesto de Cloud solo avisa.
5. **AI Studio → Rate limit:** anotar las solicitudes por minuto, los tokens por minuto y las **solicitudes por día de `gemini-3.5-flash-lite`** que muestra para el proyecto. Con un plan de pago, no deberían ser las 500 diarias del plan gratuito.
6. **En el servidor:** el proceso del puerto 8502 ya está identificado (NuevaMente, ajeno a este proyecto). Usa su propia clave gratuita; no requiere ninguna acción.

### Prueba controlada propuesta (no ejecutada; requiere autorización)

Una sola llamada a Gemini desde PowerShell, con la clave del `.env` cargada solo en la sesión y **sin Groq** para que no pueda intervenir el respaldo:

```powershell
cd C:\PROYECTOS\IJF-SOR-Assistant
$env:GEMINI_API_KEY = ((Get-Content .env | Where-Object { $_ -match '^\s*GEMINI_API_KEY\s*=' }) -split '=',2)[1].Trim()
Remove-Item Env:GROQ_API_KEY -ErrorAction SilentlyContinue
python -c "import sys,time,json;sys.path.insert(0,'src');from llm_provider import GeminiClient,LLMProviderError;c=GeminiClient();t=time.time()
try:
  txt=c.generate(prompt='Responde solo: OK');st=200
except LLMProviderError as e:
  txt=None;st=e.status_code;print('error:',e.error_type,str(e)[:300])
print(json.dumps({'proveedor':'Gemini','modelo_configurado':c.model,'http':st,'ms':round((time.time()-t)*1000),'tokens':getattr(c,'last_usage',None),'fin':getattr(c,'last_finish_reason',None),'generacion':bool(txt)},ensure_ascii=False))"
```

**Qué registra:**
* el modelo configurado y el proveedor (solo Gemini);
* el código HTTP y el tiempo de respuesta;
* los tokens de entrada y salida;
* el motivo de fin y si hubo generación.

**Coste:**
* El cliente **no devuelve el coste**. Se puede calcular con los tokens y la tarifa vigente del modelo, y comprobar en **AI Studio → Usage** unos minutos después.
* Una llamada de unos 10 tokens tiene un coste despreciable en el plan de pago. En el plan gratuito no cuesta nada y consume 1 de las 500 solicitudes diarias.

**Lo que la prueba no dice:** **no demuestra el plan de pago**. Una respuesta 200 se obtiene en ambos planes. Solo los pasos 2 a 5 lo confirman. Si saliera 429 con el texto `free_tier`, sería la prueba directa de que el proyecto sigue en el plan gratuito.

## Dictamen final

| Pregunta | Respuesta |
|---|---|
| ¿La aplicación usa la clave del proyecto facturado? | **Sí** (confirmado a las 23:59: `ro_g` es del proyecto IJF-SOR-ASSISTANT, en «Pagado 1»). **Usa la clave nueva (`ro_g`)** en el PC (`.env`, tras quitar la variable de Windows antigua) y en los dos contenedores de OCI. **No está verificado que esa clave pertenezca al proyecto facturado**: mírelo en AI Studio → API keys (paso 1). |
| ¿Google reconoce el proyecto como plan de pago? | **Sí** (actualización de las 23:56): IJF-SOR-ASSISTANT está en **«Pagado 1»**, con prepago y **COP 14.170** de saldo. La recarga automática está desactivada. |
| ¿Las cuotas históricas corresponden al plan gratuito? | **Sí.** Las 149 respuestas 429 de Gemini indican `generate_content_free_tier_requests, limit: 500 … per day … Free Tier`, todas con la clave antigua `…YoA`. Los otros 7 fallos de Gemini fueron 503 por alta demanda, que no dependen de la cuota. |
| ¿Hay errores atribuibles a Groq? | **Sí:** 130 (65 por petición demasiado grande y 65 por el límite de tokens por minuto). El prompt de análisis no cabe en sus 8000 tokens por minuto, así que el respaldo no podía compensar los fallos de Gemini. Además, 38 generaciones históricas se hicieron con Groq y mezclan proveedores en esas corridas. |
| ¿Se puede ejecutar una evaluación completa solo con Gemini? | **Sí, con condiciones:** que el proyecto esté en el plan de pago con saldo, o que el volumen no pase de 500 solicitudes diarias; y ejecutarla sin `GROQ_API_KEY` en la sesión para que el respaldo no intervenga. La evaluación de respuesta única ya fue 100 % Gemini. |
| ¿Qué falta verificar antes de nuevas pruebas? | 1. Proyecto de la clave `ro_g`. 2. Billing Tier del proyecto. 3. Plan y saldo prepago. 4. Monthly spend cap. 5. Límites reales en AI Studio → Rate limit. 6. (Resuelto: el puerto 8502 es NuevaMente, ajeno al asistente.) 7. Que la prueba controlada se ejecute sin Groq. |


## Actualización 2026-11-16 23:56 — captura de AI Studio → Facturación de la API de Gemini

Datos comprobados en la captura aportada por el responsable:

| Campo | Valor |
|---|---|
| Cuenta de facturación | «My Billing Account 1» |
| Nivel | **Pagado 1** (nivel 1 del plan de pago) |
| Límite mensual de la cuenta (nivel) | COP 790.867,50 |
| Proyectos vinculados | **1: IJF-SOR-ASSISTANT** |
| Plan | **Prepago** |
| Créditos comprados | COP 15.000, el 16 de noviembre |
| **Crédito disponible** | **COP 14.170** (gastados unos COP 830) |
| Recarga automática | **Desactivada** |
| Créditos de Google Cloud aptos | COP 0 |

**Conclusiones:**
* **El proyecto IJF-SOR-ASSISTANT está en el plan de pago (nivel 1) y tiene saldo prepago.** Esto responde a las preguntas 2 y 4 del §4.
* **Riesgo de saldo:** con la recarga automática desactivada, cuando el saldo llegue a 0 la API dejará de responder en todos los proyectos de la cuenta, producción incluida.
* **Coste estimado de una evaluación (inferencia, no verificada):** el gasto de unos COP 830 coincide en el tiempo con la evaluación de respuesta única (≈ 590 000 tokens) y las comprobaciones de cuota. Si fue así, cada evaluación completa de 82 generaciones costaría del orden de COP 800–1000, y el saldo actual alcanzaría para unas 15. Se puede confirmar en AI Studio → Usage.

**Pendiente:**
1. **AI Studio → API keys:** confirmar que la clave terminada en `ro_g` es del proyecto IJF-SOR-ASSISTANT. Es lo más probable, porque es el único proyecto de la cuenta, pero no está visto.
2. **AI Studio → Rate limit:** límites reales de `gemini-3.5-flash-lite` en el nivel 1.
3. **AI Studio → Spend:** límite de gasto propio del proyecto, si se definió uno.

## Prueba controlada (2026-11-16 23:58, autorizada; ejecutada por el responsable en su PC)

Una sola llamada REST directa a Gemini (sin Groq), con la clave leída del `.env` sin mostrarla.

| Campo | Resultado |
|---|---|
| Proveedor | Gemini (Groq no intervino) |
| Clave | termina en `ro_g` |
| Modelo configurado | `gemini-flash-lite-latest` |
| **Modelo efectivo** (`modelVersion`) | **`gemini-3.5-flash-lite`** |
| **HTTP** | **200** |
| Tiempo de respuesta | 992 ms |
| Tokens entrada / salida / total | 5 / 1 / 6 |
| Motivo de fin | STOP |
| Generación | OK («OK») |
| Coste | No lo devuelve la API; despreciable con 6 tokens; consultar AI Studio → Usage |

**Conclusión:** la clave nueva funciona y genera con el modelo esperado. Como se advirtió, un 200 no demuestra por sí mismo el plan de pago. Eso lo demuestra la captura de facturación: nivel «Pagado 1», prepago con saldo y el proyecto IJF-SOR-ASSISTANT como único proyecto de la cuenta. **Confirmado por el responsable (23:59):** la clave `ro_g` pertenece al proyecto IJF-SOR-ASSISTANT.

## Fuentes

* [Gemini API — Billing](https://ai.google.dev/gemini-api/docs/billing): plan de pago, prepago mínimo, página Projects (Billing Tier), Billing y Spend cap.
* [Gemini API — Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits): niveles, límites de gasto y página Rate limit de AI Studio.
* [Google Cloud — Protect your spending with budgets](https://cloud.google.com/blog/topics/developers-practitioners/protect-your-google-cloud-spending-budgets): los presupuestos solo avisan.

Diagnóstico terminado. No se implementó ninguna corrección. A la espera de instrucciones.
