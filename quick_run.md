# Quick Run Guide: Telugu Kids YouTube Automation

Follow these exact steps to generate, brand, and automatically upload a new YouTube Short.

## Pre-Flight Checklist
Before you begin, verify the following are in place:
1. **API Keys**: Ensure your `.env` file contains your valid `GROQ_API_KEY`.
2. **Channel Logo**: Ensure your transparent channel logo is saved precisely at `assets/logo.png`.
3. **YouTube Credentials** *(One-time setup)*:
   If you haven't linked your YouTube channel yet, run this in your terminal to generate your `token.json`:
   ```powershell
   py services/youtube_auth.py
   ```

---

## Step 1: Start Chrome in Debugging Mode

The system needs a completely isolated Chrome instance with an open debugging port so the AI can physically type out the prompt and click download in Gemini.

Open a **BRAND NEW PowerShell window** (do not close it) and run:
```powershell
 & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug-profile"

```

## Step 2: Log into Gemini
Because Step 1 opened a totally clean, isolated Chrome profile, it does not have your normal browser cookies. 
1. In that newly opened Chrome window, navigate to `https://gemini.google.com/`
2. **Log into your Google Account** so Gemini is ready and waiting for a prompt.

## Step 3: Run the Orchestrator

Go back to your main VS Code terminal and execute the workflow:
```powershell
py main.py
```

### What to expect:
1. **Buffer Check**: The AI checks your YouTube schedule. If your backlog is below the threshold, it triggers generation.
2. **Story Writing**: Groq generates 5 ideas, scores them, and writes a complete Telugu metadata package.
3. **Prompting**: An English video prompt is constructed with strict instructions for *Telugu-only* audio.
4. **Browser Automation**: Watch as Playwright takes over your Chrome window, submits the prompt, and downloads the video.
5. **Branding**: FFmpeg dynamically scales your logo and perfectly covers the Gemini watermark.
6. **Publishing**: The video is pushed to YouTube, marked as "Made for Kids", and automatically scheduled for `18:00` on the next available open day!
