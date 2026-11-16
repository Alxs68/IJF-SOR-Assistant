"""Componentes EXPERIMENTALES de la Fase 10 (modo SHADOW).

Nada de este paquete forma parte de la ruta de decision productiva:
  * ada_assistant, rre_engine y decision_integrity NO lo importan (verificado por
    tests/test_fase10_experimental.py).
  * Sus salidas llevan siempre experimental_label = EXPERIMENTAL_NO_DECISORIO y no
    contienen campos de decision (status, SUCCESS, PERMITIR, citations).
  * No modifican el corpus, los documentos SHADOW ni la configuracion de produccion.
"""
EXPERIMENTAL_LABEL = "EXPERIMENTAL_NO_DECISORIO"
