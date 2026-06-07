import sys
import os
import datetime
from dateutil import parser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.youtube_scheduler import get_schedule_info, get_authenticated_service
from config.config import config
from services.logger import logger

class BufferAgent:
    def __init__(self):
        # Read from config if present, otherwise default to requirements rules
        self.min_buffer = config.settings.get('buffer', {}).get('min_days', 7)
        self.max_buffer = config.settings.get('buffer', {}).get('max_days', 30)
        self.trigger_threshold = 30 # User requested to increase buffer to 30 days

    def check_buffer(self, youtube_service=None):
        """
        Checks the current schedule buffer on YouTube.
        Returns the current buffer size in days and the number of videos needed to reach max_buffer.
        """
        logger.info("Checking content publishing buffer...")
        
        if not youtube_service:
            youtube_service = get_authenticated_service()
            if not youtube_service:
                logger.error("Failed to authenticate with YouTube to check buffer.")
                return 0, 0
                
        # Get the latest date from YouTube via the scheduler service
        schedule_info = get_schedule_info(youtube_service)
        latest_date_str = schedule_info.get("latest_date")
        
        if not latest_date_str:
            logger.info("No scheduled videos found. Buffer is 0 days.")
            buffer_days = 0
        else:
            latest_date = parser.isoparse(latest_date_str)
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = latest_date - now
            buffer_days = max(0, delta.days)
            
        logger.info(f"Current publishing buffer: {buffer_days} days.")
        
        videos_needed = 0
        if buffer_days < self.trigger_threshold:
            # If buffer is less than 10, generate enough to fill the max buffer (30 days)
            videos_needed = self.max_buffer - buffer_days
            logger.info(f"Buffer is below threshold ({self.trigger_threshold}). We need to generate {videos_needed} videos.")
        else:
            logger.info(f"Buffer is healthy. No new videos needed right now.")
            
        return buffer_days, videos_needed

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Buffer Management Agent...")
    agent = BufferAgent()
    try:
        buffer_days, needed = agent.check_buffer()
        print(f"\n--- Buffer Report ---")
        print(f"Current Buffer: {buffer_days} days")
        print(f"Videos needed to reach max capacity ({agent.max_buffer} days): {needed}")
    except Exception as e:
        print(f"Error during test: {e}")
        print("Ensure your YouTube credentials.json and token.json are configured correctly.")
