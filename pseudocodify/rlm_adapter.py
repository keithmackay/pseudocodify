import os

from rlm import RLM


class RLMError(Exception):
    """Wraps any exception raised by the rlms library."""


class RLMAdapter:
    def __init__(self, model: str, verbose: bool = False):
        self._rlm = RLM(
            backend="anthropic",
            backend_kwargs={
                "model_name": model,
                "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            },
            verbose=verbose,
        )

    def run(self, prompt: str, context: str | None = None) -> str:
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        try:
            result = self._rlm.completion(full_prompt)
            return result.response
        except Exception as e:
            raise RLMError(str(e)) from e
