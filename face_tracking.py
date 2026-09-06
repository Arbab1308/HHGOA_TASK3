import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FaceTracker:
    """
    Track faces across different social platforms and temporal dimensions.
    Creates a comprehensive Person Profile from raw search matches.
    """
    
    def __init__(self):
        logger.info("Initializing FaceTracker module...")
    
    def create_person_profile(self, face_id: str, discovered_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a comprehensive profile of a person based on discovered social posts"""
        if not discovered_posts:
            return {"person_id": face_id, "profile_strength": 0}
            
        try:
            # Sort posts chronologically based on simulated metadata or creation times
            # In a real implementation we would parse dates; here we use order of discovery/confidence
            # For hackathon safety, we mock the timeline if actual timestamps aren't present
            sorted_posts = discovered_posts.copy()
            
            platforms = list(set([p.get('platform', 'unknown') for p in discovered_posts]))
            total_engagement = sum([p.get('likes', 0) + p.get('comments', 0) for p in discovered_posts])
            
            profile = {
                "person_id": face_id,
                "profile_strength": len(discovered_posts),
                "total_appearances": len(discovered_posts),
                "platforms_present": platforms,
                "total_digital_engagement": total_engagement,
                "cross_platform_presence": len(platforms) > 1,
                "posts_timeline": sorted_posts,
                "primary_platform": self._get_primary_platform(discovered_posts),
                "tracking_generated_at": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info(f"Created person profile for {face_id} with {profile['profile_strength']} appearances across {len(platforms)} platforms.")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create person profile: {e}")
            return {"person_id": face_id, "error": str(e)}

    def _get_primary_platform(self, posts: List[Dict[str, Any]]) -> str:
        """Determine primary platform by frequency of appearance"""
        platforms = [p.get('platform') for p in posts if p.get('platform')]
        if not platforms:
            return "unknown"
        return max(set(platforms), key=platforms.count)
