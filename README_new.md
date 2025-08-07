# Bajaj_AR - PDF Extraction API

A Flask API service for extracting PDFs from URLs as part of the HackRX challenge.

## Setup

1. **Create and activate virtual environment:**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

## API Usage

**POST** `http://localhost:5000/hackrx/run`

**Request:**

```json
{
  "documents": "https://example.com/document.pdf",
  "questions": ["Question 1", "Question 2"]
}
```

**Response:**

```json
{
  "status": "success",
  "message": "PDF downloaded successfully",
  "pdf_path": "downloads/document.pdf",
  "file_size_bytes": 123456,
  "questions_count": 2
}
```

Downloaded PDFs are saved in the `downloads/` folder.
