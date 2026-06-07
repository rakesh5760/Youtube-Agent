import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from services.logger import logger

class GeminiBrowserAgent:
    def __init__(self, debugging_port=9222):
        self.debugging_port = debugging_port
        self.download_dir = os.path.abspath("generated/videos")
        os.makedirs(self.download_dir, exist_ok=True)

    def generate_video(self, prompt, timeout_minutes=15):
        """
        Connects to an existing Chrome instance, opens Gemini, and submits the prompt to generate a video.
        Make sure Chrome is running with: --remote-debugging-port=9222
        """
        logger.info(f"Connecting to Chrome on port {self.debugging_port}...")
        
        try:
            with sync_playwright() as p:
                try:
                    # Use 127.0.0.1 instead of localhost to avoid IPv6 ECONNREFUSED ::1 errors on Windows
                    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{self.debugging_port}")
                except Exception as e:
                    logger.error(f"Failed to connect to Chrome. Make sure it's running with --remote-debugging-port={self.debugging_port}. Error: {e}")
                    return None
                    
                context = browser.contexts[0]
                page = context.new_page()
                
                logger.info("Navigating to Gemini...")
                page.goto("https://gemini.google.com/", timeout=60000, wait_until="domcontentloaded")
                
                # Locate the chat input
                logger.info("Locating the chat input...")
                
                # Gemini uses rich-textarea or a div with contenteditable
                chat_input = page.locator("rich-textarea").first
                if not chat_input.is_visible():
                    chat_input = page.locator("[contenteditable='true']").first
                    
                logger.info(f"Submitting video prompt:\n{prompt}")
                chat_input.click()
                # Use keyboard to type out the prompt to simulate human interaction and avoid clipboard issues
                page.keyboard.insert_text(prompt)
                
                # Press Enter to submit
                time.sleep(1)
                page.keyboard.press("Enter")
                
                logger.info(f"Waiting for video generation to complete (timeout: {timeout_minutes} mins)...")
                
                start_time = time.time()
                video_downloaded_path = None
                
                while (time.time() - start_time) < timeout_minutes * 60:
                    # Look for a download button or link inside the latest response.
                    # Since Gemini's exact DOM structure for video downloads might change,
                    # we check for generic download hints in the latest elements, including the specific mat-icon.
                    download_button = page.locator("button[aria-label*='Download'], a[download], mat-icon[data-mat-icon-name='download']").last
                    
                    if download_button.is_visible():
                        logger.info("Download button found! Downloading video...")
                        try:
                            with page.expect_download() as download_info:
                                download_button.click()
                            download = download_info.value
                            
                            file_name = f"gemini_video_{int(time.time())}.mp4"
                            video_downloaded_path = os.path.join(self.download_dir, file_name)
                            download.save_as(video_downloaded_path)
                            logger.info(f"Video saved to {video_downloaded_path}")
                            break
                        except Exception as e:
                            logger.warning(f"Found a download button but failed to download: {e}")
                    
                    time.sleep(5)
                
                page.close()
                browser.close()
                
                if video_downloaded_path:
                    return video_downloaded_path
                else:
                    logger.error("Timeout reached while waiting for video generation.")
                    return None
                    
        except Exception as e:
            logger.error(f"Error during browser automation: {e}")
            return None

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Gemini Browser Agent...")
    print("Make sure you have installed Playwright browsers: 'playwright install'")
    print("WARNING: This requires Chrome to be already running with --remote-debugging-port=9222")
    
    agent = GeminiBrowserAgent()
    # Uncomment to actually run a test:
    # test_prompt = "Generate a 10 second vertical 9:16 cartoon video of an Indian boy running."
    # agent.generate_video(test_prompt, timeout_minutes=5)
