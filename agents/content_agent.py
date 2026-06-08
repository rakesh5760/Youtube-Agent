import json
import os
import sys
import uuid
import sqlite3

# Add the project root to the Python path so it can find 'services' and 'config'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from services.logger import logger
from config.config import config

class ContentAgent:
    def __init__(self):
        api_key = config.groq_api_key
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY is not set or is using the default placeholder.")
            
        self.client = Groq(api_key=api_key)
        self.language = config.settings.get('channel', {}).get('language', 'Telugu')
        self.audience = config.settings.get('content', {}).get('audience', 'Kids')
        self.duration = config.settings.get('content', {}).get('duration', 10)
        self.model = "llama-3.1-8b-instant" # Groq recommended fast model
        
        self.characters = self._load_characters()

    def _load_characters(self):
        char_path = "assets/characters.json"
        if os.path.exists(char_path):
            with open(char_path, "r", encoding='utf-8') as f:
                return json.load(f)
        return []

    def _get_json_response(self, prompt, max_tokens=2500):
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"},
                max_tokens=max_tokens
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return None

    def _get_recent_titles(self):
        """Fetches the last 15 video titles from the database to prevent duplicate content."""
        db_path = "database/agent.db"
        if not os.path.exists(db_path):
            return []
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM videos ORDER BY created_at DESC LIMIT 15")
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error fetching recent titles from DB: {e}")
            return []

    def generate_story_ideas(self):
        """Generates 3 story ideas."""
        logger.info("Generating 3 story ideas...")
        recent_titles = self._get_recent_titles()
        recent_context = ""
        if recent_titles:
            recent_context = "\nCRITICAL AVOIDANCE: Do NOT generate ideas similar to these recent videos:\n" + "\n".join(f"- {t}" for t in recent_titles)
            
        prompt = f"""
        You are an expert children's content creator for YouTube Shorts.
        Language: {self.language}
        Audience: {self.audience}
        Duration: {self.duration} seconds.
        Available characters: {json.dumps(self.characters)} (Do not use copyrighted characters like Chhota Bheem, Peppa Pig, etc).
        {recent_context}
        
        Generate exactly 3 distinct, fun, and engaging story ideas for a 10-second vertical cartoon short.
        Provide a variety of themes:
        - Idea 1: A traditional fun character story (e.g. magical discovery, funny interaction, moral).
        - Idea 2: An action-packed animated transformation story (e.g. a car or object turns into a robot by rearranging parts with sound effects).
        - Idea 3: A creative mix of humor and engaging visuals.
        
        You must respond in JSON format with a single key "ideas" containing a list of 3 strings.
        Example:
        {{
            "ideas": [
                "Idea 1...",
                "Idea 2..."
            ]
        }}
        """
        result = self._get_json_response(prompt, max_tokens=1200)
        if result and "ideas" in result:
            return result["ideas"]
        return []

    def score_ideas(self, ideas):
        """Scores ideas and returns the best one."""
        logger.info("Scoring ideas...")
        prompt = f"""
        Evaluate the following {len(ideas)} story ideas for a YouTube Short.
        Score them out of 10 based on Fun, Curiosity, Educational value, Visual appeal, and Virality potential.
        
        Ideas:
        {json.dumps(ideas, indent=2)}
        
        Calculate the average score for each idea.
        You must respond in JSON format with a key "scores" containing a list of objects with "index" (0 to {len(ideas)-1}) and "score" (a float).
        Example:
        {{
            "scores": [
                {{"index": 0, "score": 8.5}},
                {{"index": 1, "score": 9.2}}
            ]
        }}
        """
        result = self._get_json_response(prompt, max_tokens=500)
        best_idea = None
        best_score = -1
        
        if result and "scores" in result:
            for i, score_obj in enumerate(result["scores"]):
                # Handle cases where LLM just returns a list of numbers instead of objects
                if isinstance(score_obj, (int, float)):
                    score_val = float(score_obj)
                    idx = i
                elif isinstance(score_obj, dict):
                    score_val = float(score_obj.get("score", 0))
                    idx = int(score_obj.get("index", i))
                else:
                    continue
                    
                if score_val > best_score and idx < len(ideas):
                    best_score = score_val
                    best_idea = ideas[idx]
                    
        if not best_idea and ideas:
            # Fallback to the first idea if scoring fails
            best_idea = ideas[0]
            
        logger.info(f"Best idea selected with score {best_score}: {best_idea}")
        return best_idea

    def generate_content(self, idea):
        """Generates the full content package based on the selected idea."""
        logger.info("Generating full content from the best idea...")
        prompt = f"""
        Based on the following story idea, generate a complete content package for a 10-second YouTube Short.
        Language: {self.language} (A modern, energetic mix of conversational {self.language} and English slang).
        Audience: Kids on YouTube Shorts.
        Idea: {idea}
        
        CRITICAL CONTENT RULES:
        1. Script & Dialogue: Write a tight script (approx 130-150 words). The language MUST feel natural to a 2026 audience: modern {self.language} heavily mixed with English coding/slang (casual, relatable, trendy memes mix, e.g. "Enduku ra mechanical text books chustav, update avvu"). Include audio/voiceover cues.
        2. Visuals: If the idea involves a transformation, make sure the script explicitly describes the parts rearranging with sound effects. Otherwise, describe the fun character interactions clearly.
        3. Title: Create an ultra-catchy, clickbaity YouTube Shorts title using emojis, caps, and engaging hooks.
        4. Description: Write an engaging 3-4 sentence SEO description. Include a Call To Action (e.g. "Subscribe for more fun!"), a brief plot summary, and 5-8 relevant hashtags.
        5. Tags: Generate EXACTLY 8 to 12 highly optimized YouTube SEO tags.
        
        CRITICAL JSON RULES:
        1. You MUST respond in strictly valid JSON format.
        2. DO NOT split strings with unescaped commas outside of quotes. 
        3. The "description" key MUST contain exactly ONE single string value.
        4. DO NOT wrap the text in its own double quotes inside the JSON value. Example: Use "description": "Hello" NOT "description": ""Hello"".
        5. The "script" MUST be a JSON array of strings (e.g. ["Line 1", "Line 2"]). Do NOT make it a single string. This prevents formatting errors.
        
        You must respond with the following exact JSON structure:
        {{
          "story": "A short, energetic summary of the story. MUST BE IN ENGLISH so the video generator understands the visual scene.",
          "script": [
            "Line 1 of the dialogue/script",
            "Line 2 of the dialogue/script"
          ],
          "title": "A catchy, clickbaity YouTube title with emojis 🚀🔥",
          "description": "Engaging YouTube description with CTA and hashtags. NO INTERNAL DOUBLE QUOTES.",
          "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "... up to 12 tags"]
        }}
        """
        result = self._get_json_response(prompt, max_tokens=2500)
        
        if result and "script" in result and isinstance(result["script"], list):
            result["script"] = "\n".join(result["script"])
            
        return result

    def run_pipeline(self):
        """Runs the full content generation pipeline."""
        ideas = self.generate_story_ideas()
        if not ideas:
            logger.error("Failed to generate ideas.")
            return None
            
        best_idea = self.score_ideas(ideas)
        if not best_idea:
            logger.error("Failed to select the best idea.")
            return None
            
        content = self.generate_content(best_idea)
        if content:
            logger.info("Content generation pipeline completed successfully.")
            
            # Save to metadata folder
            os.makedirs("generated/metadata", exist_ok=True)
            content_id = str(uuid.uuid4())[:8]
            file_path = f"generated/metadata/content_{content_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved content to {file_path}")
            
            return content
        return None

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Content Agent (Groq)...")
    agent = ContentAgent()
    if agent.client.api_key == "your_groq_api_key_here" or not agent.client.api_key:
        print("Please set your GROQ_API_KEY in the .env file to test.")
    else:
        content = agent.run_pipeline()
        if content:
            print("\nGenerated Content:")
            print(json.dumps(content, indent=2, ensure_ascii=False))
        else:
            print("Failed to generate content.")
