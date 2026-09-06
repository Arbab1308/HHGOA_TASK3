"""
Main Pipeline Orchestrator
Coordinates the multi-face identification -> social search -> IPFS storage -> blockchain verification workflow
"""

import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from face_detector import FaceDetector
from social_search import SocialMediaSearcher
from blockchain_handler import BlockchainVerifier
from audit_logger import AuditLogger
from error_recovery import RobustErrorRecovery
from ipfs_integration import IPFSVerificationStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FaceBlockchainPipeline:
    """
    Enterprise-grade pipeline for multi-face biometric identification, social tracking,
    immutable IPFS storage, and blockchain verification.
    """
    
    def __init__(self, output_dir: str = "output", use_local_blockchain: bool = True):
        """Initialize the robust pipeline"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Core modules
        self.face_detector = FaceDetector()
        self.social_searcher = SocialMediaSearcher()
        self.blockchain_verifier = BlockchainVerifier(use_local_chain=use_local_blockchain)
        self.blockchain_verifier.setup_account()
        
        # Enterprise enhancement modules
        self.audit_logger = AuditLogger(output_dir=str(self.output_dir))
        self.error_recovery = RobustErrorRecovery()
        self.ipfs_storage = IPFSVerificationStorage()
        
        logger.info("Enterprise Pipeline initialized successfully")
    
    def run(self, image_path: str, save_results: bool = True) -> Dict:
        """Run the complete robust pipeline"""
        start_time = time.time()
        pipeline_id = self._generate_pipeline_id()
        
        logger.info("=" * 80)
        logger.info(f"STARTING FACE-BLOCKCHAIN ENTERPRISE PIPELINE [{pipeline_id}]")
        logger.info("=" * 80)
        
        results = {
            "pipeline_id": pipeline_id,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "input_image": str(image_path),
            "steps": {}
        }
        
        try:
            # Validate input
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            # ---------------------------------------------------------
            # Step 1: Face Detection & Liveness
            # ---------------------------------------------------------
            logger.info("\n[STEP 1/3] Multi-Face Detection and Liveness Check")
            face_result = self.error_recovery.safe_execute(
                "face_detection",
                self._step_face_detection,
                fallback_func=None,  # Face detection is critical, no fallback without CV changes
                image_path=image_path
            )
            
            results["steps"]["face_detection"] = face_result
            if not face_result["success"]:
                raise Exception(f"Face detection failed: {face_result.get('error')}")
                
            face_data = face_result["result"]
            
            # ---------------------------------------------------------
            # Step 2: Social Media Search & Face Tracking
            # ---------------------------------------------------------
            logger.info("\n[STEP 2/3] Social Media Search & Timeline Construction")
            search_result = self.error_recovery.safe_execute(
                "social_search",
                self._step_social_search,
                fallback_func=None,
                image_path=image_path,
                face_signature=face_data["primary_face_signature"]
            )
            
            results["steps"]["social_search"] = search_result
            if not search_result["success"]:
                raise Exception(f"Social search failed: {search_result.get('error')}")
                
            social_data = search_result["result"]
            
            # ---------------------------------------------------------
            # Step 3: IPFS & Blockchain Verification
            # ---------------------------------------------------------
            logger.info("\n[STEP 3/3] IPFS Archiving and Blockchain Verification")
            bc_result = self.error_recovery.safe_execute(
                "blockchain_verification",
                self._step_blockchain_verification,
                fallback_func=None,
                face_signature=face_data["primary_face_signature"],
                social_post=social_data["top_match"],
                post_metadata=social_data["post_metadata"],
                person_profile=social_data["person_profile"],
                liveness_data=face_data["liveness_data"]
            )
            
            results["steps"]["blockchain_verification"] = bc_result
            if not bc_result["success"]:
                raise Exception(f"Blockchain verification failed: {bc_result.get('error')}")

            # Pipeline completed successfully
            duration = time.time() - start_time
            results["status"] = "success"
            results["end_time"] = datetime.utcnow().isoformat() + "Z"
            results["duration_sec"] = round(duration, 2)
            results["recovery_report"] = self.error_recovery.get_recovery_report()
            
            self.audit_logger.log_pipeline_execution(pipeline_id, image_path, "success", duration)
            
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            
            if save_results:
                self._save_results(results)
                
            return results
            
        except Exception as e:
            logger.error(f"Pipeline crashed: {e}")
            duration = time.time() - start_time
            self.audit_logger.log_pipeline_execution(pipeline_id, image_path, "failed", duration)
            
            results["status"] = "failed"
            results["error"] = str(e)
            results["end_time"] = datetime.utcnow().isoformat() + "Z"
            results["duration_sec"] = round(duration, 2)
            results["recovery_report"] = self.error_recovery.get_recovery_report()
            
            if save_results:
                self._save_results(results)
            return results

    def _step_face_detection(self, image_path: str) -> Dict[str, Any]:
        """Execute face detection step"""
        face_encodings, face_locations, liveness_results = self.face_detector.encode_faces(image_path)
        
        if not face_encodings:
            self.audit_logger.log_face_detection(image_path, 0, 0.0, "failed", "No faces detected")
            raise ValueError("No faces detected in image")
            
        # Select primary face (e.g. largest or first)
        primary_idx = 0
        primary_encoding = face_encodings[primary_idx]
        primary_liveness = liveness_results[primary_idx]
        face_sig = self.face_detector.get_face_encoding_signature(primary_encoding)
        
        self.audit_logger.log_face_detection(
            image_path, 
            len(face_encodings), 
            primary_liveness.get("confidence", 0.0), 
            "success"
        )
        
        return {
            "total_faces_detected": len(face_encodings),
            "primary_face_signature": face_sig,
            "liveness_data": primary_liveness,
            "face_location": face_locations[primary_idx]
        }

    def _step_social_search(self, image_path: str, face_signature: str) -> Dict[str, Any]:
        """Execute social media search and face tracking step"""
        top_match = self.social_searcher.get_top_match(image_path)
        if not top_match:
            raise ValueError("No social media matches found")
            
        # Build comprehensive person profile
        person_profile = self.social_searcher.generate_person_profile(face_signature, image_path)
        post_metadata = self.social_searcher.create_post_metadata(top_match)
        
        return {
            "top_match": top_match,
            "post_metadata": post_metadata,
            "person_profile": person_profile
        }

    def _step_blockchain_verification(self, face_signature: str, social_post: Dict, 
                                      post_metadata: Dict, person_profile: Dict, 
                                      liveness_data: Dict) -> Dict[str, Any]:
        """Execute IPFS storage and Blockchain verification step"""
        # Aggregate complete verification package
        verification_package = {
            "face_signature": face_signature,
            "liveness_checks": liveness_data,
            "social_metadata": post_metadata,
            "person_profile": person_profile,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # 1. Store on IPFS
        ipfs_record = self.ipfs_storage.store_verification_on_ipfs(verification_package)
        
        # 2. Upload IPFS hash to Blockchain
        # Add IPFS hash to metadata for blockchain payload
        enhanced_metadata = post_metadata.copy()
        enhanced_metadata["ipfs_hash"] = ipfs_record["ipfs_hash"]
        
        tx_hash, blockchain_record = self.blockchain_verifier.upload_to_blockchain(
            face_signature, social_post, enhanced_metadata
        )
        
        # 3. Verify
        data_hash = blockchain_record["data_hash"]
        is_verified, verification_details = self.blockchain_verifier.verify_data_on_blockchain(data_hash)
        
        self.audit_logger.log_blockchain_transaction(
            tx_hash, data_hash, is_verified, "success" if is_verified else "failed"
        )
        
        certificate = self.blockchain_verifier.get_verification_certificate(data_hash, blockchain_record)
        certificate["ipfs_archive"] = ipfs_record
        
        return {
            "transaction_hash": tx_hash,
            "data_hash": data_hash,
            "ipfs_record": ipfs_record,
            "blockchain": self.blockchain_verifier.chain_name,
            "is_verified": is_verified,
            "blockchain_record": blockchain_record,
            "certificate": certificate
        }

    def _generate_pipeline_id(self) -> str:
        """Generate unique pipeline execution ID"""
        data = f"{datetime.utcnow().isoformat()}{time.time()}".encode()
        import hashlib
        return hashlib.sha256(data).hexdigest()[:16]

    def _save_results(self, results: Dict):
        """Save pipeline results"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"pipeline_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved complete pipeline results to {results_file}")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <image_path> [--local] [--output <dir>]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    use_local = "--local" in sys.argv
    output_dir = "output"
    
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
            
    pipeline = FaceBlockchainPipeline(output_dir=output_dir, use_local_blockchain=use_local)
    results = pipeline.run(image_path)
    
    print("\n" + "=" * 80)
    print("PIPELINE RESULTS SUMMARY")
    print("=" * 80)
    print(f"Status: {results['status']}")
    if results['status'] == 'success':
        print(f"Pipeline ID: {results['pipeline_id']}")
        print(f"Duration: {results['duration_sec']}s")
        bd = results["steps"].get("blockchain_verification", {}).get("result", {})
        if bd:
            print(f"Transaction Hash: {bd.get('transaction_hash')}")
            print(f"IPFS Hash: {bd.get('ipfs_record', {}).get('ipfs_hash')}")
            print(f"Verified: {bd.get('is_verified')}")
    else:
        print(f"Error: {results.get('error')}")

if __name__ == "__main__":
    main()
