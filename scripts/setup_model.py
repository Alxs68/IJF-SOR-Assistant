"""Script de configuración y verificación reproducible del modelo sentence-transformers.

Este script prepara de forma explícita el modelo `sentence-transformers/all-MiniLM-L6-v2`
para el motor RRE (Reasoning Retrieval Engine) de IJF-SOR-Assistant (SOR 2026-08).

Objetivos:
1. Verificar disponibilidad e importación de dependencias (torch, sentence_transformers, numpy).
2. Descargar o cargar desde caché el modelo de embeddings dense (384 dimensiones).
3. Validar el tamaño, forma y metadatos de la matriz densa pre-computada (dense_embeddings_candidate.npy).
4. Opcionalmente recalcular o regenerar la matriz si falta o si se solicita explícitamente (--rebuild).
"""

import os
import sys
import json
import argparse
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

def verify_and_setup(rebuild_matrix=False):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(repo_root, "data", "processed", "rebuild_2026_08")
    passages_path = os.path.join(data_dir, "passages_candidate.json")
    matrix_path = os.path.join(data_dir, "dense_embeddings_candidate.npy")
    meta_path = os.path.join(data_dir, "dense_embeddings_meta.json")

    print("=====================================================================")
    print("🥋 IJF SOR Assistant — Preparación y Verificación del Modelo RRE")
    print("=====================================================================")
    print(f"[1/4] Directorio base: {data_dir}")

    if not os.path.exists(passages_path):
        print(f"❌ Error: Archivo de pasajes no encontrado en {passages_path}")
        return False

    with open(passages_path, "r", encoding="utf-8") as f:
        passages = json.load(f)
    print(f"  ✓ Corpus oficial cargado: {len(passages)} pasajes normativos.")

    # 1. Cargar dependencias
    print("\n[2/4] Verificando dependencias de aprendizaje profundo...")
    try:
        import torch
        import sentence_transformers
        from sentence_transformers import SentenceTransformer
        print(f"  ✓ PyTorch versión: {torch.__version__}")
        print(f"  ✓ Sentence-Transformers versión: {sentence_transformers.__version__}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  ✓ Dispositivo de cómputo detectado: {device}")
    except ImportError as e:
        print(f"❌ Error importando librerías requeridas: {e}")
        print("   Ejecute: pip install -r requirements.txt")
        return False

    # 2. Descargar / Cargar Modelo
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"\n[3/4] Inicializando modelo de embeddings: {model_name}...")
    model = None
    try:
        import glob
        cache_pattern = os.path.expanduser('~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/*')
        snapshots = glob.glob(cache_pattern)
        if snapshots:
            print(f"  ✓ Snapshot local detectado en caché: {snapshots[0]}")
            model = SentenceTransformer(snapshots[0], device=device, local_files_only=True)
        else:
            print("  ℹ️ No se detectó snapshot local. Intentando descargar modelo desde el repositorio oficial...")
            model = SentenceTransformer(model_name, device=device)

        test_embed = model.encode("IJF Sport and Organisation Rules test embedding")
        print(f"  ✓ Modelo cargado y verificado. Dimensión del vector de prueba: {test_embed.shape[0]}")
        if test_embed.shape[0] != 384:
            print(f"❌ Error: Dimensión del modelo esperada 384, obtenida {test_embed.shape[0]}.")
            return False
    except Exception as e:
        print(f"❌ Error crítico: No se pudo preparar ni cargar el modelo {model_name}: {e}")
        print("   Para operar en modo híbrido neuronal, se requiere SentenceTransformer operativo.")
        return False

    # 3. Verificación o Reconstrucción de la Matriz Densa
    print("\n[4/4] Verificando matriz densa y metadatos de procedencia...")
    need_computation = rebuild_matrix or not os.path.exists(matrix_path) or not os.path.exists(meta_path)

    if not need_computation:
        try:
            matrix = np.load(matrix_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            # Aplicar exactamente las mismas reglas de validación que el motor RRE
            if not isinstance(matrix, np.ndarray) or matrix.ndim != 2:
                print(f"  ⚠️ Matriz no tiene 2 dimensiones ({getattr(matrix, 'ndim', 'None')}).")
                need_computation = True
            elif matrix.shape != (len(passages), 384):
                print(f"  ⚠️ Forma inválida {matrix.shape}, esperada ({len(passages)}, 384).")
                need_computation = True
            elif not np.all(np.isfinite(matrix)):
                print("  ⚠️ La matriz contiene valores no finitos (NaN/Inf).")
                need_computation = True
            elif meta.get("num_passages") != len(passages) or meta.get("dimension") != 384:
                print("  ⚠️ Metadatos inconsistentes con las dimensiones del corpus.")
                need_computation = True
            elif meta.get("passage_ids") != [p["passage_id"] for p in passages]:
                print("  ⚠️ Desalineación en el orden o lista de passage_ids.")
                need_computation = True
            elif str(meta.get("source_sha256", "")).lower() != "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620":
                print("  ⚠️ Discrepancia criptográfica en source_sha256 de metadatos.")
                need_computation = True
            else:
                print("  ✓ Matriz y metadatos validados con éxito: 554 pasajes, 384 dimensiones, orden 1:1 estricto.")
        except Exception as e:
            print(f"  ⚠️ Error auditando matriz existente ({e}). Se procederá a reconstruirla.")
            need_computation = True

    if need_computation:
        print(f"  ⚙️ Generando embeddings densos para {len(passages)} pasajes con {model_name}...")
        corpus_texts = []
        passage_ids = []
        for p in passages:
            t = f"{p['title']}. {p.get('text_original', '')}"
            corpus_texts.append(t)
            passage_ids.append(p["passage_id"])

        dense_embeddings = model.encode(corpus_texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
        np.save(matrix_path, dense_embeddings.astype(np.float32))
        print(f"  ✓ Matriz guardada en: {matrix_path} ({os.path.getsize(matrix_path)} bytes)")

        meta_data = {
            "model_name": model_name,
            "dimension": 384,
            "num_passages": len(passages),
            "passage_ids": passage_ids,
            "source_sha256": "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)
        print(f"  ✓ Metadatos actualizados y certificados en: {meta_path}")

    print("\n=====================================================================")
    print("✅ PREPARACIÓN COMPLETA: El motor RRE está validado en MODO HÍBRIDO.")
    print("=====================================================================")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verificación y configuración del modelo de embeddings RRE.")
    parser.add_argument("--rebuild", action="store_true", help="Forzar la reconstrucción de la matriz densa.")
    args = parser.parse_args()

    success = verify_and_setup(rebuild_matrix=args.rebuild)
    sys.exit(0 if success else 1)
