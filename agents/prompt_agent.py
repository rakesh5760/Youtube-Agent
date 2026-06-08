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

    def optimize_prompt(self, content):
        """
        Extracts the basic concept and formats it for Gemini to handle creatively.
        """
        logger.info("Formatting basic concept prompt for Gemini...")
        
        story = content.get("story", "")
        title = content.get("title", "")
        
        if not story:
            logger.error("No story provided to PromptAgent.")
            return None
            
        master_prompt = f"""Generate a 10-second 9:16 vertical 3D animated cartoon video.
        
Title: {title}
Story/Concept: {story}

CRITICAL CONSTRAINTS:
- Language: All dialogue, text, or audio must be strictly in Telugu (and English/Teluglish).
- Transformation: Ensure the requested transformation (e.g., objects changing shape/rearranging) is clearly visualized.
- Creativity: Use your own creative internal logic to direct the scene, camera, and character designs!
"""
        
        logger.info("Basic Gemini prompt formatted.")
        return master_prompt

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Prompt Formatting Agent...")
    agent = PromptAgent()
    
    sample_content = {
        "title": "Super Car to Robot!",
        "story": "A sleek red sports car speeds down the road and dramatically transforms into a giant robot by rearranging its parts."
    }
    optimized = agent.optimize_prompt(sample_content)
    
    if optimized:
        print("\nGemini Prompt:")
        print(optimized)
    else:
        print("Failed to optimize prompt.")
