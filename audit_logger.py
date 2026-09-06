import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Complete audit trail of:
    - Every image processed
    - Every face detected
    - Every blockchain transaction
    - Every verification
    - Performance metrics
    """
    
    def __init__(self, output_dir: str = "output", log_filename: str = "audit_trail.jsonl"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.log_file = self.output_dir / log_filename
    
    def log_face_detection(self, image_path: str, faces_found: int, liveness_score: float, status: str = "success", error: str = ""):
        """Log face detection event"""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "face_detection",
            "image_path": str(image_path),
            "faces_found": faces_found,
            "liveness_score": round(liveness_score, 3) if liveness_score else None,
            "status": status,
            "error": error
        }
        self._write_log(event)
    
    def log_blockchain_transaction(self, tx_hash: str, data_hash: str, verification_result: bool, status: str = "success", error: str = ""):
        """Log blockchain transaction"""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "blockchain_transaction",
            "transaction_hash": tx_hash,
            "data_hash": data_hash,
            "verification_result": verification_result,
            "status": status,
            "error": error
        }
        self._write_log(event)
        
    def log_pipeline_execution(self, pipeline_id: str, image_path: str, status: str, duration_sec: float):
        """Log the overall pipeline run"""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "pipeline_execution",
            "pipeline_id": pipeline_id,
            "image_path": str(image_path),
            "status": status,
            "duration_sec": round(duration_sec, 2)
        }
        self._write_log(event)
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate complete audit report summarizing the entire log"""
        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_events": self._count_events(),
            "face_detections": self._count_by_type("face_detection"),
            "blockchain_transactions": self._count_by_type("blockchain_transaction"),
            "pipeline_executions": self._count_by_type("pipeline_execution"),
            "errors": self._count_errors()
        }
        
        return report
    
    def _write_log(self, event: Dict[str, Any]):
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to audit log: {e}")
    
    def _count_events(self) -> int:
        try:
            if not self.log_file.exists():
                return 0
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except Exception:
            return 0
            
    def _count_by_type(self, event_type: str) -> int:
        try:
            if not self.log_file.exists():
                return 0
            count = 0
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("event_type") == event_type:
                        count += 1
            return count
        except Exception:
            return 0
            
    def _count_errors(self) -> int:
        try:
            if not self.log_file.exists():
                return 0
            count = 0
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("status") == "failed" or data.get("error"):
                        count += 1
            return count
        except Exception:
            return 0
