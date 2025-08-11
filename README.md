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
