import logging
import os
import platform
import subprocess
import tempfile
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'downloads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'eml', 'msg'}

# Create downloads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def is_valid_document_url(url):
    """Check if the URL is valid and points to a supported document"""
    try:
        parsed_url = urlparse(url)
        # Check if URL has valid scheme
        if parsed_url.scheme not in ['http', 'https']:
            return False
        
        # Check if the path or query contains supported file extensions
        full_url = url.lower()
        path = parsed_url.path.lower()
        query = parsed_url.query.lower()
        
        supported_extensions = ['.pdf', '.docx', '.doc', '.eml', '.msg']
        
        # Check if any supported extension is in the path, query, or full URL
        return (any(ext in path for ext in supported_extensions) or
                any(ext in query for ext in supported_extensions) or
                any(ext in full_url for ext in supported_extensions) or
                # Special handling for Office 365 viewer URLs
                'officeapps.live.com' in parsed_url.netloc or
                'office.com' in parsed_url.netloc or
                # Azure blob storage or SharePoint
                'blob.core.windows.net' in parsed_url.netloc or
                'sharepoint.com' in parsed_url.netloc)
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False

def convert_to_pdf(input_filepath, output_pdf_path):
    """Convert various document formats to PDF"""
    try:
        file_ext = os.path.splitext(input_filepath)[1].lower()
        logger.info(f"Converting {file_ext} file to PDF: {input_filepath}")
        
        if file_ext == '.pdf':
            # Already PDF, just copy if paths are different
            if input_filepath != output_pdf_path:
                import shutil
                shutil.copy2(input_filepath, output_pdf_path)
                logger.info(f"PDF file copied to: {output_pdf_path}")
                return output_pdf_path
            else:
                # Same file, just return the path
                logger.info(f"File is already a PDF at correct location: {output_pdf_path}")
                return input_filepath
            
        elif file_ext in ['.docx', '.doc']:
            # Convert Word documents to PDF using python-docx and reportlab
            try:
                from docx import Document
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import (Paragraph, SimpleDocTemplate,
                                                Spacer)

                # Read DOCX content
                doc = Document(input_filepath)
                
                # Create PDF
                pdf_doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        para = Paragraph(paragraph.text, styles['Normal'])
                        story.append(para)
                        story.append(Spacer(1, 12))
                
                pdf_doc.build(story)
                logger.info(f"Word document converted to PDF: {output_pdf_path}")
                return output_pdf_path
                
            except Exception as e:
                logger.error(f"Error converting Word to PDF: {e}")
                # Fallback: Try using LibreOffice if available
                return convert_with_libreoffice(input_filepath, output_pdf_path)
                
        elif file_ext in ['.eml', '.msg']:
            # Convert email files to PDF
            try:
                import email
                from email import policy

                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.platypus import (Paragraph, SimpleDocTemplate,
                                                Spacer)

                # Read email content
                with open(input_filepath, 'rb') as f:
                    msg = email.message_from_bytes(f.read(), policy=policy.default)
                
                # Create PDF
                pdf_doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                # Add email headers
                story.append(Paragraph(f"<b>From:</b> {msg.get('From', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"<b>To:</b> {msg.get('To', 'Unknown')}", styles['Normal']))
                story.append(Paragraph(f"<b>Subject:</b> {msg.get('Subject', 'No Subject')}", styles['Normal']))
                story.append(Paragraph(f"<b>Date:</b> {msg.get('Date', 'Unknown')}", styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Add email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_content()
                            break
                else:
                    body = msg.get_content()
                
                if body:
                    # Split body into paragraphs
                    for line in body.split('\n'):
                        if line.strip():
                            para = Paragraph(line, styles['Normal'])
                            story.append(para)
                            story.append(Spacer(1, 6))
                
                pdf_doc.build(story)
                logger.info(f"Email converted to PDF: {output_pdf_path}")
                return output_pdf_path
                
            except Exception as e:
                logger.error(f"Error converting email to PDF: {e}")
                # Create a simple text-based PDF
                return create_text_pdf(input_filepath, output_pdf_path, f"Email file: {os.path.basename(input_filepath)}")
        
        else:
            # Unsupported format, create a placeholder PDF
            return create_text_pdf(input_filepath, output_pdf_path, f"Unsupported file format: {file_ext}")
            
    except Exception as e:
        logger.error(f"Error in convert_to_pdf: {e}")
        # Create error PDF
        return create_text_pdf(input_filepath, output_pdf_path, f"Error converting file: {str(e)}")

def convert_with_libreoffice(input_filepath, output_pdf_path):
    """Try to convert document using LibreOffice command line"""
    try:
        output_dir = os.path.dirname(output_pdf_path)
        
        # Try LibreOffice conversion
        if platform.system() == "Windows":
            libreoffice_cmd = "soffice"
        else:
            libreoffice_cmd = "libreoffice"
            
        cmd = [
            libreoffice_cmd,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            input_filepath
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # LibreOffice creates PDF with same name but .pdf extension
            base_name = os.path.splitext(os.path.basename(input_filepath))[0]
            generated_pdf = os.path.join(output_dir, f"{base_name}.pdf")
            
            if os.path.exists(generated_pdf) and generated_pdf != output_pdf_path:
                os.rename(generated_pdf, output_pdf_path)
                
            logger.info(f"Document converted to PDF using LibreOffice: {output_pdf_path}")
            return output_pdf_path
        else:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")
            
    except Exception as e:
        logger.error(f"LibreOffice conversion failed: {e}")
        # Fallback to text PDF
        return create_text_pdf(input_filepath, output_pdf_path, f"Could not convert {os.path.basename(input_filepath)}")

def create_text_pdf(input_filepath, output_pdf_path, message):
    """Create a simple text PDF with a message"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        
        pdf_doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph(f"<b>Document Conversion Notice</b>", styles['Title']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(message, styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Original file: {os.path.basename(input_filepath)}", styles['Normal']))
        
        pdf_doc.build(story)
        logger.info(f"Created text PDF: {output_pdf_path}")
        return output_pdf_path
        
    except Exception as e:
        logger.error(f"Error creating text PDF: {e}")
        raise e

def download_document_from_url(url, filename=None):
    """Download document from URL and save it locally"""
    try:
        logger.info(f"Downloading document from URL: {url}")
        
        # Handle Office 365 viewer URLs by extracting the actual document URL
        actual_url = url
        if 'officeapps.live.com' in url or 'office.com' in url:
            parsed_url = urlparse(url)
            if 'src=' in parsed_url.query:
                # Extract the src parameter which contains the actual document URL
                from urllib.parse import parse_qs
                query_params = parse_qs(parsed_url.query)
                if 'src' in query_params:
                    actual_url = query_params['src'][0]
                    logger.info(f"Extracted actual document URL from Office viewer: {actual_url}")
        
        # Make request with headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(actual_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Get content type and determine file extension
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"Content type: {content_type}")
        
        # Generate filename if not provided
        if not filename:
            # Use actual_url for filename generation (in case it was extracted from Office viewer)
            parsed_actual_url = urlparse(actual_url)
            base_filename = os.path.basename(parsed_actual_url.path) or 'document'
            
            # Remove existing extension and determine original file type
            base_name = os.path.splitext(base_filename)[0] or 'document'
            
            # Determine original file extension based on content type or URL
            original_ext = ''
            if 'pdf' in content_type or '.pdf' in actual_url.lower():
                original_ext = '.pdf'
            elif 'word' in content_type or 'officedocument' in content_type or '.docx' in actual_url.lower():
                original_ext = '.docx'
            elif 'msword' in content_type or '.doc' in actual_url.lower():
                original_ext = '.doc'
            elif 'message' in content_type or 'rfc822' in content_type or '.eml' in actual_url.lower():
                original_ext = '.eml'
            elif '.msg' in actual_url.lower():
                original_ext = '.msg'
            else:
                original_ext = '.pdf'  # Default to PDF
            
            # Temporary filename for downloaded file
            temp_filename = base_name + original_ext
        else:
            temp_filename = filename
        
        # Save the document temporarily
        temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
        
        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Document downloaded temporarily: {temp_filepath}")
        
        # Convert to PDF (final filename will always be .pdf)
        if temp_filename.endswith('.pdf'):
            # Already a PDF, no conversion needed
            final_pdf_path = temp_filepath
            logger.info(f"File is already PDF, no conversion needed: {final_pdf_path}")
        else:
            # Convert the downloaded file to PDF
            pdf_filename = os.path.splitext(temp_filename)[0] + '.pdf'
            pdf_filepath = os.path.join(UPLOAD_FOLDER, pdf_filename)
            final_pdf_path = convert_to_pdf(temp_filepath, pdf_filepath)
            
            # Clean up temporary file if it's different from the final PDF
            if temp_filepath != final_pdf_path and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
                logger.info(f"Cleaned up temporary file: {temp_filepath}")
        
        logger.info(f"Document converted and saved as PDF: {final_pdf_path}")
        return final_pdf_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading document: {e}")
        raise Exception(f"Failed to download document: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise Exception(f"Unexpected error downloading document: {str(e)}")

@app.route('/hackrx/run', methods=['POST'])
def hackrx_run():
    """Handle the POST request to extract documents from URL"""
    try:
        # Check if request has JSON data
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'status': 'failed'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'documents' not in data:
            return jsonify({
                'error': 'Missing required field: documents',
                'status': 'failed'
            }), 400
        
        documents_url = data['documents']
        questions = data.get('questions', [])
        
        # Validate the document URL
        if not is_valid_document_url(documents_url):
            return jsonify({
                'error': 'Invalid document URL provided. Supported formats: PDF, DOCX, DOC, EML, MSG',
                'status': 'failed'
            }), 400
        
        # Download and convert the document to PDF
        try:
            pdf_filepath = download_document_from_url(documents_url)
            
            # Get file size for verification
            file_size = os.path.getsize(pdf_filepath)
            
            # All documents are now converted to PDF
            response_data = {
                'status': 'success',
                'message': 'Document downloaded and converted to PDF successfully',
                'document_path': pdf_filepath,
                'document_type': 'PDF',
                'file_size_bytes': file_size,
                'questions_count': len(questions),
                'document_url': documents_url,
                'conversion_note': 'All documents are automatically converted to PDF format'
            }
            
            # Include questions in response for reference
            if questions:
                response_data['questions'] = questions
            
            return jsonify(response_data), 200
            
        except Exception as e:
            return jsonify({
                'error': f'Failed to download document: {str(e)}',
                'status': 'failed'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in hackrx_run endpoint: {e}")
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status': 'failed'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Document extraction and PDF conversion service is running',
        'supported_input_formats': ['PDF', 'DOCX', 'DOC', 'EML', 'MSG'],
        'output_format': 'PDF (all documents converted to PDF)',
        'features': ['Document download', 'Automatic PDF conversion', 'Office 365 viewer support']
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'failed'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'status': 'failed'
    }), 405

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
