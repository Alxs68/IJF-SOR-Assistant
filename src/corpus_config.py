import os

# Configuración de versión única del corpus normativo oficial vigente de la IJF
EDITION_2026_08 = "2026-08"

# Edición oficial única y exclusiva en el entorno operativo (14 de agosto de 2026).
ACTIVE_EDITION = EDITION_2026_08

CORPUS_CONFIG = {
    EDITION_2026_08: {
        "version_label": "14 August 2026 (Official)",
        "source_id": "SOR-2026-08-14-ENG",
        "source_sha256": "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620",
        "official_url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf",
        "data_dir": "data/processed/rebuild_2026_08_corrected",
        "passages_file": "data/processed/rebuild_2026_08_corrected/passages_candidate.json",
        "graph_file": "data/processed/rebuild_2026_08_corrected/knowledge_graph_candidate.json",
        "vector_file": "data/processed/rebuild_2026_08_corrected/vector_index_candidate.json",
        "min_relevance_score": 0.12,
        "is_legacy": False
    }
}

def get_active_corpus_config():
    """
    Retorna exclusivamente la configuración normativa oficial vigente (SOR 14 de agosto de 2026).
    Cualquier intento de forzar otra versión retornará la edición oficial vigente.
    """
    return CORPUS_CONFIG[EDITION_2026_08]

