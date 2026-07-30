import os

MCP_VERSION = "2024-11-05"
SERVER_NAME = "Laboratorio-Orquestador-Propio"
SERVER_VERSION = "1.2.1"

# Límites y configuraciones globales
MAX_LINE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_READ_FILE_BYTES = 1 * 1024 * 1024 # 1MB

ALLOWED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".json", ".yaml", ".yml", 
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", 
    ".xml", ".html", ".css", ".sql", ".csv", ".log"
}
