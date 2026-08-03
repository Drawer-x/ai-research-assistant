"""Deterministic recommendation ranking for Sprint 4 (member B).

Pure functions only: no database, JWT, or HTTP. Candidates must come from the
caller; this module never invents paper metadata.
"""

from __future__ import annotations

import math
import re
from typing import Any

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "model", "models", "of", "on", "or", "paper",
    "research", "result", "results", "study", "the", "this", "to", "using",
    "we", "with", "一种", "以及", "使用", "分析", "基于", "实验", "方法",
    "本文", "模型", "结果", "研究", "论文", "通过",
}

_PROVIDER_W = 0.50
_SEMANTIC_W = 0.30
_FRESHNESS_W = 0.10
_CITATION_W = 0.10
_TITLE_DUP_THRESHOLD = 0.85
_REF_YEAR = 2026


def _safe_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _normalize_doi(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text or None


def _normalize_title(value: Any) -> str:
    return " ".join(str(value or "").split())


def _clamp01(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return max(0.0, min(1.0, value))


def _tokens(text: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text.casefold()).strip()
    english = re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", text.casefold())
    chinese: set[str] = set()
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        for width in range(2, min(4, len(phrase)) + 1):
            chinese.update(
                phrase[i:i + width] for i in range(len(phrase) - width + 1)
            )
    return {
        token for token in (*english, *chinese)
        if token not in _STOP_WORDS and len(token) >= 2
    }


def _weighted_tokens(paper: dict[str, Any]) -> dict[str, float]:
    authors = paper.get("authors")
    if isinstance(authors, list):
        author_text = " ".join(
            _safe_str(item.get("name")) for item in authors if isinstance(item, dict)
        )
    else:
        author_text = _safe_str(authors)
    fields = paper.get("fields_of_study") or []
    field_text = " ".join(str(item) for item in fields if isinstance(item, str))
    parts = (
        (_normalize_title(paper.get("title")), 4.0),
        (_safe_str(paper.get("abstract")), 2.5),
        (field_text, 3.0),
        (author_text, 0.3),
        (_safe_str(paper.get("venue")), 0.3),
    )
    weights: dict[str, float] = {}
    for text, weight in parts:
        for token in _tokens(text):
            weights[token] = max(weights.get(token, 0.0), weight)
    return weights


def _weighted_jaccard(left: dict[str, float], right: dict[str, float]) -> float:
    union = left.keys() | right.keys()
    if not union:
        return 0.0
    common = left.keys() & right.keys()
    numerator = sum(min(left[token], right[token]) for token in common)
    denominator = sum(max(left.get(token, 0.0), right.get(token, 0.0)) for token in union)
    return numerator / denominator if denominator else 0.0


def _title_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    a = _normalize_title(left.get("title")).casefold()
    b = _normalize_title(right.get("title")).casefold()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return _weighted_jaccard(
        {token: 1.0 for token in _tokens(a)},
        {token: 1.0 for token in _tokens(b)},
    )


def _semantic_similarity(seed: dict[str, Any], candidate: dict[str, Any]) -> float:
    return _clamp01(_weighted_jaccard(_weighted_tokens(seed), _weighted_tokens(candidate)))


def _freshness_score(year: int | None, ref_year: int) -> float:
    if year is None:
        return 0.0
    return _clamp01((year - (ref_year - 10)) / 10.0)


def _citation_score(count: int, max_count: int) -> float:
    if count <= 0 or max_count <= 0:
        return 0.0
    return _clamp01(math.log1p(count) / math.log1p(max_count))


def _provider_rank(index: int, total: int) -> float:
    if total <= 0:
        return 0.0
    if total == 1:
        return 1.0
    return _clamp01(1.0 - index / (total - 1))


def _seed_paper_ids(seeds: list[dict[str, Any]]) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for seed in seeds:
        paper_id = seed.get("paper_id")
        if isinstance(paper_id, int) and not isinstance(paper_id, bool) and paper_id > 0:
            if paper_id not in seen:
                seen.add(paper_id)
                ids.append(paper_id)
    return ids


def _candidate_key(paper: dict[str, Any]) -> tuple[str, str]:
    external_id = str(paper.get("external_id") or "").strip()
    doi = _normalize_doi(paper.get("doi")) or ""
    return external_id, doi


def _is_near_duplicate(candidate: dict[str, Any], seeds: list[dict[str, Any]]) -> bool:
    cand_doi = _normalize_doi(candidate.get("doi"))
    cand_eid = str(candidate.get("external_id") or "").strip()
    for seed in seeds:
        seed_eid = str(seed.get("external_id") or "").strip()
        if cand_eid and seed_eid and cand_eid == seed_eid:
            return True
        seed_doi = _normalize_doi(seed.get("doi"))
        if cand_doi and seed_doi and cand_doi == seed_doi:
            return True
        if _title_similarity(candidate, seed) >= _TITLE_DUP_THRESHOLD:
            return True
    return False


def _dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_eid: set[str] = set()
    seen_doi: set[str] = set()
    seen_title: set[str] = set()
    unique: list[dict[str, Any]] = []
    for paper in candidates:
        if not isinstance(paper, dict):
            continue
        eid, doi = _candidate_key(paper)
        title_key = _normalize_title(paper.get("title")).casefold()
        if eid and eid in seen_eid:
            continue
        if doi and doi in seen_doi:
            continue
        if title_key and title_key in seen_title:
            continue
        if eid:
            seen_eid.add(eid)
        if doi:
            seen_doi.add(doi)
        if title_key:
            seen_title.add(title_key)
        unique.append(paper)
    return unique


def _filter_candidates(
    candidates: list[dict[str, Any]],
    seeds: list[dict[str, Any]],
    negative_external_ids: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[dict[str, Any]]:
    negatives = {
        str(item).strip()
        for item in (negative_external_ids or [])
        if item is not None and str(item).strip()
    }
    filtered: list[dict[str, Any]] = []
    for paper in _dedupe_candidates(candidates if isinstance(candidates, list) else []):
        eid = str(paper.get("external_id") or "").strip()
        if eid and eid in negatives:
            continue
        if _is_near_duplicate(paper, seeds):
            continue
        year = _safe_int(paper.get("year"))
        if year_from is not None and (year is None or year < year_from):
            continue
        if year_to is not None and (year is None or year > year_to):
            continue
        filtered.append(paper)
    return filtered


def _common_keywords(seed: dict[str, Any], candidate: dict[str, Any], limit: int = 3) -> list[str]:
    left = _weighted_tokens(seed)
    right = _weighted_tokens(candidate)
    common = left.keys() & right.keys()
    ranked = sorted(common, key=lambda token: (-min(left[token], right[token]), -len(token), token))
    selected: list[str] = []
    for token in ranked:
        if any(token in existing or existing in token for existing in selected):
            continue
        selected.append(token)
        if len(selected) >= limit:
            break
    return selected


def _build_reasons(
    *,
    provider_rank: float,
    semantic: float,
    freshness: float,
    citation: float,
    seed: dict[str, Any] | None,
    candidate: dict[str, Any],
    multi_seed_hits: int = 0,
) -> list[str]:
    reasons: list[str] = []
    if provider_rank >= 0.6:
        reasons.append("外部平台相关性较高")
    elif provider_rank > 0:
        reasons.append("来自外部平台候选排序")
    if semantic >= 0.12 and seed is not None:
        keywords = _common_keywords(seed, candidate)
        if keywords:
            reasons.append(f"语义相近：共同主题 {('、'.join(keywords))}")
        else:
            reasons.append("与种子文献语义相近")
    elif semantic >= 0.12:
        reasons.append("与研究主题语义相近")
    if freshness >= 0.7 and _safe_int(candidate.get("year")) is not None:
        reasons.append(f"发表时间较新（{_safe_int(candidate.get('year'))}）")
    citation_count = candidate.get("citation_count")
    if citation >= 0.35 and isinstance(citation_count, int) and citation_count > 0:
        reasons.append(f"引用量较突出（{citation_count}）")
    if multi_seed_hits >= 2:
        reasons.append(f"与 {multi_seed_hits} 篇种子文献主题相关")
    if not reasons:
        reasons.append("综合排序得分靠前")
    return reasons


def _score_candidate(
    candidate: dict[str, Any],
    *,
    index: int,
    total: int,
    semantic: float,
    ref_year: int,
    max_citations: int,
    seed_for_reasons: dict[str, Any] | None,
    seed_ids: list[int],
    multi_seed_hits: int = 0,
) -> dict[str, Any]:
    provider_rank = _provider_rank(index, total)
    freshness = _freshness_score(_safe_int(candidate.get("year")), ref_year)
    citation_count = candidate.get("citation_count")
    citation = _citation_score(
        citation_count if isinstance(citation_count, int) and not isinstance(citation_count, bool) else 0,
        max_citations,
    )
    score = _clamp01(
        _PROVIDER_W * provider_rank
        + _SEMANTIC_W * semantic
        + _FRESHNESS_W * freshness
        + _CITATION_W * citation
    )
    return {
        "paper": candidate,
        "score": round(score, 6),
        "reasons": _build_reasons(
            provider_rank=provider_rank,
            semantic=semantic,
            freshness=freshness,
            citation=citation,
            seed=seed_for_reasons,
            candidate=candidate,
            multi_seed_hits=multi_seed_hits,
        ),
        "seed_paper_ids": list(seed_ids),
        "is_fallback": False,
    }


def _rank(
    candidates: list[dict[str, Any]],
    *,
    semantic_fn,
    seed_for_reasons: dict[str, Any] | None,
    seed_ids: list[int],
    limit: int,
    multi_seed_fn=None,
) -> dict[str, Any]:
    if limit <= 0 or not candidates:
        return {"items": []}
    years = [_safe_int(paper.get("year")) for paper in candidates]
    years = [year for year in years if year is not None]
    ref_year = max([_REF_YEAR, *years]) if years else _REF_YEAR
    citation_counts = [
        paper.get("citation_count")
        for paper in candidates
        if isinstance(paper.get("citation_count"), int)
        and not isinstance(paper.get("citation_count"), bool)
        and paper.get("citation_count") > 0
    ]
    max_citations = max(citation_counts) if citation_counts else 0
    total = len(candidates)
    scored: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        semantic = _clamp01(float(semantic_fn(candidate)))
        multi_hits = int(multi_seed_fn(candidate)) if multi_seed_fn else 0
        scored.append(
            _score_candidate(
                candidate,
                index=index,
                total=total,
                semantic=semantic,
                ref_year=ref_year,
                max_citations=max_citations,
                seed_for_reasons=seed_for_reasons,
                seed_ids=seed_ids,
                multi_seed_hits=multi_hits,
            )
        )
    scored.sort(
        key=lambda item: (
            -item["score"],
            str(item["paper"].get("external_id") or ""),
            _normalize_title(item["paper"].get("title")).casefold(),
        )
    )
    return {"items": scored[:limit]}


def recommend_by_paper(seed_paper: dict, candidates: list[dict], limit: int) -> dict:
    if not isinstance(seed_paper, dict):
        return {"items": []}
    try:
        limit_n = int(limit)
    except (TypeError, ValueError):
        return {"items": []}
    seeds = [seed_paper]
    filtered = _filter_candidates(candidates, seeds)
    return _rank(
        filtered,
        semantic_fn=lambda paper: _semantic_similarity(seed_paper, paper),
        seed_for_reasons=seed_paper,
        seed_ids=_seed_paper_ids(seeds),
        limit=limit_n,
    )


def recommend_for_library(
    seed_papers: list[dict],
    candidates: list[dict],
    negative_external_ids: list[str],
    limit: int,
) -> dict:
    if not isinstance(seed_papers, list) or not seed_papers:
        return {"items": []}
    seeds = [paper for paper in seed_papers if isinstance(paper, dict)][:5]
    if not seeds:
        return {"items": []}
    try:
        limit_n = int(limit)
    except (TypeError, ValueError):
        return {"items": []}
    negatives = negative_external_ids if isinstance(negative_external_ids, list) else []
    filtered = _filter_candidates(candidates, seeds, negatives)

    def semantic_fn(paper: dict[str, Any]) -> float:
        scores = [_semantic_similarity(seed, paper) for seed in seeds]
        return sum(scores) / len(scores) if scores else 0.0

    def multi_seed_fn(paper: dict[str, Any]) -> int:
        return sum(1 for seed in seeds if _semantic_similarity(seed, paper) >= 0.12)

    return _rank(
        filtered,
        semantic_fn=semantic_fn,
        seed_for_reasons=seeds[0],
        seed_ids=_seed_paper_ids(seeds),
        limit=limit_n,
        multi_seed_fn=multi_seed_fn,
    )


def recommend_by_topic(
    topic: str,
    candidates: list[dict],
    year_from: int | None,
    year_to: int | None,
    limit: int,
) -> dict:
    topic_text = _safe_str(topic)
    if not topic_text:
        return {"items": []}
    try:
        limit_n = int(limit)
    except (TypeError, ValueError):
        return {"items": []}
    year_from_n = _safe_int(year_from)
    year_to_n = _safe_int(year_to)
    topic_seed = {
        "title": topic_text,
        "abstract": topic_text,
        "fields_of_study": [topic_text],
        "authors": [],
        "venue": None,
    }
    filtered = _filter_candidates(
        candidates,
        seeds=[],
        year_from=year_from_n,
        year_to=year_to_n,
    )
    return _rank(
        filtered,
        semantic_fn=lambda paper: _semantic_similarity(topic_seed, paper),
        seed_for_reasons=None,
        seed_ids=[],
        limit=limit_n,
    )
