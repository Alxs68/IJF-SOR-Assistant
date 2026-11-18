# Despliegue experimental R3 + DIG v2 en OCI (sin tocar producción)

## Qué es
* **Instancia separada:** se llama `ijf-sor-assistant-exp` y escucha en `127.0.0.1:8510` del mismo servidor OCI. Producción (`ijf-sor-assistant`, `127.0.0.1:8501`, `https://sor.alxol.com`) no se toca: ni su contenedor, ni su directorio, ni su `.env`, ni Nginx, ni el DNS.
* **Mismo código, distintas opciones:** la imagen Docker de producción (no se construye nada ni se instalan dependencias) y el código del commit experimental, montado desde `/home/ubuntu/IJF-SOR-Assistant-exp/releases/<sha7>`.
* **Opciones activadas solo aquí:**
  * `RRE_ENABLE_SCOPE_PREFERENCE=1` y `RRE_SCOPE_BETA=0.2` (R3);
  * `DIG_NUMBER_NORMALIZATION=v2` (variante DIG);
  * `IJF_DEPLOY_LABEL` (aviso visible de instancia experimental).

  Sin estas variables, el mismo código se comporta como el original.
* **Límite de memoria:** 2,5 GB. La instalación aborta si hay menos de 1,8 GB libres.

## Pasos

1. **En el PC (Windows), crear la rama y el commit local** (sin push):
   ```powershell
   git switch -c exp/r3-dig-v2
   git add -A -- . ":!scratch" ":!data/eval/fase11/cache"
   git commit -m "exp: integrar R3 (preferencia por ambito) y DIG v2 (normalizacion de cifras) desactivados por defecto"
   ```
2. **Crear el paquete del commit exacto:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File deploy\exp\make_bundle_exp.ps1
   ```
3. **Subirlo a OCI** con la misma clave y la misma IP que en los despliegues anteriores. El comando exacto lo imprime el paso 2.
4. **En el servidor:**
   ```bash
   bash ~/server_install_exp.sh ~/ijf_exp_<sha7>.tar.gz
   ```
   El script comprueba primero la RAM, el disco, el estado y el commit de producción, y lo registra en `install_*.log`.
5. **Abrir desde el navegador del PC:**
   ```powershell
   ssh -i <clave> -N -L 8510:127.0.0.1:8510 ubuntu@<IP_OCI>
   ```
   Con la ventana de SSH abierta, entrar en **http://localhost:8510**.

## Subdominio (opcional, no aplicado)
`nginx_exp_subdomain.conf.example` permite publicar `exp.sor.alxol.com` con contraseña. Requiere tres cosas, todas aditivas y reversibles, que no modifican el bloque ni el registro DNS de producción:
* un registro DNS **nuevo**;
* un certificado;
* un archivo de Nginx propio.

## Estado y reversión
* **Estado:** `bash ~/server_status_exp.sh`.
* **Retirar la instancia experimental:** `bash ~/server_rollback_exp.sh`. Con `--purge` borra también sus archivos. Producción sigue igual y el script muestra su salud al terminar.
* **Volver al comportamiento original sin retirar la instancia:** quitar las tres variables de `docker-compose.exp.yml` y ejecutar `docker compose -p ijf-exp -f docker-compose.exp.yml up -d`.
