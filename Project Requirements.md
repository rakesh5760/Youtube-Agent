# Telugu Kids Cartoon YouTube Automation Agent

## 1. Project Overview

### Objective

Develop a fully automated AI-powered YouTube Shorts publishing system that generates Telugu children's cartoon videos, applies branding, uploads them to YouTube, and schedules them automatically.

The system should operate with minimal human intervention while maintaining a continuous content pipeline and future publishing schedule.

---

# 2. Business Goal

The system will create:

* Telugu Kids Cartoon Shorts
* Vertical videos (9:16)
* Duration: approximately 10 seconds
* Child-friendly content
* Educational, entertaining, humorous, adventurous, and informative stories

The goal is to maintain a consistent publishing schedule on YouTube and grow audience engagement organically.

---

# 3. High-Level Workflow

1. Check existing YouTube scheduled videos.
2. Determine the latest scheduled publish date.
3. Calculate content buffer.
4. Generate new content if buffer is below threshold.
5. Generate video using Gemini browser automation.
6. Download generated video.
7. Apply channel branding/logo.
8. Upload video to YouTube.
9. Schedule video after the last scheduled video.
10. Store metadata and logs.

---

# 4. Core Functional Requirements

## FR-1 Content Generation Agent

### Provider

Groq LLM

### Responsibilities

Generate:

* Story ideas
* Video scripts
* Video prompts
* YouTube titles
* Descriptions
* Tags

### Input

* Language: Telugu
* Audience: Kids
* Duration: 10 seconds
* Category preferences

### Output

```json
{
  "story": "",
  "script": "",
  "video_prompt": "",
  "title": "",
  "description": "",
  "tags": []
}
```

---

## FR-2 Story Selection System

### Process

Generate 5 candidate story concepts.

Evaluate using scoring model:

* Fun
* Curiosity
* Educational value
* Visual appeal
* Virality potential

Select highest scoring story.

### Output

Single approved story.

---

## FR-3 Character Management

### Requirements

Use recurring original cartoon characters.

Examples:

* Raju
* Chinni
* Ravi
* Meena
* Robo Raju
* Tataiah

### Constraints

Do not use copyrighted characters.

Examples prohibited:

* Motu Patlu
* Chhota Bheem
* Doraemon
* Shin Chan

Store character descriptions in configuration files.

---

## FR-4 Video Generation Agent

### Method

Browser automation.

### Tool

Playwright

### Browser Mode

Chrome Remote Debugging Port

### Responsibilities

1. Connect to existing Chrome session.
2. Open Gemini website.
3. Submit video prompt.
4. Generate video.
5. Download generated video.
6. Save video locally.

### Output

```json
{
  "video_path": "generated/video.mp4"
}
```

---

## FR-5 Branding Agent

### Responsibilities

Add channel logo to generated video.

### Requirements

* Logo visible entire video
* Fixed position
* Consistent size
* Transparent PNG

### Technology

FFmpeg

### Output

```text
final_video.mp4
```

---

## FR-6 YouTube Upload Agent

### Responsibilities

* Authenticate using YouTube API
* Upload video
* Apply metadata
* Schedule publication

### Metadata

* Title
* Description
* Tags
* Category

### Privacy

Upload as private and schedule publication.

---

## FR-7 Scheduling Engine

### Objective

Prevent duplicate scheduling.

### Process

Retrieve existing scheduled uploads.

Determine latest scheduled publish date.

Schedule new video for:

Latest Publish Date + 1 Day

Example:

Current:

June 7
June 8
June 9
June 10

New upload:

June 11

### Time

Fixed daily publishing time.

Example:

6:00 PM IST

---

## FR-8 Content Buffer System

### Minimum Buffer

7 days

### Maximum Buffer

30 days

### Logic

If scheduled content < 7 days

Generate additional content.

Continue until target buffer achieved.

---

## FR-9 Local Storage

Store:

### Videos

```text
generated/videos/
```

### Metadata

```text
generated/metadata/
```

### Logs

```text
logs/
```

---

## FR-10 Analytics Storage

Store:

* Video ID
* Publish date
* Title
* Status

Future support:

* Views
* CTR
* Retention
* Likes

---

# 5. Non-Functional Requirements

## Performance

Video generation workflow should execute automatically.

System should support unattended operation.

---

## Reliability

Retry failed operations.

Retry count:

3 attempts.

---

## Logging

Log:

* Content generation
* Video generation
* Downloads
* Uploads
* Scheduling

---

## Scalability

System should support:

* Multiple channels
* Multiple languages
* Multiple upload schedules

Future-ready architecture required.

---

# 6. Technology Stack

## Content Generation

Groq

### Purpose

* Story generation
* Titles
* Descriptions
* Tags

---

## Video Generation

Gemini Web Interface

### Access Method

Playwright Browser Automation

---

## Browser Automation

Playwright

---

## Video Editing

FFmpeg

---

## Upload System

YouTube Data API v3

---

## Scheduler

Python Scheduler

or

Cron

---

## Database

SQLite (MVP)

Future:

PostgreSQL

---

# 7. Folder Structure

```text
youtube-agent/

├── agents/
│   ├── content_agent.py
│   ├── video_agent.py
│   ├── branding_agent.py
│   ├── upload_agent.py
│   └── scheduler_agent.py
│
├── assets/
│   ├── logo.png
│   └── characters.json
│
├── generated/
│   ├── videos/
│   ├── metadata/
│   └── thumbnails/
│
├── database/
│
├── logs/
│
├── config/
│   └── settings.yaml
│
├── main.py
│
└── requirements.txt
```

---

# 8. Configuration

```yaml
channel:
  language: Telugu
  upload_time: "18:00"
  timezone: Asia/Kolkata

content:
  duration: 10
  audience: Kids
  style: Cartoon

buffer:
  min_days: 7
  max_days: 30
```

---

# 9. Environment Variables

```env
GROQ_API_KEY=

YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=

CHANNEL_UPLOAD_TIME=18:00

TIMEZONE=Asia/Kolkata
```

---

# 10. Future Enhancements

Phase 2:

* Auto thumbnail generation
* Telugu voice narration
* Subtitle generation
* Performance analytics

Phase 3:

* Multi-channel support
* Multi-language support
* Trending topic discovery
* Self-learning content recommendation engine

---

# 11. Success Criteria

The system is considered successful when:

1. Generates Telugu kids content automatically.
2. Creates video through Gemini browser automation.
3. Downloads video successfully.
4. Applies logo branding.
5. Uploads video to YouTube.
6. Schedules after latest existing upload.
7. Maintains minimum 7-day content buffer.
8. Requires no manual daily intervention.
