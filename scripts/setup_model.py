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
    passage_ids_loaded = [p.get("passage_id") for p in passages]
    if not passage_ids_loaded or any(not isinstance(pid, str) or not pid for pid in passage_ids_loaded):
        print("❌ El corpus contiene identificadores de pasaje vacíos o no válidos.")
        return False
    if len(set(passage_ids_loaded)) != len(passage_ids_loaded):
        print("❌ El corpus contiene passage_id duplicados.")
        return False
    print(f"  ✓ Corpus oficial cargado: {len(passages)} pasajes normativos.")

    expected_sha = "9426b10d11c21a4cb9eb23150c2c4fc95bfcd463511e66ba451d2cff005ae620"
    pdf_path = os.path.join(
        repo_root, "data", "raw", "sor_2026_08_rebuild",
        "IJF_Sport_and_Organisation_Rules_2026_08_14.pdf"
    )
    if os.path.isfile(pdf_path):
        import hashlib
        digest = hashlib.sha256()
        with open(pdf_path, "rb") as source_file:
            while True:
                chunk = source_file.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        actual_sha = digest.hexdigest().lower()
        if actual_sha != expected_sha:
            print(f"❌ SHA-256 del PDF físico incorrecto: {actual_sha}")
            return False
        print("  ✓ SHA-256 del PDF físico comprobado contra la fuente oficial.")
    else:
        print("  ℹ️ PDF físico no incluido en este entorno: no se afirma verificación de sus bytes; se comprobará el hash declarado en los artefactos.")

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
            elif meta.get("model_name") != model_name:
                print("  ⚠️ Metadatos declaran un modelo de embeddings incompatible.")
                need_computation = True
            elif not np.issubdtype(matrix.dtype, np.floating):
                print("  ⚠️ La matriz debe contener valores de tipo flotante.")
                need_computation = True
            elif len(set(meta.get("passage_ids", []))) != len(meta.get("passage_ids", [])):
                print("  ⚠️ Metadatos contienen passage_ids duplicados.")
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
            heading = " / ".join(p.get("heading_path") or [])
            t = f"{heading}. {p.get('text_original', '')}".strip()
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

    # Verificación final con las mismas reglas del motor productivo.
    sys.path.insert(0, os.path.join(repo_root, "src"))
    try:
        from rre_engine import ReasoningRetrievalEngine
        verified_engine = ReasoningRetrievalEngine(base_dir=data_dir, allow_degraded=False)
        if verified_engine.operating_mode != "HYBRID":
            print(f"❌ El motor terminó en modo inesperado: {verified_engine.operating_mode}")
            return False
        print("  ✓ Índice léxico, grafo, matriz, metadatos y modelo validados por RRE.")
        if verified_engine.source_sha256_verified:
            print("  ✓ Fuente física verificada criptográficamente.")
        else:
            print("  ℹ️ La fuente física no está disponible en este entorno; el hash declarado sí coincide.")
    except Exception as e:
        print(f"❌ La validación final de RRE/ADA falló: {e}")
        return False

    print("\n=====================================================================")
    print("✅ PREPARACIÓN COMPLETA: el motor RRE está validado en MODO HÍBRIDO.")
    print("=====================================================================")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verificación y configuración del modelo de embeddings RRE.")
    parser.add_argument("--rebuild", action="store_true", help="Forzar la reconstrucción de la matriz densa.")
    args = parser.parse_args()

    success = verify_and_setup(rebuild_matrix=args.rebuild)
    sys.exit(0 if success else 1)
