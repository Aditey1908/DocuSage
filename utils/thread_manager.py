"""
Thread Manager for Document Chat System
Manages conversation threads, memory, and state for document-based chats
"""

import os
import time
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import threading
from collections import deque
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables before using them
load_dotenv(override=True)

# Constants for memory management
MAX_MEMORY_TOKENS = 4000  # Maximum tokens to keep in memory
MAX_TURNS = 30  # Maximum conversation turns before reset
TTL_MINUTES = 120  # Default TTL for threads (2 hours)
LAST_K_TURNS = 5  # Number of recent turns to keep verbatim
COMPACTION_THRESHOLD = 10  # Turns before compaction

# Thread locks for concurrency control
thread_locks = {}
thread_lock = threading.Lock()  # Global lock for thread_locks dictionary

class ThreadMemory:
    """In-memory storage for thread state and memory"""
    def __init__(self):
        self.threads = {}  # thread_id -> thread_data
        self.messages = {}  # thread_id -> [messages]
        self.working_memory = {}  # thread_id -> working memory
        self.ttl_timestamps = {}  # thread_id -> last_activity_time
        self.version = {}  # thread_id -> version number
    
    def cleanup_expired(self):
        """Clean up expired threads based on TTL"""
        now = time.time()
        expired = []
        
        for thread_id, timestamp in self.ttl_timestamps.items():
            if now - timestamp > TTL_MINUTES * 60:
                expired.append(thread_id)
        
        for thread_id in expired:
            self.delete_thread(thread_id)
    
    def delete_thread(self, thread_id: str):
        """Delete all data for a thread"""
        with thread_lock:
            if thread_id in thread_locks:
                del thread_locks[thread_id]
        
        if thread_id in self.threads:
            del self.threads[thread_id]
        
        if thread_id in self.messages:
            del self.messages[thread_id]
        
        if thread_id in self.working_memory:
            del self.working_memory[thread_id]
        
        if thread_id in self.ttl_timestamps:
            del self.ttl_timestamps[thread_id]
        
        if thread_id in self.version:
            del self.version[thread_id]

# Global in-memory storage
memory = ThreadMemory()

# Initialize OpenAI client with fallback for testing
try:
    # Try to read directly from .env file if environment variable isn't working
    import dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    env_vars = dotenv.dotenv_values(dotenv_path)
    api_key = os.environ.get("OPENAI_API_KEY") or env_vars.get("OPENAI_API_KEY")
    
    if not api_key:
        print("WARNING: OPENAI_API_KEY not found in environment variables or .env file. Using dummy key for testing.")
        api_key = "dummy_key_for_testing"  # This will fail API calls but prevent initialization error
    else:
        print("OpenAI API key loaded successfully")
        
    openai_client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"ERROR initializing OpenAI client: {str(e)}")
    # Still create a client with dummy key to prevent initialization errors
    openai_client = OpenAI(api_key="dummy_key_for_testing")

def acquire_thread_lock(thread_id: str) -> bool:
    """Acquire lock for a thread, with timeout"""
    with thread_lock:
        if thread_id not in thread_locks:
            thread_locks[thread_id] = threading.Lock()
    
    return thread_locks[thread_id].acquire(timeout=10)  # 10-second timeout

def release_thread_lock(thread_id: str):
    """Release lock for a thread"""
    with thread_lock:
        if thread_id in thread_locks:
            try:
                thread_locks[thread_id].release()
            except RuntimeError:
                # Lock wasn't acquired, ignore
                pass

def create_thread(doc_ids: List[str], memory_budget: int = MAX_MEMORY_TOKENS, 
                 ttl_minutes: int = TTL_MINUTES) -> str:
    """Create a new thread for document chat
    
    Args:
        doc_ids: List of document IDs associated with this thread
        memory_budget: Max tokens to keep in memory
        ttl_minutes: Inactivity timeout in minutes
    
    Returns:
        thread_id: Unique ID for the thread
    """
    thread_id = str(uuid.uuid4())
    
    # Initialize thread data
    thread_data = {
        "thread_id": thread_id,
        "doc_ids": doc_ids,
        "created_at": time.time(),
        "index_version": "1.0",
        "memory_budget": memory_budget,
        "ttl_minutes": ttl_minutes,
        "turns_used": 0,
        "memory_tokens": 0,
        "exhausted": False
    }
    
    # Initialize working memory
    working_memory = {
        "rolling_summary": "",
        "entities_facts": {},
        "last_k_turns": deque(maxlen=LAST_K_TURNS)
    }
    
    # Store in memory
    memory.threads[thread_id] = thread_data
    memory.messages[thread_id] = []
    memory.working_memory[thread_id] = working_memory
    memory.ttl_timestamps[thread_id] = time.time()
    memory.version[thread_id] = 1
    
    return thread_id

