import os
import cv2
import hashlib
import logging
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import face_recognition

logger = logging.getLogger(__name__)

class BiometricSecurityVerification:
    """Handles biometric security such as liveness detection."""
    
    @staticmethod
    def verify_liveness(image_path: str, face_location: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """Check if face is real/living (not spoofed) using texture variance."""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {"liveness_detected": False, "confidence": 0.0, "texture_variance": 0}
                
            # face_location is (top, right, bottom, left)
            top, right, bottom, left = face_location
            
            # Ensure coordinates are within image bounds
            h, w = img.shape[:2]
            top = max(0, top)
            bottom = min(h, bottom)
            left = max(0, left)
            right = min(w, right)
            
            face_region = img[top:bottom, left:right]
            if face_region.size == 0:
                return {"liveness_detected": False, "confidence": 0.0, "texture_variance": 0}
                
            # Convert to grayscale for Laplacian
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            
            # Compute texture variance (blur detection)
            # Real faces tend to have higher variance/texture than flat printed photos
            texture_variance = float(np.var(cv2.Laplacian(gray, cv2.CV_64F)))
            
            # Simple thresholding logic for simulation
            # Normally we would tune this threshold (e.g., 100) based on dataset
            liveness_score = float(min(texture_variance / 500.0, 1.0))
            
            return {
                "liveness_detected": bool(liveness_score > 0.4),
                "confidence": float(round(liveness_score, 3)),
                "texture_variance": float(round(texture_variance, 2))
            }
        except Exception as e:
            logger.error(f"Liveness detection failed: {e}")
            return {"liveness_detected": False, "confidence": 0.0, "texture_variance": 0, "error": str(e)}

class FaceDetector:
    """
    Handles face detection, multi-face tracking, and encoding using dlib via face_recognition library.
    """
    def __init__(self):
        logger.info("Initializing FaceDetector module...")
        self.biometrics = BiometricSecurityVerification()

    def encode_faces(self, image_path: str) -> Tuple[Optional[List[np.ndarray]], Optional[List[Tuple[int, int, int, int]]], Optional[List[Dict[str, Any]]]]:
        """
        Loads an image, detects ALL faces, and generates 128-dimensional encodings and liveness scores.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (face_encodings, face_locations, liveness_scores) or (None, None, None)
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
                
            # Load the image
            image = face_recognition.load_image_file(image_path)
            
            # Find ALL face locations and encodings
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                logger.warning(f"No faces detected in {image_path}")
                return None, None, None
                
            face_encodings = face_recognition.face_encodings(image, face_locations)
            face_encodings_list = [encoding.tolist() for encoding in face_encodings]
            
            # Check liveness for all faces
            liveness_results = []
            for loc in face_locations:
                liveness = self.biometrics.verify_liveness(image_path, loc)
                liveness_results.append(liveness)
                
            logger.info(f"Detected {len(face_locations)} faces. Liveness checked.")
            return face_encodings_list, face_locations, liveness_results
            
        except Exception as e:
            logger.error(f"Error during face encoding: {e}")
            raise

    def get_face_encoding_signature(self, face_encoding: np.ndarray) -> str:
        """
        Generates a cryptographic SHA-256 signature from the 128-dim face encoding.
        """
        try:
            if isinstance(face_encoding, list):
                face_encoding = np.array(face_encoding)
                
            rounded_encoding = np.round(face_encoding, decimals=5)
            encoding_bytes = rounded_encoding.tobytes()
            signature = hashlib.sha256(encoding_bytes).hexdigest()
            return signature
            
        except Exception as e:
            logger.error(f"Error generating face signature: {e}")
            raise
