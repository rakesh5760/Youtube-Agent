import sqlite3
import os
from services.logger import logger

DB_PATH = "database/agent.db"

def init_db():
    """Initializes the SQLite database with required tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Table for storing generated videos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                tags TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'generated',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for storing analytics and upload data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                youtube_id TEXT,
                publish_date TIMESTAMP,
                status TEXT DEFAULT 'scheduled',
                FOREIGN KEY(video_id) REFERENCES videos(id)
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
