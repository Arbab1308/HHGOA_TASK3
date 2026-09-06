import logging
import traceback
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

class RobustErrorRecovery:
    """
    Multi-level error handling:
    1. Attempt operation normally
    2. Fallback logic if provided
    3. Return structured error state to prevent pipeline crash
    """
    
    def __init__(self):
        self.error_log = []
        self.recovery_stats = {
            "total_errors": 0,
            "recovered": 0,
            "failed": 0
        }
    
    def safe_execute(self, step_name: str, primary_func: Callable, fallback_func: Callable = None, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute a pipeline step safely with multi-level recovery
        """
        logger.info(f"Safe Execution started for: {step_name}")
        
        try:
            # Level 1: Normal execution
            result = primary_func(*args, **kwargs)
            return {
                "success": True,
                "result": result,
                "recovery_used": False
            }
            
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.warning(f"Level 1 failed for {step_name}: {error_msg}")
            
            self.error_log.append({
                "step": step_name,
                "level": 1,
                "error": error_msg,
                "trace": stack_trace
            })
            self.recovery_stats["total_errors"] += 1
            
            # Level 2: Fallback execution if provided
            if fallback_func:
                try:
                    logger.info(f"Attempting Level 2 fallback for {step_name}...")
                    result = fallback_func(*args, **kwargs)
                    
                    self.recovery_stats["recovered"] += 1
                    logger.info(f"Level 2 fallback successful for {step_name}")
                    
                    return {
                        "success": True,
                        "result": result,
                        "recovery_used": True,
                        "original_error": error_msg
                    }
                except Exception as e2:
                    error_msg2 = str(e2)
                    logger.error(f"Level 2 fallback failed for {step_name}: {error_msg2}")
                    
                    self.error_log.append({
                        "step": step_name,
                        "level": 2,
                        "error": error_msg2
                    })
                    
            self.recovery_stats["failed"] += 1
            logger.error(f"All recovery levels failed for {step_name}")
            
            return {
                "success": False,
                "error": error_msg,
                "recovery_used": fallback_func is not None
            }
            
    def get_recovery_report(self) -> Dict[str, Any]:
        """Detailed recovery statistics"""
        total = max(self.recovery_stats['total_errors'], 1)
        rate = (self.recovery_stats['recovered'] / total) * 100
        
        return {
            "statistics": self.recovery_stats,
            "recovery_rate": f"{rate:.2f}%",
            "error_log": self.error_log[-10:]  # Last 10 errors
        }