def get_thread_state(thread_id: str) -> Dict[str, Any]:
    """Get the current state of a thread
    
    Args:
        thread_id: Thread ID
    
    Returns:
        Thread state including turns used, memory size, etc.
    """
    if thread_id not in memory.threads:
        return {"error": "Thread not found"}
    
    thread = memory.threads[thread_id]
    
    # Update with latest stats
    ttl_remaining = TTL_MINUTES * 60 - (time.time() - memory.ttl_timestamps[thread_id])
    ttl_remaining_minutes = max(0, int(ttl_remaining / 60))
    
    return {
        "thread_id": thread_id,
        "state": "active" if not thread["exhausted"] else "exhausted",
        "turns_used": thread["turns_used"],
        "memory_tokens": thread["memory_tokens"],
        "memory_budget": thread["memory_budget"],
        "ttl_remaining_minutes": ttl_remaining_minutes,
        "doc_ids": thread["doc_ids"],
        "index_version": thread["index_version"],
        "created_at": thread["created_at"]
    }

def reset_thread(thread_id: str) -> Dict[str, Any]:
    """Reset a thread's working memory while preserving thread metadata
    
    Args:
        thread_id: Thread ID
    
    Returns:
        Status of reset operation
    """
    if thread_id not in memory.threads:
        return {"error": "Thread not found"}
    
    # Acquire lock
    if not acquire_thread_lock(thread_id):
        return {"error": "Could not acquire thread lock"}
    
    try:
        # Keep thread data but reset counts
        memory.threads[thread_id]["turns_used"] = 0
        memory.threads[thread_id]["memory_tokens"] = 0
        memory.threads[thread_id]["exhausted"] = False
        
        # Reset working memory
        memory.working_memory[thread_id] = {
            "rolling_summary": "",
            "entities_facts": {},
            "last_k_turns": deque(maxlen=LAST_K_TURNS)
        }
        
        # Keep messages for history
        memory.ttl_timestamps[thread_id] = time.time()
        memory.version[thread_id] += 1
        
        return {"status": "reset", "thread_id": thread_id}
    finally:
        release_thread_lock(thread_id)

def add_message(thread_id: str, role: str, content: str, 
               idempotency_key: str, parent_message_id: str = None, 
               memory_version: int = None) -> Dict[str, Any]:
    """Add a message to a thread
    
    Args:
        thread_id: Thread ID
        role: Message role ("user" or "assistant")
        content: Message content
        idempotency_key: Client-provided key for deduplication
        parent_message_id: Parent message ID for ordering
        memory_version: Expected thread version for optimistic concurrency
    
    Returns:
        Added message data or error
    """
    # Check if thread exists
    if thread_id not in memory.threads:
        return {"error": "Thread not found"}
    
    # Check for idempotency
    for msg in memory.messages[thread_id]:
        if msg.get("idempotency_key") == idempotency_key:
            # Return existing message
            return {
                "message_id": msg["message_id"],
                "thread_id": thread_id,
                "status": "already_exists"
            }
    
    # Check version for optimistic concurrency
    if memory_version and memory_version != memory.version[thread_id]:
        return {
            "error": "Version conflict",
            "expected": memory_version,
            "current": memory.version[thread_id]
        }
    
    # Check parent exists if specified
    if parent_message_id:
        parent_exists = any(msg["message_id"] == parent_message_id for msg in memory.messages[thread_id])
        if not parent_exists:
            return {"error": f"Parent message {parent_message_id} not found"}
    
    # Acquire thread lock
    if not acquire_thread_lock(thread_id):
        return {"error": "Could not acquire thread lock"}
    
    try:
        # Check if thread is exhausted
        if memory.threads[thread_id]["exhausted"]:
            return {"error": "Thread exhausted, reset required"}
        
        # Create message
        message_id = str(uuid.uuid4())
        timestamp = time.time()
        
        message = {
            "message_id": message_id,
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "created_at": timestamp,
            "parent_id": parent_message_id,
            "idempotency_key": idempotency_key
        }
        
        # Add to messages
        memory.messages[thread_id].append(message)
        
        # Update thread stats
        memory.threads[thread_id]["turns_used"] += 1
        memory.ttl_timestamps[thread_id] = timestamp
        
        # If it's a user or assistant message, add to working memory
        if role in ["user", "assistant"]:
            memory.working_memory[thread_id]["last_k_turns"].append({
                "role": role,
                "content": content
            })
        
        # Estimate token count (rough approximation)
        tokens = len(content.split())
        memory.threads[thread_id]["memory_tokens"] += tokens
        
        # Check for memory compaction needs
        if (memory.threads[thread_id]["turns_used"] % COMPACTION_THRESHOLD == 0 or
            memory.threads[thread_id]["memory_tokens"] > memory.threads[thread_id]["memory_budget"] * 0.8):
            compact_memory(thread_id)
        
        # Check for exhaustion
        if (memory.threads[thread_id]["turns_used"] >= MAX_TURNS or
            memory.threads[thread_id]["memory_tokens"] >= memory.threads[thread_id]["memory_budget"]):
            memory.threads[thread_id]["exhausted"] = True
        
        # Increment version
        memory.version[thread_id] += 1
        
        return {
            "message_id": message_id,
            "thread_id": thread_id,
            "role": role,
            "created_at": timestamp,
            "memory_version": memory.version[thread_id]
        }
    finally:
        release_thread_lock(thread_id)

