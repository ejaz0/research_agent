from __future__ import annotations

from collections.abc import Callable
from html import escape
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..config import Settings
from ..core.agent import ResearchPipeline, build_default_pipeline
from ..domain.models import Conversation, ConversationMessage, ResearchReport
from ..memory import ConversationStore
from ..providers.search import SearchError
from .schemas import (
    ChatMessageRequest,
    ConversationCreateRequest,
    ConversationMessageResponse,
    ConversationResponse,
    ConversationSummaryResponse,
    HealthResponse,
    ResearchRequest,
    ResearchResponse,
)

PipelineFactory = Callable[[int | None], ResearchPipeline]


def default_pipeline_factory(max_sources: int | None = None) -> ResearchPipeline:
    settings = Settings.from_env()
    return build_default_pipeline(settings, max_search_results=max_sources)


def _serialize_report(report: ResearchReport, include_markdown: bool) -> dict[str, Any]:
    payload = report.to_dict()
    payload["markdown"] = report.to_markdown() if include_markdown else None
    return payload


def _serialize_message(
    message: ConversationMessage,
    *,
    include_markdown: bool,
) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
        "report": _serialize_report(message.report, include_markdown) if message.report else None,
    }


def _serialize_conversation(
    conversation: Conversation,
    *,
    include_markdown: bool,
) -> dict[str, Any]:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [
            _serialize_message(item, include_markdown=include_markdown)
            for item in conversation.messages
        ],
    }


def _serialize_conversation_summary(conversation: Conversation) -> dict[str, Any]:
    last_message = conversation.messages[-1].content if conversation.messages else ""
    return {
        "id": conversation.id,
        "title": conversation.title,
        "updated_at": conversation.updated_at,
        "last_message_excerpt": last_message[:120],
    }


def _frontend_not_built_response(frontend_dist: Path) -> HTMLResponse:
    content = f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Research Agent Frontend</title>
        <style>
          body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: linear-gradient(180deg, #f7f2ea 0%, #efe8dc 100%);
            color: #182225;
          }}
          main {{
            max-width: 720px;
            margin: 24px;
            padding: 28px;
            border-radius: 24px;
            background: rgba(255, 250, 243, 0.9);
            border: 1px solid rgba(24, 34, 37, 0.1);
            box-shadow: 0 18px 60px rgba(20, 27, 28, 0.08);
          }}
          code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          }}
        </style>
      </head>
      <body>
        <main>
          <h1>Research Agent Frontend</h1>
          <p>The backend is running, but the React frontend has not been built yet.</p>
          <p>Run <code>cd frontend && npm install && npm run build</code>, then refresh this page.</p>
          <p>Expected build directory: <code>{escape(str(frontend_dist))}</code></p>
        </main>
      </body>
    </html>
    """
    return HTMLResponse(content=content)


def create_app(pipeline_factory: PipelineFactory | None = None) -> FastAPI:
    project_root = Path(__file__).resolve().parents[2]
    frontend_dist = project_root / "frontend" / "dist"
    assets_dir = frontend_dist / "assets"
    app = FastAPI(
        title="Research Agent API",
        version="0.1.0",
        description="HTTP wrapper around the research brief pipeline.",
    )
    app.state.pipeline_factory = pipeline_factory or default_pipeline_factory
    app.state.conversation_store = ConversationStore()
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False, response_model=None)
    def serve_frontend():
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return _frontend_not_built_response(frontend_dist)

    @app.get("/health", response_model=HealthResponse)
    @app.get("/api/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post("/research", response_model=ResearchResponse)
    @app.post("/api/research", response_model=ResearchResponse)
    def run_research(payload: ResearchRequest, request: Request) -> ResearchResponse:
        factory: PipelineFactory = request.app.state.pipeline_factory

        try:
            pipeline = factory(payload.max_sources)
            report = pipeline.run(payload.query)
        except (SearchError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return ResearchResponse.model_validate(
            _serialize_report(report, include_markdown=payload.include_markdown)
        )

    @app.get(
        "/api/conversations",
        response_model=list[ConversationSummaryResponse],
    )
    def list_conversations(request: Request) -> list[ConversationSummaryResponse]:
        store: ConversationStore = request.app.state.conversation_store
        return [
            ConversationSummaryResponse.model_validate(_serialize_conversation_summary(item))
            for item in store.list_conversations()
        ]

    @app.post(
        "/api/conversations",
        response_model=ConversationResponse,
        status_code=201,
    )
    def create_conversation(
        payload: ConversationCreateRequest,
        request: Request,
    ) -> ConversationResponse:
        store: ConversationStore = request.app.state.conversation_store
        conversation = store.create_conversation(title=payload.title)
        return ConversationResponse.model_validate(
            _serialize_conversation(conversation, include_markdown=False)
        )

    @app.get(
        "/api/conversations/{conversation_id}",
        response_model=ConversationResponse,
    )
    def get_conversation(conversation_id: str, request: Request) -> ConversationResponse:
        store: ConversationStore = request.app.state.conversation_store
        conversation = store.get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        return ConversationResponse.model_validate(
            _serialize_conversation(conversation, include_markdown=True)
        )

    @app.post(
        "/api/conversations/{conversation_id}/messages",
        response_model=ConversationResponse,
    )
    def send_message(
        conversation_id: str,
        payload: ChatMessageRequest,
        request: Request,
    ) -> ConversationResponse:
        store: ConversationStore = request.app.state.conversation_store
        conversation = store.get_conversation(conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        prior_history = list(conversation.messages)
        store.append_message(conversation_id, role="user", content=payload.content)

        factory: PipelineFactory = request.app.state.pipeline_factory
        try:
            pipeline = factory(payload.max_sources)
            report = pipeline.run(payload.content, conversation_history=prior_history)
            store.append_message(
                conversation_id,
                role="assistant",
                content=report.executive_summary,
                report=report,
            )
        except (SearchError, ValueError) as exc:
            store.append_message(conversation_id, role="error", content=str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        updated = store.get_conversation(conversation_id)
        return ConversationResponse.model_validate(
            _serialize_conversation(updated, include_markdown=payload.include_markdown)
        )

    return app


app = create_app()
