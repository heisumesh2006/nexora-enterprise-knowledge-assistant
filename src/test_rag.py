from rag.chain import RAGChain


def run_test(rag: RAGChain, question: str):
    print("\n" + "=" * 70)
    print(f"QUESTION: {question}")
    print("=" * 70)

    result = rag.ask(question)

    print("\nRetrieved Context:")
    print("-" * 70)
    print(result["context"])

    print("\nGenerated Answer:")
    print("-" * 70)
    print(result["answer"])

    return result


def main():
    print("=" * 70)
    print("MODULE 6 - BASIC RAG TEST")
    print("=" * 70)

    print("\nInitializing RAG chain...")

    rag = RAGChain(
        top_k=3,
    )

    print("RAG chain initialized successfully.")

    # ---------------------------------------------------------------
    # Test 1: Leave policy
    # ---------------------------------------------------------------

    result_1 = run_test(
        rag,
        "How many paid leave days do employees receive?",
    )

    assert "18" in result_1["answer"]

    # ---------------------------------------------------------------
    # Test 2: Working hours
    # ---------------------------------------------------------------

    result_2 = run_test(
        rag,
        "What are the standard working hours?",
    )

    assert "9" in result_2["answer"]
    assert "6" in result_2["answer"]

    # ---------------------------------------------------------------
    # Test 3: Unknown information
    # ---------------------------------------------------------------

    result_3 = run_test(
        rag,
        "What is the company's annual bonus policy?",
    )

    print("\nChecking hallucination protection...")

    answer_3 = result_3["answer"].lower()

    assert (
        "not available" in answer_3
        or "not provided" in answer_3
        or "does not contain" in answer_3
        or "provided company documents" in answer_3
    )

    print("Unknown-information handling: PASSED")

    print("\n" + "=" * 70)
    print("ALL RAG TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()