def compact_memory(thread_id: str):
    """Compact thread memory by summarizing older turns
    
    Args:
        thread_id: Thread ID to compact
    """
    if thread_id not in memory.threads:
        return
    
    # Get current working memory
    working_memory = memory.working_memory[thread_id]
    
    # If we have a rolling summary and enough past turns, summarize
    past_messages = memory.messages[thread_id][:-LAST_K_TURNS] if len(memory.messages[thread_id]) > LAST_K_TURNS else []
    
    if not past_messages:
        return  # Nothing to summarize
    
    # Prepare messages to summarize
    messages_to_summarize = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in past_messages
        if msg["role"] in ["user", "assistant"]
    ]
    
    if not messages_to_summarize:
        return  # No user/assistant messages to summarize
    
    # Current rolling summary
    current_summary = working_memory["rolling_summary"]
    
    # Prepare system prompt
    system_prompt = """You are a conversation summarizer. 
    Summarize the conversation history into a concise summary that captures key points, 
    questions asked, and information provided. Focus on facts, entities, and important context.
    Be brief but comprehensive."""
    
    try:
        # Format messages for summarization
        openai_messages = []
        if current_summary:
            openai_messages.append({"role": "system", "content": system_prompt})
            openai_messages.append({"role": "user", "content": "Here is the current summary:\n" + current_summary})
            openai_messages.append({"role": "user", "content": "Update the summary with these new conversation turns:"})
            
            # Add messages
            for msg in messages_to_summarize:
                openai_messages.append(msg)
        else:
            openai_messages.append({"role": "system", "content": system_prompt})
            openai_messages.append({"role": "user", "content": "Summarize this conversation:"})
            
            # Add messages
            for msg in messages_to_summarize:
                openai_messages.append(msg)
        
        # Generate summary
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Use most appropriate model
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.3
        )
        
        # Update rolling summary
        new_summary = response.choices[0].message.content.strip()
        working_memory["rolling_summary"] = new_summary
        
        # Update token count (approximate)
        old_token_count = len(" ".join(msg["content"].split() for msg in messages_to_summarize))
        new_token_count = len(new_summary.split())
        
        # Update memory token count
        memory.threads[thread_id]["memory_tokens"] -= old_token_count
        memory.threads[thread_id]["memory_tokens"] += new_token_count
        
    except Exception as e:
        print(f"Error compacting memory: {str(e)}")

def get_conversation_context(thread_id: str, question: str) -> Dict[str, Any]:
    """Get conversation context for a thread to answer a question
    
    Args:
        thread_id: Thread ID
        question: The current question
    
    Returns:
        Context information for answering
    """
    if thread_id not in memory.threads:
        return {"error": "Thread not found"}
    
    # Update last activity
    memory.ttl_timestamps[thread_id] = time.time()
    
    # Get working memory
    working_memory = memory.working_memory[thread_id]
    
    # Prepare conversation history
    conversation_history = []
    
    # Add rolling summary if exists
    if working_memory["rolling_summary"]:
        conversation_history.append({
            "type": "summary",
            "content": working_memory["rolling_summary"]
        })
    
    # Add recent turns
    for turn in working_memory["last_k_turns"]:
        conversation_history.append({
            "type": "message",
            "role": turn["role"],
            "content": turn["content"]
        })
    
    return {
        "thread_id": thread_id,
        "conversation_history": conversation_history,
        "entities_facts": working_memory["entities_facts"],
        "doc_ids": memory.threads[thread_id]["doc_ids"],
        "memory_version": memory.version[thread_id]
    }

