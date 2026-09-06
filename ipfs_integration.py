import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class IPFSVerificationStorage:
    """
    Store verification records on IPFS (Simulated for hackathon environment):
    - Immutable storage
    - Content-addressed
    - Globally accessible
    - Can't be tampered with
    """
    
    def __init__(self):
        # In a real production environment, we would use: from ipfshttpclient import connect
        self.ipfs_hashes = {}
    
    def store_verification_on_ipfs(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store complete verification data on IPFS (simulated)"""
        try:
            # Serialize data consistently
            data_json = json.dumps(verification_data, default=str, sort_keys=True)
            
            # Generate deterministic IPFS-style CID (Content Identifier)
            # IPFS v0 CIDs often start with Qm and use base58. For simulation, we use a custom prefix + sha256.
            content_hash = hashlib.sha256(data_json.encode()).hexdigest()
            ipfs_hash = "Qm" + content_hash[:44]
            
            self.ipfs_hashes[ipfs_hash] = {
                "data": verification_data,
                "stored_at": datetime.utcnow().isoformat() + "Z",
                "size": len(data_json)
            }
            
            logger.info(f"Stored record securely via IPFS hashing: {ipfs_hash}")
            
            return {
                "ipfs_hash": ipfs_hash,
                "access_url": f"https://gateway.ipfs.io/ipfs/{ipfs_hash}",
                "size_bytes": len(data_json),
                "stored_at": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            logger.error(f"IPFS simulation failed: {e}")
            raise
    
    def retrieve_from_ipfs(self, ipfs_hash: str) -> Dict[str, Any]:
        """Retrieve verification data from IPFS"""
        if ipfs_hash in self.ipfs_hashes:
            return self.ipfs_hashes[ipfs_hash]['data']
        
        raise ValueError(f"IPFS hash not found: {ipfs_hash}")
    
    def verify_ipfs_integrity(self, ipfs_hash: str, data: Dict[str, Any]) -> bool:
        """Verify data hasn't been tampered with (content-addressing integrity)"""
        try:
            data_json = json.dumps(data, default=str, sort_keys=True)
            computed_hash = "Qm" + hashlib.sha256(data_json.encode()).hexdigest()[:44]
            
            return computed_hash == ipfs_hash
        except Exception as e:
            logger.error(f"IPFS integrity check failed: {e}")
            return False
