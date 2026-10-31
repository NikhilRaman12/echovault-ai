# EchoVault AI 🏛️

> **"Some voices fade. Their stories don't have to."**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-1b3b2b.svg)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Primary_AI-Gemma_via_Ollama-c5a059.svg)](https://ollama.com/)
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Local_Inference-2a543e.svg)]()
[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest_2026-Ghost_in_the_Machine-darkred.svg)]()

EchoVault AI is a private, local-first artificial intelligence platform engineered to preserve, organize, and recount authentic family oral histories. Built specifically for Hacktoberfest 2026 (Week 4: *Ghost in the Machine*), EchoVault bridges the fragile divide between ephemeral spoken memory and enduring heritage.

---

## 1. Problem Statement

Commercial AI assistants operate on cloud infrastructure that requires transmitting intimate family stories, vulnerable grief, personal names, and ancestral anecdotes to remote corporate data centers. Furthermore, large language models are notorious for **confabulation**—inventing fictional dates, synthetic relatives, or imagined quotes to produce a fluent narrative.

For family oral history, confabulation is unacceptable.
**Preserve what people actually said. Do not manufacture what they might have said.**

EchoVault AI solves this through:
- **Zero Cloud Leakage**: 100% local inference using Google Gemma via Ollama and local SQLite storage.
- **Strict Grounded Remembrance**: Question answering bound strictly to verified source passages with exact citations.
- **Explicit Abstention**: If a detail is missing from your preserved records, EchoVault abstains with *"I couldn't find this information in your saved memories"* rather than fabricating an answer.
- **Relational & Search Provenance**: Full text indexing via SQLite FTS5 (BM25 ranking), SHA-256 deduplication, and immutable audit logs.

---

## 2. Multi-Agent Architecture

EchoVault employs a coordinated state machine of seven specialized agents. Deterministic tasks rely on robust, explainable Python logic, while language-intensive semantic extraction is powered by **Gemma**.

```
                           +-------------------------------------------------------+
                           |             EchoVault Streamlit UI                    |
                           |  Capture · Vault · Ask · Timeline · Studio · Settings |
                           +-------------------------------------------------------+
                                                      |
                                                      v
                           +-------------------------------------------------------+
                           |         Deterministic State Machine Orchestrator      |
                           |        Typed State · Execution Tracing · Fallbacks    |
                           +-------------------------------------------------------+
                                   |                                        |
       [ INGESTION PIPELINE ]      |                                        |     [ RETRIEVAL & Q&A PIPELINE ]
                                   v                                        v
                 +-----------------------------------+    +------------------------------------+
                 | Agent 1: Memory Intake Agent      |    | Agent 5: Memory Retrieval Agent    |
                 | - Validates size, format & sandbx |    | - Queries SQLite FTS5 index        |
                 | - Generates UUID & SHA-256 hash   |    | - Extracts ranked BM25 passages    |
                 +-----------------------------------+    +------------------------------------+
                                   |                                        |
                                   v                                        v
                 +-----------------------------------+    +------------------------------------+
                 | Agent 2: Transcription Agent      |    | Agent 6: Remembrance Agent         |
                 | - faster-whisper local audio      |    | - Gemma evidence-bound synthesis   |
                 | - Timestamps & manual review pass |    | - Explicit abstention on absence   |
                 +-----------------------------------+    +------------------------------------+
                                   |                                        |
                                   v                                        v
                 +-----------------------------------+    +------------------------------------+
                 | Agent 3: Memory Intelligence      |    | Agent 7: Integrity & Privacy Agent |
                 | - Gemma structured JSON extraction|    | - Enforces citation traceability   |
                 | - People, places, dates, quotes   |    | - Logs tamper-evident audit trail  |
                 +-----------------------------------+    +------------------------------------+
                                   |
                                   v
                 +-----------------------------------+
                 | Agent 4: Memory Archivist Agent   |
                 | - Atomic SQLite relational commit |
                 | - FTS5 virtual table sync         |
                 | - Duplicate rejection             |
                 +-----------------------------------+
```

### Agent Responsibilities & Contracts

| Agent | Technology | Inputs / Outputs | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **1. Intake Agent** | Python / Hashlib | `RawInput` $\rightarrow$ `State` | Sandboxes file uploads, computes SHA-256 hash, generates memory IDs. |
| **2. Transcription Agent** | `faster-whisper` | `AudioFile` $\rightarrow$ `Transcript` | Local audio-to-text; gracefully falls back to manual editing if whisper/ffmpeg is missing. |
| **3. Memory Intelligence** | **Gemma** (Ollama) | `StoryText` $\rightarrow$ `MemoryIntelligence` | Extracts people, places, dates, quotes, themes, and tags uncertainty. |
| **4. Archivist Agent** | SQLite (WAL/FTS5) | `Intelligence` $\rightarrow$ `MemoryRecord` | Transaction-safe atomic writes; prevents duplicate submissions. |
| **5. Retrieval Agent** | SQLite FTS5 | `UserQuery` $\rightarrow$ `RetrievedPassage[]`| Executes full-text search with BM25 snippet extraction and stopword pruning. |
| **6. Remembrance Agent** | **Gemma** (Ollama) | `Evidence` $\rightarrow$ `GroundedAnswer` | Synthesizes answers grounded exclusively in retrieved evidence; abstains if absent. |
| **7. Integrity & Privacy** | Python / Validation | `Candidate` $\rightarrow$ `VerifiedAnswer` | Verifies citations, prevents ungrounded assertions, records audit events. |

