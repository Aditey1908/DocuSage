import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from chunker_reworked import hierarchical_chunk_file
from pdf_parser import extract_document

app = Flask(__name__)
CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "*"))

load_dotenv()
CORS(app, resources={r"/*": {"origins": os.getenv("FRONTEND_URL", "*")}})


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})


def parse_questions_payload(raw_questions):
    if isinstance(raw_questions, list):
        return [question for question in raw_questions if str(question).strip()]

    if isinstance(raw_questions, str) and raw_questions.strip():
        try:
            parsed = json.loads(raw_questions)
            if isinstance(parsed, list):
                return [question for question in parsed if str(question).strip()]
        except json.JSONDecodeError:
            pass

        split_questions = [line.strip() for line in raw_questions.splitlines() if line.strip()]
        if split_questions:
            return split_questions

    return []


def resolve_input_document(tmpdir):
    uploaded_file = request.files.get("document") or request.files.get("file")

    if request.is_json:
        payload = request.get_json(silent=True) or {}
        file_url = payload.get("documents") or payload.get("document_url") or payload.get("url")
        raw_questions = payload.get("questions")
    else:
        file_url = request.form.get("documents") or request.form.get("document_url") or request.form.get("url")
        raw_questions = request.form.get("questions")

    questions = parse_questions_payload(raw_questions)

    if uploaded_file and uploaded_file.filename:
        _, file_ext = os.path.splitext(uploaded_file.filename)
        if not file_ext:
            file_ext = ".pdf"
        input_path = os.path.join(tmpdir, f"upload{file_ext}")
        uploaded_file.save(input_path)
        print(f"[INFO] Uploaded file saved to {input_path}")
        return input_path, questions, "upload"

    if file_url:
        file_ext = file_url.split("?")[0].split(".")[-1]
        input_path = os.path.join(tmpdir, f"doc.{file_ext}")
        print(f"[INFO] Downloading file to {input_path}")
        with requests.get(file_url, stream=True, timeout=15) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("application/pdf"):
                raise ValueError(f"URL did not return a PDF. Content-Type: {content_type}")
            with open(input_path, "wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    file_handle.write(chunk)
        print("[INFO] File downloaded.")
        return input_path, questions, "url"

    raise ValueError("Provide either a PDF upload or a document URL.")


@app.route("/process", methods=["POST"])
def process_document():
    session_id = str(uuid.uuid4())
    print(f"[INFO] Session started: {session_id}")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            pdf_path, questions, source_type = resolve_input_document(tmpdir)
        except Exception as e:
            print(f"[ERROR] Failed to prepare input document: {e}")
            return jsonify({"error": f"Failed to prepare input document: {str(e)}"}), 400

        if not questions:
            print("[ERROR] Bad request: missing questions")
            return jsonify({"error": "At least one question is required."}), 400

        txt_path = os.path.join(tmpdir, "document.txt")
        print("[INFO] Extracting text from document...")
        text = extract_document(pdf_path)
        print(f"[INFO] Extracted {len(text)} characters of text.")

        with open(txt_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(text)
        print(f"[INFO] Wrote extracted text to {txt_path}")

        chunked_path = os.path.join(tmpdir, "chunked.txt")
        print("[INFO] Chunking text...")
        hierarchical_chunk_file(txt_path, chunked_path)
        print(f"[INFO] Chunked text written to {chunked_path}")

        questions_path = os.path.join(tmpdir, "questions.json")
        with open(questions_path, "w", encoding="utf-8") as file_handle:
            json.dump(questions, file_handle)
        print(f"[INFO] Questions written to {questions_path}")

        print("[INFO] Launching runner.py subprocess...")
        runner_path = os.path.join(os.path.dirname(__file__), "runner.py")
        env = os.environ.copy()

        result = subprocess.run(
            [sys.executable, runner_path, chunked_path, questions_path],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(__file__),
        )
        print("[INFO] runner.py finished.")

        if result.returncode != 0:
            print("[ERROR] Runner failed (returncode=%d)" % result.returncode)
            print("[ERROR] STDOUT:", result.stdout)
            print("[ERROR] STDERR:", result.stderr)
            details = result.stderr or result.stdout or "no output captured"
            return jsonify({"error": "Runner failed", "details": details}), 500

        try:
            json_text = re.search(r"(\{[\s\S]*\})", result.stdout).group(1)
            runner_result = json.loads(json_text)
            print("[INFO] Successfully parsed runner output JSON.")
        except Exception as e:
            print("[WARNING] Could not parse runner output JSON:", e)
            runner_result = {"raw_output": result.stdout}

        print(f"[INFO] Session complete: {session_id}")

        return jsonify(
            {
                "answer": runner_result,
                "session_id": session_id,
                "source_type": source_type,
                "question_count": len(questions),
            }
        )


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
