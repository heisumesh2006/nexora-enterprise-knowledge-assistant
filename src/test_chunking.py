from pathlib import Path

from langchain_core.documents import Document

from ingestion.loader import load_documents_from_folder
from chunking.splitter import split_documents


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "sample_documents"


def test_real_documents():
    print("=" * 70)
    print("TEST 1 - REAL DOCUMENTS")
    print("=" * 70)

    documents = load_documents_from_folder(DOCUMENTS_DIR)

    print(f"\nOriginal Document objects: {len(documents)}")

    chunks = split_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    print(f"Generated chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page")

        print(f"\nChunk #{index}")
        print("-" * 70)
        print(f"Source: {Path(source).name}")

        if page is not None:
            print(f"Page: {page}")

        print(f"Characters: {len(chunk.page_content)}")
        print(f"Content:\n{chunk.page_content}")

    assert len(documents) == 3
    assert len(chunks) == 3

    print("\nReal document test: PASSED")


def test_long_document():
    print("\n" + "=" * 70)
    print("TEST 2 - LONG DOCUMENT CHUNKING")
    print("=" * 70)

    long_text = (
        "Nexora Enterprise provides employees with several workplace policies. "
        "Employees receive 18 days of paid leave every calendar year. "
        "Casual leave should normally be requested at least two working days "
        "in advance through the HR portal. "
        "Managers are responsible for reviewing and approving leave requests. "
        "Employees should contact HR when they need extended leave. "
        "Remote work is available subject to manager approval and company policy. "
        "Standard working hours are from 9:00 AM to 6:00 PM, Monday through Friday. "
        "All employees are expected to maintain professional and respectful behavior. "
        "Employees should follow company policies and contact the appropriate "
        "department when they need clarification."
    )

    document = Document(
        page_content=long_text,
        metadata={
            "source": "synthetic_test_document.txt"
        },
    )

    chunks = split_documents(
        [document],
        chunk_size=200,
        chunk_overlap=50,
    )

    print(f"\nOriginal characters: {len(long_text)}")
    print(f"Generated chunks: {len(chunks)}")

    assert len(chunks) > 1

    for index, chunk in enumerate(chunks, start=1):
        print(f"\nChunk #{index}")
        print("-" * 70)
        print(f"Characters: {len(chunk.page_content)}")
        print(chunk.page_content)

        assert chunk.metadata["source"] == "synthetic_test_document.txt"

    print("\nLong document test: PASSED")


def main():
    test_real_documents()
    test_long_document()

    print("\n" + "=" * 70)
    print("ALL MODULE 3 TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()