import unittest

from briefing.core.agent import ResearchPipeline
from briefing.domain.models import Document, SearchResult, SourceSummary
from briefing.providers.fetch import FetchError


class FakeSearchProvider:
    def search(self, query: str, max_results: int) -> list[SearchResult]:
        return [
            SearchResult(title="Healthy Source", url="https://good.example"),
            SearchResult(title="Broken Source", url="https://bad.example"),
        ][:max_results]


class FakeFetcher:
    def fetch(self, result: SearchResult) -> Document:
        if "bad.example" in result.url:
            raise FetchError("HTTP 403 while fetching the page.")

        return Document(
            title=result.title,
            url=result.url,
            text="This source says the product now handles citations correctly.",
        )


class FakeWriter:
    def summarize_source(self, document: Document) -> SourceSummary:
        return SourceSummary(
            title=document.title,
            url=document.url,
            summary="The product now handles citations correctly.",
        )

    def synthesize_report(self, query, source_summaries, failures):
        return (
            "The pipeline produced a valid report from the surviving sources.",
            ["The product now handles citations correctly."],
        )


class ResearchPipelineTests(unittest.TestCase):
    def test_pipeline_keeps_partial_failures_out_of_source_summaries(self):
        pipeline = ResearchPipeline(
            search_provider=FakeSearchProvider(),
            fetcher=FakeFetcher(),
            writer=FakeWriter(),
            max_search_results=5,
        )

        report = pipeline.run("What changed?")

        self.assertEqual(report.executive_summary, "The pipeline produced a valid report from the surviving sources.")
        self.assertEqual(len(report.source_summaries), 1)
        self.assertEqual(report.source_summaries[0].url, "https://good.example")
        self.assertEqual(len(report.failures), 1)
        self.assertIn("HTTP 403", report.failures[0].error)


if __name__ == "__main__":
    unittest.main()
