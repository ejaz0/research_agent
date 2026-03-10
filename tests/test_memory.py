import tempfile
import unittest
from pathlib import Path

from briefing.domain.models import ResearchReport
from briefing.memory.store import ConversationStore


class ConversationStoreTests(unittest.TestCase):
    def test_store_persists_conversations_and_reports_across_instances(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "conversations.sqlite3"

            store = ConversationStore(db_path)
            conversation = store.create_conversation()
            store.append_message(
                conversation.id,
                role="user",
                content="tell me about iran",
            )
            store.append_message(
                conversation.id,
                role="assistant",
                content="Here is a summary.",
                report=ResearchReport(
                    query="tell me about iran",
                    executive_summary="Here is a summary.",
                    key_findings=["Finding one."],
                ),
            )
            store.close()

            reopened = ConversationStore(db_path)
            loaded = reopened.get_conversation(conversation.id)

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.title, "tell me about iran")
            self.assertEqual(len(loaded.messages), 2)
            self.assertEqual(loaded.messages[1].report.executive_summary, "Here is a summary.")
            reopened.close()


if __name__ == "__main__":
    unittest.main()
