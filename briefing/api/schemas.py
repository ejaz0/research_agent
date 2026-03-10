from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Research question to investigate.")
    max_sources: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional override for the number of search results to process.",
    )
    include_markdown: bool = Field(
        default=False,
        description="Include the Markdown rendering of the report in the response.",
    )


class SourceSummaryResponse(BaseModel):
    title: str
    url: str
    summary: str


class SourceFailureResponse(BaseModel):
    title: str
    url: str
    error: str


class ResearchResponse(BaseModel):
    query: str
    executive_summary: str
    key_findings: list[str]
    source_summaries: list[SourceSummaryResponse]
    failures: list[SourceFailureResponse]
    markdown: str | None = None


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class ChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, description="Message to send to the research agent.")
    max_sources: int | None = Field(default=None, ge=1, le=10)
    include_markdown: bool = Field(default=False)


class ConversationMessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant", "error"]
    content: str
    created_at: str
    report: ResearchResponse | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[ConversationMessageResponse]


class ConversationSummaryResponse(BaseModel):
    id: str
    title: str
    updated_at: str
    last_message_excerpt: str


class HealthResponse(BaseModel):
    status: str
