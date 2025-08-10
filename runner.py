# Requirements:
# pip install openai voyageai astrapy python-dotenv

import os
import sys
import re
import json
import uuid
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
import voyageai
from astrapy import DataAPIClient

# Load environment variables
load_dotenv()

# Constants
BATCH_SIZE_EMBEDDINGS = 128
BATCH_SIZE_INSERTS = 1000
ANN_K = 20  # Top K from vector search
TOP_M_FOR_LLM = 5  # Top M after reranking (before adding neighbors)
DIM = 1536

# Configuration from environment
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
ASTRA_DB_ID = os.environ["ASTRA_DB_ID"]
ASTRA_DB_REGION = os.environ["ASTRA_DB_REGION"]
ASTRA_DB_APPLICATION_TOKEN = os.environ["ASTRA_DB_APPLICATION_TOKEN"]
ASTRA_KEYSPACE = os.getenv("ASTRA_KEYSPACE", "default_keyspace")
ASTRA_COLLECTION = os.getenv("ASTRA_COLLECTION", "rag_chunks")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4.1-nano-2025-04-14")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
voyage_client = voyageai.Client(api_key=VOYAGE_API_KEY)

# Sample questions (hardcoded for now)
QUESTIONS = [
    "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
    "What is the waiting period for pre-existing diseases (PED) to be covered?",
    "Does this policy cover maternity expenses, and what are the conditions?",
    "What is the waiting period for cataract surgery?",
    "Are the medical expenses for an organ donor covered under this policy?",
    "What is the No Claim Discount (NCD) offered in this policy?",
    "Is there a benefit for preventive health check-ups?",
    "How does the policy define a 'Hospital'?",
    "What is the extent of coverage for AYUSH treatments?",
    "Are there any sub-limits on room rent and ICU charges for Plan A?"
]

def normalize_text(text: str) -> str:
    """Normalize line endings and clean up text."""
    return text.replace('\r\n', '\n').replace('\r', '\n').strip()

def parse_chunks(file_path: str) -> List[Dict[str, Any]]:
    """Parse chunks from the input file."""
    print(f"📖 Reading file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)
    
    content = normalize_text(content)
    
    # Regex to match chunk headers like "=== CHUNK 1 ===" or similar patterns
    chunk_pattern = r'===\s*CHUNK\s+(\d+)\s*==='
    
    # Split content by chunk headers
    parts = re.split(chunk_pattern, content)
    
    chunks = []
    chunk_index = 1
    
    # Process the split parts
    for i in range(1, len(parts), 2):  # Skip first part (before first chunk), then take every other part
        if i + 1 < len(parts):
            chunk_number = parts[i]
            chunk_text = parts[i + 1].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunk_id = f"c{chunk_index}"
                chunks.append({
                    "id": chunk_id,
                    "text_full": chunk_text,
                    "meta": {"chunk_index": chunk_index}
                })
                chunk_index += 1
    
    print(f"✅ Parsed {len(chunks)} chunks")
    
    if chunks:
        print(f"📋 First chunk sample (ID: {chunks[0]['id']}):")
        sample_text = chunks[0]['text_full'][:200] + "..." if len(chunks[0]['text_full']) > 200 else chunks[0]['text_full']
        print(f"   {sample_text}")
    
    return chunks

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a batch of texts using OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"❌ Error getting embeddings: {e}")
        raise

