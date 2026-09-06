# Face-Blockchain Verification Pipeline

A comprehensive end-to-end pipeline that combines face identification, social media search, and blockchain verification to create tamper-evident records of face-to-social-post connections.

## Overview

This project demonstrates an advanced pipeline with three sequential stages:

1. **Face Detection & Encoding** - Detects faces in input images and generates 128-dimensional face encodings
2. **Social Media Search** - Performs reverse image search to find matching social media posts across multiple platforms
3. **Blockchain Verification** - Uploads and verifies discovered data on blockchain, creating tamper-evident records

## Architecture

```
Input Image
    ↓
[Face Detection Module] → 128-dim face encoding
    ↓
[Social Search Module] → Find matching social posts (Instagram, Twitter, Facebook, etc.)
    ↓
[Blockchain Module] → Upload to blockchain & verify
    ↓
Verification Certificate
```

## Features

- ✅ **Face Detection**: Uses industry-standard `face_recognition` library for accurate face detection
- ✅ **Social Media Search**: Simulates real-world reverse image search across multiple platforms
- ✅ **Blockchain Integration**: Uploads data to blockchain with transaction hash generation
- ✅ **Verification Certificate**: Generates cryptographic certificates proving verification
- ✅ **Web Interface**: User-friendly Flask-based interface for easy testing
- ✅ **Offline Mode**: Works without blockchain connection (simulates blockchain transactions)
- ✅ **Detailed Logging**: Comprehensive logging of all pipeline steps
- ✅ **JSON Export**: All results saved as structured JSON files

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- (Optional) Ganache CLI for local blockchain testing

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/face-blockchain-pipeline.git
cd face-blockchain-pipeline
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install dlib (required for face_recognition)**

On macOS/Linux:
```bash
brew install cmake
pip install dlib
```

On Windows:
```bash
pip install cmake
pip install dlib
```

## Usage

### Command Line

Run the pipeline with an image file:

```bash
python pipeline.py path/to/face_image.jpg --local --output ./results
```

**Arguments:**
- `image_path` - Path to input face image (required)
- `--local` - Use local Ganache blockchain (default behavior)
- `--output <dir>` - Output directory for results (default: ./output)

### Example

```bash
python pipeline.py samples/face.jpg --local --output ./verification_results
```

### Web Interface

Start the web server:

