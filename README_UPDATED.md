# **DocuSage - The Oracle of Files**

This project implements a **streamlined, production-ready pipeline** for transforming complex PDF documents into **retrieval-ready vector data** for AI applications.  
It combines robust text extraction, semantic chunking, and vector database integration to enable **high-accuracy, context-rich responses** in Retrieval-Augmented Generation (RAG) systems.

---

## **Overview**
- **PDF Parsing** — High-fidelity extraction using *PyMuPDF* with advanced heuristics to remove recurring headers, footers, and boilerplate.  
- **Semantic Chunking** — Structure-aware, token-conscious segmentation that preserves context for downstream language models.  
- **Vector Storage** — Embeddings generated with *OpenAI* / *VoyageAI* and stored in **Astra DB** with optimized indexing for fast, relevant search.  
- **Thread-Based Memory** — Maintains conversation context across multiple questions with memory management.
- **End-to-End Automation** — Modular design with an orchestrated runner that ingests, processes, embeds, stores, and cleans data in a single execution flow.  

---

## **Key Modules**
- **`docusage.py`** — Consolidated application with all API endpoints for thread-based document chat and legacy processing.
- **`pdf_parser.py`** — Converts PDFs into clean, structured text while detecting and preserving tables and lists.  
- **`chunker_reworked.py`** — Builds a hierarchical content model, then chunks text into retrieval-friendly segments with contextual overlap.  
- **`thread_manager.py`** — Manages conversation threads, memory, and state for document chats.
- **`runner.py`** — Orchestrates parsing, embedding, storage, and cleanup with parallel execution for scale.  
- **`create_rag_collection.py`** — Initializes an **Astra DB** vector collection with tuned parameters for semantic search.  

---

## **Technology Stack**
- **Languages**: Python 3.10+  
- **Core Libraries**: PyMuPDF, astrapy, OpenAI API, VoyageAI API, python-dotenv, Flask  
- **Vector DB**: Astra DB (DataStax)  

---

## **Setup**

1. **Install dependencies**:  
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables in `.env` file**:
   ```
   OPENAI_API_KEY=your_openai_api_key
   VOYAGE_API_KEY=your_voyage_api_key
   ASTRA_DB_ID=your_astra_db_id
   ASTRA_DB_REGION=your_astra_db_region
   ASTRA_DB_APPLICATION_TOKEN=your_astra_db_application_token
   ASTRA_KEYSPACE=default_keyspace
   ASTRA_COLLECTION=rag_chunks
   OPENAI_LLM_MODEL=gpt-4.1-nano-2025-04-14
   ```

3. **Create the RAG collection in AstraDB** (optional, only if you need to reset the collection):
   ```
   python create_rag_collection.py
   ```

## **Running the Server**

```bash
python docusage.py
```

The server runs on port 5000 by default.

---

## **API Endpoints**

### Thread-Based API

- **Create Thread**
  - `POST /threads`
  - Request: `{"document_url": "https://example.com/document.pdf", "memory_budget": 4000, "ttl_minutes": 120}`

- **Get Thread State**
  - `GET /threads/{thread_id}`

- **Reset Thread**
  - `POST /threads/{thread_id}/reset`

- **Process Message**
  - `POST /messages`
  - Request: `{"thread_id": "your-thread-id", "content": "question content", "idempotency_key": "optional-key", "memory_version": "optional-version", "parent_message_id": "optional-parent-id"}`

### Legacy API

- **Process Document**
  - `POST /process`
  - Request: `{"documents": "https://example.com/document.pdf", "questions": ["question 1", "question 2"]}`

---

## **File Structure**

- `docusage.py`: Main application file with all API endpoints
- `runner.py`: RAG pipeline for embedding, search and answer generation
- `pdf_parser.py`: PDF text extraction
- `chunker_reworked.py`: Text chunking
- `thread_manager.py`: Thread and memory management
- `data/`: Directory for document storage
  - `thread_documents/`: Storage for thread documents

---

## **Shutting Down**

Press `Ctrl+C` to properly shut down the server and all processes.
