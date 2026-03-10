from __future__ import annotations

import json
import re
from typing import Any, Iterable, Protocol

from ..domain.models import Document, SourceFailure, SourceSummary


class LLMError(RuntimeError):
    """Raised when the language model interaction fails."""


class ResearchWriter(Protocol):
    def summarize_source(self, document: Document) -> SourceSummary:
        """Create a summary for a single document."""

    def synthesize_report(
        self,
        query: str,
        source_summaries: list[SourceSummary],
        failures: list[SourceFailure],
    ) -> tuple[str, list[str]]:
        """Create the executive summary and key findings."""


def extract_text_from_content_blocks(blocks: Iterable[Any]) -> str:
    parts: list[str] = []
    for block in blocks:
        text = None
        if isinstance(block, str):
            text = block
        elif isinstance(block, dict):
            text = block.get("text") or block.get("content")
        else:
            text = getattr(block, "text", None)

        if isinstance(text, str):
            text = text.strip()
            if text:
                parts.append(text)

    if not parts:
        raise LLMError("The model response did not contain any text blocks.")

    return "\n".join(parts)


def _parse_structured_report(text: str) -> tuple[str, list[str]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("The model returned invalid JSON for the report synthesis step.") from exc

    executive_summary = str(payload.get("executive_summary", "")).strip()
    if not executive_summary:
        raise LLMError("The synthesis response did not include an executive summary.")

    raw_findings = payload.get("key_findings", [])
    if not isinstance(raw_findings, list):
        raise LLMError("The synthesis response did not include a findings list.")

    findings = [str(item).strip() for item in raw_findings if str(item).strip()]
    return executive_summary, findings


def derive_key_findings(source_summaries: list[SourceSummary], limit: int = 5) -> list[str]:
    findings: list[str] = []
    for item in source_summaries:
        text = item.summary.replace("\n", " ").strip()
        if not text:
            continue

        sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
        findings.append(sentence or text)
        if len(findings) == limit:
            break

    return findings


class AnthropicResearchWriter:
    def __init__(self, api_key: str | None, model: str):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise LLMError("CLAUDE_API_KEY is not configured.")

        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.api_key)

        return self._client

    def _create_message(self, prompt: str, max_tokens: int):
        client = self._get_client()
        return client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

    def summarize_source(self, document: Document) -> SourceSummary:
        prompt = (
            "Summarize the following source for a research brief.\n"
            "Keep it to 4-6 sentences, focus on concrete facts, and avoid filler.\n\n"
            f"Title: {document.title}\n"
            f"URL: {document.url}\n\n"
            f"{document.text}"
        )
        response = self._create_message(prompt, max_tokens=250)
        summary = extract_text_from_content_blocks(response.content)
        return SourceSummary(title=document.title, url=document.url, summary=summary)

    def synthesize_report(
        self,
        query: str,
        source_summaries: list[SourceSummary],
        failures: list[SourceFailure],
    ) -> tuple[str, list[str]]:
        source_section = "\n\n".join(
            [
                (
                    f"Source {index + 1}\n"
                    f"Title: {item.title}\n"
                    f"URL: {item.url}\n"
                    f"Summary: {item.summary}"
                )
                for index, item in enumerate(source_summaries)
            ]
        )
        failure_section = "\n".join(
            f"- {item.title} ({item.url}): {item.error}" for item in failures
        ) or "- None"

        prompt = (
            "You are compiling a research brief from source summaries.\n"
            f"Research question: {query}\n\n"
            "Available source summaries:\n"
            f"{source_section}\n\n"
            "Fetch or processing failures:\n"
            f"{failure_section}\n\n"
            "Return strict JSON only with this schema:\n"
            '{"executive_summary": "2-4 sentence answer", "key_findings": ["finding 1", "finding 2", "finding 3"]}\n'
            "Each finding must be grounded in the provided summaries."
        )
        response = self._create_message(prompt, max_tokens=350)
        text = extract_text_from_content_blocks(response.content)
        return _parse_structured_report(text)
