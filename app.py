import os
import tempfile
import uuid
import requests
from flask import Flask, request, jsonify
from pdf_parser import extract_document
from chunker_reworked import hierarchical_chunk_file
import subprocess
import json

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_document():
    data = request.get_json(force=True)
    file_url = data.get('documents')
    questions = data.get('questions')

    if not file_url or not questions or not isinstance(questions, list) or not questions:
        print("[ERROR] Bad request: missing documents or questions")
        return jsonify({'error': 'Both \"documents\" (url) and \"questions\" (list) required.'}), 400

    session_id = str(uuid.uuid4())
    print(f"[INFO] Session started: {session_id}")

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
        result = subprocess.run(
            ['python', 'runner.py', chunked_path, questions_path],
            capture_output=True, text=True
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

        return jsonify({'answer': runner_result, 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
