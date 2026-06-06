import os
import yaml
from dotenv import load_dotenv

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Load environment variables
        load_dotenv()
        
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.youtube_client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.youtube_client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.channel_upload_time = os.getenv("CHANNEL_UPLOAD_TIME", "18:00")
        self.timezone = os.getenv("TIMEZONE", "Asia/Kolkata")
        
        # Load YAML settings
        self.settings = {}
        config_path = os.path.join(os.path.dirname(__file__), "settings.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.settings = yaml.safe_load(f)

config = Config()
