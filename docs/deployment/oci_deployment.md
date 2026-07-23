# Guía de Despliegue en la Nube (OCI)
## Proyecto: IJF SOR Assistant

Esta guía detalla el aprovisionamiento, seguridad y despliegue del asistente en la infraestructura de **Oracle Cloud Infrastructure (OCI)**.

---

## ☁️ 1. Especificaciones de la Infraestructura

*   **Proveedor:** Oracle Cloud Infrastructure (OCI)
*   **Región:** Colombia Central (Bogotá)
*   **Forma de la Instancia:** `VM.Standard.A1.Flex` (ARM Ampere)
*   **Recursos:** 1 OCPU, 6 GB de memoria RAM, 1 Gbps ancho de banda de red.
*   **Sistema Operativo:** Canonical Ubuntu 24.04 LTS.

---

## 🔒 2. Seguridad y Accesos SSH

### Restricción de Claves en Windows
Para evitar advertencias de seguridad de OpenSSH debido a permisos demasiado abiertos en la clave privada (`.key`), ejecute en PowerShell:
```powershell
# Remover herencia y usuarios adicionales (SID S-1-5-11 / S-1-5-32-545)
icacls.exe "C:\PROYECTOS\ssh-key-2026-07-20.key" /inheritance:r
icacls.exe "C:\PROYECTOS\ssh-key-2026-07-20.key" /remove:g *S-1-5-11
icacls.exe "C:\PROYECTOS\ssh-key-2026-07-20.key" /remove:g *S-1-5-32-545
icacls.exe "C:\PROYECTOS\ssh-key-2026-07-20.key" /grant:r "$($env:USERNAME):(R)"
```

### Conexión por SSH
```powershell
ssh -i "C:\PROYECTOS\ssh-key-2026-07-20.key" ubuntu@149.130.187.132
```

---

## 🌐 3. Configuración de Red en OCI

Para permitir que los usuarios accedan a la aplicación web de Streamlit, se debe abrir el puerto `8501`:
1.  **En OCI Console:** Vaya a `public subnet-vcn-ijf-assistant` -> `Default Security List` -> `Add Ingress Rules`.
    *   **Source CIDR:** `0.0.0.0/0`
    *   **IP Protocol:** `TCP`
    *   **Destination Port Range:** `8501`
2.  **En Ubuntu Server (Firewall interno):**
    ```bash
    sudo ufw allow 8501/tcp
    ```

---

## 🚀 4. Métodos de Despliegue

### Método A: Despliegue Nativo (Python venv)
1.  Subir archivos por SCP:
    ```powershell
    scp -r -i "C:\PROYECTOS\ssh-key-2026-07-20.key" "C:\PROYECTOS\IJF-SOR-Assistant" ubuntu@149.130.187.132:/home/ubuntu/
    ```
2.  Conectarse por SSH, preparar el entorno y ejecutar:
    ```bash
    cd IJF-SOR-Assistant
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    
    # Ejecutar en segundo plano con redirección de logs
    nohup streamlit run app.py --server.address=0.0.0.0 --server.port=8501 > streamlit.log 2>&1 &
    ```

### Método B: Despliegue con Contenedores (Docker)
1.  Instalar Docker en Ubuntu:
    ```bash
    sudo apt update && sudo apt install docker.io -y
    sudo usermod -aG docker ubuntu
    ```
2.  Construir y arrancar usando Docker Compose:
    ```bash
    cd IJF-SOR-Assistant
    docker compose up -d --build
    ```
    *El servicio utiliza `--restart unless-stopped` para garantizar que la aplicación se reinicie automáticamente si el servidor físico se reinicia o se cae.*

### Método C: Despliegue Profesional con Systemd (Servicio del Sistema)

Para ejecutar la aplicación como un servicio en segundo plano robusto que inicie automáticamente con el servidor y se reinicie ante fallos:

1.  **Crear el Archivo del Servicio:**
    Cree el archivo `/etc/systemd/system/ijf-assistant.service` con permisos de superusuario:
    ```ini
    [Unit]
    Description=Servicio del Asistente IJF SOR Streamlit (ADA)
    After=network.target

    [Service]
    User=ubuntu
    WorkingDirectory=/home/ubuntu/IJF-SOR-Assistant
    EnvironmentFile=/home/ubuntu/IJF-SOR-Assistant/.env
    ExecStart=/home/ubuntu/IJF-SOR-Assistant/.venv/bin/streamlit run app.py --server.address=0.0.0.0 --server.port=8501
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    ```
2.  **Configurar Variables de Entorno Seguras:**
    Cree el archivo `/home/ubuntu/IJF-SOR-Assistant/.env` y declare su API Key de Gemini:
    ```bash
    GEMINI_API_KEY="tu-api-key-de-gemini-aqui"
    ```
    Asegure los permisos del archivo para que solo sea legible por su usuario:
    ```bash
    chmod 600 /home/ubuntu/IJF-SOR-Assistant/.env
    ```
3.  **Habilitar y Arrancar el Servicio:**
    Recargue el demonio de Systemd, habilite el auto-arranque e inicie el servicio:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable ijf-assistant.service
    sudo systemctl start ijf-assistant.service
    ```
4.  **Monitorear Estado y Logs:**
    *   Verificar estado activo: `sudo systemctl status ijf-assistant`
    *   Ver logs en tiempo real: `sudo journalctl -u ijf-assistant -f`

