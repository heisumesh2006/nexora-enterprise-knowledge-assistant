import sys
import time
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from llm.ollama_client import OllamaLLM


load_dotenv()


def main():
    print("Initializing Ollama provider...")

    llm = OllamaLLM()

    print(f"Model: {llm.model}")
    print(f"Base URL: {llm.base_url}")
    print()

    system_prompt = (
        "You are a helpful enterprise knowledge assistant. "
        "Answer clearly and concisely."
    )

    user_prompt = (
        "What is the purpose of an enterprise knowledge assistant? "
        "Answer in 2-3 sentences."
    )

    print("Generating response...")
    start = time.perf_counter()

    answer = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=100,
    )

    elapsed = time.perf_counter() - start

    print()
    print("Response:")
    print(answer)
    print()
    print(f"Generation time: {elapsed:.3f} seconds")


if __name__ == "__main__":
    main()