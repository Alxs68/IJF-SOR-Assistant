# Auditoría de actualización y consistencia de la barra lateral

- **Fecha:** 2026-11-21.
- **Versión auditada:** producción `0f86677` (`https://sor.alxol.com`).
- **Método:**
  - inventario del código (`app.py`, bloque `with st.sidebar`, y textos de `src/i18n`, en español e inglés);
  - inspección de la web pública;
  - contraste con la implementación real: `ada_assistant`, `llm_provider`, `corpus_config`, `citation_resolver`, `answer_verification` y `answer_presentation`, más la configuración del contenedor de producción, de la que solo se consultó si existen las variables, sin leer valores.
- **Sin cambios de código.**

## 1. Inventario

| # | Elemento | Tipo | Origen en el código |
|---|---|---|---|
| A | «ℹ️ Información y Documentación del Proyecto» | Desplegable con 6 subtemas | `sidebar_docs_expander_title` |
| A1 | 1. Proyecto | Texto | `sidebar_project_content` |
| A2 | 2. Propósito | Texto y aviso de validez | `sidebar_purpose_content` |
| A3 | 3. Fuentes Oficiales | Texto | `sidebar_sources_content` |
| A4 | 4. Autor | Texto | `sidebar_author_content` |
| A5 | 5. Versión | Versión, edición y hash | `sidebar_version_label`, `engine.config` |
| A6 | 6. Guía de Usuario | Resumen y PDF descargable | `sidebar_guide_summary` y `docs/guides/IJF_SOR_Assistant_Guia_Usuario.pdf` |
| A7 | Guía Rápida de Referencia (dentro de A6) | 4 pasos | `sidebar_guide_quick_content` |
| B | Selector de idioma | Control | `lang_selector_label` |
| C | Selector de tema | Control | Texto fijo en `app.py` |
| D | «⚡ Cuotas de IA Gratuita y Continuidad» | Tarjeta informativa | `quota_info_title`, `quota_info_desc` |
| E | «7. Administración de Novedades» | Desplegable con acceso por clave | `sidebar_admin_title` y otras |

**Recursos externos:** solo el PDF de la guía, incrustado como enlace `data:`. La barra lateral no tiene enlaces a sitios externos.

## 2. Verificación y clasificación

