# Nexora retrieval investigation and fix

## Repository reviewed

The active application is React/Vite -> Node/Express -> Python/FastAPI ->
Chroma/MiniLM -> the configured LLM. Ollama with `qwen2.5:1.5b` is configured
locally; NVIDIA remains available through the existing provider factory.

The history runs from ingestion, chunking, embeddings and persistent vectors
through RAG, citations, provider selection, FastAPI, Node, React and upload
foundation. HEAD is `4c9805f` (Module 9). The working tree already contained
changes to ten tracked files and uploaded files when this investigation began.
Those changes were preserved. No commit, push, reindex or production collection
reset was performed.

Reviewed source includes the React application and styles/configuration, Node
routes and service/registry modules, FastAPI schemas/routes, indexers, loaders,
splitter, embedder, Chroma wrapper, RAG chain, both LLM clients and factory,
existing test scripts, dependency manifests, environment configuration (without
exposing secrets), sample documents and the actual stored Chroma chunks.

The root README is stale: it describes Module 1 and a Streamlit roadmap.
Streamlit is also in the old dependency list, but is not part of the active
application. This fix does not introduce or use it. The current requirements
list also omits an explicit FastAPI dependency despite FastAPI being installed
in the existing virtual environment; dependency cleanup is separate work.

## Exact request and upload paths

1. `frontend/src/App.jsx` posts `{question}` to Node `/api/ask`.
2. `backend/server.js` validates it; `services/aiService.js` forwards it to
   FastAPI `/ask`, with a 30-second timeout from the existing configuration.
3. `ai-service/api.py` invokes its shared `RAGChain(top_k=3)`.
4. `DocumentEmbedder` uses local `all-MiniLM-L6-v2`, producing normalized
   384-dimensional question embeddings.
5. `ChromaVectorStore.search` queries persistent `data/chroma`, collection
   `nexora_documents`. Its stored vector metric is L2.
6. The RAG chain combines semantic candidates with lexical/field evidence
   from the current collection snapshot, then constructs context.
7. Validated passenger-table and complete coach/seat questions receive an exact
   extractive answer from retrieved rows. Other questions and unknown layouts
   use the selected Ollama or NVIDIA client for generation.
8. Citations are derived from the selected chunks' stored source/page metadata;
   zero-based PDF pages are displayed as one-based pages.
9. FastAPI and Node return the existing `{question, answer, citations}` schema
   for React to display.

Uploads use multipart field `document` -> Multer (PDF/TXT/DOCX, 10 MB limit) ->
disk and JSON registry -> FastAPI `/index` with path/document ID -> format
loader -> recursive 500-character chunks with 50-character overlap -> MiniLM
embeddings -> Chroma upserts. No changes to this path were required.

## Observed root cause

Read-only SQLite inspection confirmed 24 stored chunks, including all 17
ticket chunks. Ticket chunk index 0 contains the passenger row and exact
departure/arrival values; index 1 contains the PNR/train/class table. Extraction
and persistence were not the cause of the reported missed fields.

The previous reranker:

- Left `departing` unmatched against `Departure`, effectively reverting that
  question to semantic ranking.
- Gave large boosts for field words anywhere in a chunk, including instructions
  mentioning departure, arrival or passenger names without their actual values.
- Used raw keyword counts and a small inverse-distance contribution on
  incompatible scales.
- Keyed semantic distances by document text instead of unique chunk ID.
- Always padded to top_k and allowed duplicate uploads to consume context.

Live testing also exposed a generation issue once retrieval was corrected:
Qwen interpreted instruction sections as additional passengers and confused
the PNR column with the train-number column in a collapsed PDF table.

## Implemented changes

`src/rag/retrieval.py` contains the focused retrieval implementation:

- Unicode/token normalization and small, explicit aliases, such as
  departing/departs -> departure and arriving/arrives -> arrival.
- BM25 lexical scoring over all current chunks, so an exact field can be
  recovered even when absent from the semantic candidate pool.
- Reciprocal rank fusion of semantic and lexical ranks, avoiding assumptions
  that Chroma distances and lexical scores share a scale.
- Field evidence based on adjacent values or populated table rows. Merely
  mentioning a field no longer receives the value boost. Booking date can be
  distinguished from journey/start date. Policy/rule questions retain prose
  retrieval.
- When recognized field evidence exists, field questions use those chunks
  without padding context with unrelated instructions. Otherwise they retain
  semantic/lexical fallback. top_k remains the maximum result count.
- Same-document/source/page support for separated fare labels and amount
  blocks. No amount-to-label mapping is invented.
- Duplicate context removal, ID-based score/distance association, and unchanged
  source metadata. Lexical-only hits have `None` for unmeasured distances.
- For passenger/seat/coach questions, verbatim populated-table excerpts exclude
  adjacent payment and itinerary blocks. Full chunks remain available in the
  retrieval results, with their original IDs and metadata.
