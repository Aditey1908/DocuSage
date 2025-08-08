import uuid
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
import faiss
from sentence_transformers import SentenceTransformer

# ✅ Gemini Semantic Chunker (batched + JSON mode + safe parse + fallback)
def _split_long_block(block: str, target_chars=800, max_chars=1200):
    """Split a single oversized block by sentences/lines into <= max_chars pieces."""
    # Prefer sentence boundaries; fall back to lines; finally hard split.
    # 1) sentence-ish split
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9(])', block.strip())
    if len(" ".join(parts)) < len(block) * 0.95:  # sentence split worked
        units = parts
    else:
        # 2) line split
        units = [u for u in block.splitlines() if u.strip()]
        if not units:
            # 3) last-resort hard split every ~500 chars
            units = [block[i:i+500] for i in range(0, len(block), 500)]

    chunks, cur, cur_len = [], [], 0
    for u in units:
        u = u.strip()
        if not u:
            continue
        if cur_len + len(u) <= max_chars:
            cur.append(u); cur_len += len(u)
        else:
            if cur:
                chunks.append({"title": "", "text": " ".join(cur).strip()})
            cur, cur_len = [u], len(u)
    if cur:
        chunks.append({"title": "", "text": " ".join(cur).strip()})
    return chunks

def chunk_fast(text: str, target_chars=800, max_chars=1200):
    """
    Fast, layout-aware chunker:
    - Splits on headings/numbered sections/tables/annexures
    - Recombines into ~target_chars, never exceeding max_chars
    - Splits any single oversize block further to obey max_chars
    """
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    blocks = re.split(
        r'(?m)(?=^#{1,3}\s+.+$)|(?=^\d+(?:\.\d+)*\s+.+$)|(?=^TABLE\b)|(?=^Annexure\b)',
        text
    )
    blocks = [b.strip() for b in blocks if b and b.strip()]

    # First ensure no single block exceeds max_chars
    normalized = []
    for b in blocks:
        if len(b) <= max_chars:
            normalized.append(b)
        else:
            # break this big boi down
            smalls = _split_long_block(b, target_chars=target_chars, max_chars=max_chars)
            normalized.extend([s["text"] for s in smalls])

    # Then coalesce into windows up to max_chars
    chunks, cur, cur_len = [], [], 0
    for b in normalized:
        # keep paragraph cohesion where possible
        paras = [p.strip() for p in re.split(r'\n{2,}', b) if p.strip()]
        block_text = "\n\n".join(paras) if paras else b
        if cur_len + len(block_text) <= max_chars:
            cur.append(block_text); cur_len += len(block_text)
        else:
            if cur:
                chunks.append({"title": "", "text": "\n\n".join(cur).strip()})
            cur, cur_len = [block_text], len(block_text)
    if cur:
        chunks.append({"title": "", "text": "\n\n".join(cur).strip()})
    return chunks

# ✅ Gemini Answer Generator (Google Generative AI)
def generate_answer_with_gemini(query: str, context: list):
    context_text = "\n".join(f"- {c['metadata']['text']}" for c in context)
    prompt = f"""
You are an intelligent assistant. Based on the following facts, answer the user's question clearly.

User Query:
"{query}"

Relevant Context:
{context_text}

Answer:
"""
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('models/gemini-2.0-flash')
    response = model.generate_content(prompt)
    return response.text.strip()


# ✅ FAISS setup
faiss_index = None
faiss_texts = []

# ✅ Load MiniLM model
model = SentenceTransformer("all-MiniLM-L6-v2")
dim = model.get_sentence_embedding_dimension()


# --------- MAIN PROCESSING FUNCTION ----------

def process_text_for_semantic_search(full_text: str, max_chunks: int = 200):
    """
    Chunks, embeds, and stores the provided text in FAISS.
    Returns the number of vectors indexed.
    """
    global faiss_index, faiss_texts
    print(f"Loaded text chars: {len(full_text)}")
    chunks = chunk_fast(full_text)
    print(f"Fast chunks: {len(chunks)}")
    if len(chunks) > max_chunks:
        print(f"Capping to first {max_chunks} chunks for speed.")
        chunks = chunks[:max_chunks]

    texts = [(c["text"] or "").strip() for c in chunks if (c["text"] or "").strip()]
    embs = model.encode(texts, batch_size=64, show_progress_bar=False)
    embs = embs.astype('float32')
    faiss_index = faiss.IndexFlatL2(dim)
    faiss_index.add(embs)
    faiss_texts = texts
    print(f"Indexed {len(texts)} vectors in FAISS.")
    return len(texts)

# Function to query FAISS index
def faiss_query(query: str, top_k: int = 5):
    global faiss_index, faiss_texts
    if faiss_index is None or not faiss_texts:
        raise RuntimeError("FAISS index is not built. Please process text first.")
    query_emb = model.encode([query], show_progress_bar=False).astype('float32')
    D, I = faiss_index.search(query_emb, top_k)
    results = []
    for idx in I[0]:
        if idx < len(faiss_texts):
            results.append({"metadata": {"text": faiss_texts[idx]}})
    return results
