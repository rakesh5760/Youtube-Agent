import sys
import os
import subprocess
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger

class BrandingAgent:
    def __init__(self, logo_path="assets/logo.png"):
        self.logo_path = os.path.abspath(logo_path)
        
    def _get_video_dimensions(self, file_path):
        """Uses ffprobe to get the width and height of the video."""
        cmd = [
            "ffprobe", "-v", "error", 
            "-select_streams", "v:0", 
            "-show_entries", "stream=width,height", 
            "-of", "json", file_path
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            data = json.loads(result.stdout)
            width = int(data['streams'][0]['width'])
            height = int(data['streams'][0]['height'])
            return width, height
        except Exception as e:
            logger.error(f"Failed to probe video dimensions: {e}. Defaulting to 720x1280.")
            return 720, 1280

    def add_watermark(self, input_video, output_video, position="bottom_right"):
        """
        Overlays the logo onto the video using FFmpeg.
        Automatically scales and positions the logo to perfectly cover the Gemini watermark.
        """
        logger.info(f"Adding branding to {input_video}...")
        
        if not os.path.exists(input_video):
            logger.error(f"Input video not found: {input_video}")
            return False
            
        if not os.path.exists(self.logo_path):
            logger.error(f"Logo not found at {self.logo_path}. Cannot apply branding.")
            return False

        width, height = self._get_video_dimensions(input_video)
        
        # Determine exact Gemini watermark dimensions and margins based on video resolution
        if width <= 1024:
            # e.g., 720p vertical (720x1280) -> 48x48 logo with 32px margin
            logo_size = 48
            margin = 32
        else:
            # e.g., 1080p vertical (1080x1920) or higher -> 96x96 logo with 64px margin
            logo_size = 96
            margin = 64
            
        # We scale the logo slightly larger (+4 pixels) to ensure it completely eclipses 
        # the underlying Gemini watermark, adjusting the margin by half that amount 
        # to keep it perfectly centered over the original spot.
        eclipse_padding = 4
        final_logo_size = logo_size + eclipse_padding
        final_margin = margin - (eclipse_padding // 2)

        # Scale the logo image and overlay it at the exact coordinates
        if position == "bottom_right":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay=main_w-overlay_w-{final_margin}:main_h-overlay_h-{final_margin}"
        elif position == "top_right":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay=main_w-overlay_w-{final_margin}:{final_margin}"
        elif position == "top_left":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay={final_margin}:{final_margin}"
        elif position == "bottom_left":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay={final_margin}:main_h-overlay_h-{final_margin}"
        else:
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay=main_w-overlay_w-{final_margin}:main_h-overlay_h-{final_margin}"
            
        command = [
            "ffmpeg",
            "-y", # Overwrite output if exists
            "-i", input_video,
            "-i", self.logo_path,
            "-filter_complex", filter_complex,
            "-c:v", "libx264", # Re-encode video using H.264
            "-preset", "fast",
            "-crf", "23",      # Maintain good quality
            "-c:a", "copy",    # Copy audio without re-encoding
            output_video
        ]
        
        try:
            logger.info(f"Running FFmpeg to overlay {final_logo_size}x{final_logo_size} logo with {final_margin}px margin...")
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
    
    if not os.path.exists(agent.logo_path):
        os.makedirs(os.path.dirname(agent.logo_path), exist_ok=True)
        print(f"Note: Missing logo file. Place a transparent logo at {agent.logo_path} to test FFmpeg processing.")
            
    test_input = "assets/test_video.mp4"
    test_output = "generated/videos/test_branded.mp4"
    
    if os.path.exists(test_input) and os.path.exists(agent.logo_path):
        agent.add_watermark(test_input, test_output)
    else:
        print(f"Please place a valid {test_input} and {agent.logo_path} to run the full test.")
