import time
import os
import sys

# Asegurar que los módulos core y config se resuelven correctamente 
# ejecutando el servidor desde cualquier ubicación
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.transport import StdioTransport
from core.protocol import MCPProtocolHandler
from core.logger import mcp_logger
from tools.filesystem import FsExistsTool, ListDirectoryTool, ReadFileTool, GetMetadataTool

def main():
    mcp_logger.info("Iniciando Servidor MCP Síncrono v1.0...", extra={"method": "STARTUP"})
    
    transport = StdioTransport()
    protocol = MCPProtocolHandler()
    
    # Importar el registry dinámicamente para inyectar herramientas
    from core.registry import registry
    registry.register("fs_exists", FsExistsTool())
    registry.register("fs_list_directory", ListDirectoryTool())
    registry.register("fs_read_file", ReadFileTool())
    registry.register("fs_get_metadata", GetMetadataTool())
    mcp_logger.info("Herramientas de Filesystem registradas exitosamente.")

    while True:
        raw_line = transport.read_line()
        if raw_line is None:
            break  # Pipe cerrado por el cliente de forma limpia
            
        if not raw_line:
            continue

        start_time = time.perf_counter()
        
        # El transporte pasa la línea al protocolo
        response_string = protocol.handle_line(raw_line)
        
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Si el protocolo generó un output (no es notificación), el transporte lo escribe
        if response_string:
            transport.write_line(response_string)
            
            # Telemetría síncrona registrada de forma paralela en stderr
            mcp_logger.info(
                "Línea de transporte procesada.", 
                extra={"duration_ms": round(duration_ms, 2)}
            )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        mcp_logger.info("Servidor MCP terminado manualmente.", extra={"method": "SHUTDOWN"})