def extract_entities_and_facts(thread_id: str, question: str, answer: str) -> Dict[str, Any]:
    """Extract entities and facts from question/answer pair
    
    Args:
        thread_id: Thread ID
        question: User question
        answer: Assistant response
    
    Returns:
        Updated facts/entities
    """
    if thread_id not in memory.threads:
        return {}
    
    # Get current entities/facts
    current = memory.working_memory[thread_id]["entities_facts"]
    
    # Skip if too many facts already (keep memory limited)
    if len(current) > 50:
        return current
    
    try:
        # Prepare prompt for entity/fact extraction
        system_prompt = """Extract key facts, entities, and relationships from this question and answer pair.
        Focus on names, dates, numbers, terms, definitions, and specific facts mentioned.
        Return as a JSON dictionary with entity/fact as key and value/description as value.
        Be concise and only include significant facts and entities."""
        
        content = f"Question: {question}\n\nAnswer: {answer}"
        
        # Call LLM for extraction
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Use appropriate model
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            max_tokens=800,
            temperature=0.1
        )
        
        # Parse response
        try:
            facts = json.loads(response.choices[0].message.content)
            if isinstance(facts, dict):
                # Merge with existing facts
                current.update(facts)
                
                # Limit size to prevent bloat
                if len(current) > 50:
                    # Keep most recent facts
                    current = dict(list(current.items())[-50:])
                
                # Update working memory
                memory.working_memory[thread_id]["entities_facts"] = current
        except json.JSONDecodeError:
            print("Failed to parse entity extraction result as JSON")
            
    except Exception as e:
        print(f"Error extracting entities: {str(e)}")
    
    return current

def process_message(thread_id: str, question: str, idempotency_key: str, 
                   memory_version: int = None, parent_message_id: str = None) -> Dict[str, Any]:
    """Process a user message, get answer, and update thread memory
    
    Args:
        thread_id: Thread ID
        question: User question
        idempotency_key: Client-provided key for deduplication
        memory_version: Expected thread version for optimistic concurrency
        parent_message_id: Parent message ID for ordering
    
    Returns:
        Answer and updated thread state
    """
    # This function would integrate with your existing RAG pipeline
    # For now, this is a placeholder that will need to be integrated with your runner.py
    
    # Check idempotency - if we already have this message, return cached result
    if thread_id in memory.messages:
        for msg in memory.messages[thread_id]:
            if msg.get("idempotency_key") == idempotency_key and msg["role"] == "user":
                # Find the assistant response that followed
                for reply in memory.messages[thread_id]:
                    if reply.get("parent_id") == msg["message_id"] and reply["role"] == "assistant":
                        return {
                            "thread_id": thread_id,
                            "message_id": reply["message_id"],
                            "content": reply["content"],
                            "status": "cached"
                        }
    
    # Add user message
    user_msg = add_message(
        thread_id=thread_id,
        role="user",
        content=question,
        idempotency_key=idempotency_key,
        parent_message_id=parent_message_id,
        memory_version=memory_version
    )
    
    if "error" in user_msg:
        return user_msg
    
    # Get conversation context
    context = get_conversation_context(thread_id, question)
    
    # This is where you would integrate with your RAG pipeline (runner.py)
    # For now, we'll return a placeholder
    
    # Placeholder for answer
    answer = "This is a placeholder answer. Integration with runner.py needed."
    
    # Add assistant message
    assistant_msg = add_message(
        thread_id=thread_id,
        role="assistant",
        content=answer,
        idempotency_key=f"reply-{idempotency_key}",
        parent_message_id=user_msg["message_id"],
    )
    
    # Extract entities and facts
    extract_entities_and_facts(thread_id, question, answer)
    
    # Get updated thread state
    thread_state = get_thread_state(thread_id)
    
    return {
        "thread_id": thread_id,
        "message_id": assistant_msg["message_id"],
        "content": answer,
        "parent_id": user_msg["message_id"],
        "thread_state": thread_state,
        "memory_version": memory.version[thread_id]
    }

# Periodic cleanup for expired threads
def cleanup_thread():
    """Periodic thread to clean up expired threads"""
    while True:
        time.sleep(300)  # Run every 5 minutes
        memory.cleanup_expired()

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_thread, daemon=True)
cleanup_thread.start()
