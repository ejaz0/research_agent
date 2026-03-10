from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from threading import Lock
from uuid import uuid4

from ..domain.models import (
    Conversation,
    ConversationMessage,
    ResearchReport,
    SourceFailure,
    SourceSummary,
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationStore:
    def __init__(self, db_path: str | Path):
        self._lock = Lock()
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    report_json TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
                ON conversations(updated_at DESC);

                CREATE INDEX IF NOT EXISTS idx_messages_conversation_created_at
                ON messages(conversation_id, created_at ASC);
                """
            )

    def close(self) -> None:
        with self._lock:
            if self._connection is None:
                return
            self._connection.close()
            self._connection = None

    def _report_to_json(self, report: ResearchReport | None) -> str | None:
        if report is None:
            return None
        return json.dumps(report.to_dict())

    def _report_from_json(self, payload: str | None) -> ResearchReport | None:
        if not payload:
            return None

        data = json.loads(payload)
        return ResearchReport(
            query=data["query"],
            executive_summary=data["executive_summary"],
            key_findings=list(data.get("key_findings", [])),
            source_summaries=[SourceSummary(**item) for item in data.get("source_summaries", [])],
            failures=[SourceFailure(**item) for item in data.get("failures", [])],
        )

    def _message_from_row(self, row: sqlite3.Row) -> ConversationMessage:
        return ConversationMessage(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
            report=self._report_from_json(row["report_json"]),
        )

    def _load_messages(self, conversation_id: str) -> list[ConversationMessage]:
        rows = self._connection.execute(
            """
            SELECT id, role, content, created_at, report_json
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC, rowid ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [self._message_from_row(row) for row in rows]

    def list_conversations(self) -> list[Conversation]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC, created_at DESC
                """
            ).fetchall()
            return [
                Conversation(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    messages=self._load_messages(row["id"]),
                )
                for row in rows
            ]

    def create_conversation(self, title: str | None = None) -> Conversation:
        now = _timestamp()
        conversation = Conversation(
            id=uuid4().hex,
            title=title or "New Conversation",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO conversations (id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        conversation.id,
                        conversation.title,
                        conversation.created_at,
                        conversation.updated_at,
                    ),
                )
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                WHERE id = ?
                """,
                (conversation_id,),
            ).fetchone()
            if row is None:
                return None

            return Conversation(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                messages=self._load_messages(conversation_id),
            )

    def append_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        report: ResearchReport | None = None,
    ) -> ConversationMessage:
        with self._lock:
            now = _timestamp()
            row = self._connection.execute(
                "SELECT title FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise KeyError(conversation_id)

            next_title = row["title"]
            if role == "user" and next_title == "New Conversation":
                next_title = content[:72].strip() or next_title

            message = ConversationMessage(
                id=uuid4().hex,
                role=role,
                content=content,
                created_at=now,
                report=report,
            )
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, created_at, report_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        message.id,
                        conversation_id,
                        message.role,
                        message.content,
                        message.created_at,
                        self._report_to_json(report),
                    ),
                )
                self._connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (next_title, now, conversation_id),
                )

        return message
