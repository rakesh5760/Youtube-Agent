import os
import sys
import time
import sqlite3

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.logger import logger
from database.db_setup import init_db
from agents.buffer_agent import BufferAgent
from agents.content_agent import ContentAgent
from agents.prompt_agent import PromptAgent
from agents.gemini_browser_agent import GeminiBrowserAgent
from agents.branding_agent import BrandingAgent
from agents.publish_agent import PublishAgent

def run_workflow():
    logger.info("Starting Telugu Kids YouTube Automation Agent Workflow...")
    init_db()

    # Step 1: Check Buffer
    buffer_agent = BufferAgent()
    buffer_days, needed_videos = buffer_agent.check_buffer()
    
    if needed_videos <= 0:
        logger.info("Buffer is full. Exiting workflow.")
        return

    logger.info(f"Proceeding to generate {needed_videos} videos...")
    
    # We will process 1 video per workflow run for safety, 
    # allowing cron/scheduler to re-trigger this script automatically.
    logger.info("Processing 1 video for this execution cycle...")

    # Step 2: Generate Content
    logger.info(">>> [STAGE 1] Generating Content")
    content_agent = ContentAgent()
    content = content_agent.run_pipeline()
    if not content:
        logger.error("Failed to generate content. Exiting.")
        return

    story = content.get("story", "")
    title = content.get("title", "Cartoon Short")
    description = content.get("description", "")
    tags = content.get("tags", [])

    # Step 3: Optimize Prompt
    logger.info(">>> [STAGE 2] Optimizing Video Prompt")
    prompt_agent = PromptAgent()
    video_prompt = prompt_agent.optimize_prompt(content)
    if not video_prompt:
        logger.warning("Prompt optimization failed, falling back to basic prompt.")
        video_prompt = content.get("video_prompt")
        
    if not video_prompt:
        logger.error("Failed to secure a video prompt. Exiting.")
        return

    # Step 4: Generate Video, Monitor, and Download
    logger.info(">>> [STAGE 3] Browser Automation: Gemini Video Generation")
    # Requires Chrome started with --remote-debugging-port=9222
    gemini_agent = GeminiBrowserAgent(debugging_port=9222)
    raw_video_path = gemini_agent.generate_video(video_prompt)
    
    if not raw_video_path:
        logger.error("Video generation or download failed. Exiting.")
        return

    # Step 5: Branding
    logger.info(">>> [STAGE 4] Applying Branding & Watermark")
    branding_agent = BrandingAgent(logo_path="assets/logo.png")
    branded_video_path = f"generated/videos/branded_{int(time.time())}.mp4"
    success = branding_agent.add_watermark(raw_video_path, branded_video_path)
    
    if not success:
        logger.error("Branding failed. Exiting.")
        return

    # Step 6: Database Logging, Upload, and Schedule
    logger.info(">>> [STAGE 5] Uploading and Scheduling")
    
    # Store locally first
    conn = sqlite3.connect("database/agent.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (title, description, tags, file_path, status)
        VALUES (?, ?, ?, ?, 'branded')
    ''', (title, description, ",".join(tags), branded_video_path))
    local_video_id = cursor.lastrowid
    conn.commit()
    conn.close()

    publish_agent = PublishAgent()
    publish_success = publish_agent.publish_video(
        file_path=branded_video_path,
        title=title,
        description=description,
        tags=tags,
        local_video_id=local_video_id
    )

    if publish_success:
        logger.info(">>> Workflow completed successfully!")
    else:
        logger.error(">>> Workflow failed at the final publish stage.")

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    run_workflow()
