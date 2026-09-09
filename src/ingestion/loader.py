from pathlib import Path

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)


SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".docx": Docx2txtLoader,
}


def load_document(file_path: str):
    """
    Load a single supported document.

    Returns:
        list[Document]: LangChain Document objects.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))

        raise ValueError(
            f"Unsupported file type '{extension}'. "
            f"Supported types: {supported}"
        )

    loader_class = SUPPORTED_EXTENSIONS[extension]

    if extension == ".txt":
        loader = loader_class(
            str(path),
            encoding="utf-8",
        )
    else:
        loader = loader_class(str(path))

    documents = loader.load()

    return documents


def load_documents_from_folder(folder_path: str):
    """
    Load all supported documents from a folder.

    Unsupported files are ignored.
    """

    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(
            f"Folder not found: {folder_path}"
        )

    if not folder.is_dir():
        raise ValueError(
            f"Path is not a directory: {folder_path}"
        )

    documents = []

    for file_path in sorted(folder.iterdir()):

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(
                f"Skipping unsupported file: {file_path.name}"
            )
            continue

        print(f"Loading: {file_path.name}")

        loaded_documents = load_document(
            str(file_path)
        )

        documents.extend(loaded_documents)

    return documents