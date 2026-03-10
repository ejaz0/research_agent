from __future__ import annotations

from ..config import Settings
from ..domain.models import ResearchReport, SourceFailure
from ..providers.fetch import DocumentFetcher, FetchError, RequestsDocumentFetcher
from ..providers.llm import AnthropicResearchWriter, LLMError, ResearchWriter, derive_key_findings
from ..providers.search import SearchProvider, SerpApiSearchProvider


class ResearchPipeline:
    def __init__(
        self,
        search_provider: SearchProvider,
        fetcher: DocumentFetcher,
        writer: ResearchWriter,
        max_search_results: int,
    ):
        self.search_provider = search_provider
        self.fetcher = fetcher
        self.writer = writer
        self.max_search_results = max_search_results

    def run(self, query: str) -> ResearchReport:
        query = query.strip()
        if not query:
            raise ValueError("The research query cannot be empty.")

        search_results = self.search_provider.search(query, self.max_search_results)
        if not search_results:
            return ResearchReport(
                query=query,
                executive_summary="No search results were returned for this query.",
            )

        source_summaries = []
        failures: list[SourceFailure] = []

        for result in search_results:
            try:
                document = self.fetcher.fetch(result)
                source_summaries.append(self.writer.summarize_source(document))
            except (FetchError, LLMError) as exc:
                failures.append(
                    SourceFailure(
                        title=result.title,
                        url=result.url,
                        error=str(exc),
                    )
                )

        if not source_summaries:
            return ResearchReport(
                query=query,
                executive_summary=(
                    "The report could not be generated because every fetched source failed."
                ),
                failures=failures,
            )

        try:
            executive_summary, key_findings = self.writer.synthesize_report(
                query=query,
                source_summaries=source_summaries,
                failures=failures,
            )
        except LLMError as exc:
            failures.append(SourceFailure(title="Synthesis stage", url="", error=str(exc)))
            executive_summary = (
                "Compiled from the surviving source summaries below because the final "
                "synthesis step failed."
            )
            key_findings = derive_key_findings(source_summaries)

        return ResearchReport(
            query=query,
            executive_summary=executive_summary,
            key_findings=key_findings,
            source_summaries=source_summaries,
            failures=failures,
        )


def build_default_pipeline(
    settings: Settings | None = None,
    *,
    max_search_results: int | None = None,
) -> ResearchPipeline:
    settings = settings or Settings.from_env()
    return ResearchPipeline(
        search_provider=SerpApiSearchProvider(settings.serpapi_api_key),
        fetcher=RequestsDocumentFetcher(
            timeout_seconds=settings.request_timeout_seconds,
            max_document_chars=settings.max_document_chars,
        ),
        writer=AnthropicResearchWriter(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        ),
        max_search_results=max_search_results or settings.max_search_results,
    )


def research_agent(query: str) -> str:
    return build_default_pipeline().run(query).to_markdown()
