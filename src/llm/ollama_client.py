import os

from openai import OpenAI


class OllamaLLM:
    """
    Local LLM provider using Ollama's OpenAI-compatible API.
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL",
            "http://127.0.0.1:11434/v1",
        )

        self.client = OpenAI(
            base_url=self.base_url,
            api_key="ollama",
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 100,
    ) -> str:
        """
        Generate a response from the local Ollama model.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content.strip()