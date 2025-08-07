# Bajaj_AR - Document to PDF Conversion and Text Extraction API

A Flask API service that downloads documents from URLs, automatically converts them to PDF format, and extracts text content using a dedicated PDF processing module for the HackRX challenge.

## Features

- ✅ **Multi-format support**: PDF, DOCX, DOC, EML, MSG
- ✅ **Automatic PDF conversion**: All documents converted to PDF
- ✅ **Text extraction**: Extracts text content from PDFs using `extract_pdf.py`
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
  "message": "Document downloaded, converted to PDF, and text extracted successfully",
  "document_path": "downloads/document.pdf",
  "text_path": "downloads/document.txt",
  "document_type": "PDF",
  "file_size_bytes": 123456,
  "text_length_chars": 5432,
  "questions_count": 2,
  "extracted_text": "Full text content of the document...",
  "text_extraction": "success",
  "conversion_note": "All documents are automatically converted to PDF format and text is extracted"
}
```

All downloaded documents are saved as PDF files in the `downloads/` folder.
