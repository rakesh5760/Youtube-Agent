import datetime
import json
from dateutil import parser, tz
from services.youtube_auth import get_authenticated_service
from services.logger import logger
from config.config import config

def get_scheduled_videos(youtube):
    """
    Fetches the recently uploaded videos and finds those scheduled for future publication.
    """
    try:
        # 1. Get the 'uploads' playlist ID for the authenticated channel
        channel_request = youtube.channels().list(
            part="contentDetails",
            mine=True
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get('items'):
            logger.warning("No channel found for the authenticated user.")
            return []
            
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # 2. Get the latest 50 videos from the uploads playlist
        playlist_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50
        )
        playlist_response = playlist_request.execute()
        
        video_ids = []
        for item in playlist_response.get('items', []):
            video_ids.append(item['snippet']['resourceId']['videoId'])
            
        if not video_ids:
            return []

        # 3. Get status details for these videos to check 'publishAt'
        videos_request = youtube.videos().list(
            part="status",
            id=",".join(video_ids)
        )
        videos_response = videos_request.execute()
        
        scheduled_dates = []
        for video in videos_response.get('items', []):
            status = video.get('status', {})
            # Scheduled videos have privacyStatus = private and a publishAt date
            if status.get('privacyStatus') == 'private' and 'publishAt' in status:
                dt = parser.isoparse(status['publishAt'])
                scheduled_dates.append(dt)
                
        return scheduled_dates
    except Exception as e:
        logger.error(f"Error fetching scheduled videos: {e}")
        return []

def get_schedule_info(youtube):
    """
    Returns a dictionary containing the latest_date and next_date correctly adjusted for local timezone.
    """
    logger.info("Inspecting YouTube schedule...")
    scheduled_dates = get_scheduled_videos(youtube)
    
    upload_time_str = config.channel_upload_time # "18:00"
    upload_hour, upload_minute = map(int, upload_time_str.split(':'))
    
    # Get the configured local timezone
    local_tz = tz.gettz(config.settings.get('channel', {}).get('timezone', 'Asia/Kolkata'))
    now = datetime.datetime.now(local_tz)
    
    if not scheduled_dates:
        logger.info("No scheduled videos found.")
        next_date = now + datetime.timedelta(days=1)
        next_date = next_date.replace(hour=upload_hour, minute=upload_minute, second=0, microsecond=0)
        
        return {
            "latest_date": None,
            "next_date": next_date.isoformat()
        }
        
    # Find the maximum date and convert it to local timezone BEFORE replacing the time
    latest_dt_utc = max(scheduled_dates)
    latest_dt_local = latest_dt_utc.astimezone(local_tz)
    
    # The next date is exactly 1 day after the latest scheduled date
    next_dt_local = latest_dt_local + datetime.timedelta(days=1)
    
    # Ensure the time matches the configured local time
    next_dt_local = next_dt_local.replace(hour=upload_hour, minute=upload_minute, second=0, microsecond=0)
    
    result = {
        "latest_date": latest_dt_utc.isoformat(),
        "next_date": next_dt_local.isoformat()
    }
    logger.info(f"Schedule info: {json.dumps(result, indent=2)}")
    return result

if __name__ == "__main__":
    # Test script for YouTube Schedule Inspector
    print("Testing YouTube Schedule Inspector...")
    try:
        youtube_service = get_authenticated_service()
        if youtube_service:
            schedule_info = get_schedule_info(youtube_service)
            print("Output:")
            print(json.dumps(schedule_info, indent=2))
        else:
            print("Authentication failed.")
    except Exception as e:
        print(f"Error during test: {e}")
