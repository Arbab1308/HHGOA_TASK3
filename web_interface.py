import os
import logging
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from pipeline import FaceBlockchainPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize our pipeline (zero-setup local chain)
pipeline = FaceBlockchainPipeline(output_dir="output", use_local_blockchain=True)

@app.route('/', methods=['GET'])
def index():
    """Render the minimal UI frontend."""
    return render_template('index.html')

@app.route('/api/verify', methods=['POST'])
def verify_face():
    """Handle the face upload and trigger the backend pipeline."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Save the uploaded file
            file.save(filepath)
            logger.info(f"Received image: {filepath}")
            
            # Execute the end-to-end pipeline
            results = pipeline.run(filepath, save_results=True)
            
            # Clean up the uploaded file to save space
            if os.path.exists(filepath):
                os.remove(filepath)
                
            if results.get('status') == 'success':
                return jsonify(results)
            else:
                return jsonify(results), 500
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return jsonify({'error': str(e), 'status': 'failed'}), 500

if __name__ == '__main__':
    logger.info("Starting Web Interface on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
