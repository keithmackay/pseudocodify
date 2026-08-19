import pytest
from unittest.mock import MagicMock, patch
from pseudocodify.rlm_adapter import RLMAdapter, RLMError


def test_run_returns_response_string():
    mock_completion = MagicMock()
    mock_completion.response = "translated output"
    mock_rlm = MagicMock()
    mock_rlm.completion.return_value = mock_completion

    with patch("pseudocodify.rlm_adapter.RLM", return_value=mock_rlm):
        adapter = RLMAdapter(model="claude-opus-4-6")
        result = adapter.run("translate this")
    assert result == "translated output"


def test_run_with_context_prepends_context():
    mock_completion = MagicMock()
    mock_completion.response = "output"
    mock_rlm = MagicMock()
    mock_rlm.completion.return_value = mock_completion

    with patch("pseudocodify.rlm_adapter.RLM", return_value=mock_rlm):
        adapter = RLMAdapter(model="claude-opus-4-6")
        adapter.run("prompt", context="extra context")

    call_args = mock_rlm.completion.call_args[0][0]
    assert "extra context" in call_args
    assert "prompt" in call_args


def test_rlm_exception_wrapped_as_rlm_error():
    mock_rlm = MagicMock()
    mock_rlm.completion.side_effect = Exception("rlms internal error")

    with patch("pseudocodify.rlm_adapter.RLM", return_value=mock_rlm):
        adapter = RLMAdapter(model="claude-opus-4-6")
        with pytest.raises(RLMError, match="rlms internal error"):
            adapter.run("prompt")


def test_rlm_error_is_not_base_exception():
    assert issubclass(RLMError, Exception)
    assert not issubclass(RLMError, BaseException) or issubclass(RLMError, Exception)


def test_backend_kwargs_includes_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-123")
    mock_rlm_class = MagicMock()

    with patch("pseudocodify.rlm_adapter.RLM", mock_rlm_class):
        RLMAdapter(model="claude-opus-4-6")

    _, kwargs = mock_rlm_class.call_args
    assert kwargs["backend_kwargs"]["api_key"] == "test-api-key-123"
