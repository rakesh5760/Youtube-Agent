import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger

class BrandingAgent:
    def __init__(self, logo_path="assets/logo.png"):
        self.logo_path = os.path.abspath(logo_path)
        
    def add_watermark(self, input_video, output_video, position="top_right"):
        """
        Overlays the logo onto the video using FFmpeg.
        Positions: top_right, top_left, bottom_right, bottom_left
        """
        logger.info(f"Adding branding to {input_video}...")
        
        if not os.path.exists(input_video):
            logger.error(f"Input video not found: {input_video}")
            return False
            
        if not os.path.exists(self.logo_path):
            logger.error(f"Logo not found at {self.logo_path}. Cannot apply branding.")
            return False

        # Define position logic
        # W = video width, H = video height
        # w = watermark width, h = watermark height
        # 20 is the padding in pixels from the edge
        if position == "top_right":
            overlay = "main_w-overlay_w-20:20"
        elif position == "top_left":
            overlay = "20:20"
        elif position == "bottom_right":
            overlay = "main_w-overlay_w-20:main_h-overlay_h-20"
        elif position == "bottom_left":
            overlay = "20:main_h-overlay_h-20"
        else:
            overlay = "main_w-overlay_w-20:20" # Default top_right
            
        # FFmpeg command
        command = [
            "ffmpeg",
            "-y", # Overwrite output if exists
            "-i", input_video,
            "-i", self.logo_path,
            "-filter_complex", f"overlay={overlay}",
            "-c:v", "libx264", # Re-encode video using H.264
            "-preset", "fast",
            "-crf", "23",      # Maintain good quality (lower is better, 23 is default for good quality)
            "-c:a", "copy",    # Copy audio without re-encoding
            output_video
        ]
        
        try:
            logger.info("Running FFmpeg command...")
            # Run the command and capture output
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Branding applied successfully! Saved to {output_video}")
                return True
            else:
                logger.error(f"FFmpeg failed with exit code {result.returncode}")
                # Log only the last few lines of the error to avoid huge logs
                error_lines = result.stderr.strip().split('\n')
                logger.error(f"FFmpeg error snippet: {os.linesep.join(error_lines[-5:])}")
                return False
                
        except FileNotFoundError:
            logger.error("FFmpeg not found! Please install FFmpeg and make sure it is added to your system PATH.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during branding: {e}")
            return False

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Branding Agent...")
    agent = BrandingAgent()
    
    # We create a dummy logo for testing if it doesn't exist
    if not os.path.exists(agent.logo_path):
        os.makedirs(os.path.dirname(agent.logo_path), exist_ok=True)
        print(f"Note: Missing logo file. Place a transparent logo at {agent.logo_path} to test FFmpeg processing.")
            
    test_input = "assets/test_video.mp4"
    test_output = "generated/videos/test_branded.mp4"
    
    if os.path.exists(test_input) and os.path.exists(agent.logo_path):
        agent.add_watermark(test_input, test_output)
    else:
        print(f"Please place a valid {test_input} and {agent.logo_path} to run the full test.")
