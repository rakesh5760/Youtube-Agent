# YouTube Automation Agent 🚀

This personal automation project fully automates the creation, editing, and scheduling of YouTube Shorts using AI. It acts as an orchestrator to manage YouTube scheduling, content generation, and uploading.

## 🛠️ Workflow

1. **Schedule Buffer Check**: The AI checks your YouTube channel schedule via the YouTube API. If your scheduled video buffer (up to 90 days) falls below the threshold, it triggers the content generation pipeline.
2. **Content Ideation (Groq)**: The agent uses Groq's high-speed LLM (`openai/gpt-oss-20b`) to generate 3 unique story ideas. 
3. **Memory Module (SQLite)**: Before finalizing, it cross-references `database/agent.db` to ensure the generated ideas do not duplicate recent videos.
4. **Content Generation**: The best idea is expanded into a tight JSON package containing:
   - Script (Telugu/English slang)
   - Visual/Sound Effect Cues (e.g., ASMR glass scraping)
   - Optimized Title, Description, and Tags.
5. **Video Creation (Gemini)**: The prompt is sent to Google Gemini via browser automation (Playwright) running in an isolated Chrome debug profile. The generated MP4 video is automatically downloaded.
6. **Video Branding**: Uses OpenCV/FFmpeg to edit the video and overlay a custom channel logo over the AI watermarks.
7. **YouTube Upload**: Uploads the final video via the YouTube Data API, scheduling it for the default `18:00 IST` publishing time.

## 💻 Tech Stack
- **AI Core**: Groq (`openai/gpt-oss-20b`) for lightning-fast JSON content generation.
- **Backend / Orchestrator**: Python 3.11
- **Database (Memory)**: SQLite (`agent.db`)
- **Video Generation**: Google Gemini (via Playwright browser automation)
- **Video Processing**: OpenCV / FFmpeg
- **Integrations**: YouTube Data API v3 (Auth & Uploads)

## 🚀 Quick Start
Check out `quick_run.md` for instructions on how to start the Chrome remote debugging profile and execute the workflow.