- Conservative hints for recognized passenger and PNR/train/class rows, plus
  complete status/coach/seat/preference reservation codes. These copy
  values into separately labelled columns for the small local model. The raw
  source excerpt stays present; unknown layouts receive no fabricated hint.
- Recognized passenger rows and complete unambiguous seat/coach codes use exact
  extractive answers. This avoids the observed small-model inconsistency of
  either copying adjacent non-passenger fields or claiming a valid table is
  missing. Other questions still use the configured LLM. No ticket-specific
  values are involved in this decision or extraction.

`src/rag/chain.py` delegates reranking to that module and includes the structured
hints in context. Its shorter grounding prompt explicitly requires abstention
when information is absent, with temperature zero. The existing RAG test was
updated to accept citations to duplicate uploaded leave-policy filenames and
to reject speculative bonus answers while accepting clear abstention wording.
`src/vectorstore/chroma_store.py` respects the requested
candidate count, caps it to collection size and returns a consistent empty
result. The RAG caller explicitly requests at least 15 semantic candidates.

No new package or additional model is required. Production code contains no
particular ticket values, filenames or document IDs. API routes, providers,
frontend, ingestion and existing stored embeddings remain compatible.

## Repeatable verification

Offline retrieval and contract tests (synthetic alternative ticket values):

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
```

Live answer checks against the existing indexed ticket and company documents,
with Ollama, FastAPI and Node running:

```powershell
.venv/Scripts/python.exe -B tests/verify_live_rag.py
```

The live script's expected ticket values are test assertions only. It checks
all eight requested questions, API shape, citation presence, wrong-column
confusion and spurious extra passengers.

The existing ingestion, chunking, embedding and persistent-vector test scripts
were also run. Backend `npm test` is a syntax check rather than an HTTP test;
the live script separately exercises the actual Node -> FastAPI -> RAG -> LLM
path. Frontend lint/build are available; no frontend test runner is configured.

## Scope and limitations

The lexical scan is deliberately simple and reads the current snapshot on each
question, making new uploads visible immediately. It is appropriate for this
small repository; a much larger corpus should use an incrementally maintained
lexical index. Field patterns are conservative heuristics, not a universal PDF
table parser. Ambiguous fare alignment remains an extraction/layout limitation,
not permission to guess.

The API currently searches the entire knowledge base and carries no selected
document ID or conversation history. Several conflicting tickets would require
an explicit identifying question or future document scoping. This change does
not silently assume the most recently uploaded document.

Cold local inference can exceed the existing Node timeout. Warmed answer tests
and any remaining timeouts are reported separately from retrieval correctness.
NVIDIA provider selection is covered without sending a cloud inference request.

## Verified results

The final full HTTP run used the actual stored Chroma collection, actual local
MiniLM embeddings and actual Ollama `qwen2.5:1.5b`, through an unmodified Node
server and the FastAPI application on temporary local ports. The Node timeout
remained 30 seconds. The model was warmed before the measured eight requests;
those requests completed in approximately 0.08-8.3 seconds each.

| Question | Verified answer |
| --- | --- |
| When is the train departing? | 08:35 on 02-Sept-2026 |
| What is the arrival time? | 14:00 on 02-Sept-2026 |
| List out the passenger details. | A DEVI, 45, F, booking/current CNF/D7/35/NO CHOICE, coach D7, seat 35, preference NO CHOICE |
| What is the PNR number? | 4556164612 |
| What is the train number and name? | 12639 / BRINDAVAN SF EXP |
| Paid leave days | 18 days per calendar year |
| Working hours | 9:00 AM-6:00 PM, Monday-Friday |
| Annual bonus policy | The requested information could not be found in the provided documents. |

Ticket answers cite the actual stored ticket filename, page 1. Company answers
cite actual retrieved company-document metadata. Additional live checks returned
booking date `01-Sept-2026 19:25:34 HRS` and total fare `157.25`.
The coach/seat follow-up returned `Coach: D7; Seat/berth: 35`. These fields and
recognized passenger rows now use exact extraction for consistent labels.

Validation completed:

- 23 offline retrieval/API/provider/vector-store contract tests passed.
- All eight required live Node -> FastAPI -> RAG checks passed, with Qwen for
  generated answers and exact extraction for validated passenger rows.
- Existing ingestion, chunking, embedding and persistent-vector checks passed.
- Existing RAG answer/citation/unknown-information script passed with the
  strengthened abstention assertions and duplicate-upload citation handling.
- Backend `npm test` passed (syntax check).
- Frontend `npm run lint` and `npm run build` passed. Vite initially hit sandbox
  `spawn EPERM`; the approved build outside the sandbox completed successfully.
- `git diff --check` passed. Production Chroma still contains 24 chunks.

Initial failures were not counted as successes: early requests timed out during
local inference startup; intermediate runs exposed spurious passengers, PNR/train
column confusion and speculative bonus answers. The implementation was refined
and the full required live suite was rerun successfully after those fixes.

No frontend browser automation or live NVIDIA cloud inference was performed.
Temporary verification Node/FastAPI instances were stopped after testing.
