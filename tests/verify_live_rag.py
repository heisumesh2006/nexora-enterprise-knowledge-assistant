"""Opt-in HTTP smoke checks against the user's indexed ticket and company KB.

Start Ollama, FastAPI and Node first. Run with the project virtualenv:
  python tests/verify_live_rag.py --url http://127.0.0.1:5000/api/ask
Expected ticket values below are test assertions only, never retrieval rules.
"""

import argparse
import json
import re
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


CASES = [
    ("When is the train departing?", [r"08:35"]),
    ("What is the arrival time?", [r"14:00"]),
    ("List out the passenger details.", [r"A\s+DEVI", r"\b45\b", r"\b(?:F|Female)\b", r"CNF\s*/\s*D7\s*/\s*35\s*/\s*NO CHOICE"]),
    ("What is the PNR number?", [r"4556164612"]),
    ("What is the train number and name?", [r"12639", r"BRINDAVAN SF EXP"]),
    ("How many paid leave days do employees receive?", [r"\b18\b"]),
    ("What are the standard working hours?", [r"9(?::00)?\s*AM", r"6(?::00)?\s*PM"]),
    ("What is the company's annual bonus policy?", [r"(?:not|no|unavailable|cannot|couldn't|can't)"]),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5000/api/ask")
    args = parser.parse_args()
    failed = []
    for question, patterns in CASES:
        start = time.monotonic()
        request = Request(args.url, data=json.dumps({"question": question}).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=180) as response:
                result = json.load(response)
            assert set(result) == {"question", "answer", "citations"}, result
            assert result["question"] == question
            assert all(re.search(pattern, result["answer"], re.I) for pattern in patterns), result["answer"]
            assert result["citations"] and all(c["source"] for c in result["citations"])
            if question == CASES[-1][0]:
                answer = result["answer"].lower()
                assert any(phrase in answer for phrase in (
                    "could not be found", "not addressed", "not explicitly stated",
                    "not mentioned", "not provided", "do not contain", "does not contain",
                    "not available", "not specified", "no information",
                )), result["answer"]
                assert not any(phrase in answer for phrase in (
                    "may offer", "might", "suggests", "does not have", "no annual bonus",
                )), result["answer"]
            if question == CASES[2][0]:
                assert not re.search(r"passenger\s*[23]|clerkage|waitlisted e-ticket", result["answer"], re.I), result["answer"]
            if question == CASES[4][0]:
                assert not re.search(r"train number\s*(?:is|:)\s*4556164612", result["answer"], re.I), result["answer"]
            print(json.dumps({"status": "PASS", "seconds": round(time.monotonic() - start, 2), **result}), flush=True)
        except Exception as exc:
            detail = exc.read().decode() if isinstance(exc, HTTPError) else str(exc)
            failed.append(question)
            print(json.dumps({"status": "FAIL", "question": question, "detail": detail}), flush=True)
    if failed:
        raise SystemExit(f"{len(failed)} checks failed")
    print("All 8 live answer checks passed.", flush=True)


if __name__ == "__main__":
    main()
