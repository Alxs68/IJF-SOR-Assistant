# Release 2026-11-21: consulta por voz (`20f24e8`)

- **Producción:** `https://sor.alxol.com`.
- **Infraestructura:** Cloudflare Tunnel hacia el puerto 8501, con Docker Compose y el contenedor `ijf-sor-assistant`.

## Commit

- **Commit:** `20f24e85128202892cba3dab7d65a6c54e266c71`, hijo de `827c5db` (la versión anterior en producción). Commit hecho por el responsable.
- **Archivos (+420/−3):**

  | Archivo | Cambio |
  |---|---|
  | `src/voice_input.py` | Nuevo; solo importa `json` |
  | `app.py` | +9/−1: la importación y el control, fuera del formulario |
  | `src/i18n/__init__.py` | Textos ES/EN y una línea de ayuda sobre el dictado y la privacidad |
  | `tests/test_voice_input.py` | Nuevo, 9 pruebas |

- **Sin cambios:**
  - `requirements.txt`, `Dockerfile`, `docker-compose.yml` y la imagen (`290ab72e6a7f`);
  - RRE, ADA, recuperación, citas, verificación y respuestas;
  - el override, donde F3 sigue en modo shadow.

## Diseño

**Componente**
- Botón «🎤 Dictar» bajo el campo de consulta. Usa `components.html`, el mismo patrón que el acordeón de la barra lateral.
- Usa la Web Speech API del navegador: `SpeechRecognition` o `webkitSpeechRecognition`.
- Toma el constructor del documento principal. El iframe de Streamlit incluye `microphone` en su política `allow`.

**Flujo**
- La transcripción se añade al final del texto que ya hubiera en el campo de consulta. Se inserta con el *setter* nativo y un evento `input`.
- No se envía sola: el único envío sigue siendo el botón **Enviar** del formulario.
- **Por qué se inserta en el navegador:** el campo está dentro de un `st.form`, y lo que el usuario escribe no llega a Python hasta que envía. Insertando la transcripción en el navegador, se conserva lo ya escrito.

**Idioma**
- Sale del selector de la barra lateral: `es` → `es-CO`, `en` → `en-US`.
- Al cambiar el idioma o el tema, el iframe se recrea, el reconocimiento activo se aborta y aparece un aviso.
- La transcripción no se traduce.

**Estados de la interfaz**
- Inactivo, solicitando permiso, escuchando (con texto provisional), procesando, transcripción disponible y error.
- El aviso de transcripción disponible vuelve a inactivo cuando el campo se vacía (al enviar o al borrar).

**Errores y degradación**
- Permiso denegado, sin micrófono, red, sin voz, navegador incompatible y conexión no segura.
- Si no hay soporte, el botón se desactiva y la consulta escrita sigue igual.

**Móvil**
- En Android se dicta una frase por pulsación (`continuous=false`), porque el modo continuo duplica resultados.
- No se fuerza el foco en el campo, para que no salte el teclado.

**Privacidad**
- La aplicación no graba, no guarda ni envía audio.
- El reconocimiento lo hace el navegador. En Chrome, la voz se procesa en los servidores de Google. Así lo indica la ayuda «Cómo consultar».

## Validación previa

- **Suite completa sin el conjunto sellado:** 853 pasan, 21 omitidas (por entorno) y 2 deseleccionadas, en 129 s. Corrió sobre un contenido idéntico al del commit.
- **Pruebas específicas:** 88 pasan.
- **Hashes protegidos:** 17/17.
- **Pruebas funcionales locales** (Chromium, con un reconocimiento simulado):
  - escribir y luego dictar; dictado con el campo vacío;
  - consulta larga con terminología de judo;
  - edición, sin envío automático y con envío manual;
  - errores de permiso, sin micrófono, red, sin voz y `service-not-allowed`;
  - navegador incompatible;
  - cambio ES↔EN con el dictado activo;
  - temas claro y oscuro, y móvil a 375 px.

## Respaldo (OCI)

- **Directorio:** `/home/ubuntu/backups_ijf/prod_827c5db_pre_voz_20261121_054451/`. Copia idéntica, de 690 MB, que incluye `.git`, el override y `.env` (no leído).
- **Archivos asociados:** `…_054451.ESTADO.txt` y `…_054451.compose_resuelto.yml` (permisos 600).
- **Imagen Docker:** `ijf-sor-assistant-streamlit:backup-827c5db`.
- **Tag Git:** `backup/prod-827c5db`.

## Despliegue

- `main` local avanzó por fast-forward a `20f24e8`.
- El bundle `deploy_20f24e8.bundle` (rango `827c5db..main`) se aplicó con `git merge --ff-only` en el servidor, seguido de `docker compose restart streamlit`.

## Reversión

```bash
cd /home/ubuntu/IJF-SOR-Assistant
git reset --hard backup/prod-827c5db
docker compose restart streamlit
```

**Reversión total:** restaurar el directorio de respaldo indicado arriba.

## Verificación en producción (2026-11-21 UTC)

**Infraestructura**
- Health 200 al segundo intento.
- `https://sor.alxol.com` responde 200, con certificado de Google Trust Services válido hasta el 07-01-2027 (comprobado desde OCI).
- 0 reinicios y logs sin errores.
- 8502 y 8510 responden 200, y `cloudflared` está activo.

**Dentro del contenedor (Streamlit 1.67)**
- Pruebas de voz, barra lateral, citas e i18n: 83 pasan.
- F3: `ADA_REFERENCE_CHECK=shadow`.

**Web pública**
- **Control:** visible e inactivo, con HTTPS (contexto seguro). La API nativa está disponible, el iframe tiene `allow` con `microphone` y el idioma es `es-CO`.
- **API real, sin simulación:** el panel de pruebas no tiene micrófono y su permiso está denegado. La secuencia fue «Solicitando acceso…» → «Permiso de micrófono denegado…», sin errores.
- **Dictado simulado:** inactivo → solicitando permiso → escuchando (texto provisional) → procesando → disponible. Después:
  1. se editó el texto añadiendo « en un combate?»;
  2. tras 3 s no se había enviado nada;
  3. se envió con **Enviar**.

  Respuesta real de Gemini: tres shidos, Art. 18.1, Pág. 176, con enlaces `#page=176/190/194`, sin `javascript:`. El campo se vacía y el control vuelve a inactivo.
- **Consulta escrita (regresión):** tolerancia del pesaje aleatorio → 5 %, Art. 6.3, Pág. 79. Correcta.
- **Idioma:**
  - ES→EN con el dictado activo: se aborta, aparece el aviso y el siguiente dictado usa `en-US`; la ayuda en inglés menciona «🎤 Dictate»;
  - EN→ES: el siguiente dictado usa `es-CO`.
- **Móvil (375 px):** aviso de «sin micrófono» en dos líneas, sin scroll horizontal.

**No verificado:** el reconocimiento con un micrófono físico (sin hardware en este entorno). Queda como comprobación manual en Chrome de escritorio y en Chrome de Android:
1. dictar en español y en inglés;
2. revisar el texto;
3. pulsar **Enviar**.
