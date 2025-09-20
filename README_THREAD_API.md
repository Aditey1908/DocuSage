# DocuSage - Document Chat with Memory

DocuSage is a document chat system that allows users to have persistent conversations with their documents. It implements a thread-based architecture for maintaining conversation history and context across multiple requests.

## Features

- **Thread-based Conversations**: Each document or set of documents has its own conversation thread
- **Memory Management**: Maintains conversation context with efficient token usage
- **Concurrency Handling**: Thread-specific locks and versioning for concurrent requests
- **Memory Compaction**: Automatically summarizes older parts of conversations to stay within token limits
- **TTL and Exhaustion Policies**: Automatic cleanup of expired threads and memory management

## API Endpoints

### Create a Thread

```
POST /threads
```

**Request Body**:
```json
{
  "document_url": "https://example.com/document.pdf",
  "memory_budget": 4000,  // Optional, default 4000 tokens
  "ttl_minutes": 120      // Optional, default 120 minutes (2 hours)
}
```

**Response**:
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "created",
  "document_info": {
    "url": "https://example.com/document.pdf",
    "characters": 12345
  }
}
```

### Send a Message

```
POST /messages
```

**Request Body**:
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "What is the main topic of this document?",
  "idempotency_key": "unique-request-id-123",  // Optional, auto-generated if not provided
  "memory_version": 1,  // Optional, for optimistic concurrency
  "parent_message_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"  // Optional, for ordering
}
```

**Response**:
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "8b5eda7a-2a8a-43d0-b11c-945f911531f1",
  "answer": "The main topic of this document is insurance policies and coverage details...",
  "parent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "thread_state": {
    "turns_used": 3,
    "memory_tokens": 1200,
    "state": "active"
  },
  "memory_version": 4
}
```

### Get Thread State

```
GET /threads/{thread_id}
```

**Response**:
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "active",
  "turns_used": 5,
  "memory_tokens": 1500,
  "memory_budget": 4000,
  "ttl_remaining_minutes": 110,
  "doc_ids": ["9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"],
  "index_version": "1.0",
  "created_at": 1632167419.3928089
}
```

### Reset Thread

```
POST /threads/{thread_id}/reset
```

**Response**:
```json
{
  "status": "reset",
  "thread_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Legacy Endpoint

For backward compatibility, the system still supports the original endpoint:

```
POST /process
```

This endpoint handles multiple questions in one request but doesn't maintain conversation history between requests.

## Thread Memory Management

The system automatically manages conversation memory:

- **Rolling Summary**: Older turns are summarized to save tokens
- **Entities & Facts**: Key information is extracted and maintained
- **Last K Turns**: Most recent turns are kept verbatim
- **TTL**: Threads expire after inactivity (default 2 hours)
- **Exhaustion**: When memory limit or turn limit is reached, thread signals reset

## Installation & Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   VOYAGE_API_KEY=your_voyage_api_key
   ASTRA_DB_ID=your_astra_db_id
   ASTRA_DB_REGION=your_astra_db_region
   ASTRA_DB_APPLICATION_TOKEN=your_astra_db_token
   ASTRA_KEYSPACE=default_keyspace
   ASTRA_COLLECTION=rag_chunks
   OPENAI_LLM_MODEL=gpt-4.1-nano-2025-04-14
   ```

3. Run the application:
   ```
   python app_thread.py
   ```

## Usage Flow

1. Create a thread for your document
2. Send questions one by one to the same thread
3. The system will maintain context between questions
4. When you're done, the thread will expire automatically after the TTL
5. If memory is exhausted, reset the thread to start fresh
