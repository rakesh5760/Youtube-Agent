import os
from googleapiclient.http import MediaFileUpload
from services.youtube_auth import get_authenticated_service
from services.logger import logger

def upload_video(youtube, file_path, title, description, tags, category_id="27", privacy_status="private", publish_at=None):
    """
    Uploads a video to YouTube.
    category_id="27" is Education.
    """
    logger.info(f"Preparing to upload {file_path}...")
    
    if not os.path.exists(file_path):
        logger.error(f"Video file not found: {file_path}")
        return None

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': True  # Important for Kids channel
        }
    }
    
    if publish_at:
        body['status']['publishAt'] = publish_at

    # chunksize=-1 means the whole file will be loaded into memory, which is fine for 10s shorts.
    # Otherwise, specify a chunksize e.g. 1024 * 1024
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    try:
        logger.info("Uploading video...")
        response = request.execute()
        video_id = response.get('id')
        logger.info(f"Video uploaded successfully! Video ID: {video_id}")
        return video_id
    except Exception as e:
        logger.error(f"An error occurred during upload: {e}")
        return None

if __name__ == "__main__":
    # Test script for YouTube Upload Module
    print("Testing YouTube Upload Module...")
    
    test_video_path = "assets/test_video.mp4"
    if not os.path.exists(test_video_path):
        os.makedirs(os.path.dirname(test_video_path), exist_ok=True)
        # Create a tiny dummy file just for structure, though YouTube API might reject it if it's not a real mp4.
        # It's better to provide a real mp4 for testing.
        with open(test_video_path, "w") as f:
            f.write("dummy")
        print(f"Note: Created a dummy file at {test_video_path}. YouTube might reject it because it's not a real MP4.")
        print("Please place a real test_video.mp4 in the assets/ directory to perform a real test.")
        
    try:
        youtube_service = get_authenticated_service()
        if youtube_service:
            print("Authenticated successfully. Attempting upload...")
            video_id = upload_video(
                youtube=youtube_service,
                file_path=test_video_path,
                title="Test Telugu Kids Cartoon Short",
                description="This is a test upload for the Telugu Kids YouTube Automation Agent.",
                tags=["Telugu Kids", "Cartoon", "Test"],
                privacy_status="private"
            )
            if video_id:
                print(f"Test upload successful! Video ID: {video_id}")
            else:
                print("Test upload failed. Please check the logs.")
        else:
            print("Authentication failed.")
    except Exception as e:
        print(f"Error during test: {e}")
