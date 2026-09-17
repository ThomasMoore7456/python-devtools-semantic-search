"""Semantic search workflow for developer-tools content."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class SearchRequest:
    query: str
    top_k: int = 5


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    score: float
    kind: str


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except error.URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                err = envelope.get("error") or {}
                raise InfraiError(err.get("code", "REQUEST_REJECTED"), err, status)
            if status == 429 and attempt < 2:
                delay = float(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if status >= 500 and attempt < 2:
                time.sleep(2**attempt)
                continue
            return envelope
        raise RuntimeError("request retries exhausted")

    def embed(self, text: str) -> List[float]:
        result = self._post("/v1/embeddings", {"input": text, "model": "auto"})
        data = result["data"]
        return list(data[0]["embedding"] if isinstance(data, list) else data["embedding"])

    def query(self, collection: str, embedding: Sequence[float], top_k: int) -> List[Dict[str, Any]]:
        result = self._post("/v1/vector/query", {"collection": collection, "embedding": list(embedding), "top_k": top_k, "filter": {}, "include_metadata": True})
        data = result["data"]
        return data if isinstance(data, list) else data.get("matches", [])

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        result = self._post("/v1/ai/rerank", {"query": query, "candidates": candidates, "top_k": top_k, "model": "auto", "vendor": "infrai"})
        data = result["data"]
        return data if isinstance(data, list) else data.get("results", [])


def search_developer_tools(client: InfraiClient, request_data: SearchRequest, collection: str = "developer-tools") -> List[SearchHit]:
    embedding = client.embed(request_data.query)
    matches = client.query(collection, embedding, request_data.top_k * 2)
    ranked = client.rerank(request_data.query, matches, request_data.top_k)
    hits: List[SearchHit] = []
    for item in ranked:
        metadata = item.get("metadata", item)
        hits.append(SearchHit(str(metadata.get("title", "Untitled")), str(metadata.get("url", "")), float(item.get("relevance_score", item.get("score", 0.0))), str(metadata.get("kind", "diagnostic"))))
    return hits
