from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from ..domain.models import Conversation, ConversationMessage, ResearchReport


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationStore:
    def __init__(self):
        self._lock = Lock()
        self._conversations: dict[str, Conversation] = {}

    def list_conversations(self) -> list[Conversation]:
        with self._lock:
            items = [deepcopy(item) for item in self._conversations.values()]

        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    def create_conversation(self, title: str | None = None) -> Conversation:
        now = _timestamp()
        conversation = Conversation(
            id=uuid4().hex,
            title=title or "New Conversation",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._conversations[conversation.id] = conversation
        return deepcopy(conversation)

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._lock:
            conversation = self._conversations.get(conversation_id)
            return deepcopy(conversation) if conversation else None

    def append_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        report: ResearchReport | None = None,
    ) -> ConversationMessage:
        with self._lock:
            conversation = self._conversations[conversation_id]
            now = _timestamp()
            message = ConversationMessage(
                id=uuid4().hex,
                role=role,
                content=content,
                created_at=now,
                report=replace(report) if report else None,
            )
            conversation.messages.append(message)
            conversation.updated_at = now
            if role == "user" and conversation.title == "New Conversation":
                conversation.title = content[:72].strip() or conversation.title
            stored = deepcopy(message)

        return stored
