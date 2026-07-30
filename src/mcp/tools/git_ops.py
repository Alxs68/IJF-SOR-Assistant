import subprocess
import re
from core.registry import BaseTool, ToolContext

def _run_git_command(workspace: str, args: list) -> str:
    """Ejecuta un comando git de forma segura sin shell=True y retorna el stdout."""
    if not workspace:
        raise ValueError("Workspace no definido en el ToolContext.")
    
    cmd = ["git"] + args
    try:
        # capture_output=True y text=True aplican utf-8 por defecto
        # check=False para leer el error si git falla
        result = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise ValueError(f"Git error ({result.returncode}): {result.stderr.strip()}")
        return result.stdout.strip()
    except FileNotFoundError:
        raise ValueError("Git no está instalado o no se encuentra en el PATH del sistema.")
    except Exception as e:
        raise ValueError(f"Fallo al ejecutar git: {str(e)}")

class GitStatusTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "git_status",
            "description": "Obtiene el estado actual del repositorio Git (archivos modificados, staged, untracked).",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> list:
        stdout = _run_git_command(context.workspace, ["status", "--porcelain"])
        if not stdout:
            return []
        
        status_list = []
        for line in stdout.splitlines():
            if len(line) < 3:
                continue
            status_code = line[0:2]
            file_path = line[3:]
            status_list.append({
                "status_code": status_code,
                "file": file_path
            })
        return status_list

class GitLogTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "git_log",
            "description": "Obtiene el historial reciente de commits de Git.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Número de commits a mostrar (por defecto 10, máximo 50)."
                    }
                },
                "required": []
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> list:
        count = arguments.get("count", 10)
        if not isinstance(count, int) or count <= 0:
            count = 10
        count = min(count, 50)
        
        stdout = _run_git_command(context.workspace, ["log", "--oneline", f"-n{count}"])
        if not stdout:
            return []
            
        logs = []
        for line in stdout.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2:
                logs.append({
                    "hash": parts[0],
                    "message": parts[1]
                })
        return logs

class GitShowTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "git_show",
            "description": "Obtiene los detalles y el diff de un commit específico.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "commit_hash": {
                        "type": "string",
                        "description": "El hash corto o largo del commit."
                    }
                },
                "required": ["commit_hash"]
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> dict:
        commit_hash = arguments.get("commit_hash", "")
        if not commit_hash:
            raise ValueError("Parámetro requerido 'commit_hash' ausente.")
            
        # Validación de seguridad estricta para el hash
        if not re.match(r"^[a-fA-F0-9]{4,40}$", commit_hash):
            raise ValueError("El 'commit_hash' proporcionado no tiene un formato válido o contiene caracteres inseguros.")
            
        stdout = _run_git_command(context.workspace, ["show", commit_hash])
        return {"commit_hash": commit_hash, "details": stdout}

class GitDiffTool(BaseTool):
    def get_schema(self) -> dict:
        return {
            "name": "git_diff",
            "description": "Obtiene el diff de los cambios locales no commiteados.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "staged": {
                        "type": "boolean",
                        "description": "Si es true, muestra los cambios cacheados (staged). Si es false (por defecto), muestra los cambios en el árbol de trabajo."
                    }
                },
                "required": []
            }
        }

    def execute(self, context: ToolContext, arguments: dict) -> dict:
        staged = arguments.get("staged", False)
        args = ["diff"]
        if staged:
            args.append("--staged")
            
        stdout = _run_git_command(context.workspace, args)
        return {"diff": stdout, "staged": staged}
