import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from services.logger import logger

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly']

CREDENTIALS_FILE = 'credentials/credentials.json'
TOKEN_FILE = 'credentials/token.json'

def get_authenticated_service():
    """Authenticates the user and returns a YouTube Data API service object."""
    creds = None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logger.info("Loaded existing credentials from token.json")
        except Exception as e:
            logger.error(f"Error loading token.json: {e}")

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Credentials expired. Refreshing token...")
            try:
                creds.refresh(Request())
                logger.info("Token refreshed successfully.")
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            logger.info("Initiating new authentication flow...")
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"Missing {CREDENTIALS_FILE}. Please download it from Google Cloud Console.")
                raise FileNotFoundError(f"Missing {CREDENTIALS_FILE}")
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            logger.info("Saved new credentials to token.json")

    try:
        # Build the YouTube service object
        youtube = build('youtube', 'v3', credentials=creds)
        return youtube
    except Exception as e:
        logger.error(f"Failed to build YouTube service: {e}")
        raise

def verify_channel_access(youtube):
    """Verifies access to the channel by fetching channel details."""
    try:
        logger.info("Verifying channel access...")
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        
        if not response.get('items'):
            logger.warning("No channel found for the authenticated user.")
            return None
            
        channel = response['items'][0]
        channel_id = channel['id']
        channel_title = channel['snippet']['title']
        
        logger.info(f"Successfully connected to channel: '{channel_title}' (ID: {channel_id})")
        return {
            "channel_title": channel_title,
            "channel_id": channel_id
        }
    except Exception as e:
        logger.error(f"Error verifying channel access: {e}")
        return None

if __name__ == "__main__":
    # Test script for YouTube Authentication Module
    print("Testing YouTube Authentication Module...")
    try:
        youtube_service = get_authenticated_service()
        channel_info = verify_channel_access(youtube_service)
        if channel_info:
            print(f"Success! Channel Name: {channel_info['channel_title']}")
            print(f"Success! Channel ID:   {channel_info['channel_id']}")
        else:
            print("Failed to retrieve channel info.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("Make sure config/credentials.json exists and contains valid OAuth 2.0 Client IDs.")
