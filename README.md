# **DocuSage - The Oracle of Files**

This project implements a **streamlined, production-ready pipeline** for transforming complex PDF documents into **retrieval-ready vector data** for AI applications.  
It combines robust text extraction, semantic chunking, and vector database integration to enable **high-accuracy, context-rich responses** in Retrieval-Augmented Generation (RAG) systems.

---

## **Overview**
- **PDF Parsing** — High-fidelity extraction using *PyMuPDF* with advanced heuristics to remove recurring headers, footers, and boilerplate.  
- **Semantic Chunking** — Structure-aware, token-conscious segmentation that preserves context for downstream language models.  
- **Vector Storage** — Embeddings generated with *OpenAI* / *VoyageAI* and stored in **Astra DB** with optimized indexing for fast, relevant search.  
- **End-to-End Automation** — Modular design with an orchestrated runner that ingests, processes, embeds, stores, and cleans data in a single execution flow.  

---

## **Key Modules**
- **`pdf_parser.py`** — Converts PDFs into clean, structured text while detecting and preserving tables and lists.  
- **`chunker_reworked.py`** — Builds a hierarchical content model, then chunks text into retrieval-friendly segments with contextual overlap.  
- **`create_rag_collection.py`** — Initializes an **Astra DB** vector collection with tuned parameters for semantic search.  
- **`runner.py`** — Orchestrates parsing, embedding, storage, and cleanup with parallel execution for scale.  

---

## **Technology Stack**
- **Languages**: Python 3.10+  
- **Core Libraries**: PyMuPDF, astrapy, OpenAI API, VoyageAI API, python-dotenv  
- **Vector DB**: Astra DB (DataStax)  

---

## **Setup**
1. **Clone the repository**  
2. **Install dependencies**:  
   ```bash
   pip install -r requirements.txt

   ## Frontend

   This repo contains two frontends: the legacy `frontend` (Vite) and a newer Next.js app at `frontend_new`.

   To run both backend and the new frontend together for development, use the helper script at the repo root:

   PowerShell:

   ```powershell
   .\start_all.ps1
   ```

   This launches the Flask backend and the Next.js dev server (`frontend_new`). The backend endpoint is available at `http://localhost:5000` and the frontend dev server defaults to `http://localhost:3000`.

   If you prefer to run manually:

   1. Start the backend:

   ```powershell
   python DocuSage/app.py
   ```

   2. Start the frontend:

   ```powershell
   cd DocuSage/frontend_new
   npm install
   npm run dev
   ```

---

## Critical Implementation Detail (read this first)

- **Chunking defaults:** The project uses a hierarchical + semantic chunking strategy with defaults of *max_tokens = 500* and *overlap_tokens = 75*. Those numbers are counted as words using Python's `split()` (not model/tokenizer tokens).
- **Where it's implemented:** See `chunker_reworked.py` — the `hierarchical_chunk_file()` call sets `max_tokens` and `overlap_tokens` and `create_semantic_chunks()` enforces them.
- **Why it matters:** Because counts are word-based, the default does NOT map 1:1 to LLM tokenizer tokens. For production (precise token budgets, LLM prompt sizing, or billing-sensitive setups) switch to a tokenizer-aware token counter (e.g., `tiktoken` or the encoder used by your embedding/LLM model) before choosing chunk sizes.
- **How to change quickly:** Edit the parameters when calling `hierarchical_chunk_file()` or pass different `max_tokens`/`overlap_tokens` values from the ingestion pipeline. If you want strict model-token limits, replace `len(text.split())` with a tokenizer function in `HierarchicalNode.count_tokens()` and related split helpers.
- **Recommendation (practical):** Keep hierarchical+semantic chunking (it preserves headings/context), but set `max_tokens` to ~400–600 model tokens (use tokenizer) and overlap to ~20–30% of that value. This balances retrieval precision and prompt-budget efficiency.

---

## Deployment

- **Live deployment:** This project is deployed — backend and frontend are configured for hosting (see `render.yaml`, `Procfile` and `vercel.json`). The frontend is prepared for Vercel and the backend is prepared for Render/Heroku-style deployment; check your Render / Vercel dashboards or your configured domains to view the live app.
- **How to verify:** Visit your deployment dashboards or the configured domain for the app. For backend health, hit the backend health endpoint (if configured) `https://<your-backend-domain>/health` or the API root. For frontend, open the site domain and use the UI to run a sample query against the backend.

## Implementation logic (practical details)

- **Ingestion:** Files are parsed by `pdf_parser.py` into cleaned text with preserved page metadata and simple table/list detection.
- **Preprocessing:** `clean_text()` removes repeated headers/footers and normalizes whitespace; OCR confidence filtering is not enabled by default but can be added in the parser.
- **Chunking:** `chunker_reworked.py` builds a hierarchical tree of the document (headings, lists, tables) then creates semantically-coherent chunks with contextual overlap. Defaults are `max_tokens=500` (word count) and `overlap_tokens=75` (word count). Large sections are split while preserving context headers.
- **Embedding generation:** Embeddings are produced in batch (see `create_rag_collection.py`). The repo supports using OpenAI embeddings or an alternative model; embeddings are stored alongside metadata for provenance.
- **Vector storage & indexing:** Vectors and metadata are stored through an adapter layer (Astra DB by default in this repo). The index uses ANN (HNSW/IVF options) and supports metadata filtering for domain-specific queries.
- **Retrieval & ranking:** Query embedding → ANN top-N retrieval → composite re-ranking (cosine + lexical/BM25 + heuristics). Deduplication and chunk-quality scoring reduce noise before context assembly.
- **Prompting & LLM:** The assembled context is fed to the LLM with a strict prompt that requests citation of chunks and refusal when evidence is insufficient. Answers are post-validated to ensure all citations map to included chunks.
- **Operational concerns:** The pipeline supports incremental upserts (embeddings versioned per `doc_version`), cache invalidation on updates, and configurable token-budget strategies (summaries-first cascade recommended).

---

If you want, I can (A) replace the current word-based token counting with a tokenizer-based approach in `chunker_reworked.py`, or (B) add a short `DEPLOY.md` with exact deploy/health-check steps for Render/Vercel. Which do you prefer?

