"""
Pruebas unitarias de PassageStitcher para RRE 3.0 Fase 2.

Verifica:
1. Continuidad sintáctica y delimitadores entre páginas consecutivas.
2. Comportamiento en artículos multi-página (Art. 14 págs. 166-167, Art. 18.1.4 págs. 188-189).
3. Aislamiento estricto de artículos y secciones en una misma página física (pág. 188 S195 vs S196).
4. Exclusión taxativa de 'GENERAL' y apéndices extensos ('H1.1').
5. Preservación del KUN primario, composite_kun y arreglo source_spans.
6. Notificación explícita en caso de truncamiento por tope de seguridad max_expansion_pages.
"""

import pytest
from src.passage_stitcher import PassageStitcher


@pytest.fixture
def sample_corpus():
    return {
        # Artículo 14 en páginas 166 y 167
        "SOR-2026-08-P166-S187": {
            "passage_id": "SOR-2026-08-P166-S187",
            "article_id": "Article 14",
            "pdf_page_index": 166,
            "heading_path": ["Article 14 Ippon"],
            "text_original": "Rule 14.1 Ippon criteria. 2. All situations in which one of the athletes voluntarily makes a bridge will be ippon.",
            "source_url": "https://example.com/sor.pdf"
        },
        "SOR-2026-08-P167-S187": {
            "passage_id": "SOR-2026-08-P167-S187",
            "article_id": "Article 14",
            "pdf_page_index": 167,
            "heading_path": ["Article 14 Ippon"],
            "text_original": "This decision is taken for safety. No score or penalty will be given if the landing of uke occurs on the body of tori.",
            "source_url": "https://example.com/sor.pdf"
        },
        # Misma página física 188 con dos artículos distintos
        "SOR-2026-08-P188-S195": {
            "passage_id": "SOR-2026-08-P188-S195",
            "article_id": "Article 18.1.3",
            "pdf_page_index": 188,
            "heading_path": ["Article 18.1.3 Untidy Attire"],
            "text_original": "Untidy attire or hair wasting time.",
            "source_url": "https://example.com/sor.pdf"
        },
        "SOR-2026-08-P188-S196": {
            "passage_id": "SOR-2026-08-P188-S196",
            "article_id": "Article 18.1.4",
            "pdf_page_index": 188,
            "heading_path": ["Article 18.1.4 Cadet Competitions"],
            "text_original": "33. Tori cannot use head. 34. Uke cannot use head to defend, penalised with shido.",
            "source_url": "https://example.com/sor.pdf"
        },
        "SOR-2026-08-P189-S196": {
            "passage_id": "SOR-2026-08-P189-S196",
            "article_id": "Article 18.1.4",
            "pdf_page_index": 189,
            "heading_path": ["Article 18.1.4 Cadet Competitions"],
            "text_original": "35. Reverse seoi-nage is forbidden in cadets, shido.",
            "source_url": "https://example.com/sor.pdf"
        },
        # Artículo GENERAL que no debe concatenarse
        "SOR-2026-08-P012-S001": {
            "passage_id": "SOR-2026-08-P012-S001",
            "article_id": "GENERAL",
            "pdf_page_index": 12,
            "heading_path": ["GENERAL INFORMATION"],
            "text_original": "General information page 12.",
            "source_url": "https://example.com/sor.pdf"
        },
        "SOR-2026-08-P013-S002": {
            "passage_id": "SOR-2026-08-P013-S002",
            "article_id": "GENERAL",
            "pdf_page_index": 13,
            "heading_path": ["GENERAL INFORMATION"],
            "text_original": "General information page 13.",
            "source_url": "https://example.com/sor.pdf"
        },
        # Artículo largo de 4 páginas
        "SOR-2026-08-P084-S100": {
            "passage_id": "SOR-2026-08-P084-S100",
            "article_id": "6.5",
            "pdf_page_index": 84,
            "heading_path": ["6.5 Teams Weigh-in"],
            "text_original": "Weigh-in part 1",
            "source_url": "https://example.com/sor.pdf"
        },
        "SOR-2026-08-P085-S100": {
            "passage_id": "SOR-2026-08-P085-S100",
            "article_id": "6.5",
            "pdf_page_index": 85,
            "heading_path": ["6.5 Teams Weigh-in"],
            "text_original": "Weigh-in part 2",
            "source_url": "https://example.com/sor.pdf"
        },
        "SOR-2026-08-P086-S100": {
            "passage_id": "SOR-2026-08-P086-S100",
            "article_id": "6.5",
            "pdf_page_index": 86,
            "heading_path": ["6.5 Teams Weigh-in"],
            "text_original": "Weigh-in part 3",
            "source_url": "https://example.com/sor.pdf"
        },
        "SOR-2026-08-P087-S100": {
            "passage_id": "SOR-2026-08-P087-S100",
            "article_id": "6.5",
            "pdf_page_index": 87,
            "heading_path": ["6.5 Teams Weigh-in"],
            "text_original": "Weigh-in part 4",
            "source_url": "https://example.com/sor.pdf"
        }
    }