| Elemento | Contenido actual (resumen) | Estado | Problema identificado | Recomendación |
|---|---|---|---|---|
| A, título del desplegable | «Información y Documentación del Proyecto» | INCOMPLETO | Mezcla la información del proyecto con la guía de uso, que queda en el 6.º subtema. Lo que más necesita el usuario, cómo usar el asistente, es lo menos visible | Separar en «Cómo usar el asistente» (primero) y «Acerca del asistente» |
| A1, Proyecto | Asistente sobre el SOR de la IJF con respuestas basadas exclusivamente en documentación oficial | ACTUALIZADO | Correcto. Se solapa en parte con A2 | Fusionar con A2 en un solo texto |
| A2, Propósito | Apoyo al estudio y consulta; ayuda documental; prevalecen los documentos oficiales de la IJF | CONSERVAR | El aviso de validez es correcto y necesario | Mantener el aviso y unir el resto con A1 |
| A3, Fuentes | «Exclusivamente fuentes oficiales… reglamentos, documentos técnicos, comunicados y otros recursos». En inglés: «SOR, refereeing guidelines, technical circulars, appendices» | INCORRECTO | **La respuesta y su verificación se basan solo en el SOR del 14-08-2026** (`corpus_config`: una única edición, 385 pasajes). Portal de reglas, vídeos, comunicados y códigos aparecen solo como **enlaces complementarios** (`citation_resolver`, 29 recursos, uno de ellos desactivado). El texto da a entender que responde con todas esas fuentes. Además, ES y EN no coinciden | Indicar que la base es el SOR 2026 y que los demás recursos son complementarios. Igualar ES y EN |
| A4, Autor | Nombre, árbitro nacional (Colombia), 2.º Dan, © 2026 | CONSERVAR | Es información que decide el responsable; no se ha verificado | Sin cambios, salvo que el responsable indique otra cosa |
| A5, Versión | «Versión **3.2.0 (Lean RRE 3.0 / Multi-Source)**» | DESACTUALIZADO | Se fijó el 2026-11-10 (`10f7013`). Desde entonces han entrado v1.4.0 (DIG, R1 y R2, 18-11), V4 (verificación frase a frase, 19-11), «evidencias utilizadas» (19-11), citas UI, D1, F1, F3 (`40d7ac9`) y texto literal (`0f86677`). Además conviven dos numeraciones (3.2.0 en la UI y `v1.4.0` en las release), y «Lean RRE 3.0 / Multi-Source» es nomenclatura interna | El responsable decide el número de versión. Mostrar versión y fecha de actualización, sin nombres de arquitectura |
| A5, Basado en | «14 August 2026 (Official)» | ACTUALIZADO | Correcto (`version_label`). La etiqueta está en inglés también en la interfaz en español | Mostrar «SOR IJF, edición del 14 de agosto de 2026» según el idioma |
| A5, Hash SHA-256 | `9426b10d11c21a4c…` | CONSERVAR | Correcto (`source_sha256`) y útil para comprobar el PDF | Mantener, con una etiqueta comprensible («Huella del PDF oficial») |
| A6, Guía de Usuario (resumen) | «Manual técnico integral… navegación, consultas, citas y trazabilidad, visor PDF…» | DESACTUALIZADO | Describe un PDF desactualizado (fila siguiente) y lo presenta como «manual técnico integral» | Ocultar el PDF hasta rehacerlo, o actualizarlo antes de seguir enlazándolo |
| A6, PDF de la guía | 3 páginas, generado el 2026-11-10 | DESACTUALIZADO e INCORRECTO | Describe elementos que ya no existen: «Selector opcional de ejemplos» en la barra lateral, «Configuración Multi-LLM… parámetros RAG» en la barra lateral y la estructura «Nivel 1 / Nivel 2». Dice «haga clic en el identificador normativo», cuando ahora se pulsan las píldoras 📍 y los enlaces 📄 Pág. No menciona la verificación frase a frase, la abstención como resultado normal, el historial ni el formulario de reportes. **Incluye criterios normativos escritos a mano** (cadetes, head diving, puente, protocolo médico) que no salen del sistema verificado. Solo hay versión en español | Retirarlo del enlace o rehacerlo según el §3. Si se rehace, sin dictámenes normativos propios: solo instrucciones de uso |
| A7, paso 1 (Idioma) | «Seleccione *Español* o *English* en la parte superior de la barra lateral» | INCORRECTO (menor) | El selector está debajo del desplegable de información, no en la parte superior | Subir el selector al primer lugar (propuesta) o corregir el texto |
| A7, paso 2 (Consulta) | «Escriba su consulta… o seleccione una de las sugerencias predefinidas» | INCORRECTO | **No hay sugerencias predefinidas**: el código conserva `prefill_query` y `auto_run_query`, pero ningún control las activa | Eliminar la mención de las sugerencias |
| A7, paso 3 (Citas y visor) | «Haga clic en las píldoras de cita para abrir el visor… en la página exacta» | ACTUALIZADO | Correcto y verificado en producción: la píldora abre el visor en la página certificada | Mantener y añadir los enlaces 📄 Pág. |
| A7, paso 4 (Cotejo) | Orientación técnica; ante controversias, contrastar con el SOR oficial | CONSERVAR | Correcto | Mantener |
| A7, lo que falta | — | INCOMPLETO | No explica cuándo y por qué el asistente se abstiene, aunque ocurre a menudo y es intencionado (en las pruebas de producción: judogi compuesto, premios). Tampoco explica las secciones de la respuesta, el «Historial de consultas» de la sesión ni «Ayúdanos a mejorar» | Añadir «Cómo leer la respuesta» y «Cuándo no responde» (§3) |
| B, selector de idioma | ES/EN; ayuda bilingüe | CONSERVAR | Funciona y cambia la interfaz | Moverlo al primer lugar |
| C, selector de tema | Automático / Claro / Oscuro | CONSERVAR | Funciona | Sin cambios |
| D, cuotas (texto principal) | «Modelos de IA en modalidad **gratuita**… Gemini 15/min y 1.500/día; Groq 30/min» | INCORRECTO | La clave de Gemini es **de pago (prepago)**, según el traspaso del proyecto (§1.10), así que «gratuita» y los límites del plan gratuito no se aplican. Las cifras no se pueden comprobar desde el código. Además, el modelo y los límites son detalle interno que no ayuda a consultar | Sustituir por una nota breve de disponibilidad, sin proveedores ni cuotas (§3) |
| D, «¿Qué ocurre si se alcanza el límite?» | «El asistente NO deja de funcionar: se activa el **Modo Alternativo Local**… garantizando respuestas oficiales continuas y verificables» | INCORRECTO | Comportamiento real (`llm_provider.generate_with_fallback` y `ada_assistant`): si falla Gemini se intenta Groq (hay clave configurada). Si no hay modelo disponible, el resultado es **«Abstención (modo local sin modelo generativo)»**: no hay respuesta. El generador determinista (`_build_deterministic_arbitration_brief`) existe, pero ninguna parte del código lo usa. Con V4, el verificador también es un modelo de Gemini, así que sin Gemini la respuesta tampoco se puede verificar | Eliminar la promesa de «respuestas continuas». Decir que, si el servicio de IA no está disponible, el asistente lo indica y no improvisa |
| E, Administración | «7. Administración de Novedades»; acceso por clave; métricas, CSV, filtro, adjuntos, reinicio de métricas | ACTUALIZADO en función; REDUNDANTE en numeración | Funciona (clave configurada en producción). Mostrar la consulta y el comentario como texto literal ya está corregido en `0f86677`. El «7.» sigue la numeración del desplegable A, pero es un bloque aparte. Para el público basta con saber que es de acceso restringido | Renombrar a «🔒 Administración (acceso restringido)», sin número, al final |

**Resumen:**

