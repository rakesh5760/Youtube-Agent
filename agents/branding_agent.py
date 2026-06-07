import sys
import os
import subprocess
import json
import cv2
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger

class BrandingAgent:
    def __init__(self, logo_path="assets/logo.png", template_path="assets/gemini_template.png"):
        self.logo_path = os.path.abspath(logo_path)
        self.template_path = os.path.abspath(template_path)
        
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

    def find_watermark_coordinates(self, video_path):
        """
        Uses OpenCV to read the first frame and find the Gemini watermark using edge detection template matching.
        Returns (margin_right, margin_bottom, width, height)
        """
        if not os.path.exists(self.template_path):
            logger.warning(f"Template {self.template_path} not found. Falling back to default margins.")
            return None, None, None, None
            
        try:
            # Read template with alpha channel
            template = cv2.imread(self.template_path, cv2.IMREAD_UNCHANGED)
            if template is None or template.shape[2] != 4:
                logger.error("Template must be a PNG with an alpha channel (transparency).")
                return None, None, None, None
                
            template_alpha = template[:, :, 3]
            
            # Read first frame of video
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return None, None, None, None
            
            h, w = frame.shape[:2]
            
            # Crop strictly to the bottom right corner (last 300 pixels) to avoid false positives in clouds/text
            roi_y = max(0, h - 300)
            roi_x = max(0, w - 300)
            frame_roi = frame[roi_y:h, roi_x:w]
            
            frame_gray = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)
            frame_edges = cv2.Canny(frame_gray, 50, 200)
                
            best_val = -1
            best_loc = None
            best_t_size = None
            
            # Resize the alpha mask to find the sparkler size
            for test_size in range(32, 140, 4):
                resized_alpha = cv2.resize(template_alpha, (test_size, test_size))
                
                # The alpha channel is the shape of the sparkler. We extract its edges!
                template_edges = cv2.Canny(resized_alpha, 50, 200)
                
                # Match template using CCOEFF_NORMED on edge maps
                result = cv2.matchTemplate(frame_edges, template_edges, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_val:
                    best_val = max_val
                    best_loc = max_loc
                    best_t_size = test_size
            
            logger.info(f"OpenCV edge match confidence: {best_val} at size {best_t_size}")
            
            # High confidence threshold for CCOEFF_NORMED on edge maps
            if best_val > 0.05: 
                x_roi, y_roi = best_loc
                
                # Convert ROI coordinates back to full frame coordinates
                x = x_roi + roi_x
                y = y_roi + roi_y
                
                # Calculate margins from bottom right
                margin_right = w - (x + best_t_size)
                margin_bottom = h - (y + best_t_size)
                
                logger.info(f"Calculated x:{x}, y:{y}, w:{w}, h:{h}. Margin right:{margin_right}, bottom:{margin_bottom}")
                
                # For safety, ensure margins aren't totally crazy (must be near the corner)
                if margin_right > 250 or margin_bottom > 250:
                    logger.warning("Detected margins are too far from the corner. Rejecting false positive.")
                    return None, None, None, None
                    
                return margin_right, margin_bottom, w, h
                
            return None, None, None, None
        except Exception as e:
            logger.error(f"Error in OpenCV detection: {e}")
            return None, None, None, None

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

        # First, try dynamic OpenCV detection!
        dynamic_mr, dynamic_mb, width, height = self.find_watermark_coordinates(input_video)
        
        if dynamic_mr is not None and dynamic_mb is not None:
            logger.info(f"OpenCV dynamically detected watermark at margins -> Right: {dynamic_mr}px, Bottom: {dynamic_mb}px")
            margin_right = dynamic_mr
            # Adjust the bottom margin slightly down to perfectly center over the edge-detected box
            margin_bottom = dynamic_mb
            
            if width <= 1024:
                logo_size = 64
            else:
                logo_size = 96
        else:
            logger.warning("Dynamic detection failed or disabled. Using fallback hardcoded coordinates.")
            width, height = self._get_video_dimensions(input_video)
            
            # Match the exact coordinates the user provided in 'ice cream.mp4'
            if width <= 1024:
                logo_size = 64
                margin_right = 86
                margin_bottom = 90
            else:
                logo_size = 96
                margin_right = 130
                margin_bottom = 136
            
        final_logo_size = logo_size

        # Scale the logo image and overlay it at the exact coordinates
        if position == "bottom_right":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay=main_w-overlay_w-{margin_right}:main_h-overlay_h-{margin_bottom}"
        elif position == "top_right":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay=main_w-overlay_w-{margin_right}:{margin_bottom}"
        elif position == "top_left":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay={margin_right}:{margin_bottom}"
        elif position == "bottom_left":
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay={margin_right}:main_h-overlay_h-{margin_bottom}"
        else:
            filter_complex = f"[1:v]scale={final_logo_size}:{final_logo_size}[logo];[0:v][logo]overlay=main_w-overlay_w-{margin_right}:main_h-overlay_h-{margin_bottom}"
            
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
            logger.info(f"Running FFmpeg to overlay {final_logo_size}x{final_logo_size} logo with {margin_right}px right margin and {margin_bottom}px bottom margin...")
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
