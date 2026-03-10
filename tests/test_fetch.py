import unittest
from unittest.mock import Mock

import requests

from briefing.domain.models import SearchResult
from briefing.providers.fetch import DEFAULT_HEADERS, FetchError, RequestsDocumentFetcher


class RequestsDocumentFetcherTests(unittest.TestCase):
    def test_fetch_uses_browser_headers_and_extracts_main_content(self):
        response = Mock()
        response.headers = {"Content-Type": "text/html; charset=utf-8"}
        response.text = (
            "<html><body><nav>Menu</nav><main><h1>OpenAI</h1>"
            "<p>Research lab building models.</p></main></body></html>"
        )
        response.raise_for_status.return_value = None

        session = Mock()
        session.get.return_value = response

        fetcher = RequestsDocumentFetcher(session=session, timeout_seconds=7, max_document_chars=500)
        result = fetcher.fetch(SearchResult(title="OpenAI", url="https://example.com"))

        session.get.assert_called_once_with(
            "https://example.com",
            headers=DEFAULT_HEADERS,
            timeout=7,
        )
        self.assertEqual(result.title, "OpenAI")
        self.assertEqual(result.text, "OpenAI Research lab building models.")

    def test_fetch_raises_fetch_error_for_http_failures(self):
        response = Mock()
        response.headers = {"Content-Type": "text/html; charset=utf-8"}
        response.status_code = 403
        response.raise_for_status.side_effect = requests.HTTPError(response=response)

        session = Mock()
        session.get.return_value = response

        fetcher = RequestsDocumentFetcher(session=session)

        with self.assertRaises(FetchError) as ctx:
            fetcher.fetch(SearchResult(title="Blocked", url="https://blocked.example"))

        self.assertIn("HTTP 403", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
