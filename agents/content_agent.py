import json
import os
import sys
import uuid

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

    def _get_json_response(self, prompt):
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return None

    def generate_story_ideas(self):
        """Generates 5 story ideas."""
        logger.info("Generating 5 story ideas...")
        prompt = f"""
        You are an expert children's content creator for YouTube Shorts.
        Language: {self.language}
        Audience: {self.audience}
        Duration: {self.duration} seconds.
        Available characters: {json.dumps(self.characters)} (Do not use copyrighted characters like Chhota Bheem, Peppa Pig, etc).
        
        Generate exactly 5 distinct, fun, and engaging story ideas for a 10-second vertical cartoon short.
        You must respond in JSON format with a single key "ideas" containing a list of 5 strings.
        Example:
        {{
            "ideas": [
                "Idea 1...",
                "Idea 2..."
            ]
        }}
        """
        result = self._get_json_response(prompt)
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
        result = self._get_json_response(prompt)
        best_idea = None
        best_score = -1
        
        if result and "scores" in result:
            for score_obj in result["scores"]:
                if score_obj["score"] > best_score:
                    best_score = score_obj["score"]
                    best_idea = ideas[score_obj["index"]]
                    
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
        Language: {self.language} (The title, description, tags, and script should be in {self.language} where appropriate, or a mix of {self.language} and English).
        Idea: {idea}
        
        CRITICAL JSON RULES:
        1. You MUST respond in strictly valid JSON format.
        2. DO NOT include raw line breaks or unescaped characters inside the JSON strings.
        3. Properly escape all quotes.
        
        You must respond with the following exact JSON structure:
        {{
          "story": "A short summary of the story.",
          "script": "The exact script/dialogue.",
          "video_prompt": "A highly detailed prompt for an AI video generator (like Gemini or Sora) to create this video. This MUST be in English.",
          "title": "A catchy YouTube title.",
          "description": "YouTube description including hashtags.",
          "tags": ["tag1", "tag2", "tag3"]
        }}
        """
        result = self._get_json_response(prompt)
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
