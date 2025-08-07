import logging
import os
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
ALLOWED_EXTENSIONS = {'pdf'}

# Create downloads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def is_valid_pdf_url(url):
    """Check if the URL is valid and points to a PDF"""
    try:
        parsed_url = urlparse(url)
        # Check if URL has valid scheme
        if parsed_url.scheme not in ['http', 'https']:
            return False
        
        # Check if the path contains .pdf (handles query parameters)
        path = parsed_url.path.lower()
        return path.endswith('.pdf') or '.pdf' in path
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False

def download_pdf_from_url(url, filename=None):
    """Download PDF from URL and save it locally"""
    try:
        logger.info(f"Downloading PDF from URL: {url}")
        
        # Make request with headers to mimic browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check if content type is PDF (more flexible check)
        content_type = response.headers.get('content-type', '').lower()
        # Accept if content-type contains 'pdf' OR if URL path contains .pdf OR if content-type is application/octet-stream (common for blob storage)
        is_pdf_content = ('pdf' in content_type or 
                         '.pdf' in url.lower() or 
                         'application/octet-stream' in content_type or
                         'binary/octet-stream' in content_type)
        
        if not is_pdf_content:
            logger.warning(f"Content type: {content_type}, but proceeding since URL suggests PDF")
        
        # Generate filename if not provided
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or 'document.pdf'
            if not filename.endswith('.pdf'):
                filename += '.pdf'
        
        # Save the PDF
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"PDF downloaded successfully: {filepath}")
        return filepath
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading PDF: {e}")
        raise Exception(f"Failed to download PDF: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise Exception(f"Unexpected error downloading PDF: {str(e)}")

@app.route('/hackrx/run', methods=['POST'])
def hackrx_run():
    """Handle the POST request to extract PDF from URL"""
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
        
        # Validate the PDF URL
        if not is_valid_pdf_url(documents_url):
            return jsonify({
                'error': 'Invalid PDF URL provided',
                'status': 'failed'
            }), 400
        
        # Download the PDF
        try:
            pdf_filepath = download_pdf_from_url(documents_url)
            
            # Get file size for verification
            file_size = os.path.getsize(pdf_filepath)
            
            response_data = {
                'status': 'success',
                'message': 'PDF downloaded successfully',
                'pdf_path': pdf_filepath,
                'file_size_bytes': file_size,
                'questions_count': len(questions),
                'document_url': documents_url
            }
            
            # Include questions in response for reference
            if questions:
                response_data['questions'] = questions
            
            return jsonify(response_data), 200
            
        except Exception as e:
            return jsonify({
                'error': f'Failed to download PDF: {str(e)}',
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
        'message': 'PDF extraction service is running'
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
