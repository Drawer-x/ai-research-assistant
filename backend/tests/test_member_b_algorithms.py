"""Unit tests for member B recommendation and enhanced relation algorithms."""

from __future__ import annotations

import unittest

from app.services.enhanced_relation_adapter_service import (
    generate_enhanced_relations as adapter_generate_enhanced_relations,
)
from app.services.enhanced_relation_service import generate_enhanced_relations
from app.services.recommendation_adapter_service import (
    recommend_by_paper as adapter_recommend_by_paper,
    recommend_by_topic as adapter_recommend_by_topic,
    recommend_for_library as adapter_recommend_for_library,
)
from app.services.recommendation_service import (
    recommend_by_paper,
    recommend_by_topic,
    recommend_for_library,
)


def _paper(
    external_id: str,
    title: str,
    *,
    abstract: str | None = None,
    year: int | None = 2024,
    citation_count: int = 0,
    doi: str | None = None,
    authors: list[dict] | None = None,
    fields_of_study: list[str] | None = None,
) -> dict:
    return {
        "provider": "semantic_scholar",
        "external_id": external_id,
        "title": title,
        "abstract": abstract,
        "authors": authors or [],
        "year": year,
        "venue": None,
        "doi": doi,
        "citation_count": citation_count,
        "reference_count": 0,
        "fields_of_study": fields_of_study or [],
        "is_imported": False,
        "local_paper_id": None,
    }


