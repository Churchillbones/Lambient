from __future__ import annotations

import logging
import re
from typing import List

import bleach

logger = logging.getLogger("ambient_scribe")


def sanitize_input(user_input: str) -> str:
    """Return HTML-sanitized *user_input* (stripped of tags)."""
    return bleach.clean(user_input, tags=[], strip=True)


def semantic_chunking(text: str, max_tokens: int = 1000, min_chunk_size: int = 200) -> List[str]:
    """Split *text* into semantic chunks smaller than *max_tokens*."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    for sent in sentences:
        sent_len = len(sent) // 4  # rough token approximation
        if cur_len + sent_len > max_tokens and cur_len >= min_chunk_size:
            chunks.append(" ".join(cur))
            cur, cur_len = [sent], sent_len
        else:
            cur.append(sent)
            cur_len += sent_len
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def find_similar_chunks(chunks: List[str], embedding_service, target_index: int, top_k: int = 2) -> List[int]:
    """Return indices of *top_k* chunks most similar to *target_index*."""
    if embedding_service is None:
        logger.warning("Embedding service not available – cannot find similar chunks")
        return []

    embeddings = embedding_service.get_batch_embeddings(chunks)
    tgt_vec = embeddings[target_index]
    sims: list[tuple[int, float]] = []
    for i, vec in enumerate(embeddings):
        if i == target_index:
            continue
        sims.append((i, embedding_service.cosine_similarity(tgt_vec, vec)))
    sims.sort(key=lambda t: t[1], reverse=True)
    return [i for i, _ in sims[:top_k]]


def cluster_by_topic(chunks: List[str], embedding_service, num_clusters: int = 5):
    """Group *chunks* into up to *num_clusters* clusters using embeddings."""
    if embedding_service is None:
        logger.warning("Embedding service not available – cannot cluster chunks")
        return {}

    embeddings = embedding_service.get_batch_embeddings(chunks)
    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=min(num_clusters, len(chunks)), random_state=42)
    labels = kmeans.fit_predict(embeddings)
    clusters: dict[int, list[int]] = {}
    for idx, lbl in enumerate(labels):
        clusters.setdefault(lbl, []).append(idx)
    return clusters 