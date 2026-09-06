"""
Main Pipeline Orchestrator
Coordinates the face identification -> social search -> blockchain verification workflow
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

from face_detector import FaceDetector
from social_search import SocialMediaSearcher
from blockchain_handler import BlockchainVerifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FaceBlockchainPipeline:
    """
    Complete pipeline for face identification and blockchain verification
    
    Flow:
    1. Face Detection: Detect and encode face from input image
    2. Social Search: Find matching social media posts
    3. Blockchain Upload: Verify and record on blockchain
    """
    
    def __init__(self, output_dir: str = "output", use_local_blockchain: bool = True):
        """Initialize the pipeline"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.face_detector = FaceDetector()
        self.social_searcher = SocialMediaSearcher()
        self.blockchain_verifier = BlockchainVerifier(use_local_chain=use_local_blockchain)
        self.blockchain_verifier.setup_account()
        
        logger.info("Pipeline initialized successfully")
    
    def run(self, image_path: str, save_results: bool = True) -> Dict:
        """
        Run the complete pipeline
        
        Args:
            image_path: Path to input face image
            save_results: Whether to save results to files
        
        Returns:
            Complete pipeline results dictionary
        """
        logger.info("=" * 80)
        logger.info("STARTING FACE-BLOCKCHAIN VERIFICATION PIPELINE")
        logger.info("=" * 80)
        
        # Validate input
        if not Path(image_path).exists():
            logger.error(f"Image not found: {image_path}")
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        results = {
            "pipeline_id": self._generate_pipeline_id(),
            "start_time": datetime.utcnow().isoformat() + "Z",
            "input_image": str(image_path),
            "steps": {}
        }
        
        try:
            # Step 1: Face Detection
            logger.info("\n[STEP 1/3] Face Detection and Encoding")
            logger.info("-" * 80)
            face_results = self._step_face_detection(image_path)
            results["steps"]["face_detection"] = face_results
            
            if not face_results["success"]:
                raise Exception("Face detection failed")
            
            face_encoding = face_results["face_encoding"]
            face_encoding_sig = face_results["face_encoding_signature"]
            
            # Step 2: Social Media Search
            logger.info("\n[STEP 2/3] Social Media Search")
            logger.info("-" * 80)
            search_results = self._step_social_search(image_path)
            results["steps"]["social_search"] = search_results
            
            if not search_results["success"]:
                raise Exception("Social media search failed")
            
            top_match = search_results["top_match"]
            post_metadata = search_results["post_metadata"]
            
            # Step 3: Blockchain Verification
            logger.info("\n[STEP 3/3] Blockchain Upload and Verification")
            logger.info("-" * 80)
            blockchain_results = self._step_blockchain_verification(
                face_encoding_sig, top_match, post_metadata
            )
            results["steps"]["blockchain_verification"] = blockchain_results
            
            if not blockchain_results["success"]:
                raise Exception("Blockchain verification failed")
            
            # Pipeline completed successfully
            results["status"] = "success"
            results["end_time"] = datetime.utcnow().isoformat() + "Z"
            
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            
            # Save results if requested
            if save_results:
                self._save_results(results)
            
            return results
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            results["end_time"] = datetime.utcnow().isoformat() + "Z"
            return results
    
    def _step_face_detection(self, image_path: str) -> Dict:
        """Execute face detection step"""
        logger.info(f"Processing image: {image_path}")
        
        try:
            face_encodings, face_locations = self.face_detector.encode_faces(image_path)
            
            if face_encodings is None:
                logger.error("No faces detected in image")
                return {"success": False, "error": "No faces detected"}
            
            # Use first detected face
            face_encoding = face_encodings[0]
            face_location = face_locations[0]
            
            # Generate signature for blockchain
            face_encoding_sig = self.face_detector.get_face_encoding_signature(face_encoding)
            
            logger.info(f"Face detected at location: {face_location}")
            logger.info(f"Face encoding generated (128-dim vector)")
            logger.info(f"Face signature (for blockchain): {face_encoding_sig[:32]}...")
            
            return {
                "success": True,
                "faces_detected": len(face_encodings),
                "face_location": face_location,
                "face_encoding": face_encoding,
                "face_encoding_signature": face_encoding_sig,
                "encoding_dimensions": len(face_encoding)
            }
        
        except Exception as e:
            logger.error(f"Face detection step failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _step_social_search(self, image_path: str) -> Dict:
        """Execute social media search step"""
        logger.info(f"Searching for matching social media posts...")
        
        try:
            # Get top matching post
            top_match = self.social_searcher.get_top_match(image_path)
            
            if not top_match:
                logger.error("No matching social posts found")
                return {"success": False, "error": "No matches found"}
            
            # Get platform results
            platform_results = self.social_searcher.search_social_platforms(image_path)
            
            # Create standardized metadata
            post_metadata = self.social_searcher.create_post_metadata(top_match)
            
            logger.info(f"Found matching post on {top_match['platform']}")
            logger.info(f"Username: {top_match['username']}")
            logger.info(f"Post URL: {top_match['post_url']}")
            logger.info(f"Engagement: {top_match.get('likes', 0)} likes, "
                       f"{top_match.get('comments', 0)} comments")
            
            return {
                "success": True,
                "platforms_searched": len(platform_results),
                "platform_results": platform_results,
                "top_match": top_match,
                "post_metadata": post_metadata,
                "total_matches": sum(len(posts) for posts in platform_results.values())
            }
        
        except Exception as e:
            logger.error(f"Social search step failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _step_blockchain_verification(self, face_encoding_sig: str, 
                                      social_post: Dict, 
                                      post_metadata: Dict) -> Dict:
        """Execute blockchain verification step"""
        logger.info(f"Uploading verification data to blockchain...")
        
        try:
            # Upload to blockchain
            tx_hash, blockchain_record = self.blockchain_verifier.upload_to_blockchain(
                face_encoding_sig, social_post, post_metadata
            )
            
            # Get data hash for verification
            data_hash = blockchain_record["data_hash"]
            
            # Verify the data
            is_verified, verification_details = self.blockchain_verifier.verify_data_on_blockchain(data_hash)
            
            # Generate certificate
            certificate = self.blockchain_verifier.get_verification_certificate(
                data_hash, blockchain_record
            )
            
            logger.info(f"Blockchain upload successful")
            logger.info(f"Transaction hash: {tx_hash}")
            logger.info(f"Data hash: {data_hash}")
            logger.info(f"Blockchain: {self.blockchain_verifier.chain_name}")
            logger.info(f"Verification status: {'VERIFIED' if is_verified else 'FAILED'}")
            
            return {
                "success": True,
                "transaction_hash": tx_hash,
                "data_hash": data_hash,
                "blockchain": self.blockchain_verifier.chain_name,
                "is_verified": is_verified,
                "blockchain_record": blockchain_record,
                "verification_details": verification_details,
                "certificate": certificate
            }
        
        except Exception as e:
            logger.error(f"Blockchain verification step failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_pipeline_id(self) -> str:
        """Generate unique pipeline execution ID"""
        import hashlib
        import time
        data = f"{datetime.utcnow().isoformat()}{time.time()}".encode()
        return hashlib.sha256(data).hexdigest()[:16]
    
    def _save_results(self, results: Dict):
        """Save complete pipeline results to files"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save complete results
        results_file = self.output_dir / f"pipeline_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved pipeline results to {results_file}")
        
        # Save blockchain record separately
        if results["steps"].get("blockchain_verification", {}).get("success"):
            blockchain_record = results["steps"]["blockchain_verification"]["blockchain_record"]
            blockchain_file = self.output_dir / f"blockchain_record_{timestamp}.json"
            self.blockchain_verifier.save_blockchain_record(blockchain_record, str(blockchain_file))
            
            # Save certificate
            certificate = results["steps"]["blockchain_verification"]["certificate"]
            cert_file = self.output_dir / f"verification_certificate_{timestamp}.json"
            self.blockchain_verifier.save_certificate(certificate, str(cert_file))
        
        # Save social search results
        if results["steps"].get("social_search", {}).get("success"):
            search_results = {
                "platform_results": results["steps"]["social_search"]["platform_results"],
                "top_match": results["steps"]["social_search"]["top_match"]
            }
            search_file = self.output_dir / f"social_search_results_{timestamp}.json"
            self.social_searcher.save_search_results(search_results, str(search_file))
        
        return results_file


def main():
    """Main entry point"""
    import sys
    
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <image_path> [--local] [--output <dir>]")
        print("\nExample: python pipeline.py face_image.jpg --local --output ./results")
        sys.exit(1)
    
    image_path = sys.argv[1]
    use_local = "--local" in sys.argv
    output_dir = "output"
    
    # Parse arguments
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
    
    # Run pipeline
    pipeline = FaceBlockchainPipeline(output_dir=output_dir, use_local_blockchain=use_local)
    results = pipeline.run(image_path)
    
    # Print summary
    print("\n" + "=" * 80)
    print("PIPELINE RESULTS SUMMARY")
    print("=" * 80)
    print(f"Status: {results['status']}")
    if results['status'] == 'success':
        print(f"Pipeline ID: {results['pipeline_id']}")
        
        bd = results["steps"].get("blockchain_verification", {})
        if bd.get("success"):
            print(f"Transaction Hash: {bd['transaction_hash']}")
            print(f"Data Hash: {bd['data_hash']}")
            print(f"Blockchain: {bd['blockchain']}")
            print(f"Verified: {bd['is_verified']}")
    else:
        print(f"Error: {results.get('error')}")


if __name__ == "__main__":
    main()