| Estado | Elementos |
|---|---|
| ACTUALIZADO | 4 (A1, A5 «Basado en», A7 paso 3, E en función) |
| CONSERVAR | 6 (A2, A4, hash, A7 paso 4, B, C) |
| DESACTUALIZADO | 3 (A5 versión, A6 resumen, PDF de la guía) |
| INCORRECTO | 5 (A3, A7 paso 2, cuotas, «Modo Alternativo Local», A7 paso 1, este último menor) |
| INCOMPLETO | 2 (A título, A7 lo que falta) |
| REDUNDANTE | 1 (numeración de E) |

Los dos errores con más impacto para el usuario son:
- **D, cuotas:** promete respuestas continuas sin IA, cuando el sistema se abstiene, y describe la IA como gratuita.
- **A3, fuentes:** da a entender que responde con comunicados y otros documentos, cuando la respuesta se apoya solo en el SOR.

## 3. Propuesta consolidada de la barra lateral

**Orden propuesto:**
1. Idioma.
2. Tema.
3. **Cómo usar el asistente**, desplegable y el primero que se lee.
4. **Acerca del asistente**, desplegable.
5. Nota de disponibilidad.
6. Administración (acceso restringido).

Los textos de abajo son la versión en español. El inglés debe tener el mismo contenido, porque hoy no coincide en A3.

### 3. Cómo usar el asistente

> **Cómo consultar**
> Escriba su pregunta en lenguaje natural, en español o en inglés, y pulse **Enviar**. Las preguntas concretas (una situación, una categoría o un artículo) obtienen respuestas más precisas. Si su duda tiene varias partes, hágalas por separado.
>
> **Cómo leer la respuesta**
> La respuesta se basa únicamente en el reglamento oficial SOR de la IJF y se comprueba frase a frase contra el texto oficial antes de mostrarse. Indica la respuesta, la regla aplicable y, cuando corresponde, las condiciones y excepciones. Pulse una cita **📍 Art. · Pág.** o un enlace **📄 Pág.** para abrir el PDF oficial en esa página.
>
> **Cuándo no responde**
> Si el reglamento no contiene información suficiente o la respuesta no puede comprobarse con el texto oficial, el asistente **se abstiene** y lo indica, en lugar de suponer. Los pasajes consultados quedan disponibles como referencia.
>
> **Historial y reportes**
> En **Historial de consultas** puede volver a las preguntas de esta sesión. Si detecta un error, use **Ayúdanos a mejorar**, bajo la respuesta.
>
> **Importante**
> El asistente es una ayuda de estudio y consulta. Ante una decisión arbitral o una controversia, prevalecen siempre el texto oficial del SOR y las decisiones de los órganos competentes de la IJF.

### 4. Acerca del asistente

> **Proyecto y propósito**
> IJF SOR Assistant facilita la consulta del *Sport and Organisation Rules* (SOR) de la Federación Internacional de Judo a árbitros, entrenadores, deportistas y demás miembros de la comunidad del judo, con respuestas fundamentadas en el texto oficial y enlazadas a su página.
>
> **Fuentes**
> Las respuestas se basan exclusivamente en el SOR de la IJF, edición oficial del 14 de agosto de 2026. Algunas respuestas incluyen enlaces complementarios a recursos oficiales de la IJF (portal de reglas, vídeos de arbitraje, comunicados). Son material de consulta y no sustituyen al SOR.
>
> **Versión**
> Reglamento: SOR IJF, edición del 14 de agosto de 2026
> Huella del PDF oficial (SHA-256): `9426b10d11c21a4c…`
> Aplicación: versión **[a definir por el responsable]**, actualizada el 21-11-2026
>
> **Autor**
> *(sin cambios)*
>
> **Guía de usuario (PDF)**
> *(Ocultar hasta rehacer el PDF con las instrucciones de «Cómo usar el asistente», sin criterios normativos propios. Mientras tanto, la sección 3 cubre lo esencial.)*

### 5. Disponibilidad

> **Disponibilidad del servicio**
> El asistente redacta y comprueba las respuestas con un servicio de IA. Si ese servicio no está disponible temporalmente, el asistente no genera respuestas sin comprobar: lo indicará y podrá intentarlo de nuevo más tarde.

### 6. Administración

> 🔒 **Administración (acceso restringido)**
> *(Funcionamiento sin cambios.)*

## 4. Decisiones pendientes del responsable

1. **Número de versión.** Hoy conviven 3.2.0 en la UI y v1.4.0 en las release. Hay que elegir uno y fijar su relación con las release de `docs/deployment/`.
2. **Guía en PDF:** ocultarla ya o rehacerla. Si se rehace, también en inglés o no.
3. **Nota de disponibilidad:** mantener la propuesta neutral (recomendado) o mencionar los proveedores.
4. **Cuándo aplicar los cambios.** Afectan a `src/i18n` (ES y EN) y al orden del bloque `with st.sidebar` en `app.py`, sin tocar RRE, ADA ni la verificación. Se pueden probar con AppTest y en el navegador, igual que el cambio `0f86677`.
