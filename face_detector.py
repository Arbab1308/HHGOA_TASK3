import os
import hashlib
import logging
from typing import Tuple, List, Optional
import numpy as np
import face_recognition

logger = logging.getLogger(__name__)

class FaceDetector:
    """
    Handles face detection and encoding using dlib via face_recognition library.
    """
    def __init__(self):
        logger.info("Initializing FaceDetector module...")

    def encode_faces(self, image_path: str) -> Tuple[Optional[List[np.ndarray]], Optional[List[Tuple[int, int, int, int]]]]:
        """
        Loads an image, detects faces, and generates 128-dimensional encodings.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (face_encodings, face_locations) or (None, None) if no faces found
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
                
            # Load the image
            image = face_recognition.load_image_file(image_path)
            
            # Find all face locations and face encodings in the image
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                logger.warning(f"No faces detected in {image_path}")
                return None, None
                
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            # Convert face encodings to lists so they are JSON serializable
            face_encodings_list = [encoding.tolist() for encoding in face_encodings]
            
            return face_encodings_list, face_locations
            
        except Exception as e:
            logger.error(f"Error during face encoding: {e}")
            raise

    def get_face_encoding_signature(self, face_encoding: np.ndarray) -> str:
        """
        Generates a cryptographic SHA-256 signature from the 128-dim face encoding.
        This provides a privacy-preserving fingerprint of the face for blockchain storage.
        
        Args:
            face_encoding: list or numpy array representing the face
            
        Returns:
            Hex string of the SHA-256 hash
        """
        try:
            # Ensure it's a numpy array for rounding
            if isinstance(face_encoding, list):
                face_encoding = np.array(face_encoding)
                
            # Round the encoding to standard precision to ensure consistency
            rounded_encoding = np.round(face_encoding, decimals=5)
            
            # Convert numpy array to bytes
            encoding_bytes = rounded_encoding.tobytes()
            
            # Generate SHA-256 hash
            signature = hashlib.sha256(encoding_bytes).hexdigest()
            return signature
            
        except Exception as e:
            logger.error(f"Error generating face signature: {e}")
            raise
