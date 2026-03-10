import unittest
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from briefing.api.app import create_app
from briefing.domain.models import ResearchReport, SourceFailure, SourceSummary
from briefing.memory import ConversationStore
from briefing.providers.search import SearchError


class FakePipeline:
    def run(self, query: str, conversation_history=None) -> ResearchReport:
        return ResearchReport(
            query=query,
            executive_summary="The API returned a structured research brief.",
            key_findings=["The system exposes the same pipeline over HTTP."],
            source_summaries=[
                SourceSummary(
                    title="Example Source",
                    url="https://example.com",
                    summary="Example summary.",
                )
            ],
            failures=[
                SourceFailure(
                    title="Blocked Source",
                    url="https://blocked.example",
                    error="HTTP 403 while fetching the page.",
                )
            ],
        )


class ErrorPipeline:
    def run(self, query: str, conversation_history=None) -> ResearchReport:
        raise SearchError("Search backend is unavailable.")


class RecordingPipelineFactory:
    def __init__(self):
        self.calls = []

    def __call__(self, max_sources=None):
        calls = self.calls

        class Pipeline:
            def run(self, query: str, conversation_history=None) -> ResearchReport:
                calls.append(
                    {
                        "query": query,
                        "history_roles": [item.role for item in conversation_history or []],
                    }
                )
                return ResearchReport(
                    query=query,
                    executive_summary=f"Handled: {query}",
                )

        return Pipeline()


class ApiTests(unittest.TestCase):
    def make_client(self, pipeline_factory):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        store = ConversationStore(Path(temp_dir.name) / "api.sqlite3")
        self.addCleanup(store.close)
        app = create_app(pipeline_factory, conversation_store=store)
        return TestClient(app)

    def test_root_serves_chat_ui(self):
        client = self.make_client(lambda max_sources=None: FakePipeline())

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])

    def test_health_endpoint(self):
        client = self.make_client(lambda max_sources=None: FakePipeline())

        response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_research_endpoint_returns_report_payload(self):
        client = self.make_client(lambda max_sources=None: FakePipeline())

        response = client.post(
            "/api/research",
            json={
                "query": "How does the API work?",
                "max_sources": 3,
                "include_markdown": True,
            },
        )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["query"], "How does the API work?")
        self.assertEqual(payload["executive_summary"], "The API returned a structured research brief.")
        self.assertEqual(payload["key_findings"], ["The system exposes the same pipeline over HTTP."])
        self.assertEqual(payload["source_summaries"][0]["title"], "Example Source")
        self.assertIn("# Research Brief", payload["markdown"])

    def test_research_endpoint_maps_pipeline_errors_to_bad_request(self):
        client = self.make_client(lambda max_sources=None: ErrorPipeline())

        response = client.post("/api/research", json={"query": "fail please"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Search backend is unavailable."})

    def test_conversation_message_flow_persists_history_and_returns_assistant_reply(self):
        factory = RecordingPipelineFactory()
        client = self.make_client(factory)

        created = client.post("/api/conversations", json={})
        conversation_id = created.json()["id"]

        first = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": "tell me about the current war in iran"},
        )
        second = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": "what about casualties"},
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        payload = second.json()
        self.assertEqual(len(payload["messages"]), 4)
        self.assertEqual(payload["messages"][-1]["role"], "assistant")
        self.assertEqual(factory.calls[0]["history_roles"], [])
        self.assertEqual(factory.calls[1]["history_roles"], ["user", "assistant"])

    def test_conversations_persist_across_app_instances_when_using_same_db(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "shared.sqlite3"
            store_one = ConversationStore(db_path)
            client_one = TestClient(
                create_app(lambda max_sources=None: FakePipeline(), conversation_store=store_one)
            )

            created = client_one.post("/api/conversations", json={})
            conversation_id = created.json()["id"]
            client_one.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": "tell me about iran"},
            )
            store_one.close()

            store_two = ConversationStore(db_path)
            self.addCleanup(store_two.close)
            client_two = TestClient(
                create_app(lambda max_sources=None: FakePipeline(), conversation_store=store_two)
            )

            loaded = client_two.get(f"/api/conversations/{conversation_id}")

            self.assertEqual(loaded.status_code, 200)
            self.assertEqual(len(loaded.json()["messages"]), 2)


if __name__ == "__main__":
    unittest.main()
