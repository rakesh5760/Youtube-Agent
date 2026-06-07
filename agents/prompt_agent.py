import json
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from services.logger import logger
from config.config import config

class PromptAgent:
    def __init__(self):
        api_key = config.groq_api_key
        if not api_key or api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY is not set or is using the default placeholder.")
            
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    def optimize_prompt(self, story):
        """Generates an optimized Gemini video prompt based on the story."""
        logger.info("Optimizing video prompt for Gemini...")
        
        prompt = f"""
        You are an expert AI video prompt engineer. Your job is to convert a story into a highly optimized text-to-video prompt for Google Gemini Video generation.
        
        The video must be:
        - 9:16 vertical orientation
        - 10 seconds duration
        - High quality 3D cartoon style (similar to Pixar/Disney)
        - Visually appropriate for a Telugu kids audience (e.g. Indian village/city setting, characters in casual Indian wear)
        - CRITICAL: Any spoken dialogue, voiceover, or background audio MUST be strictly in the Telugu language. Do not use English audio.
        
        Story:
        {story}
        
        Please generate the final, detailed, and highly descriptive prompt in English. 
        Focus on camera angles, lighting, character descriptions, and dynamic action.
        
        You must respond in JSON format with a single key "prompt" containing the prompt string.
        Example:
        {{
            "prompt": "9:16 vertical, 10 second duration, high quality 3D cartoon style. A young Indian boy in a yellow shirt..."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            if result and "prompt" in result:
                logger.info("Prompt optimized successfully.")
                return result["prompt"]
        except Exception as e:
            logger.error(f"Error calling Groq API for prompt optimization: {e}")
            
        return None

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Prompt Optimization Agent...")
    agent = PromptAgent()
    
    sample_story = "Raju and Chinni find a magical glowing fruit in their backyard."
    optimized = agent.optimize_prompt(sample_story)
    
    if optimized:
        print("\nOptimized Video Prompt:")
        print(optimized)
    else:
        print("Failed to optimize prompt.")
