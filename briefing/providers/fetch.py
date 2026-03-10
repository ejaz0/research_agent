from __future__ import annotations

import re
from typing import Protocol

import requests
from bs4 import BeautifulSoup

from ..domain.models import Document, SearchResult


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_REMOVE_TAGS = ("script", "style", "noscript", "svg", "header", "footer", "nav", "aside")


class FetchError(RuntimeError):
    """Raised when a document cannot be fetched or extracted."""


class DocumentFetcher(Protocol):
    def fetch(self, result: SearchResult) -> Document:
        """Fetch a readable document for a search result."""


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_readable_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag_name in _REMOVE_TAGS:
        for node in soup.find_all(tag_name):
            node.decompose()

    container = soup.find("main") or soup.find("article") or soup.body or soup
    text = " ".join(container.stripped_strings)
    return _normalize_whitespace(text)


class RequestsDocumentFetcher:
    def __init__(
        self,
        timeout_seconds: int = 10,
        max_document_chars: int = 6000,
        session: requests.Session | None = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.max_document_chars = max_document_chars
        self.session = session or requests.Session()

    def fetch(self, result: SearchResult) -> Document:
        response = None
        try:
            response = self.session.get(
                result.url,
                headers=DEFAULT_HEADERS,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None) or getattr(
                response, "status_code", "unknown"
            )
            raise FetchError(f"HTTP {status_code} while fetching the page.") from exc
        except requests.RequestException as exc:
            raise FetchError(f"Request failed: {exc}") from exc

        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" in content_type:
            text = extract_readable_text(response.text)
        elif "text/plain" in content_type or not content_type:
            text = _normalize_whitespace(response.text)
        else:
            raise FetchError(f"Unsupported content type: {content_type}")

        if not text:
            raise FetchError("No readable text could be extracted from the page.")

        return Document(
            title=result.title,
            url=result.url,
            text=text[: self.max_document_chars],
        )