def embed_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Embed all chunks using batched requests."""
    print(f"🔍 Embedding {len(chunks)} chunks...")
    
    start_time = time.time()
    
    for i in range(0, len(chunks), BATCH_SIZE_EMBEDDINGS):
        batch_chunks = chunks[i:i + BATCH_SIZE_EMBEDDINGS]
        batch_texts = [chunk["text_full"] for chunk in batch_chunks]
        
        print(f"   Processing embedding batch {i//BATCH_SIZE_EMBEDDINGS + 1}/{(len(chunks) + BATCH_SIZE_EMBEDDINGS - 1)//BATCH_SIZE_EMBEDDINGS}")
        
        embeddings = get_embeddings_batch(batch_texts)
        
        for j, embedding in enumerate(embeddings):
            chunks[i + j]["$vector"] = embedding
    
    embedding_time = time.time() - start_time
    print(f"✅ Embeddings completed in {embedding_time:.2f} seconds")
    
    return chunks

def store_chunks_in_astra(chunks: List[Dict[str, Any]], request_id: str):
    """Store chunks in Astra DB with batched inserts."""
    print(f"💾 Storing {len(chunks)} chunks in Astra DB...")
    
    # Setup Astra connection
    endpoint = f"https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com"
    client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
    db = client.get_database_by_api_endpoint(endpoint, token=ASTRA_DB_APPLICATION_TOKEN, keyspace=ASTRA_KEYSPACE)
    collection = db.get_collection(ASTRA_COLLECTION)
    
    # Add request_id to all chunks
    for chunk in chunks:
        chunk["request_id"] = request_id
    
    start_time = time.time()
    
    # Insert in batches
    for i in range(0, len(chunks), BATCH_SIZE_INSERTS):
        batch = chunks[i:i + BATCH_SIZE_INSERTS]
        print(f"   Inserting batch {i//BATCH_SIZE_INSERTS + 1}/{(len(chunks) + BATCH_SIZE_INSERTS - 1)//BATCH_SIZE_INSERTS}")
        
        try:
            collection.insert_many(batch)
        except Exception as e:
            print(f"❌ Error inserting batch: {e}")
            raise
    
    storage_time = time.time() - start_time
    print(f"✅ Storage completed in {storage_time:.2f} seconds")
    
    return collection

def search_and_rerank(question: str, collection, request_id: str, total_chunks: int) -> List[Dict[str, Any]]:
    """Search for relevant chunks and rerank them."""
    print(f"🔍 Processing question: {question[:100]}...")
    
    # Embed the question
    print("   📝 Embedding question...")
    question_embedding = get_embeddings_batch([question])[0]
    
    # Vector search in Astra
    print(f"   🎯 Vector search (top {ANN_K})...")
    search_results = collection.find(
        filter={"request_id": request_id},
        sort={"$vector": question_embedding},
        limit=ANN_K
    )
    
    search_results_list = list(search_results)
    print(f"   📊 Found {len(search_results_list)} results from vector search")
    
    if not search_results_list:
        print("   ⚠  No results found in vector search")
        return []
    
    ann_ids = [doc["id"] for doc in search_results_list]
    print(f"   🔢 ANN hit IDs: {ann_ids}")
    
    # Rerank using VoyageAI
    print(f"   🎯 Reranking with VoyageAI...")
    documents_for_rerank = [doc["text_full"] for doc in search_results_list]
    
    try:
        rerank_response = voyage_client.rerank(
            model="rerank-2.5-lite",
            query=question,
            documents=documents_for_rerank
        )
        
        # Sort by relevance score and get top results
        reranked_results = []
        for result in rerank_response.results:
            original_doc = search_results_list[result.index]
            original_doc["rerank_score"] = result.relevance_score
            reranked_results.append(original_doc)
        
        # Sort by rerank score (highest first)
        reranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        reranked_ids = [doc["id"] for doc in reranked_results]
        rerank_scores = [f"{doc['rerank_score']:.3f}" for doc in reranked_results]
        print(f"   🎯 Reranked IDs: {reranked_ids}")
        print(f"   📈 Rerank scores: {rerank_scores}")
        
        # Take top M results
        top_results = reranked_results[:TOP_M_FOR_LLM]
        print(f"   🏆 Selected top {len(top_results)} results for LLM")
        
    except Exception as e:
        print(f"❌ Error during reranking: {e}")
        # Fallback to original search results
        top_results = search_results_list[:TOP_M_FOR_LLM]
        print(f"   🔄 Fallback: using top {len(top_results)} from vector search")
    
    # Add immediate neighbors
    print("   👥 Adding immediate neighbors...")
    neighbor_chunks = set()
    
    for doc in top_results:
        chunk_index = doc["meta"]["chunk_index"]
        
        # Add previous chunk (if exists)
        if chunk_index > 1:
            neighbor_chunks.add(chunk_index - 1)
        
        # Add next chunk (if exists)
        if chunk_index < total_chunks:
            neighbor_chunks.add(chunk_index + 1)
    
    # Retrieve neighbor chunks from Astra
    final_chunks = list(top_results)  # Start with reranked results
    
    if neighbor_chunks:
        print(f"   🔍 Fetching {len(neighbor_chunks)} neighbor chunks: {sorted(neighbor_chunks)}")
        
        for neighbor_index in neighbor_chunks:
            # Check if we already have this chunk
            if not any(doc["meta"]["chunk_index"] == neighbor_index for doc in final_chunks):
                neighbor_results = collection.find(
                    filter={
                        "request_id": request_id,
                        "meta.chunk_index": neighbor_index
                    },
                    limit=1
                )
                neighbor_list = list(neighbor_results)
                if neighbor_list:
                    final_chunks.append(neighbor_list[0])
    
    # Sort by chunk_index for coherent context
    final_chunks.sort(key=lambda x: x["meta"]["chunk_index"])
    
    final_ids = [doc["id"] for doc in final_chunks]
    final_indices = [doc["meta"]["chunk_index"] for doc in final_chunks]
    print(f"   📚 Final context chunks: {final_ids} (indices: {final_indices})")
    
    return final_chunks

def create_llm_context(chunks: List[Dict[str, Any]]) -> str:
    """Create formatted context for LLM."""
    context_parts = []
    
    for chunk in chunks:
        context_parts.append(f"[Chunk {chunk['id']}]")
        context_parts.append(chunk["text_full"])
        context_parts.append("")  # Empty line for separation
    
    return "\n".join(context_parts)

def answer_question(question: str, context: str) -> str:
    """Get answer from LLM using the provided context."""
    system_prompt = """You are a precise insurance policy assistant. Answer questions based solely on the provided document context.

