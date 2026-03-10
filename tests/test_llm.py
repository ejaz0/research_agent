import unittest
from types import SimpleNamespace

from briefing.domain.models import SourceSummary
from briefing.providers.llm import LLMError, derive_key_findings, extract_text_from_content_blocks


class ContentExtractionTests(unittest.TestCase):
    def test_extract_text_from_sdk_blocks(self):
        blocks = [
            SimpleNamespace(text="First paragraph."),
            SimpleNamespace(text="Second paragraph."),
        ]

        text = extract_text_from_content_blocks(blocks)

        self.assertEqual(text, "First paragraph.\nSecond paragraph.")

    def test_extract_text_raises_when_blocks_have_no_text(self):
        with self.assertRaises(LLMError):
            extract_text_from_content_blocks([{"type": "tool_use"}])

    def test_derive_key_findings_uses_first_sentence_per_summary(self):
        summaries = [
            SourceSummary(
                title="One",
                url="https://one.example",
                summary="OpenAI launched a new release. It added more tooling.",
            ),
            SourceSummary(
                title="Two",
                url="https://two.example",
                summary="The company also expanded enterprise support.\nMore details followed.",
            ),
        ]

        findings = derive_key_findings(summaries)

        self.assertEqual(
            findings,
            [
                "OpenAI launched a new release.",
                "The company also expanded enterprise support.",
            ],
        )


if __name__ == "__main__":
    unittest.main()
