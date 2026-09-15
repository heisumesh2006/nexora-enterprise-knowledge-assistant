import os

from llm.nvidia_client import NVIDIACloudLLM
from llm.ollama_client import OllamaLLM


def create_llm_provider():
    """
    Create the configured LLM provider.

    Supported providers:
    - ollama
    - nvidia
    """

    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        return OllamaLLM()

    if provider == "nvidia":
        return NVIDIACloudLLM()

    raise ValueError(
        f"Unsupported LLM_PROVIDER: '{provider}'. "
        "Expected 'ollama' or 'nvidia'."
    )