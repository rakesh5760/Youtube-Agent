import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger

class AnalyticsAgent:
    def __init__(self):
        """
        Placeholder for the Analytics Agent.
        This agent is slated for Future Phases (Not MVP).
        """
        pass

    def fetch_metrics(self, video_id):
        """
        Future implementation to fetch Views, Likes, CTR, and Retention.
        """
        logger.info(f"Analytics Agent: Fetching metrics for {video_id} is planned for Phase 2.")
        return {
            "views": 0,
            "likes": 0,
            "ctr": 0.0,
            "retention": 0.0
        }

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Analytics Agent (Future Phase)...")
    agent = AnalyticsAgent()
    metrics = agent.fetch_metrics("dummy_video_id")
    print(metrics)
