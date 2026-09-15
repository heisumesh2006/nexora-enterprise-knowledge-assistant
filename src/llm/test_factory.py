import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from llm.factory import create_llm_provider


load_dotenv()


def main():
    provider = create_llm_provider()

    print(f"Provider type: {type(provider).__name__}")
    print(f"Model: {provider.model}")
    print(f"Base URL: {provider.base_url}")


if __name__ == "__main__":
    main()