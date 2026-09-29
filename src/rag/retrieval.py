"""Small-corpus hybrid retrieval; no extra model or persistent lexical index.

BM25 scans the current Chroma snapshot so newly uploaded chunks are immediately
searchable. Reciprocal rank fusion avoids mixing L2 distances with BM25 scores.
Field evidence guides selection; original text remains in the LLM context.
"""

from collections import Counter
from difflib import SequenceMatcher
import math
import re
import unicodedata


STOP_WORDS = set("""a an the is are was were when what where who how many much
do does did can could would should please tell me give list out of for to on in
at from my this that and or its it our us about detail details number""".split())
ALIASES = {
    "depart": "departure", "departs": "departure", "departing": "departure",
    "departures": "departure", "arrive": "arrival", "arrives": "arrival",
    "arriving": "arrival", "arrivals": "arrival", "passengers": "passenger",
    "pnrs": "pnr", "times": "time", "dates": "date", "hours": "hour",
    "days": "day", "employees": "employee", "fares": "fare",
    "berth": "seat", "seats": "seat", "berths": "seat",
}
TIME = r"(?:[01]?\d|2[0-3]):[0-5]\d(?:\s*[AP]M)?"
DATE = r"(?:\d{1,4}[-/]\w{1,9}[-/]\d{1,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})"
MONEY = r"(?:₹|rs\.?|inr|usd|\$|eur|€)\s*\d[\d,]*(?:\.\d{1,2})?"
STATUS = r"\b(?:CNF|RAC|WL)(?:\s*/\s*[\w -]+){2,}"
FARE_LABEL = r"(?im)^[ \t]*(?:total\s+|ticket\s+)?fare[ \t]*(?:\([^\n)]*\))?[ \t]*:?\s*$"

# Labels, not document identities or expected answers. Require an adjacent value
# or the immediately following populated table row, not a keyword anywhere.
FIELD_PATTERNS = {
    "departure": rf"\bdepart(?:ure|s|ing)?\s*(?:time)?\s*[*:=-]*\s*{TIME}",
    "arrival": rf"\barriv(?:al|es|ing)?\s*(?:time)?\s*[*:=-]*\s*{TIME}",
    "pnr": r"\bPNR\s*(?:(?:number|no\.?)\s*)?[:#*-]*\s*\d{6,12}\b|\bPNR[^\n]{0,65}\n\s*\d{6,12}\b",
    "train": r"\bTrain\s*(?:No\.?\s*/\s*Name|number(?:\s+and\s+name)?|no\.?)\s*[:*-]*\s*\d{4,6}\b|\bTrain\s+No\.?\s*/\s*Name[^\n]{0,25}\n\s*(?:\d{6,12}\s+)?\d{4,6}\b|\bTrain\s+Name\s*:\s*[A-Za-z][^\n]+",
    "passenger": r"\bName\s+Age\s+Gender[^\n]*\n\s*(?:\d+[.)]?\s+)?[A-Za-z][A-Za-z .'-]*\s+\d{1,3}\s+(?:[MF]|Male|Female)\b|\bPassenger(?:\s+Name)?\s*:\s*[A-Za-z][^\n]+",
    "age": r"\bAge\s*[:=-]\s*\d{1,3}\b",
    "gender": r"\bGender\s*[:=-]\s*(?:[MF]|Male|Female|Other)\b",
    "date": rf"\b(?:start\s+|journey\s+|booking\s+|travel\s+)?date\s*[*:=-]*\s*{DATE}",
    "booking_date": rf"\bbooking\s+date\s*[*:=-]*\s*{DATE}|\bbooking\s+date[ \t]*\n[^\n]{{0,50}}{DATE}",
    "seat": r"\b(?:seat|berth)(?:\s+(?:number|no\.?))?\s*[:#=-]*\s*\d+\b",
    "coach": r"\bcoach(?:\s+(?:number|no\.?))?\s*[:#=-]*\s*[A-Z]+\d+\b",
    "status": r"\b(?:booking|current)\s+status\s*[:=-]\s*(?:CNF|RAC|WL)\b",
    "fare": rf"\b(?:total\s+|ticket\s+)?fare\s*[:=-]*\s*(?:{MONEY}|\d[\d,]*\.\d{{2}})",
    "class": r"\bclass\s*[:=-]\s*[A-Za-z0-9][^\n]+",
}


