import os

# Configuración de versiones del corpus normativo IJF SOR
EDITION_2026_01 = "2026-01"
EDITION_2026_08 = "2026-08"

# Edición activa por defecto.
# Puede ser controlada mediante la variable de entorno IJF_SOR_EDITION ("2026-08" o "2026-01").
ACTIVE_EDITION = os.environ.get("IJF_SOR_EDITION", EDITION_2026_08)

CORPUS_CONFIG = {
    EDITION_2026_08: {
        "version_label": "14 August 2026 (Official)",
        "source_id": "SOR-2026-08-14-ENG",
        "source_sha256": "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620",
        "official_url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/08/IJF_Sport_and_Organisation_Rul-1787430903.pdf",
        "data_dir": "data/processed/rebuild_2026_08",
        "passages_file": "data/processed/rebuild_2026_08/passages_candidate.json",
        "graph_file": "data/processed/rebuild_2026_08/knowledge_graph_candidate.json",
        "vector_file": "data/processed/rebuild_2026_08/vector_index_candidate.json",
        "min_relevance_score": 0.12,
        "is_legacy": False
    },
    EDITION_2026_01: {
        "version_label": "January 2026 (Historical)",
        "source_id": "DOC-001",
        "source_sha256": "729B1843CB370D19D70FC71481A1A39939D2434201514A3BEF3AF402A5AB995F",
        "official_url": "https://78884ca60822a34fb0e6-082b8fd5551e97bc65e327988b444396.ssl.cf3.rackcdn.com/up/2026/01/IJF_Sport_and_Organisation_Rul-1769443746.pdf",
        "markdown_dir": "data/markdown",
        "graph_file": "scratch/knowledge_graph.json",
        "vector_file": "scratch/vector_store_index.json",
        "min_relevance_score": 0.10,
        "is_legacy": True
    }
}

def get_active_corpus_config():
    edition = os.environ.get("IJF_SOR_EDITION", ACTIVE_EDITION)
    return CORPUS_CONFIG.get(edition, CORPUS_CONFIG[EDITION_2026_08])