```bash
python web_interface.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

**Features:**
- Drag-and-drop image upload
- Real-time processing status
- Visual results display
- Demo mode for quick testing

## Blockchain Configuration

### Local Ganache (Recommended for Testing)

1. **Install Ganache CLI**
```bash
npm install -g ganache-cli
```

2. **Start local blockchain**
```bash
ganache-cli --host 0.0.0.0 --port 8545
```

3. **Run pipeline**
```bash
python pipeline.py face_image.jpg --local
```

### Public Testnet (Sepolia)

1. **Update `blockchain_handler.py`**
```python
# Change use_local_chain to False
blockchain_verifier = BlockchainVerifier(use_local_chain=False)
```

2. **Set Infura API key** (get from https://infura.io)
```python
# In blockchain_handler.py
self.w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/YOUR_INFURA_KEY'))
```

3. **Ensure account has test ETH** (from faucet: https://sepoliafaucet.com)

## Output Files

The pipeline generates the following output files:

### 1. Pipeline Results
`pipeline_results_TIMESTAMP.json` - Complete pipeline execution results
```json
{
  "pipeline_id": "abc123def456",
  "status": "success",
  "steps": {
    "face_detection": { ... },
    "social_search": { ... },
    "blockchain_verification": { ... }
  }
}
```

### 2. Blockchain Record
`blockchain_record_TIMESTAMP.json` - Tamper-proof blockchain record
```json
{
  "data_hash": "sha256hash...",
  "transaction_hash": "0xtxhash...",
  "blockchain": "Local Ganache",
  "verified": true,
  "timestamp": "2024-03-15T14:30:00Z"
}
```

### 3. Verification Certificate
`verification_certificate_TIMESTAMP.json` - Official verification proof
```json
{
  "certificate_id": "certid123",
  "is_verified": true,
  "certificate_status": "valid",
  "proof": {
    "face_identified": true,
    "social_post_found": true,
    "blockchain_recorded": true
  }
}
```

### 4. Social Search Results
`social_search_results_TIMESTAMP.json` - Discovered social media matches
```json
{
  "platform_results": { ... },
  "top_match": { ... }
}
```

## Module Documentation

### face_detector.py

Handles face detection and encoding.

**Main Methods:**
- `detect_faces(image_path)` - Detect all faces in image
- `encode_faces(image_path)` - Generate 128-dimensional encodings
- `compare_faces(encoding1, encoding2)` - Compare two faces
- `get_face_encoding_signature(encoding)` - Create blockchain-compatible signature

### social_search.py

Performs social media search and post discovery.

**Main Methods:**
- `search_bing_images(image_path)` - Search Bing for matching images
- `search_social_platforms(image_path)` - Multi-platform search
- `get_top_match(image_path)` - Get best matching post
- `create_post_metadata(post)` - Standardize post data

### blockchain_handler.py

Manages blockchain interactions and verification.

**Main Methods:**
- `upload_to_blockchain(face_sig, social_post, metadata)` - Upload to chain
- `verify_data_on_blockchain(data_hash)` - Verify on-chain record
- `get_verification_certificate(data_hash, record)` - Generate certificate

### pipeline.py

Orchestrates the complete workflow.

**Main Methods:**
- `run(image_path)` - Execute full pipeline
- `_step_face_detection(image_path)` - Stage 1
- `_step_social_search(image_path)` - Stage 2
- `_step_blockchain_verification(...)` - Stage 3

## Known Limitations

1. **Social Media Search Simulation**
   - Currently simulates search results with realistic mock data
   - In production, integrate with real APIs: Bing Image Search, TinEye, reverse.photos
   - Social platform detection is simulated (Instagram, Twitter, Facebook)

2. **Blockchain Integration**
   - Offline mode uses local registry instead of real blockchain
   - For production: integrate with real Ethereum RPC endpoints
   - Smart contracts would need deployment (currently ABI defined but not deployed)

3. **Face Recognition**
   - Uses HOG model (faster but less accurate)
   - Can switch to CNN model for higher accuracy (requires CUDA GPU)
   - Tolerance tuned to 0.6 (may need adjustment for different use cases)

4. **Web Interface**
   - Single-threaded demo mode (use production WSGI server for production)
   - No authentication or rate limiting
   - Results stored in memory (implement database for persistence)

5. **Privacy Considerations**
   - Face encodings are stored in memory and files
   - Social post data includes PII (usernames, locations)
   - Implement proper data protection and compliance measures

## Technical Stack

- **Face Recognition**: dlib, face_recognition, OpenCV
- **Web Framework**: Flask, HTML5, CSS3, JavaScript
- **Blockchain**: Web3.py, Ethereum
- **Data Processing**: NumPy, Pillow
- **Utilities**: requests, python-dotenv, Faker

## Environment Variables

Create `.env` file:

```
INFURA_API_KEY=your_infura_key_here
PRIVATE_KEY=your_account_private_key_here
BING_API_KEY=your_bing_search_api_key_here
```

## Testing

Run with demo image:

```bash
python pipeline.py samples/test_face.jpg --local
```

Or use web interface demo:
```
http://localhost:5000 → Click "Run Demo" button
```

## Performance Metrics

- Face Detection: ~100-500ms per image (HOG model)
- Social Search: ~1-2 seconds (API call simulation)
- Blockchain Upload: ~0.1 seconds (local) to 15-30 seconds (live network)
- Total Pipeline: ~2-3 seconds (local) to 30-60 seconds (live)

## Security Notes

⚠️ **Important Security Considerations:**

1. **Private Keys**: Never commit private keys to git
2. **API Keys**: Use environment variables, not hardcoded keys
3. **Face Data**: Implement encryption for stored face encodings
4. **Social Data**: Comply with platform ToS and data protection laws
5. **Smart Contracts**: Audit contracts before mainnet deployment

## Future Enhancements

- [ ] Real blockchain contract deployment
- [ ] Integration with actual reverse image search APIs
- [ ] Multi-face detection and comparison
- [ ] Real social media API integration
- [ ] Database backend for result persistence
- [ ] Advanced verification methods (zero-knowledge proofs)
- [ ] Web3 wallet integration
- [ ] Real-time notifications

## Contributing

Contributions welcome! Please:

1. Fork repository
2. Create feature branch
3. Submit pull request with description

## License

MIT License - See LICENSE file

## References

- **Face Recognition**: https://github.com/ageitgey/face_recognition
- **OpenCV**: https://opencv.org/
- **Web3.py**: https://web3py.readthedocs.io/
- **Ethereum**: https://ethereum.org/

## Support

For issues, questions, or suggestions:
- Open GitHub issue
- Check existing documentation
- Review example outputs in `output/` folder

## Disclaimer

This pipeline is for educational and demonstration purposes. For production use:
- Conduct thorough security audits
- Obtain proper legal compliance review
- Implement proper data protection measures
- Test with real blockchain before mainnet deployment

---

**Built for HH Goa 2026** | Face Identification & Blockchain Verification Task