class RecommendationServiceTests(unittest.TestCase):
    def test_by_paper_ranks_and_excludes_seed_duplicate(self):
        seed = {
            **_paper("seed1", "Retrieval Augmented Generation for QA", abstract="RAG retrieval", year=2023),
            "paper_id": 12,
        }
        candidates = [
            _paper("c1", "Survey of RAG Systems", abstract="retrieval augmented generation QA", year=2024, citation_count=120),
            _paper("c2", "Unrelated Cooking Recipes", abstract="baking bread", year=2010, citation_count=1),
            _paper("seed1", "Retrieval Augmented Generation for QA", abstract="RAG retrieval", year=2023),
            _paper("c3", "Another RAG Paper", abstract="retrieval augmented generation", year=2022, citation_count=40, doi="10.1/x"),
        ]
        result = recommend_by_paper(seed, candidates, 2)
        self.assertEqual(len(result["items"]), 2)
        ids = [item["paper"]["external_id"] for item in result["items"]]
        self.assertNotIn("seed1", ids)
        self.assertEqual(result["items"][0]["seed_paper_ids"], [12])
        self.assertFalse(result["items"][0]["is_fallback"])
        self.assertTrue(0 <= result["items"][0]["score"] <= 1)
        self.assertGreaterEqual(result["items"][0]["score"], result["items"][1]["score"])
        self.assertTrue(result["items"][0]["reasons"])

    def test_by_paper_is_deterministic(self):
        seed = {**_paper("s", "Graph Neural Networks", abstract="GNN message passing"), "paper_id": 1}
        candidates = [
            _paper("a", "GNN Survey", abstract="graph neural networks", year=2021, citation_count=10),
            _paper("b", "Message Passing Networks", abstract="graph neural message", year=2023, citation_count=5),
        ]
        first = recommend_by_paper(seed, candidates, 5)
        second = recommend_by_paper(seed, candidates, 5)
        self.assertEqual(first, second)

    def test_for_library_excludes_negatives_and_doi_duplicates(self):
        seeds = [
            {**_paper("s1", "Transformer Attention", abstract="attention transformer"), "paper_id": 1},
            {**_paper("s2", "BERT Pretraining", abstract="bert language model"), "paper_id": 2},
        ]
        candidates = [
            _paper("n1", "Bad Paper", abstract="noise", year=2020),
            _paper("c1", "Attention Is Useful", abstract="transformer attention model", year=2024, citation_count=80),
            _paper("c2", "Duplicate DOI Paper", abstract="bert", year=2022, doi="10.dup/1"),
        ]
        seeds[0]["doi"] = "10.dup/1"
        result = recommend_for_library(seeds, candidates, ["n1"], 10)
        ids = [item["paper"]["external_id"] for item in result["items"]]
        self.assertNotIn("n1", ids)
        self.assertNotIn("c2", ids)
        self.assertIn("c1", ids)
        self.assertEqual(result["items"][0]["seed_paper_ids"], [1, 2])
        self.assertFalse(result["items"][0]["is_fallback"])

    def test_by_topic_year_filter_and_empty_topic(self):
        candidates = [
            _paper("old", "RAG Old", abstract="retrieval augmented generation", year=2018),
            _paper("new", "RAG New", abstract="retrieval augmented generation", year=2024, citation_count=30),
            _paper("mid", "Cooking", abstract="pasta", year=2023),
        ]
        result = recommend_by_topic("RAG retrieval", candidates, 2022, 2026, 5)
        ids = [item["paper"]["external_id"] for item in result["items"]]
        self.assertNotIn("old", ids)
        self.assertIn("new", ids)
        self.assertEqual(recommend_by_topic("  ", candidates, None, None, 5), {"items": []})
        self.assertEqual(recommend_by_topic("RAG", [], None, None, 5), {"items": []})

    def test_adapter_uses_real_algorithm_not_fallback(self):
        candidates = [_paper("x", "RAG Systems", abstract="retrieval augmented generation", year=2024)]
        result = adapter_recommend_by_topic("RAG", candidates, None, None, 1)
        self.assertIs(result["items"][0]["paper"], candidates[0])
        self.assertFalse(result["items"][0]["is_fallback"])
        self.assertNotIn("Academic Graph", result["items"][0]["reasons"][0])

        seed = {
            **_paper("seed", "Local Seed About Retrieval", abstract="retrieval systems"),
            "paper_id": 9,
        }
        by_paper = adapter_recommend_by_paper(seed, candidates, 1)
        self.assertTrue(by_paper["items"])
        self.assertFalse(by_paper["items"][0]["is_fallback"])

        library = adapter_recommend_for_library(
            [{**_paper("s", "RAG Seed", abstract="retrieval"), "paper_id": 3}],
            candidates,
            [],
            1,
        )
        self.assertTrue(library["items"])
        self.assertFalse(library["items"][0]["is_fallback"])

    def test_empty_candidates_and_invalid_limit(self):
        seed = {**_paper("s", "Seed Title About Graphs", abstract="graph"), "paper_id": 1}
        self.assertEqual(recommend_by_paper(seed, [], 5), {"items": []})
        self.assertEqual(recommend_for_library([seed], [], [], 5), {"items": []})
        self.assertEqual(recommend_by_paper(seed, [_paper("c", "Cand")], 0), {"items": []})
        self.assertEqual(recommend_by_paper("bad", [_paper("c", "Cand")], 3), {"items": []})
        self.assertEqual(recommend_for_library([], [_paper("c", "Cand")], [], 3), {"items": []})

    def test_missing_abstract_year_and_citation_still_score(self):
        seed = {
            "paper_id": 7,
            "external_id": "seed-miss",
            "title": "Knowledge Graph Embedding Methods",
            "abstract": None,
            "authors": [],
            "year": None,
            "doi": None,
            "citation_count": None,
            "fields_of_study": ["knowledge graph"],
        }
        candidates = [
            {
                "external_id": "c-miss",
                "title": "Knowledge Graph Embedding Survey",
                "abstract": None,
                "authors": [],
                "year": None,
                "doi": None,
                "citation_count": None,
                "fields_of_study": ["knowledge graph"],
            },
            {
                "external_id": "c-partial",
                "title": "Unrelated Title Without Overlap ZZZ",
                "abstract": None,
                "authors": [],
                "year": None,
                "citation_count": 0,
                "fields_of_study": [],
            },
        ]
        result = recommend_by_paper(seed, candidates, 5)
        self.assertEqual(len(result["items"]), 2)
        for item in result["items"]:
            self.assertTrue(0.0 <= item["score"] <= 1.0)
            self.assertFalse(item["is_fallback"])
            self.assertEqual(item["seed_paper_ids"], [7])
            self.assertIsInstance(item["reasons"], list)
            self.assertTrue(item["reasons"])
        # Missing citation/year must not crash and must keep ranking deterministic.
        self.assertEqual(result, recommend_by_paper(seed, candidates, 5))

    def test_score_boundaries_and_reason_consistency(self):
        seed = {
            **_paper(
                "seed-bound",
                "Contrastive Learning for Graphs",
                abstract="contrastive learning graph neural network",
                year=2020,
                citation_count=1,
            ),
            "paper_id": 3,
        }
        strong = _paper(
            "strong",
            "Contrastive Learning Graph Neural Survey",
            abstract="contrastive learning graph neural network embedding",
            year=2025,
            citation_count=1000,
            fields_of_study=["contrastive learning", "graph"],
        )
        weak = _paper(
            "weak",
            "Ancient Cooking Manual Volume One",
            abstract="recipes and baking techniques",
            year=1990,
            citation_count=0,
        )
        result = recommend_by_paper(seed, [strong, weak], 2)
        self.assertEqual(len(result["items"]), 2)
        top, bottom = result["items"]
        self.assertEqual(top["paper"]["external_id"], "strong")
        self.assertTrue(0.0 <= bottom["score"] <= top["score"] <= 1.0)
        reason_text = " ".join(top["reasons"])
        self.assertTrue(
            any(key in reason_text for key in ("语义", "引用", "发表", "外部平台", "主题")),
            reason_text,
        )
        # Provider-only path: no semantic overlap, no citations, no year -> score from provider_rank only.
        bare_seed = {**_paper("bare-seed", "Alpha Unique Seed Title XYZ"), "paper_id": 4}
        bare = [
            {
                "external_id": "bare1",
                "title": "Completely Different Topic QQQ",
                "abstract": None,
                "year": None,
                "citation_count": None,
                "authors": [],
                "fields_of_study": [],
            }
        ]
        bare_result = recommend_by_paper(bare_seed, bare, 1)
        self.assertEqual(len(bare_result["items"]), 1)
        self.assertTrue(0.0 < bare_result["items"][0]["score"] <= 1.0)
        self.assertIn("外部平台", " ".join(bare_result["items"][0]["reasons"]))

    def test_title_near_duplicate_and_candidate_dedupe(self):
        seed = {
            **_paper("seed-dup", "Deep Residual Learning for Image Recognition", abstract="resnet"),
            "paper_id": 8,
            "doi": "10.seed/1",
        }
        candidates = [
            _paper(
                "near",
                "Deep Residual Learning for Image Recognition",
                abstract="different abstract text",
                year=2016,
            ),
            _paper("keep", "Vision Transformers Are Great Models", abstract="vision transformer", year=2021),
            _paper("dup-eid", "First Appearance", abstract="x", year=2020),
            _paper("dup-eid", "Second Appearance Same Id", abstract="y", year=2021),
            _paper("doi-a", "Paper A Unique Title", abstract="a", year=2020, doi="10.same/x"),
            _paper("doi-b", "Paper B Unique Title", abstract="b", year=2021, doi="10.same/x"),
        ]
        result = recommend_by_paper(seed, candidates, 10)
        ids = [item["paper"]["external_id"] for item in result["items"]]
        self.assertNotIn("near", ids)
        self.assertEqual(ids.count("dup-eid"), 1)
        self.assertTrue(("doi-a" in ids) ^ ("doi-b" in ids) or ids.count("doi-a") + ids.count("doi-b") == 1)
        doi_hits = [eid for eid in ids if eid in {"doi-a", "doi-b"}]
        self.assertEqual(len(doi_hits), 1)

    def test_negative_feedback_only_in_library_mode(self):
        seeds = [{**_paper("s1", "BERT Language Understanding", abstract="bert language"), "paper_id": 1}]
        candidates = [
            _paper("neg", "BERT Fine Tuning Guide", abstract="bert fine tuning", year=2023),
            _paper("pos", "Language Model Pretraining", abstract="bert language model", year=2024),
        ]
        with_neg = recommend_for_library(seeds, candidates, ["neg"], 5)
        without_neg = recommend_for_library(seeds, candidates, [], 5)
        self.assertNotIn("neg", [item["paper"]["external_id"] for item in with_neg["items"]])
        self.assertIn("neg", [item["paper"]["external_id"] for item in without_neg["items"]])