def normalized(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def stem_token(word: str) -> str:
    """Apply conservative morphology normalization to a single token.

    This is intentionally small and corpus-independent. It lets plural and
    common suffix variants share evidence while leaving field terms such as
    ``status`` intact.
    """
    if word in {"status", "analysis", "business", "booking", "working"}:
        return word
    if len(word) > 7 and word.endswith("ships"):
        return word[:-5]
    if len(word) > 5 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 4 and word.endswith("s"):
        return word[:-1]
    return word


def tokens(text: str) -> list[str]:
    return [stem_token(ALIASES.get(word, word))
            for word in re.findall(r"\w+", normalized(text))
            if word not in STOP_WORDS]


def token_similarity(left: str, right: str) -> float:
    """Return a conservative typo similarity for content tokens."""
    if left == right:
        return 1.0
    if min(len(left), len(right)) < 4:
        return 0.0
    if abs(len(left) - len(right)) > 1:
        return 0.0
    ratio = SequenceMatcher(None, left, right).ratio()
    if ratio >= 0.84:
        return ratio
    return 0.0


def requested_fields(question: str) -> set[str]:
    # Requests about procedures/rules need prose, not a ticket value boost.
    if re.search(r"\b(rules?|polic(?:y|ies)|refund|instructions?|why|apply)\b", question, re.I):
        return set()
    words = set(tokens(question))
    fields = words & FIELD_PATTERNS.keys()
    if "date" in fields and "booking" in words:
        fields.remove("date")
        fields.add("booking_date")
    if ("train" in fields and fields - {"train"}
            and not re.search(r"\btrain\s+(?:number|no\.?|name)\b", question, re.I)):
        fields.remove("train")
    return fields


def field_evidence(text: str) -> set[str]:
    text = unicodedata.normalize("NFKC", text)
    found = {field for field, pattern in FIELD_PATTERNS.items()
             if re.search(pattern, text, re.I)}
    if re.search(rf"(?im)^\s*departure\s+arrival\s*\n\s*{TIME}\s+{TIME}", text):
        found.update(("departure", "arrival"))
    if "passenger" in found and re.search(r"\bName\s+Age\s+Gender", text, re.I):
        found.update(("age", "gender"))
    if re.search(STATUS, text, re.I) and re.search(r"\b(?:booking|current)\s+status", text, re.I):
        found.update(("seat", "coach", "status"))
    if re.search(r"\bclass[^\n]*\n[^\n]+\b(?:sitting|sleeper|AC)\b", text, re.I):
        found.add("class")
    return found


def table_hint(text: str) -> str:
    """Label unambiguous PNR/train/class columns for small instruction models.

    A hint is emitted only for a recognized header and fully matched row; it
    copies values verbatim. Unknown layouts keep their original context only.
    """
    match = re.search(
        r"(?im)^\s*PNR\s+Train\s+No\.?\s*/\s*Name\s+Class\s*\n"
        r"\s*(\d{6,12})\s+(\d{4,6})\s*/\s*([^\n]+)", text,
    )
    if not match:
        return ""
    pnr, train_number, remainder = match.groups()
    # A finite class vocabulary disambiguates collapsed column whitespace;
    # no values, source names, document IDs, or passenger names are assumed.
    columns = re.fullmatch(
        r"(.+?)\s+((?:(?:FIRST|SECOND|THIRD)\s+(?:SITTING|AC)|"
        r"(?:AC\s+|EXECUTIVE\s+)?CHAIR\s+CAR|SLEEPER|FIRST\s+CLASS)"
        r"(?:\s*\([^\n)]+\))?)\s*", remainder, re.I,
    )
    if not columns:
        return ""
    train_name, travel_class = columns.groups()
    return ("Table column alignment (values copied from the row above):\n"
            f"PNR: {pnr}\nTrain number: {train_number}\n"
            f"Train name: {train_name}\nClass: {travel_class}")


def structured_hint(text: str) -> str:
    """Render recognized table/status notation without changing the source."""
    hints = [table_hint(text)]
    header = re.search(r"(?im)^\s*#?\s*Name\s+Age\s+Gender[^\n]*\n", text)
    if header:
        for line in text[header.end():].splitlines():
            row = re.fullmatch(
                r"\s*(?:\d+[.)]?\s+)?([A-Za-z][A-Za-z .'-]*?)\s+"
                r"(\d{1,3})\s+(M|F|Male|Female|Other)\b\s*(.*)", line, re.I,
            )
            if not row:
                break
            name, age, gender, status_values = row.groups()
            hints.append(
                "Passenger table row alignment:\n"
                f"Passenger name: {name}\nAge: {age}\nGender: {gender}\n"
                f"Remaining row values (verbatim): {status_values}"
            )
    if re.search(r"\b(?:booking|current)\s+status", text, re.I):
        # Recognize the railway status/coach/seat/preference notation, only
        # when all four components are present. Preserve unknown codes as raw
        # context rather than guessing missing coach/seat assignments.
        rows = re.findall(
            r"\b(CNF|RAC|WL)\s*/\s*([A-Z][A-Z0-9]*)\s*/\s*(\d+)\s*/\s*"
            r"([A-Z ]+?)(?=\s{2,}|\n|$)", text, re.I,
        )
        for status, coach, seat, preference in dict.fromkeys(rows):
            hints.append(
                "Reservation code alignment (status/coach/seat/preference):\n"
                f"Status: {status}\nCoach: {coach}\nSeat/berth: {seat}\n"
                f"Preference: {preference.strip()}"
            )
    return "\n\n".join(hint for hint in hints if hint)


def context_excerpt(text: str, question: str = "") -> str:
    """For person-field questions, keep the populated table, not nearby bills.

    The returned excerpt is verbatim source text. The full chunk remains in
    retrieval results with its ID/metadata. Unknown layouts keep full text.
    """
    fields = requested_fields(question)
    if not fields or not fields <= {"passenger", "age", "gender", "seat", "coach", "status"}:
        return text
    header = re.search(r"(?im)^\s*#?\s*Name\s+Age\s+Gender[^\n]*\n", text)
    if not header:
        return text
    rows = []
    for line in text[header.end():].splitlines():
        if not re.fullmatch(
            r"\s*(?:\d+[.)]?\s+)?[A-Za-z][A-Za-z .'-]*?\s+"
            r"\d{1,3}\s+(?:M|F|Male|Female|Other)\b\s*.*", line, re.I,
        ):
            break
        rows.append(line)
    return header.group() + "\n".join(rows) if rows else text


def extractive_answer(question: str, results: dict) -> str | None:
    """Verbatim answers for validated passenger rows / complete reservations.

    Small models can abstain on a valid table or turn nearby instructions into
    people. These two narrow intents need extraction, not generation. Unknown
    layouts and other questions still use the configured LLM.
    """
    fields = requested_fields(question)
    if fields != {"passenger"} and not (fields and fields <= {"seat", "coach"}):
        return None
    answers, seen = [], set()
    for text in (results.get("documents") or [[]])[0]:
        header = re.search(r"(?im)^\s*#?\s*Name\s+Age\s+Gender[^\n]*\n", text)
        if not header:
            continue
        for line in text[header.end():].splitlines():
            row = re.fullmatch(
                r"\s*(?:\d+[.)]?\s+)?([A-Za-z][A-Za-z .'-]*?)\s+"
                r"(\d{1,3})\s+(M|F|Male|Female|Other)\b\s*(.*)", line, re.I,
            )
            if not row:
                break
            name, age, gender, remaining = row.groups()
            if row.groups() in seen:
                continue
            seen.add(row.groups())
            codes = re.findall(
                r"\b(CNF|RAC|WL)\s*/\s*([A-Z][A-Z0-9]*)\s*/\s*(\d+)\s*/\s*"
                r"([A-Z ]+?)(?=\s{2,}|\n|$)", remaining, re.I,
            )
            if fields != {"passenger"}:
                # Different booking/current assignments need their own labels;
                # leave ambiguous codes to full context instead of choosing one.
                positions = {(code[1], code[2]) for code in codes}
                if len(positions) != 1:
                    return None
                coach, seat = next(iter(positions))
                answers.append(f"{name}: Coach: {coach}; Seat/berth: {seat}")
                continue
            values = [f"Name: {name}", f"Age: {age}", f"Gender: {gender}"]
            if len(codes) == 2 and re.search(r"Booking\s+Status\s+Current\s+Status", header.group(), re.I):
                values.extend((f"Booking Status: {'/'.join(codes[0])}",
                               f"Current Status: {'/'.join(codes[1])}"))
            elif remaining:
                values.append(f"Other passenger row fields: {remaining}")
            positions = {(code[1], code[2], code[3].strip()) for code in codes}
            if len(positions) == 1:
                coach, seat, preference = next(iter(positions))
                values.extend((f"Coach: {coach}", f"Seat/berth: {seat}", f"Preference: {preference}"))
            answers.append("\n".join(values))
    return "\n\n".join(answers) if answers else None


def bm25_scores(question: str, documents: list[str]) -> list[float]:
    counts = [Counter(tokens(text)) for text in documents]
    lengths = [sum(count.values()) for count in counts]
    average = sum(lengths) / max(len(lengths), 1) or 1
    scores = [0.0] * len(documents)
    for term in set(tokens(question)):
        vocabulary = set().union(*(count.keys() for count in counts))
        related_terms = {
            candidate: token_similarity(term, candidate)
            for candidate in vocabulary
            if token_similarity(term, candidate) > 0
        }
        frequency = sum(
            any(candidate in count for candidate in related_terms)
            for count in counts
        )
        idf = math.log(1 + (len(documents) - frequency + 0.5) / (frequency + 0.5))
        for i, count in enumerate(counts):
            tf = sum(count[candidate] * similarity
                     for candidate, similarity in related_terms.items())
            scores[i] += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * lengths[i] / average))
    return scores


