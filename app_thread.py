import os
import tempfile
import uuid
import requests
from flask import Flask, request, jsonify
import subprocess
import json
import time
import signal
import sys
from dotenv import load_dotenv

# Load environment variables at the beginning
load_dotenv(override=True)
from pdf_parser import extract_document
from chunker_reworked import hierarchical_chunk_file
from thread_manager import (
    create_thread, get_thread_state, reset_thread, 
    process_message, memory, release_thread_lock
)

app = Flask(__name__)

# Store document paths for reuse
document_paths = {}

@app.route('/threads', methods=['POST'])
def create_thread_endpoint():
    """Create a new thread for a document"""
    data = request.get_json(force=True)
    file_url = data.get('document_url')
    
    # Optional parameters
    memory_budget = data.get('memory_budget', 4000)  # Default 4000 tokens
    ttl_minutes = data.get('ttl_minutes', 120)  # Default 2 hours
    
    if not file_url:
        return jsonify({'error': 'document_url is required'}), 400
    
    session_id = str(uuid.uuid4())
    print(f"[INFO] Thread creation started: {session_id}")
    
    try:
        # Create a persistent directory for documents
        persistent_dir = os.path.join(os.path.dirname(__file__), 'thread_documents')
        os.makedirs(persistent_dir, exist_ok=True)
        
        # Create a subdirectory for this session
        session_dir = os.path.join(persistent_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Download file from URL
        file_ext = file_url.split('?')[0].split('.')[-1]
        pdf_path = os.path.join(session_dir, f'doc.{file_ext}')
        print(f"[INFO] Downloading file to {pdf_path}")
        
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(pdf_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("[INFO] File downloaded.")
        
        # Extract text
        txt_path = os.path.join(session_dir, 'document.txt')
        print("[INFO] Extracting text from document...")
        text = extract_document(pdf_path)
        print(f"[INFO] Extracted {len(text)} characters of text.")
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[INFO] Wrote extracted text to {txt_path}")
        
        # Chunk text
        chunked_path = os.path.join(session_dir, 'chunked.txt')
        print("[INFO] Chunking text...")
        hierarchical_chunk_file(txt_path, chunked_path)
        print(f"[INFO] Chunked text written to {chunked_path}")
        
        # Create a new thread
        thread_id = create_thread(
            doc_ids=[session_id],  # Use session_id as doc_id
            memory_budget=memory_budget,
            ttl_minutes=ttl_minutes
        )
        
        # Store document paths for future use
        document_paths[thread_id] = {
            'pdf_path': pdf_path,
            'txt_path': txt_path,
            'chunked_path': chunked_path,
            'file_url': file_url,
            'session_id': session_id,
            'dir_path': session_dir
        }
        
        # Prepare chunked file for future RAG queries
        # Run runner.py to set up embeddings and index
        prepare_embeddings_for_thread(thread_id)
        
        print(f"[INFO] Thread created: {thread_id}")
        
        return jsonify({
            'thread_id': thread_id,
            'session_id': session_id,
            'status': 'created',
            'document_info': {
                'url': file_url,
                'characters': len(text),
            }
        })
            
    except Exception as e:
        print(f"[ERROR] Thread creation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/threads/<thread_id>', methods=['GET'])
def get_thread_endpoint(thread_id):
    """Get thread state and info"""
    thread_state = get_thread_state(thread_id)
    
    if 'error' in thread_state:
        return jsonify(thread_state), 404
    
    return jsonify(thread_state)

@app.route('/threads/<thread_id>/reset', methods=['POST'])
def reset_thread_endpoint(thread_id):
    """Reset thread state"""
    result = reset_thread(thread_id)
    
    if 'error' in result:
        return jsonify(result), 404
    
    return jsonify(result)

@app.route('/messages', methods=['POST'])
def process_message_endpoint():
    """Process a message in a thread"""
    data = request.get_json(force=True)
    thread_id = data.get('thread_id')
    content = data.get('content')
    idempotency_key = data.get('idempotency_key', str(uuid.uuid4()))
    memory_version = data.get('memory_version')
    parent_message_id = data.get('parent_message_id')
    
    if not thread_id or not content:
        return jsonify({'error': 'thread_id and content are required'}), 400
    
    # Check if thread exists
    if thread_id not in memory.threads:
        return jsonify({'error': 'Thread not found'}), 404
    
    # Process message and get answer
    try:
        # This is where we integrate with runner.py
        result = process_message_with_rag(
            thread_id=thread_id,
            question=content,
            idempotency_key=idempotency_key,
            memory_version=memory_version,
            parent_message_id=parent_message_id
        )
        
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] Message processing failed: {str(e)}")
        # Make sure to release the lock if an error occurs
        release_thread_lock(thread_id)
        return jsonify({'error': str(e)}), 500

def prepare_embeddings_for_thread(thread_id):
    """Prepare document embeddings for a thread"""
    if thread_id not in document_paths:
        print(f"[ERROR] No document paths found for thread {thread_id}")
        return
    
    doc_paths = document_paths[thread_id]
    chunked_path = doc_paths['chunked_path']
    session_dir = doc_paths['dir_path']
    
    if not os.path.exists(chunked_path):
        print(f"[ERROR] Chunked file not found: {chunked_path}")
        return
    
    # Create temporary questions file for initial embedding to avoid cluttering the session directory
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
        json.dump(["Initialize embeddings"], temp_file)
        questions_path = temp_file.name
        print(f"[INFO] Created temporary questions file at: {questions_path}")
    
    # Track this file for cleanup
    doc_paths['temp_init_file'] = questions_path
    
    # Run runner.py to prepare embeddings
    print("[INFO] Preparing embeddings for document...")
    
    # Pass environment variables to the subprocess
    env = os.environ.copy()
    
    result = subprocess.run(
        ['python', 'runner.py', chunked_path, questions_path],
        capture_output=True, text=True,
        env=env  # Pass the environment variables
    )
    
    # Clean up temporary file
    try:
        os.unlink(questions_path)
        print(f"[INFO] Removed temporary questions file: {questions_path}")
    except Exception as e:
        print(f"[WARNING] Failed to remove temporary file: {str(e)}")
    
    if result.returncode != 0:
        print("[ERROR] Embedding preparation failed:\n", result.stderr)
        return
    
    print("[INFO] Embeddings prepared successfully")

def process_message_with_rag(thread_id, question, idempotency_key, memory_version=None, parent_message_id=None):
    """Process a message with RAG integration"""
    # Check for idempotency
    if thread_id in memory.messages:
        for msg in memory.messages[thread_id]:
            if msg.get("idempotency_key") == idempotency_key and msg["role"] == "user":
                # Find the assistant response that followed
                for reply in memory.messages[thread_id]:
                    if reply.get("parent_id") == msg["message_id"] and reply["role"] == "assistant":
                        return {
                            "thread_id": thread_id,
                            "message_id": reply["message_id"],
                            "answer": reply["content"],
                            "status": "cached"
                        }
    
    # Get document paths
    if thread_id not in document_paths:
        return {'error': 'Document not found for this thread'}
    
    doc_paths = document_paths[thread_id]
    
    # Check if we're using persistent storage or temporary files
    if 'dir_path' in doc_paths:
        # Using persistent storage
        session_dir = doc_paths['dir_path']
        chunked_path = os.path.join(session_dir, 'chunked.txt')
        
        # Make sure session directory exists
        if not os.path.exists(session_dir):
            os.makedirs(session_dir, exist_ok=True)
    else:
        # Using older temporary storage approach
        chunked_path = doc_paths['chunked_path']
    
    # Verify the chunked path exists
    if not os.path.exists(chunked_path):
        print(f"[ERROR] Chunked document not found at: {chunked_path}")
        return {'error': f'Chunked document not found. The file may have been deleted.'}
    
    print(f"[INFO] Using chunked document at: {chunked_path}")
    
    # Add user message to thread
    from thread_manager import add_message, get_conversation_context, extract_entities_and_facts
    
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
    
    # Prepare for RAG query
    # Check if we have a persistent directory to use
    if 'dir_path' in doc_paths:
        # Use session directory for question file
        questions_path = os.path.join(doc_paths['dir_path'], f'question_{uuid.uuid4()}.json')
    else:
        # Create a temporary directory for the question file
        import tempfile
        temp_dir = tempfile.mkdtemp()
        questions_path = os.path.join(temp_dir, f'question_{uuid.uuid4()}.json')
    
    print(f"[INFO] Creating question file at: {questions_path}")
    
    # Enhance question with conversation context
    enhanced_question = question
    if context["conversation_history"]:
        # Use entities and previous context to enhance question
        entities = context["entities_facts"]
        if entities:
            entities_str = ", ".join([f"{k}: {v}" for k, v in entities.items()])
            enhanced_question = f"{question}\n\nContext: {entities_str}"
    
    # Write question to file
    try:
        with open(questions_path, 'w', encoding='utf-8') as f:
            json.dump([enhanced_question], f)
        print(f"[INFO] Successfully wrote question to file: {questions_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write question file: {str(e)}")
        raise
    
    # Run runner.py to get answer
    print(f"[INFO] Processing question: {question[:100]}...")
    print(f"[INFO] Chunked path: {chunked_path}")
    print(f"[INFO] Questions path: {questions_path}")
    
    # Verify files exist
    if not os.path.exists(chunked_path):
        print(f"[ERROR] Chunked file not found: {chunked_path}")
        return {'error': 'Chunked file not found'}
    
    if not os.path.exists(questions_path):
        print(f"[ERROR] Questions file not found: {questions_path}")
        return {'error': 'Questions file not found'}
    
    # Pass environment variables to the subprocess
    env = os.environ.copy()
    
    # Run with full error output
    try:
        result = subprocess.run(
            ['python', 'runner.py', chunked_path, questions_path],
            capture_output=True, text=True,
            env=env,  # Pass the environment variables
            check=False  # Don't raise exception on non-zero exit
        )
        
        # Print any stderr output for debugging
        if result.stderr:
            print(f"[WARN] Runner stderr output: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] Failed to run subprocess: {str(e)}")
        
        # Clean up question file before returning error
        try:
            os.unlink(questions_path)
            print(f"[INFO] Removed question file: {questions_path}")
        except Exception as cleanup_error:
            print(f"[WARNING] Failed to remove question file: {str(cleanup_error)}")
            
        return {'error': f'Failed to run subprocess: {str(e)}'}
    
    # Clean up question file after use
    try:
        os.unlink(questions_path)
        print(f"[INFO] Removed question file: {questions_path}")
    except Exception as e:
        print(f"[WARNING] Failed to remove question file: {str(e)}")
    
    if result.returncode != 0:
        print("[ERROR] RAG query failed:\n", result.stderr)
        # Add error message
        add_message(
            thread_id=thread_id,
            role="assistant",
            content="Sorry, I couldn't process your question. Please try again.",
            idempotency_key=f"reply-{idempotency_key}",
            parent_message_id=user_msg["message_id"]
        )
        return {'error': 'RAG query failed', 'details': result.stderr}
    
    # Parse JSON from runner.py output
    import re
    try:
        json_text = re.search(r'(\{[\s\S]*\})', result.stdout).group(1)
        runner_result = json.loads(json_text)
        print("[INFO] Successfully parsed runner output JSON.")
        
        # Extract answer from runner result
        if isinstance(runner_result, dict) and "answers" in runner_result and runner_result["answers"]:
            answer = runner_result["answers"][0]
        else:
            answer = "No clear answer found in the document for this question."
        
    except Exception as e:
        print("[WARNING] Could not parse runner output JSON:", e)
        answer = "There was an issue processing your question."
    
    # Add assistant message
    assistant_msg = add_message(
        thread_id=thread_id,
        role="assistant",
        content=answer,
        idempotency_key=f"reply-{idempotency_key}",
        parent_message_id=user_msg["message_id"]
    )
    
    # Extract entities and facts
    extract_entities_and_facts(thread_id, question, answer)
    
    # Get updated thread state
    thread_state = get_thread_state(thread_id)
    
    return {
        "thread_id": thread_id,
        "message_id": assistant_msg["message_id"],
        "answer": answer,
        "parent_id": user_msg["message_id"],
        "thread_state": thread_state,
        "memory_version": memory.version[thread_id]
    }

@app.route('/process', methods=['POST'])
def process_document():
    """Legacy endpoint - handle multiple questions in one request
    
    This endpoint is kept for backward compatibility but will
    create a temporary thread for the request.
    """
    data = request.get_json(force=True)
    file_url = data.get('documents')
    questions = data.get('questions')

    if not file_url or not questions or not isinstance(questions, list) or not questions:
        print("[ERROR] Bad request: missing documents or questions")
        return jsonify({'error': 'Both \"documents\" (url) and \"questions\" (list) required.'}), 400

    # Create a temporary thread
    temp_thread_id = create_thread(
        doc_ids=[str(uuid.uuid4())],
        ttl_minutes=30  # Short TTL for temporary thread
    )
    
    session_id = str(uuid.uuid4())
    print(f"[INFO] Legacy session started: {session_id}")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download file from URL
        file_ext = file_url.split('?')[0].split('.')[-1]
        pdf_path = os.path.join(tmpdir, f'doc.{file_ext}')
        print(f"[INFO] Downloading file to {pdf_path}")
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(pdf_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("[INFO] File downloaded.")

        # Extract text
        txt_path = os.path.join(tmpdir, 'document.txt')
        print("[INFO] Extracting text from document...")
        text = extract_document(pdf_path)
        print(f"[INFO] Extracted {len(text)} characters of text.")

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[INFO] Wrote extracted text to {txt_path}")

        # Chunk text
        chunked_path = os.path.join(tmpdir, 'chunked.txt')
        print("[INFO] Chunking text...")
        hierarchical_chunk_file(txt_path, chunked_path)
        print(f"[INFO] Chunked text written to {chunked_path}")

        # Write questions to a JSON file
        questions_path = os.path.join(tmpdir, 'questions.json')
        with open(questions_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f)
        print(f"[INFO] Questions written to {questions_path}")

        # Run runner.py with chunked file and questions
        print("[INFO] Launching runner.py subprocess...")
        
        # Pass environment variables to the subprocess
        env = os.environ.copy()
        
        result = subprocess.run(
            ['python', 'runner.py', chunked_path, questions_path],
            capture_output=True, text=True, 
            env=env  # Pass the environment variables
        )
        print("[INFO] runner.py finished.")

        if result.returncode != 0:
            print("[ERROR] Runner failed:\n", result.stderr)
            return jsonify({'error': 'Runner failed', 'details': result.stderr}), 500

        # Parse JSON from runner.py output
        import re
        try:
            json_text = re.search(r'(\{[\s\S]*\})', result.stdout).group(1)
            runner_result = json.loads(json_text)
            print("[INFO] Successfully parsed runner output JSON.")
        except Exception as e:
            print("[WARNING] Could not parse runner output JSON:", e)
            runner_result = {'raw_output': result.stdout}

        print(f"[INFO] Session complete: {session_id}")
        
        # Clean up the temporary thread after use
        reset_thread(temp_thread_id)

        return jsonify({'answer': runner_result, 'session_id': session_id})

def cleanup_empty_questions_files():
    """Clean up any existing empty_questions.json files"""
    try:
        # Check if thread_documents directory exists
        persistent_dir = os.path.join(os.path.dirname(__file__), 'thread_documents')
        if os.path.exists(persistent_dir):
            print("[INFO] Cleaning up empty_questions.json files...")
            count = 0
            # Iterate through thread directories
            for thread_dir in os.listdir(persistent_dir):
                thread_path = os.path.join(persistent_dir, thread_dir)
                if os.path.isdir(thread_path):
                    empty_file = os.path.join(thread_path, 'empty_questions.json')
                    if os.path.exists(empty_file):
                        try:
                            os.unlink(empty_file)
                            count += 1
                        except Exception as e:
                            print(f"[WARNING] Failed to remove {empty_file}: {str(e)}")
            
            print(f"[INFO] Removed {count} empty_questions.json files")
    except Exception as e:
        print(f"[ERROR] Error cleaning up empty questions files: {str(e)}")

def shutdown_server():
    """Properly shutdown the server and all child processes"""
    print("\n[INFO] Shutting down server...")
    
    # Get all Python processes
    try:
        if os.name == 'nt':  # Windows
            # Find all Python processes
            process_info = subprocess.check_output('tasklist /FI "IMAGENAME eq python.exe" /FO CSV', shell=True).decode()
            lines = process_info.strip().split('\n')[1:]  # Skip header
            
            # Extract PIDs
            import re
            pids = []
            for line in lines:
                match = re.search(r'"python\.exe","(\d+)"', line)
                if match:
                    pids.append(int(match.group(1)))
            
            current_pid = os.getpid()
            print(f"[INFO] Current process: {current_pid}")
            
            # Kill all Python processes except current one
            for pid in pids:
                if pid != current_pid:
                    print(f"[INFO] Terminating Python process: {pid}")
                    try:
                        subprocess.call(f'taskkill /F /PID {pid}', shell=True)
                    except Exception as e:
                        print(f"[ERROR] Failed to kill process {pid}: {str(e)}")
        else:  # Unix/Linux/Mac
            # For Unix systems, we could use pkill/killall but we'll keep it simple
            print("[INFO] On Unix systems, please ensure all processes are terminated manually if needed")
    
    except Exception as e:
        print(f"[ERROR] Error while shutting down processes: {str(e)}")
    
    # Exit the main process
    print("[INFO] Server shutdown complete")
    sys.exit(0)

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    print("\n[INFO] Ctrl+C detected, initiating graceful shutdown...")
    shutdown_server()

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    print("[INFO] Starting server... Press Ctrl+C to shut down")
    print("[INFO] This server is configured to terminate all related Python processes on shutdown")
    
    # Clean up any existing empty_questions.json files at startup
    cleanup_empty_questions_files()
    
    # In production, we would use threaded=True, but for development with clean shutdown:
    # 1. use_reloader=False prevents the reloader from creating a child process
    # 2. debug=False prevents Flask from launching multiple processes
    # This setup ensures clean shutdown with Ctrl+C, but you won't get auto-reload on code changes
    app.run(debug=False, port=5000, use_reloader=False)