class EnhancedRelationServiceTests(unittest.TestCase):
    def test_recommended_from_and_same_author(self):
        local_papers = [
            {
                "paper_id": 1,
                "title": "Local RAG Paper About Retrieval Systems",
                "authors": "Alice Zhang, Bob Lee",
                "year": 2023,
                "abstract": "retrieval augmented generation",
                "full_text": "",
            },
            {
                "paper_id": 2,
                "title": "Another Local Paper On Neural Ranking",
                "authors": "Alice Zhang",
                "year": 2024,
                "abstract": "neural ranking retrieval",
                "full_text": "",
            },
        ]
        external_papers = [
            {
                "external_id": "ext1",
                "title": "External RAG Survey Paper Title",
                "authors": [{"name": "Carol Wang"}],
                "year": 2022,
                "abstract": "retrieval augmented generation survey",
                "full_text": "",
                "fields_of_study": ["RAG"],
            }
        ]
        records = [{"id": 88, "seed_paper_ids": [1], "score": 0.81, "external_id": "ext1"}]
        result = generate_enhanced_relations(
            local_papers,
            external_papers,
            records,
            ["same_author", "recommended_from", "topic_similarity"],
        )
        types = {item["relation_type"] for item in result["relations"]}
        self.assertIn("recommended_from", types)
        self.assertIn("same_author", types)
        recommended = [
            item for item in result["relations"] if item["relation_type"] == "recommended_from"
        ][0]
        self.assertEqual(recommended["source"], "local:1")
        self.assertEqual(recommended["target"], "recommendation:88")
        self.assertTrue(recommended["directed"])
        self.assertFalse(recommended["is_fallback"])
        self.assertTrue(0 <= recommended["weight"] <= 1)

        same_author = [
            item for item in result["relations"] if item["relation_type"] == "same_author"
        ][0]
        self.assertEqual({same_author["source"], same_author["target"]}, {"local:1", "local:2"})
        self.assertFalse(same_author["directed"])

    def test_citation_and_method_similarity(self):
        cited_title = "Deep Residual Learning for Image Recognition"
        local_papers = [
            {
                "paper_id": 10,
                "title": "Vision Backbone Study With Residual Networks",
                "authors": "He Kaiming",
                "year": 2016,
                "abstract": "We use CNN residual networks",
                "full_text": (
                    "Introduction uses residual learning. References\n"
                    f"{cited_title}. He et al. 2016."
                ),
            },
            {
                "paper_id": 11,
                "title": cited_title,
                "authors": "He Kaiming",
                "year": 2016,
                "abstract": "residual learning CNN",
                "full_text": "CNN residual learning paper body",
            },
        ]
        result = generate_enhanced_relations(
            local_papers,
            [],
            [],
            ["citation", "method_similarity"],
        )
        types = {item["relation_type"] for item in result["relations"]}
        self.assertIn("citation", types)
        self.assertIn("method_similarity", types)
        citation = [item for item in result["relations"] if item["relation_type"] == "citation"][0]
        self.assertEqual(citation["source"], "local:10")
        self.assertEqual(citation["target"], "local:11")
        self.assertTrue(citation["directed"])

    def test_rejects_self_loops_and_empty_inputs(self):
        self.assertEqual(
            generate_enhanced_relations([], [], [], ["topic_similarity"]),
            {"relations": []},
        )
        self.assertEqual(
            generate_enhanced_relations(
                [{"paper_id": 1, "title": "Only One", "authors": "A", "abstract": "x", "full_text": ""}],
                [],
                [{"id": 1, "seed_paper_ids": [1], "score": 1.0}],
                [],
            ),
            {"relations": []},
        )
        first = generate_enhanced_relations(
            [
                {"paper_id": 1, "title": "RAG Retrieval Paper Alpha", "authors": "Ann", "abstract": "rag retrieval", "full_text": ""},
                {"paper_id": 2, "title": "RAG Retrieval Paper Beta", "authors": "Bob", "abstract": "rag retrieval", "full_text": ""},
            ],
            [],
            [],
            ["topic_similarity"],
        )
        second = generate_enhanced_relations(
            [
                {"paper_id": 1, "title": "RAG Retrieval Paper Alpha", "authors": "Ann", "abstract": "rag retrieval", "full_text": ""},
                {"paper_id": 2, "title": "RAG Retrieval Paper Beta", "authors": "Bob", "abstract": "rag retrieval", "full_text": ""},
            ],
            [],
            [],
            ["topic_similarity"],
        )
        self.assertEqual(first, second)
        for item in first["relations"]:
            self.assertNotEqual(item["source"], item["target"])

    def test_adapter_delegates_to_real_service(self):
        result = adapter_generate_enhanced_relations(
            [{"paper_id": 1, "title": "Local Seed Paper Title Here", "authors": "Ann", "abstract": "rag", "full_text": ""}],
            [],
            [{"id": 5, "seed_paper_ids": [1], "score": 0.5}],
            ["recommended_from"],
        )
        self.assertEqual(len(result["relations"]), 1)
        self.assertFalse(result["relations"][0]["is_fallback"])
        self.assertEqual(result["relations"][0]["target"], "recommendation:5")

    def test_missing_fields_invalid_records_and_weight_clamp(self):
        local_papers = [
            {"paper_id": 1, "title": "Graph Neural Network Message Passing Study", "authors": None, "abstract": None, "full_text": None, "year": None},
            {"paper_id": 2, "title": "Graph Neural Network Representation Learning", "authors": "", "abstract": None, "full_text": "", "year": None},
            {"paper_id": -1, "title": "Invalid id ignored", "authors": "X", "abstract": "x", "full_text": ""},
        ]
        external_papers = [
            {"external_id": "", "title": "Empty id ignored", "authors": [], "abstract": None},
            {"external_id": "e1", "title": "Graph Neural Network External Paper", "authors": [{"name": "Dana"}], "abstract": None, "year": None},
        ]
        records = [
            {"id": 9, "seed_paper_ids": [1, 99], "score": 1.7},  # clamp weight, ignore unknown seed 99
            {"id": "bad", "seed_paper_ids": [1], "score": 0.2},
            {"seed_paper_ids": [1], "score": 0.2},
            {"id": 10, "seed_paper_ids": "not-a-list", "score": 0.2},
        ]
        result = generate_enhanced_relations(
            local_papers,
            external_papers,
            records,
            ["topic_similarity", "recommended_from", "same_author", "method_similarity", "citation"],
        )
        self.assertTrue(result["relations"])
        endpoints = {(item["source"], item["target"], item["relation_type"]) for item in result["relations"]}
        self.assertEqual(len(endpoints), len(result["relations"]))
        for item in result["relations"]:
            self.assertNotEqual(item["source"], item["target"])
            self.assertTrue(0.0 <= item["weight"] <= 1.0)
            self.assertTrue(item["source"].startswith(("local:", "s2:", "recommendation:")))
            self.assertTrue(item["target"].startswith(("local:", "s2:", "recommendation:")))
        recommended = [
            item for item in result["relations"] if item["relation_type"] == "recommended_from"
        ]
        self.assertEqual(len(recommended), 1)
        self.assertEqual(recommended[0]["weight"], 1.0)
        self.assertEqual(recommended[0]["source"], "local:1")

    def test_duplicate_edges_are_collapsed(self):
        papers = [
            {
                "paper_id": 1,
                "title": "Same Author Graph Paper Alpha Title",
                "authors": "Eve Stone",
                "abstract": "graph neural network",
                "full_text": "",
            },
            {
                "paper_id": 2,
                "title": "Same Author Graph Paper Beta Title",
                "authors": "Eve Stone",
                "abstract": "graph neural network",
                "full_text": "",
            },
        ]
        # Calling with duplicate relation type requests still yields unique edges.
        result = generate_enhanced_relations(papers, [], [], ["same_author", "same_author", "topic_similarity"])
        keys = [(item["source"], item["target"], item["relation_type"]) for item in result["relations"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(any(item["relation_type"] == "same_author" for item in result["relations"]))


if __name__ == "__main__":
    unittest.main()
