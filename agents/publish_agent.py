import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.youtube_auth import get_authenticated_service
from services.youtube_uploader import upload_video
from services.youtube_scheduler import get_schedule_info
from services.logger import logger

DB_PATH = "database/agent.db"

class PublishAgent:
    def __init__(self):
        self.youtube_service = get_authenticated_service()
        
    def _store_upload(self, local_video_id, youtube_id, publish_date):
        """Stores the uploaded video metadata into the database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO uploads (video_id, youtube_id, publish_date, status)
                VALUES (?, ?, ?, 'scheduled')
            ''', (local_video_id, youtube_id, publish_date))
            
            # Optionally update the videos table status if local_video_id exists
            if local_video_id:
                cursor.execute("UPDATE videos SET status = 'published' WHERE id = ?", (local_video_id,))
                
            conn.commit()
            conn.close()
            logger.info(f"Stored YouTube ID {youtube_id} in database under local video ID {local_video_id}.")
        except Exception as e:
            logger.error(f"Error storing upload in database: {e}")

    def publish_video(self, file_path, title, description, tags, local_video_id=None):
        """
        Gets the next available schedule date, uploads the video, and stores it in DB.
        """
        logger.info(f"Starting publish flow for {file_path}...")
        
        if not self.youtube_service:
            logger.error("YouTube service not authenticated.")
            return False
            
        # 1. Get next available schedule date
        schedule_info = get_schedule_info(self.youtube_service)
        next_date = schedule_info.get("next_date")
        
        if not next_date:
            logger.error("Could not determine next schedule date.")
            return False
            
        logger.info(f"Scheduling video for: {next_date}")
        
        # 2. Upload video with the schedule date as private
        youtube_id = upload_video(
            youtube=self.youtube_service,
            file_path=file_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status="private",
            publish_at=next_date
        )
        
        if not youtube_id:
            logger.error("Video upload failed.")
            return False
            
        # 3. Store Video ID in database
        self._store_upload(local_video_id, youtube_id, next_date)
        
        logger.info("Publish flow completed successfully.")
        return True

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Publish Agent...")
    print("This agent requires a valid video file and authenticated YouTube connection.")
    # Example usage:
    # agent = PublishAgent()
    # agent.publish_video(
    #     file_path="generated/videos/test_branded.mp4", 
    #     title="Test Cartoon Video", 
    #     description="Testing automatic publishing flow", 
    #     tags=["Cartoon", "Kids"],
    #     local_video_id=1
    # )