def test_passage_stitcher_art14_continuity(sample_corpus):
    stitcher = PassageStitcher(sample_corpus, max_expansion_pages=3)
    p166 = sample_corpus["SOR-2026-08-P166-S187"]
    stitched = stitcher.stitch_evidence(p166)

    assert stitched["is_stitched"] is True
    assert stitched["primary_kun"] == "SOR-2026-08-P166-S187"
    assert stitched["composite_kun"] == "SOR-2026-08-P166-P167"
    assert stitched["stitched_kuns"] == ["SOR-2026-08-P166-S187", "SOR-2026-08-P167-S187"]
    assert len(stitched["source_spans"]) == 2
    assert "[PAGE BREAK: P166 -> P167" in stitched["text_original"]
    assert "voluntarily makes a bridge" in stitched["text_original"]
    assert "landing of uke occurs on the body of tori" in stitched["text_original"]


def test_passage_stitcher_backward_expansion(sample_corpus):
    stitcher = PassageStitcher(sample_corpus, max_expansion_pages=3)
    p167 = sample_corpus["SOR-2026-08-P167-S187"]
    stitched = stitcher.stitch_evidence(p167)

    assert stitched["is_stitched"] is True
    assert stitched["primary_kun"] == "SOR-2026-08-P167-S187"
    assert stitched["stitched_kuns"] == ["SOR-2026-08-P166-S187", "SOR-2026-08-P167-S187"]
    assert stitched["source_spans"][0]["page"] == 166
    assert stitched["source_spans"][1]["page"] == 167


def test_passage_stitcher_isolates_different_articles_on_same_page(sample_corpus):
    stitcher = PassageStitcher(sample_corpus, max_expansion_pages=3)
    # S195 no tiene continuación en p. 189
    p188_attire = sample_corpus["SOR-2026-08-P188-S195"]
    stitched_attire = stitcher.stitch_evidence(p188_attire)
    assert stitched_attire["is_stitched"] is False
    assert stitched_attire["passage_id"] == "SOR-2026-08-P188-S195"

    # S196 sí tiene continuación en p. 189 S196
    p188_cadet = sample_corpus["SOR-2026-08-P188-S196"]
    stitched_cadet = stitcher.stitch_evidence(p188_cadet)
    assert stitched_cadet["is_stitched"] is True
    assert stitched_cadet["stitched_kuns"] == ["SOR-2026-08-P188-S196", "SOR-2026-08-P189-S196"]
    assert "Reverse seoi-nage is forbidden" in stitched_cadet["text_original"]


def test_passage_stitcher_excludes_general(sample_corpus):
    stitcher = PassageStitcher(sample_corpus, max_expansion_pages=3)
    p12 = sample_corpus["SOR-2026-08-P012-S001"]
    stitched = stitcher.stitch_evidence(p12)
    assert stitched["is_stitched"] is False
    assert stitched.get("composite_kun") is None


def test_passage_stitcher_expansion_cap_and_truncation_flag(sample_corpus):
    # Probar con límite estricto de expansión de 2 páginas
    stitcher = PassageStitcher(sample_corpus, max_expansion_pages=2)
    p84 = sample_corpus["SOR-2026-08-P084-S100"]
    stitched = stitcher.stitch_evidence(p84)

    assert stitched["is_stitched"] is True
    # 84 + 2 páginas hacia adelante = 84, 85, 86 (total 3 páginas)
    assert len(stitched["source_spans"]) == 3
    assert stitched["is_partial_reconstruction"] is True
    assert "Reconstrucción parcial limitada" in stitched["reconstruction_note"]
