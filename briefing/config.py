from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    anthropic_api_key: str | None
    serpapi_api_key: str | None
    anthropic_model: str
    max_search_results: int
    request_timeout_seconds: int
    max_document_chars: int
    conversation_db_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            anthropic_api_key=os.getenv("CLAUDE_API_KEY"),
            serpapi_api_key=os.getenv("SERPAPI_KEY"),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
            max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", "5")),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
            max_document_chars=int(os.getenv("MAX_DOCUMENT_CHARS", "6000")),
            conversation_db_path=Path(
                os.getenv(
                    "CONVERSATION_DB_PATH",
                    _PROJECT_ROOT / "data" / "research_agent.sqlite3",
                )
            ),
        )
