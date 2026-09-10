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

    print("\nCitations:")
    print("-" * 70)

    for citation in result["formatted_citations"]:
        print(f"- {citation}")

    return result


def main():
    print("=" * 70)
    print("MODULE 7 - RAG WITH CITATIONS TEST")
    print("=" * 70)

    print("\nInitializing RAG chain...")

    rag = RAGChain(
        top_k=3,
    )

    print("RAG chain initialized successfully.")

    # ---------------------------------------------------------------
    # Test 1: Leave policy + citations
    # ---------------------------------------------------------------

    result_1 = run_test(
        rag,
        "How many paid leave days do employees receive?",
    )

    assert "18" in result_1["answer"]

    citations_1 = result_1["citations"]

    assert len(citations_1) > 0

    sources_1 = {
        citation["source"]
        for citation in citations_1
    }

    assert "company_faq.txt" in sources_1
    assert "leave_policy.pdf" in sources_1

    pdf_citation = next(
        citation
        for citation in citations_1
        if citation["source"] == "leave_policy.pdf"
    )

    assert pdf_citation["page"] == 1

    print("\nLeave policy answer: PASSED")
    print("Citation extraction: PASSED")
    print("PDF page citation: PASSED")

    # ---------------------------------------------------------------
    # Test 2: Working hours + citations
    # ---------------------------------------------------------------

    result_2 = run_test(
        rag,
        "What are the standard working hours?",
    )

    assert "9" in result_2["answer"]
    assert "6" in result_2["answer"]

    citations_2 = result_2["citations"]

    assert len(citations_2) > 0

    sources_2 = {
        citation["source"]
        for citation in citations_2
    }

    assert "employee_handbook.docx" in sources_2

    print("\nWorking hours answer: PASSED")
    print("Working hours citations: PASSED")

    # ---------------------------------------------------------------
    # Test 3: Unknown information + citations still reflect retrieval
    # ---------------------------------------------------------------

    result_3 = run_test(
        rag,
        "What is the company's annual bonus policy?",
    )

    answer_3 = result_3["answer"].lower()

    assert (
        "not available" in answer_3
        or "not provided" in answer_3
        or "does not contain" in answer_3
        or "provided company documents" in answer_3
    )

    assert len(result_3["citations"]) > 0

    print("\nUnknown-information handling: PASSED")
    print("Unknown-question citation handling: PASSED")

    # ---------------------------------------------------------------
    # Test 4: Citation uniqueness
    # ---------------------------------------------------------------

    citation_keys = []

    for citation in result_1["citations"]:
        key = (
            citation["source"],
            citation.get("page"),
        )
        citation_keys.append(key)

    assert len(citation_keys) == len(set(citation_keys))

    print("\nCitation uniqueness: PASSED")

    # ---------------------------------------------------------------
    # Final result
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("ALL MODULE 7 TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()