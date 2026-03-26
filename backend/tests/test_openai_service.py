import json
import pytest
from unittest.mock import patch, MagicMock

from services.openai_service import generate_tutorial, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


# A minimal valid tutorial response matching the expected schema
VALID_TUTORIAL = {
    "title": "Attention Is All You Need",
    "authors": ["Vaswani et al."],
    "summary": "This paper introduces the Transformer architecture.",
    "math_foundations": [
        {
            "name": "Scaled Dot-Product Attention",
            "latex": "Attention(Q,K,V) = softmax(QK^T / sqrt(d_k))V",
            "explanation": "Computes attention weights via scaled dot products.",
        }
    ],
    "algorithms": [
        {
            "name": "Multi-Head Attention",
            "pseudocode": "Split Q, K, V into heads...",
            "implementation": "import torch\nclass MultiHeadAttention(torch.nn.Module): ...",
            "synthetic_data": "x = torch.randn(2, 10, 512)",
        }
    ],
    "visualizations": [
        {
            "title": "Attention Heatmap",
            "code": "import matplotlib.pyplot as plt\nplt.imshow(attn_weights)",
        }
    ],
    "ablation_study": {
        "description": "Vary number of attention heads",
        "code": "results = [train(heads=h) for h in [1, 2, 4, 8]]",
    },
    "exercises": [
        {
            "question": "Implement positional encoding from scratch.",
            "hint": "Use sine and cosine functions of different frequencies.",
        }
    ],
    "references": [
        "Vaswani et al., 'Attention Is All You Need', NeurIPS 2017"
    ],
}


def _make_mock_response(content: str):
    """Create a mock OpenAI chat completion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class TestGenerateTutorial:
    """Tests for generate_tutorial()."""

    @patch("services.openai_service.OpenAI")
    def test_returns_valid_dict(self, mock_openai_cls):
        """generate_tutorial returns a dict with all expected keys."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(
            json.dumps(VALID_TUTORIAL)
        )

        result = generate_tutorial("Some PDF text", "sk-test-key")

        assert isinstance(result, dict)
        for key in [
            "title", "authors", "summary", "math_foundations",
            "algorithms", "visualizations", "ablation_study",
            "exercises", "references",
        ]:
            assert key in result, f"Missing key: {key}"

    @patch("services.openai_service.OpenAI")
    def test_passes_api_key_to_client(self, mock_openai_cls):
        """The OpenAI client is constructed with the user's API key."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(
            json.dumps(VALID_TUTORIAL)
        )

        generate_tutorial("text", "sk-my-key-123")

        mock_openai_cls.assert_called_once_with(api_key="sk-my-key-123")

    @patch("services.openai_service.OpenAI")
    def test_uses_replace_not_format(self, mock_openai_cls):
        """Prompt is built with .replace(), not .format() — verify no KeyError on braces."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(
            json.dumps(VALID_TUTORIAL)
        )

        # Text with curly braces that would break .format()
        tricky_text = "The set {x | x > 0} is defined as f(x) = {1 if x > 0}"
        generate_tutorial(tricky_text, "sk-test")

        call_args = mock_client.chat.completions.create.call_args
        user_msg = call_args[1]["messages"][1]["content"]
        assert tricky_text in user_msg

    @patch("services.openai_service.OpenAI")
    def test_calls_gpt_54_model(self, mock_openai_cls):
        """The correct model (gpt-5.4) is used in the API call."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(
            json.dumps(VALID_TUTORIAL)
        )

        generate_tutorial("text", "sk-test")

        call_args = mock_client.chat.completions.create.call_args
        assert "gpt-5.4" in call_args[1]["model"]

    @patch("services.openai_service.OpenAI")
    def test_handles_json_in_markdown_fences(self, mock_openai_cls):
        """If GPT wraps JSON in ```json ... ```, we still parse it."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        wrapped = f"```json\n{json.dumps(VALID_TUTORIAL)}\n```"
        mock_client.chat.completions.create.return_value = _make_mock_response(wrapped)

        result = generate_tutorial("text", "sk-test")
        assert result["title"] == "Attention Is All You Need"

    @patch("services.openai_service.OpenAI")
    def test_raises_on_invalid_json(self, mock_openai_cls):
        """Raises ValueError when GPT returns non-JSON."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(
            "This is not JSON at all"
        )

        with pytest.raises(ValueError, match="Failed to parse"):
            generate_tutorial("text", "sk-test")

    @patch("services.openai_service.OpenAI")
    def test_raises_on_missing_keys(self, mock_openai_cls):
        """Raises ValueError when response JSON is missing required keys."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        incomplete = {"title": "Only title, nothing else"}
        mock_client.chat.completions.create.return_value = _make_mock_response(
            json.dumps(incomplete)
        )

        with pytest.raises(ValueError, match="missing required"):
            generate_tutorial("text", "sk-test")

    @patch("services.openai_service.OpenAI")
    def test_raises_on_api_auth_error(self, mock_openai_cls):
        """Raises ValueError with clear message on authentication failure."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        from openai import AuthenticationError
        mock_client.chat.completions.create.side_effect = AuthenticationError(
            message="Invalid API key",
            response=MagicMock(status_code=401),
            body=None,
        )

        with pytest.raises(ValueError, match="Invalid OpenAI API key"):
            generate_tutorial("text", "sk-bad-key")

    @patch("services.openai_service.OpenAI")
    def test_raises_on_api_generic_error(self, mock_openai_cls):
        """Raises ValueError on generic OpenAI API errors."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        from openai import APIError
        mock_client.chat.completions.create.side_effect = APIError(
            message="Server error",
            request=MagicMock(),
            body=None,
        )

        with pytest.raises(ValueError, match="OpenAI API error"):
            generate_tutorial("text", "sk-test")

    @patch("services.openai_service.OpenAI")
    def test_raises_on_rate_limit(self, mock_openai_cls):
        """Raises ValueError on rate limit errors."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None,
        )

        with pytest.raises(ValueError, match="rate limit"):
            generate_tutorial("text", "sk-test")


class TestPromptTemplate:
    """Tests for the prompt constants."""

    def test_system_prompt_exists(self):
        assert len(SYSTEM_PROMPT) > 100

    def test_user_prompt_has_placeholder(self):
        assert "{{PAPER_TEXT}}" in USER_PROMPT_TEMPLATE

    def test_user_prompt_no_python_format_braces(self):
        """Template should not use {var} style placeholders."""
        # Replace known double-brace placeholders, then check no single braces remain
        cleaned = USER_PROMPT_TEMPLATE.replace("{{PAPER_TEXT}}", "")
        # Allow JSON example braces in the prompt — just verify no {var_name} patterns
        import re
        format_vars = re.findall(r"\{[a-z_]+\}", cleaned)
        assert format_vars == [], f"Found .format()-style vars: {format_vars}"