def rerank(question: str, semantic: dict, snapshot: dict, top_k: int) -> dict:
    ids = snapshot.get("ids", [])
    texts = snapshot.get("documents", [])
    metadatas = snapshot.get("metadatas", [])
    semantic_ids = (semantic.get("ids") or [[]])[0]
    distances = (semantic.get("distances") or [[]])[0]
    semantic_rank = {chunk_id: i + 1 for i, chunk_id in enumerate(semantic_ids)}
    distance_by_id = dict(zip(semantic_ids, distances))
    lexical = bm25_scores(question, texts)
    lexical_order = sorted(range(len(texts)), key=lambda i: (-lexical[i], ids[i]))
    lexical_rank = {i: rank for rank, i in enumerate(lexical_order, 1) if lexical[i] > 0}
    fields = requested_fields(question)
    evidence = [field_evidence(text) for text in texts] if fields else [set()] * len(texts)

    def document_key(index: int) -> tuple[str, str]:
        metadata = metadatas[index] or {}
        return (
            str(metadata.get("document_id") or ""),
            str(metadata.get("source") or ""),
        )

    # A rare lexical/topic match is stronger evidence of document relevance than
    # a weak semantic hit from an unrelated document. Gate those semantic hits
    # when the matching vocabulary is concentrated in a small number of files.
    # Broad terms remain semantic-only, preserving normal FAQ/policy behavior.
    lexical_document_scores = {}
    query_terms = set(tokens(question))
    document_term_matches = {}
    for index, score in enumerate(lexical):
        vocabulary = set(tokens(texts[index]))
        matched_terms = {
            term for term in query_terms
            if any(token_similarity(term, candidate) > 0 for candidate in vocabulary)
        }
        key = document_key(index)
        document_term_matches.setdefault(key, set()).update(matched_terms)
        if score > 0:
            lexical_document_scores[key] = lexical_document_scores.get(key, 0.0) + score
    unique_documents = {document_key(i) for i in range(len(texts))}
    allowed_documents = None
    has_field_evidence = any(fields & candidate for candidate in evidence)
    if lexical_document_scores and not has_field_evidence:
        max_documents = max(2, math.ceil(len(unique_documents) * 0.5))
        max_coverage = max(document_term_matches.values(), key=len, default=set())
        coverage_documents = {
            key for key, matched_terms in document_term_matches.items()
            if len(matched_terms) == len(max_coverage) and matched_terms
        }
        if (len(max_coverage) >= 3 and coverage_documents) or (
                len(lexical_document_scores) <= max_documents
                and max(lexical_document_scores)
                and coverage_documents):
            allowed_documents = coverage_documents

    # Some PDF extractors place fare labels and money in separate text blocks.
    # Retrieve both, strictly within the same document/source/page. Never infer
    # the mapping or rewrite the stored text to invent labelled values.
    def page_key(i):
        m = metadatas[i] or {}
        return (m.get("document_id"), m.get("source"), m.get("page"))

    fare_pages = set()
    if "fare" in fields:
        fare_pages = {page_key(i) for i, text in enumerate(texts)
                      if re.search(FARE_LABEL, text)
                      and all(value is not None for value in page_key(i))}

    candidates = []
    field_candidates = set()
    for i, chunk_id in enumerate(ids):
        if allowed_documents is not None and document_key(i) not in allowed_documents:
            continue
        score = 0.0
        if chunk_id in semantic_rank:
            score += 1 / (60 + semantic_rank[chunk_id])
        if i in lexical_rank:
            score += 1 / (60 + lexical_rank[i])
        matched = fields & evidence[i]
        if matched:
            field_candidates.add(i)
            # Max two-channel RRF is < 2/60. Verified field evidence wins over
            # mere mentions; lexical/semantic ranks still order field matches.
            score += 0.04 * len(matched) / len(fields)
        if fare_pages and page_key(i) in fare_pages:
            if re.search(rf"(?im)^[ \t]*{MONEY}[ \t]*$", texts[i]):
                score += 0.04
                field_candidates.add(i)
            elif re.search(FARE_LABEL, texts[i]):
                score += 0.035
                field_candidates.add(i)
        if score:
            candidates.append((score, i))

    candidates.sort(key=lambda item: (-item[0], ids[item[1]]))
    selected, seen = [], set()
    for score, i in candidates:
        # top_k is a maximum, not a reason to pad a field answer with rules.
        # If value evidence exists, use only those chunks. With no recognized
        # evidence, retain the normal semantic/lexical fallback.
        if field_candidates and i not in field_candidates:
            continue
        fingerprint = " ".join(normalized(texts[i]).split())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        selected.append((score, i))
        if len(selected) == top_k:
            break
    return {
        "ids": [[ids[i] for _, i in selected]],
        "documents": [[texts[i] for _, i in selected]],
        "metadatas": [[metadatas[i] for _, i in selected]],
        # A lexical-only candidate has no measured distance. Do not fabricate it.
        "distances": [[distance_by_id.get(ids[i]) for _, i in selected]],
        "scores": [[score for score, _ in selected]],
    }
