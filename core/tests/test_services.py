from unittest.mock import MagicMock, patch

from django.test import TestCase

from core.services.claude import ClaudeServiceError, extract_signature, transform_text

VALID_SIGNATURE = {
    "tone": "authoritative yet approachable",
    "sentence_rhythm": "short declaratives followed by one elaborating clause",
    "formality_level": "semi-formal — professional enough for B2B, human enough to avoid stiffness",
    "forms_of_address": "second person singular (you / your); occasional we-inclusive",
    "emotional_appeal": "rational-first with aspirational payoff; benefits before feelings",
}

MOCK_PATH = "core.services.claude.anthropic.Anthropic"


def _mock_client(response_text: str) -> MagicMock:
    """Return a mock Anthropic client that yields *response_text*."""
    content_block = MagicMock()
    content_block.text = response_text
    message = MagicMock()
    message.content = [content_block]
    client = MagicMock()
    client.messages.create.return_value = message
    return client


class ExtractSignatureTests(TestCase):
    @patch(MOCK_PATH)
    def test_returns_dict_with_all_five_keys(self, mock_cls) -> None:
        import json
        mock_cls.return_value = _mock_client(json.dumps(VALID_SIGNATURE))
        result = extract_signature(["Sample brand text."])
        self.assertEqual(set(result.keys()), {
            "tone", "sentence_rhythm", "formality_level", "forms_of_address", "emotional_appeal"
        })

    @patch(MOCK_PATH)
    def test_extra_keys_stripped(self, mock_cls) -> None:
        import json
        extra = {**VALID_SIGNATURE, "unexpected_key": "ignored"}
        mock_cls.return_value = _mock_client(json.dumps(extra))
        result = extract_signature(["Sample brand text."])
        self.assertNotIn("unexpected_key", result)

    @patch(MOCK_PATH)
    def test_malformed_json_raises(self, mock_cls) -> None:
        mock_cls.return_value = _mock_client("This is not JSON at all.")
        with self.assertRaises(ClaudeServiceError) as ctx:
            extract_signature(["Sample brand text."])
        self.assertIn("malformed JSON", str(ctx.exception))

    @patch(MOCK_PATH)
    def test_missing_keys_raises(self, mock_cls) -> None:
        import json
        incomplete = {"tone": "friendly", "sentence_rhythm": "short"}
        mock_cls.return_value = _mock_client(json.dumps(incomplete))
        with self.assertRaises(ClaudeServiceError) as ctx:
            extract_signature(["Sample brand text."])
        self.assertIn("missing required keys", str(ctx.exception))

    @patch(MOCK_PATH)
    def test_api_failure_raises(self, mock_cls) -> None:
        import anthropic
        mock_cls.return_value.messages.create.side_effect = anthropic.APIError(
            message="upstream error", request=MagicMock(), body=None
        )
        with self.assertRaises(ClaudeServiceError) as ctx:
            extract_signature(["Sample brand text."])
        self.assertIn("Anthropic API error", str(ctx.exception))

    @patch(MOCK_PATH)
    def test_non_object_response_raises(self, mock_cls) -> None:
        import json
        mock_cls.return_value = _mock_client(json.dumps(["list", "not", "object"]))
        with self.assertRaises(ClaudeServiceError) as ctx:
            extract_signature(["Sample brand text."])
        self.assertIn("not a JSON object", str(ctx.exception))


class TransformTextTests(TestCase):
    @patch(MOCK_PATH)
    def test_returns_rewritten_string(self, mock_cls) -> None:
        mock_cls.return_value = _mock_client("Rewritten text in brand voice.")
        result = transform_text("Original text.", VALID_SIGNATURE)
        self.assertEqual(result, "Rewritten text in brand voice.")

    @patch(MOCK_PATH)
    def test_api_failure_raises(self, mock_cls) -> None:
        import anthropic
        mock_cls.return_value.messages.create.side_effect = anthropic.APIError(
            message="upstream error", request=MagicMock(), body=None
        )
        with self.assertRaises(ClaudeServiceError) as ctx:
            transform_text("Original text.", VALID_SIGNATURE)
        self.assertIn("Anthropic API error", str(ctx.exception))

    @patch(MOCK_PATH)
    def test_empty_response_raises(self, mock_cls) -> None:
        mock_cls.return_value = _mock_client("   ")
        with self.assertRaises(ClaudeServiceError) as ctx:
            transform_text("Original text.", VALID_SIGNATURE)
        self.assertIn("empty", str(ctx.exception))
