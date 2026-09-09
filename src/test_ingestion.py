from pathlib import Path

from ingestion.loader import load_documents_from_folder


DATA_FOLDER = Path("data/sample_documents")


def main():
    print("=" * 70)
    print("MODULE 2 - DOCUMENT INGESTION TEST")
    print("=" * 70)

    print(f"\nData folder: {DATA_FOLDER}")
    print(f"Folder exists: {DATA_FOLDER.exists()}")

    print("\nLoading documents...")

    documents = load_documents_from_folder(str(DATA_FOLDER))

    print("\n" + "=" * 70)
    print("INGESTION RESULTS")
    print("=" * 70)

    print(f"\nTotal loaded document objects: {len(documents)}")

    if not documents:
        print("\nNo documents were loaded.")
        return

    for index, document in enumerate(documents, start=1):

        print("\n" + "-" * 70)
        print(f"DOCUMENT OBJECT #{index}")
        print("-" * 70)

        print(f"Source   : {document.metadata.get('source')}")
        print(f"Metadata : {document.metadata}")

        content = document.page_content

        print(f"Length   : {len(content)} characters")

        preview = content[:500]

        print("\nContent preview:")
        print(preview)

        if len(content) > 500:
            print("\n... [preview truncated]")

    print("\n" + "=" * 70)
    print("MODULE 2 BASIC INGESTION TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()