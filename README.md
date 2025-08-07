# Bajaj_AR - Document to PDF Conversion API

A Flask API service that downloads documents from URLs and automatically converts them to PDF format for the HackRX challenge.

## Features

- ✅ **Multi-format support**: PDF, DOCX, DOC, EML, MSG
- ✅ **Automatic PDF conversion**: All documents converted to PDF
- ✅ **Office 365 viewer support**: Handles Office viewer URLs
- ✅ **Azure blob storage**: Compatible with Azure storage URLs

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

**Input formats supported:** PDF, DOCX, DOC, EML, MSG  
**Output format:** PDF (all documents automatically converted)

**Request:**

```json
{
  "documents": "https://example.com/document.docx",
  "questions": ["Question 1", "Question 2"]
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Document downloaded and converted to PDF successfully",
  "document_path": "downloads/document.pdf",
  "document_type": "PDF",
  "file_size_bytes": 123456,
  "questions_count": 2,
  "conversion_note": "All documents are automatically converted to PDF format"
}
```

All downloaded documents are saved as PDF files in the `downloads/` folder.
