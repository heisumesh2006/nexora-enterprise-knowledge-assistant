"""Offline regressions: python -m unittest discover -s tests -v."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rag.retrieval import rerank, field_evidence, requested_fields, table_hint, structured_hint, context_excerpt, extractive_answer


class RetrievalTests(unittest.TestCase):
    def rank(self, question, texts, semantic_order=None, top_k=3, metadata=None):
        ids = [f"chunk-{i}" for i in range(len(texts))]
        order = semantic_order if semantic_order is not None else list(range(len(texts)))
        return rerank(question, {
            "ids": [[ids[i] for i in order]],
            "distances": [[0.1 + rank / 10 for rank in range(len(order))]],
        }, {
            "ids": ids, "documents": texts,
            "metadatas": metadata or [{"source": f"source-{i}.pdf", "page": "0"} for i in range(len(texts))],
        }, top_k)

    def test_times_beat_instructions_even_outside_semantic_pool(self):
        texts = ["Departure and Arrival Times may change. Check departure and arrival times.",
                 "Departure rules: wait 30 minutes before departure.",
                 "Start Date* 17-Oct-2027 Departure* 06:42 Arrival* 19:17"]
        for q in ["When is the train departing?", "What is the arrival time?",
                  "When does the train arrive?", "What is the departure time?"]:
            with self.subTest(q=q):
                result = self.rank(q, texts, [0, 1])
                self.assertEqual(result["ids"][0][0], "chunk-2")
                self.assertEqual(len(result["ids"][0]), 1)
                self.assertIsNone(result["distances"][0][0])
                self.assertEqual(result["metadatas"][0][0]["source"], "source-2.pdf")

    def test_populated_passenger_table_beats_heading(self):
        texts = ["Passenger Details\nPassenger names must match identity documents.",
                 "# Name Age Gender Booking Status Current Status\n1. B KUMAR 32 M CNF/C3/19/WINDOW CNF/C3/19/WINDOW"]
        for q in ["List out the passenger details.", "What is the passenger age?",
                  "What is the gender?", "What is my seat?", "Which coach?", "What is the current status?"]:
            with self.subTest(q=q):
                self.assertEqual(self.rank(q, texts)["ids"][0][0], "chunk-1")

    def test_pnr_train_table(self):
        texts = ["PNRs are used for enquiry. Please check the train number and name.",
                 "PNR Train No./Name Class\n9876543210 54321 / WESTERN EXPRESS SECOND SITTING\n(2S)"]
        for q in ["What is the PNR number?", "What is the train number and name?", "What class?"]:
            with self.subTest(q=q):
                self.assertEqual(self.rank(q, texts)["ids"][0][0], "chunk-1")

    def test_table_hint_copies_distinct_columns(self):
        for travel_class in ["SECOND SITTING", "SLEEPER", "AC CHAIR CAR"]:
            text = f"PNR Train No./Name Class\n9876543210 54321 / WESTERN EXPRESS {travel_class}"
            hint = table_hint(text)
            self.assertIn("PNR: 9876543210", hint)
            self.assertIn("Train number: 54321", hint)
            self.assertIn("Train name: WESTERN EXPRESS\n", hint)
            self.assertIn(f"Class: {travel_class}", hint)
        self.assertEqual(table_hint("PNR Train No./Name Class\nNot a populated row"), "")
        self.assertEqual(table_hint("PNR Train No./Name Class\n9876543210 54321 / AMBIGUOUS ROW"), "")

    def test_status_hint_does_not_guess_missing_components(self):
        hint = structured_hint("Booking Status Current Status\nCNF/C3/19/WINDOW   CNF /C3/19/WINDOW")
        self.assertIn("Coach: C3", hint)
        self.assertIn("Seat/berth: 19", hint)
        self.assertEqual(hint.count("Coach:"), 1)
        self.assertEqual(structured_hint("Booking Status: WL/12"), "")

    def test_passenger_hint_copies_only_populated_rows(self):
        text = ("# Name Age Gender Booking Status Current Status\n"
                "1. B KUMAR 32 M CNF/C3/19/WINDOW   CNF/C3/19/WINDOW\n"
                "2. C SHAH 29 F CNF/C3/20/WINDOW   CNF/C3/20/WINDOW\n"
                "Instructions: all passenger names must match identity cards.")
        hint = structured_hint(text)
        self.assertIn("Passenger name: B KUMAR\nAge: 32\nGender: M", hint)
        self.assertIn("Passenger name: C SHAH\nAge: 29\nGender: F", hint)
        self.assertEqual(hint.count("Passenger name:"), 2)
        self.assertNotIn("identity cards", hint)

    def test_passenger_context_excludes_nearby_payment_but_preserves_source(self):
        table = "# Name Age Gender Booking Status Current Status\n1. B KUMAR 32 M CNF/C3/19/WINDOW"
        text = table + "\nPayment Details\nINR 650.00\nDeparture* 06:42"
        self.assertEqual(context_excerpt(text, "List passenger details"), table)
        self.assertEqual(context_excerpt(text, "What is the seat and coach?"), table)
        self.assertEqual(context_excerpt(text, "Departure time?"), text)
        self.assertEqual(context_excerpt(text, "What are the passenger rules?"), text)
        self.assertEqual(context_excerpt(text), text)

    def test_extractive_rows_preserve_values_and_do_not_invent_assignments(self):
        text = ("# Name Age Gender Booking Status Current Status\n"
                "1. B KUMAR 32 M CNF/C3/19/WINDOW   CNF /C3/19/WINDOW\n"
                "Payment Details\nINR 650.00")
        result = {"documents": [[text]]}
        answer = extractive_answer("List passenger details", result)
        for value in ["B KUMAR", "32", "Gender: M", "Booking Status: CNF/C3/19/WINDOW",
                      "Current Status: CNF/C3/19/WINDOW", "Coach: C3", "Seat/berth: 19"]:
            self.assertIn(value, answer)
        self.assertNotIn("650", answer)
        self.assertIn("Coach: C3; Seat/berth: 19", extractive_answer("What seat and coach?", result))
        self.assertIsNone(extractive_answer("Arrival time?", result))
        self.assertIsNone(extractive_answer("What seat and coach?", {"documents": [[text.replace('CNF /C3/19', 'CNF /C4/20')]]}))

    def test_labelled_fields(self):
        for question, field in [
            ("What is the date?", "Journey Date: 17-Oct-2027"),
            ("What is the fare?", "Total Fare: INR 612.50"),
            ("What is the PNR?", "PNR: 9876543210"),
            ("Who is the passenger?", "Passenger Name: B KUMAR"),
            ("What is the seat?", "Seat: 19"),
            ("Which coach?", "Coach: C3"),
            ("What is the train number?", "Train Number: 54321"),
            ("What is the train name?", "Train Name: WESTERN EXPRESS"),
            ("When does the train arrive?", "Departure Arrival\n06:42 19:17"),
        ]:
            with self.subTest(question=question):
                self.assertEqual(self.rank(question, [question + " Read the instructions.", field])["ids"][0][0], "chunk-1")

    def test_booking_date_is_not_journey_date(self):
        texts = ["Start Date* 17-Oct-2027", "Quota Distance Booking Date\nGENERAL 200 KM 16-Oct-2027 12:15"]
        self.assertEqual(self.rank("What is the booking date?", texts)["ids"][0][0], "chunk-1")

    def test_explicit_multiple_fields_keep_both_chunks(self):
        texts = ["PNR: 9876543210", "Train Number: 54321", "PNR and train number instructions"]
        result = self.rank("What are the PNR and train number?", texts, [2, 0, 1])
        self.assertEqual(set(result["ids"][0]), {"chunk-0", "chunk-1"})

    def test_fare_support_stays_on_same_document_page(self):
        texts = ["Fare refunds follow railway rules.", "Ticket Fare\nTotal Fare (all inclusive)",
                 "Payment Details\nINR 612.50\nINR 650.00", "Payment Details\nINR 999.00"]
        metadata = [{"document_id": "a", "source": "a.pdf", "page": "0"} for _ in texts]
        metadata[-1] = {"document_id": "b", "source": "b.pdf", "page": "0"}
        result = self.rank("What is the total fare?", texts, [0, 3, 1, 2], 2, metadata)
        self.assertEqual(set(result["ids"][0]), {"chunk-1", "chunk-2"})

    def test_prose_and_unknown_question_keep_semantic_retrieval(self):
        texts = ["Employees receive 18 days of paid leave per year.",
                 "Standard working hours are 9:00 AM to 6:00 PM.",
                 "Departure* 06:42 Arrival* 19:17"]
        self.assertEqual(self.rank("How many paid leave days?", texts, [0, 1, 2])["ids"][0][0], "chunk-0")
        self.assertEqual(self.rank("What are the working hours?", texts, [1, 0, 2])["ids"][0][0], "chunk-1")
        self.assertEqual(self.rank("Annual bonus?", texts, [1, 0], 1)["ids"][0], ["chunk-1"])
        self.assertEqual(self.rank("Office schedule?", texts, [1, 0], 1)["ids"][0], ["chunk-1"])
        self.assertEqual(requested_fields("What are the departure refund rules?"), set())

    def test_duplicates_do_not_displace_other_context(self):
        result = self.rank("paid leave", ["18 days paid leave", "18 days paid leave", "Leave requests go to HR."])
        self.assertEqual(len(result["documents"][0]), 2)
        self.assertEqual(result["metadatas"][0][0]["source"], "source-0.pdf")

    def test_empty_and_nonmatching_chunks(self):
        self.assertEqual(self.rank("Departure?", [])["documents"], [[]])
        self.assertEqual(self.rank("zzzz", ["unrelated"], [])["documents"], [[]])
        self.assertEqual(field_evidence("Departure and Arrival Times may change. Call 139."), set())
        self.assertNotIn("passenger", field_evidence("Passenger details: check the rules."))

    def test_identical_text_uses_chunk_id_for_distance(self):
        result = self.rank("PNR", ["PNR: 9876543210", "PNR: 9876543210"], [1])
        self.assertEqual(result["ids"][0], ["chunk-1"])
        self.assertEqual(result["distances"][0], [0.1])


if __name__ == "__main__":
    unittest.main()
