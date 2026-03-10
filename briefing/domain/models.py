from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""


@dataclass(frozen=True, slots=True)
class Document:
    title: str
    url: str
    text: str


@dataclass(frozen=True, slots=True)
class SourceSummary:
    title: str
    url: str
    summary: str


@dataclass(frozen=True, slots=True)
class SourceFailure:
    title: str
    url: str
    error: str


@dataclass(slots=True)
class ResearchReport:
    query: str
    executive_summary: str
    key_findings: list[str] = field(default_factory=list)
    source_summaries: list[SourceSummary] = field(default_factory=list)
    failures: list[SourceFailure] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "# Research Brief",
            "",
            f"Query: {self.query}",
            "",
            "## Executive Summary",
            "",
            self.executive_summary.strip(),
            "",
        ]

        if self.key_findings:
            lines.extend(["## Key Findings", ""])
            lines.extend(f"- {finding}" for finding in self.key_findings)
            lines.append("")

        if self.source_summaries:
            lines.extend(["## Source Summaries", ""])
            for item in self.source_summaries:
                lines.extend(
                    [
                        f"### {item.title}",
                        f"- URL: {item.url}",
                        f"- Summary: {item.summary.strip()}",
                        "",
                    ]
                )

        if self.failures:
            lines.extend(["## Retrieval Issues", ""])
            for failure in self.failures:
                lines.append(f"- {failure.title} ({failure.url}): {failure.error}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "executive_summary": self.executive_summary,
            "key_findings": list(self.key_findings),
            "source_summaries": [
                {"title": item.title, "url": item.url, "summary": item.summary}
                for item in self.source_summaries
            ],
            "failures": [
                {"title": item.title, "url": item.url, "error": item.error}
                for item in self.failures
            ],
        }