Guidelines:
- Provide direct, factual answers focusing on the core question
- Start with "Yes" or "No" for yes/no questions, then explain briefly
- Include specific numbers, time periods, and key conditions
- Keep answers concise (1-3 sentences) while being complete
- Avoid long lists unless specifically asked for comprehensive details
- State exact waiting periods, percentages, and limits when mentioned
- Only say "Not found in the provided document." if the information is truly absent after thorough search

Answer format: Be direct and fact-focused, similar to policy summaries."""
    
    # Check context size and truncate if too large (GPT-4o-mini has ~128K token limit)
    max_context_chars = 1000000  # ~12K tokens, leaving room for system prompt and response
    if len(context) > max_context_chars:
        print(f"   ⚠  Context too large ({len(context):,} chars), truncating to {max_context_chars:,}")
        context = context[:max_context_chars] + "\n\n[Context truncated due to size limits]"
    
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Debug info
        finish_reason = response.choices[0].finish_reason
        tokens_used = response.usage.completion_tokens if response.usage else "unknown"
        print(f"   🔧 Debug: finish_reason={finish_reason}, tokens_used={tokens_used}")
        
        if not answer:
            return "Error: Empty response from LLM."
        
        return answer
        
    except Exception as e:
        print(f"❌ Error getting LLM response: {e}")
        print(f"   📏 Context size was: {len(context):,} chars / {len(context.encode('utf-8')):,} bytes")
        print(f"   📝 Question was: {question[:100]}...")
        return f"Error: {str(e)}"

def cleanup_request_data(collection, request_id: str):
    """Clean up all documents with the current request_id."""
    print(f"🧹 Cleaning up request data (request_id: {request_id})...")
    
    try:
        # Count documents before deletion
        try:
            count_before = collection.count_documents(filter={"request_id": request_id}, upper_bound=10000)
        except:
            # Handle API signature differences
            count_before = collection.count_documents(filter={"request_id": request_id})
        
        print(f"   🗑  Deleting {count_before} documents...")
        
        # Delete all documents with this request_id
        delete_result = collection.delete_many(filter={"request_id": request_id})
        print(f"   ✅ Deleted {delete_result.deleted_count} documents")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python runner.py /path/to/chunked.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    request_id = str(uuid.uuid4())
    
    print(f"🚀 Starting RAG pipeline (request_id: {request_id})")
    print(f"📄 Input file: {file_path}")
    print(f"🤖 LLM Model: {OPENAI_LLM_MODEL}")
    print(f"🎯 ANN_K: {ANN_K}, TOP_M_FOR_LLM: {TOP_M_FOR_LLM}")
    print("-" * 80)
    
    start_total = time.time()
    
    try:
        # Step 1: Parse chunks
        chunks = parse_chunks(file_path)
        if not chunks:
            print("❌ No chunks found in file")
            sys.exit(1)
        
        total_chunks = len(chunks)
        
        # Step 2: Embed chunks
        chunks_with_embeddings = embed_chunks(chunks)
        
        # Step 3: Store in Astra
        collection = store_chunks_in_astra(chunks_with_embeddings, request_id)
        
        print("-" * 80)
        
        # Step 4: Process questions
        answers = []
        
        for i, question in enumerate(QUESTIONS, 1):
            print(f"\n❓ Question {i}/{len(QUESTIONS)}")
            
            # Search and rerank
            relevant_chunks = search_and_rerank(question, collection, request_id, total_chunks)
            
            if not relevant_chunks:
                answer = "Not found in the provided document."
                print(f"   💬 Answer: {answer}")
            else:
                # Create context
                context = create_llm_context(relevant_chunks)
                context_size = len(context.encode('utf-8'))
                print(f"   📏 Context size: {context_size:,} bytes ({len(relevant_chunks)} chunks)")
                
                # Get answer
                print("   🤖 Generating answer...")
                answer = answer_question(question, context)
                print(f"   💬 Answer: {answer}")
            
            answers.append(answer)
        
        # Step 5: Output results
        print("\n" + "=" * 80)
        print("📋 FINAL RESULTS")
        print("=" * 80)
        
        results = {
            "questions": QUESTIONS,
            "answers": answers
        }
        
        print(json.dumps(results, indent=2))
        
        # Step 6: Cleanup
        print("\n" + "-" * 80)
        cleanup_request_data(collection, request_id)
        
        total_time = time.time() - start_total
        print(f"✅ Pipeline completed in {total_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        # Still attempt cleanup
        try:
            endpoint = f"https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com"
            client = DataAPIClient(ASTRA_DB_APPLICATION_TOKEN)
            db = client.get_database_by_api_endpoint(endpoint, token=ASTRA_DB_APPLICATION_TOKEN, keyspace=ASTRA_KEYSPACE)
            collection = db.get_collection(ASTRA_COLLECTION)
            cleanup_request_data(collection, request_id)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()