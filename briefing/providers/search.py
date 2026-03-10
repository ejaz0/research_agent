from __future__ import annotations

from typing import Protocol

from ..domain.models import SearchResult


class SearchError(RuntimeError):
    """Raised when search results cannot be collected."""


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int) -> list[SearchResult]:
        """Return search results for the query."""


class SerpApiSearchProvider:
    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def search(self, query: str, max_results: int) -> list[SearchResult]:
        if not self.api_key:
            raise SearchError("SERPAPI_KEY is not configured.")

        from serpapi import GoogleSearch

        search = GoogleSearch(
            {
                "q": query,
                "api_key": self.api_key,
                "num": max_results,
            }
        )
        payload = search.get_dict()

        if payload.get("error"):
            raise SearchError(str(payload["error"]))

        results: list[SearchResult] = []
        for raw in payload.get("organic_results", [])[:max_results]:
            url = raw.get("link")
            if not url:
                continue

            results.append(
                SearchResult(
                    title=raw.get("title", "Untitled result"),
                    url=url,
                    snippet=raw.get("snippet", ""),
                )
            )

        return results
