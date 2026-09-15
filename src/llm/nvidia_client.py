import os

from openai import OpenAI


class NVIDIACloudLLM:
    """
    NVIDIA cloud LLM provider using the OpenAI-compatible API.
    """

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ):
        self.model = model or os.getenv(
            "NVIDIA_MODEL",
            "nvidia/nemotron-3-ultra-550b-a55b",
        )

        self.base_url = base_url or os.getenv(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1",
        )

        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is required when using the NVIDIA provider."
            )

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 100,
    ) -> str:
        """
        Generate a response using the NVIDIA cloud model.
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