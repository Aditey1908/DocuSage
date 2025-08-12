
import logging
import os
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
UPLOAD_FOLDER = 'downloads'

# Create downloads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def is_valid_document_url(url):
    """Check if URL is valid and points to supported document"""
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ['http', 'https']:
            return False
        
        full_url = url.lower()
        supported_extensions = ['.pdf', '.docx', '.doc', '.eml', '.msg']
        
        return (any(ext in full_url for ext in supported_extensions) or
                'officeapps.live.com' in parsed_url.netloc or
                'office.com' in parsed_url.netloc or
                'blob.core.windows.net' in parsed_url.netloc or
                'sharepoint.com' in parsed_url.netloc)
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False

def convert_to_pdf(input_path, output_path):
    """Convert document to PDF"""
    file_ext = os.path.splitext(input_path)[1].lower()
    
    if file_ext == '.pdf':
        if input_path != output_path:
            import shutil
            shutil.copy2(input_path, output_path)
        return output_path
    
    # For Word documents
    if file_ext in ['.docx', '.doc']:
        try:
            from docx import Document
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
            
            doc = Document(input_path)
            pdf_doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    story.append(Paragraph(paragraph.text, styles['Normal']))
                    story.append(Spacer(1, 12))
            
            pdf_doc.build(story)
            return output_path
        except Exception as e:
            logger.error(f"Word conversion failed: {e}")
    
    # For email files
    if file_ext in ['.eml', '.msg']:
        try:
            import email
            from email import policy

            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
            
            with open(input_path, 'rb') as f:
                msg = email.message_from_bytes(f.read(), policy=policy.default)
            
            pdf_doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = [
                Paragraph(f"<b>From:</b> {msg.get('From', 'Unknown')}", styles['Normal']),
                Paragraph(f"<b>Subject:</b> {msg.get('Subject', 'No Subject')}", styles['Normal']),
                Spacer(1, 20)
            ]
            
            body = msg.get_content() if not msg.is_multipart() else ""
            if body:
                for line in body.split('\n')[:50]:  # Limit lines
                    if line.strip():
                        story.append(Paragraph(line, styles['Normal']))
            
            pdf_doc.build(story)
            return output_path
        except Exception as e:
            logger.error(f"Email conversion failed: {e}")
    
    # Fallback: create simple PDF with error message
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate
        
        pdf_doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph(f"Could not convert {file_ext} file", styles['Normal'])]
        pdf_doc.build(story)
        return output_path
    except:
        return input_path

def download_and_convert(url):
    """Download document and convert to PDF"""
    # Handle Office 365 URLs
    actual_url = url
    if 'officeapps.live.com' in url or 'office.com' in url:
        from urllib.parse import parse_qs
        parsed = urlparse(url)
        if 'src=' in parsed.query:
            params = parse_qs(parsed.query)
            if 'src' in params:
                actual_url = params['src'][0]
    
    # Download file
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(actual_url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()
    
    # Determine file extension
    content_type = response.headers.get('content-type', '').lower()
    parsed_url = urlparse(actual_url)
    base_name = os.path.basename(parsed_url.path) or 'document'
    base_name = os.path.splitext(base_name)[0]
    
    if 'pdf' in content_type or '.pdf' in actual_url.lower():
        ext = '.pdf'
    elif 'word' in content_type or 'officedocument' in content_type:
        ext = '.docx'
    elif 'msword' in content_type:
        ext = '.doc'
    elif 'message' in content_type or '.eml' in actual_url.lower():
        ext = '.eml'
    elif '.msg' in actual_url.lower():
        ext = '.msg'
    else:
        ext = '.pdf'
    
    # Save temporary file
    temp_path = os.path.join(UPLOAD_FOLDER, base_name + ext)
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    # Convert to PDF
    pdf_path = os.path.join(UPLOAD_FOLDER, base_name + '.pdf')
    final_path = convert_to_pdf(temp_path, pdf_path)
    
    # Clean up temp file if different
    if temp_path != final_path and os.path.exists(temp_path):
        os.remove(temp_path)
    
    return final_path

@app.route('/hackrx/run', methods=['POST'])
def hackrx_run():
    """Download document and convert to PDF"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON', 'status': 'failed'}), 400
        
        data = request.get_json()
        if 'documents' not in data:
            return jsonify({'error': 'Missing required field: documents', 'status': 'failed'}), 400
        
        url = data['documents']
        if not is_valid_document_url(url):
            return jsonify({'error': 'Invalid document URL', 'status': 'failed'}), 400
        
        pdf_path = download_and_convert(url)
        file_size = os.path.getsize(pdf_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Document converted to PDF successfully',
            'document_path': pdf_path,
            'file_size_bytes': file_size,
            'document_url': url
        }), 200
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e), 'status': 'failed'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Document conversion service running',
        'supported_formats': ['PDF', 'DOCX', 'DOC', 'EML', 'MSG'],
        'features': ['Document download', 'PDF conversion', 'Office 365 support', 'Azure blob storage']
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'status': 'failed'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed', 'status': 'failed'}), 405

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
