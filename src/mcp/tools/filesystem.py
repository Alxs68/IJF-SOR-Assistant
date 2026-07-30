import os
from core.registry import BaseTool, ToolContext
import config

def _resolve_safe_path(workspace: str, requested_path: str) -> str:
    """
    Resuelve una ruta relativa al workspace de manera segura.
    Previene ataques de Path Traversal y resuelve symlinks para asegurar confinamiento estricto.
    """
    if not workspace:
        raise ValueError("Workspace no definido en el ToolContext.")
        
    abs_workspace = os.path.abspath(workspace)
    target_path = os.path.abspath(os.path.join(abs_workspace, requested_path))
    target_path = os.path.realpath(target_path)
    
    if os.path.commonpath([abs_workspace, target_path]) != abs_workspace:
        raise ValueError(f"Acceso denegado: La ruta '{requested_path}' intenta escapar del workspace.")
        
    return target_path

class FsExistsTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "fs_exists",
            "description": "Verifica si un archivo o directorio existe en el workspace.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta relativa al workspace."
                    }
                },
                "required": ["path"]
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> dict:
        req_path = arguments.get("path")
        if not req_path:
            raise ValueError("Parámetro requerido 'path' ausente.")
            
        safe_path = _resolve_safe_path(context.workspace, req_path)
        return {"exists": os.path.exists(safe_path)}

class ListDirectoryTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "fs_list_directory",
            "description": "Lista el contenido de un directorio dentro del workspace de manera determinista (directorios primero, luego archivos, alfabéticamente).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta del directorio a listar (relativa al workspace). Usa '.' para la raíz."
                    }
                },
                "required": ["path"]
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> list:
        req_path = arguments.get("path", ".")
        safe_path = _resolve_safe_path(context.workspace, req_path)
        
        if not os.path.exists(safe_path):
            raise ValueError(f"El directorio no existe: {req_path}")
        if not os.path.isdir(safe_path):
            raise ValueError(f"La ruta no es un directorio: {req_path}")
            
        entries = []
        for entry_name in os.listdir(safe_path):
            entry_path = os.path.join(safe_path, entry_name)
            is_dir = os.path.isdir(entry_path)
            entries.append({
                "name": entry_name,
                "type": "directory" if is_dir else "file"
            })
            
        # Comportamiento determinista: directorios primero, ordenados alfabéticamente
        entries.sort(key=lambda e: (0 if e["type"] == "directory" else 1, e["name"].lower()))
        return entries

class ReadFileTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "fs_read_file",
            "description": f"Lee el contenido de un archivo de texto dentro del workspace (Límite: {config.MAX_READ_FILE_BYTES//1024//1024}MB).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta del archivo a leer (relativa al workspace)."
                    }
                },
                "required": ["path"]
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> dict:
        req_path = arguments.get("path")
        if not req_path:
            raise ValueError("Parámetro requerido 'path' ausente.")
            
        safe_path = _resolve_safe_path(context.workspace, req_path)
        
        if not os.path.exists(safe_path):
            raise ValueError(f"El archivo no existe: {req_path}")
        if not os.path.isfile(safe_path):
            raise ValueError(f"La ruta no es un archivo: {req_path}")
            
        # Validación de extensión en lista blanca estricta
        ext = os.path.splitext(safe_path)[1].lower()
        if ext not in config.ALLOWED_TEXT_EXTENSIONS:
            raise ValueError(f"Extensión no permitida: {ext}. Solo se permiten extensiones de la lista blanca de texto/código.")
            
        # Validar tamaño máximo
        file_size = os.path.getsize(safe_path)
        if file_size > config.MAX_READ_FILE_BYTES:
            raise ValueError(f"Archivo demasiado grande ({file_size} bytes). El límite es {config.MAX_READ_FILE_BYTES} bytes.")
            
        try:
            with open(safe_path, "r", encoding="utf-8", errors="strict") as f:
                content = f.read()
        except UnicodeDecodeError:
            raise ValueError(f"El archivo {req_path} no es UTF-8 válido (error estricto).")
            
        return {"content": content, "path": req_path}

class GetMetadataTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "fs_get_metadata",
            "description": "Obtiene metadatos básicos de un archivo o directorio (tamaño, última modificación).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Ruta relativa al workspace."
                    }
                },
                "required": ["path"]
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> dict:
        req_path = arguments.get("path")
        if not req_path:
            raise ValueError("Parámetro requerido 'path' ausente.")
            
        safe_path = _resolve_safe_path(context.workspace, req_path)
        
        if not os.path.exists(safe_path):
            raise ValueError(f"La ruta no existe: {req_path}")
            
        stat = os.stat(safe_path)
        return {
            "path": req_path,
            "is_directory": os.path.isdir(safe_path),
            "size_bytes": stat.st_size,
            "modified_timestamp": stat.st_mtime
        }