---

## 3. Technology Stack

- **Runtime**: Python 3.11+
- **Application Interface**: Streamlit (Editorial Archival Theme with Forest Green, Warm Ivory, and Antique Gold)
- **Primary AI Engine**: **Gemma** (via Ollama local HTTP API)
- **Audio Processing**: `faster-whisper` (CPU int8 quantization with offline fallback)
- **Relational Storage**: SQLite with Foreign Keys and WAL Mode
- **Search Engine**: SQLite FTS5 (Full-Text Search with BM25 ranking)
- **Data Validation**: Pydantic v2
- **Testing**: Pytest

---

## 4. Installation & Setup

### Prerequisites
- Python 3.11 or higher
- [Ollama](https://ollama.com/) installed and running locally
- Git

### 1. Clone the Repository
```powershell
git clone https://github.com/NikhilRaman12/echovault-ai.git
cd echovault-ai
```

### 2. Configure Python Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. Setup Local Gemma in Ollama
Make sure the Ollama daemon is running:
```powershell
ollama list
```
Pull or run a Gemma model (e.g. `gemma:2b` or `gemma:7b`):
```powershell
ollama pull gemma:2b
```

### 4. Configuration (.env)
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Adjust parameters if desired:
```ini
OLLAMA_BASE_URL=http://localhost:11434
GEMMA_MODEL=gemma:2b
OLLAMA_TIMEOUT_SECONDS=45
```

---

## 5. Running EchoVault AI

Launch the Streamlit interface:
```powershell
streamlit run app.py
```
Open your web browser at `http://localhost:8501`.

---

## 6. How Gemma Powers EchoVault

EchoVault uses Google's open-weight **Gemma** model as the language intelligence core across two vital phases:

1. **Information Extraction**:
   When a family story is ingested, Gemma inspects the verbatim account and produces a validated JSON payload containing:
   - Respected, evocative title and factual 2-3 sentence summary.
   - Named people and explicit relationships to the narrator.
   - Specific geographical anchors (towns, buildings, countries).
   - Temporal dates and approximate eras.
   - Notable verbatim quotations.
   - Explicit facts vs. narrator-declared uncertainties.

2. **Grounded Remembrance Synthesis**:
   When an inquiry is made, the Retrieval Agent fetches relevant source passages from SQLite FTS5. Gemma is prompted with strict systemic constraints:
   *Use only the provided memory evidence. If the information is missing, respond: "I couldn't find this information in your saved memories."*

---

## 7. Running the Test Suite

EchoVault includes automated tests covering schema validation, database operations, FTS5 search, duplicate rejection, Gemma JSON recovery, offline fallback, and Q&A abstention.

```powershell
python -m pytest tests/ -v
```

*Synthetic test fixtures are used exclusively. No personal family memories are ever included in automated test suites.*

---

## 8. Export, Portability & Privacy

- **Data Sovereignty**: All memories, audio recordings, entities, and database tables reside inside the `data/` directory on your local machine.
- **Portability**: EchoVault provides one-click export into:
  - **Complete JSON Archive**: Machine-readable format with full entities and provenance hashes.
  - **Markdown Memory Book**: Editorial book format formatted for reading, printing, or preservation.
- **Safe Deletion**: Deleting a memory purges all database records, entities, and FTS5 search entries.

---

## 9. Known Limitations & Roadmap

- **Audio Dependencies**: Audio transcription requires `faster-whisper` and system `ffmpeg`. If missing, EchoVault operates in text-first mode with manual transcript editing.
- **Hardware Headroom**: Gemma requires sufficient RAM or virtual memory. If memory allocation fails on resource-constrained systems, EchoVault automatically enters **Archival & Keyword Search Mode**, ensuring zero data loss.
- **Future Roadmap**:
  - Offline vector embedding hybrid search (`sqlite-vss` / `chromadb`).
  - Multi-speaker diarization for family interviews.
  - Interactive genealogical graph visualization.

---

## 10. License

EchoVault AI is released under the [Apache License 2.0](LICENSE).
Contributed with ❤️ for **Hacktoberfest 2026 — Week 4: Ghost in the Machine**.
