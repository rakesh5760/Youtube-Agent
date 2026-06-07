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
        Combines the structured character and animation prompts from the content package 
        into a single master prompt for Google Gemini Video generation.
        """
        logger.info("Formatting video prompt for Gemini from structured content...")
        
        character_prompt = content.get("character_prompt", "")
        animation_prompts = content.get("animation_prompts", [])
        
        if not character_prompt or not animation_prompts:
            # Fallback for old content JSON formats
            logger.warning("Missing structured prompts. Falling back to basic story prompt.")
            story = content.get("story", "")
            return f"9:16 vertical, 10 second duration, high quality 3D cartoon style. {story}"
            
        master_prompt = "Generate a single continuous 10-second vertical 9:16 video based on the following sequence:\n\n"
        
        master_prompt += "### CHARACTER DESIGN (Keep this character consistent throughout the video):\n"
        master_prompt += f"{character_prompt}\n\n"
        
        master_prompt += "### SHOT-BY-SHOT ANIMATION SEQUENCE:\n"
        for i, scene in enumerate(animation_prompts):
            master_prompt += f"- Shot {i+1}: {scene}\n"
            
        master_prompt += "\nCRITICAL: Maintain smooth motion, 24fps, cinematic lighting, no morphing, crisp details."
        
        logger.info("Master prompt formatting complete.")
        return master_prompt

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Prompt Formatting Agent...")
    agent = PromptAgent()
    
    sample_content = {
        "character_prompt": "A 3D Pixar-style animated character, a 24-year-old South Indian male software engineer, curly black hair...",
        "animation_prompts": [
            "Scene 1: Close-up shot of an exhausted Indian techie character staring blankly at his computer screen.",
            "Scene 2: The camera slowly zooms into his shocked expression as a red error notification pops up on screen."
        ]
    }
    optimized = agent.optimize_prompt(sample_content)
    
    if optimized:
        print("\nOptimized Master Video Prompt:")
        print(optimized)
    else:
        print("Failed to optimize prompt.")
