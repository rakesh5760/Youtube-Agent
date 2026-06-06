import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger

class GeminiMonitor:
    def __init__(self, page):
        """
        Initializes the monitor with a Playwright page object.
        """
        self.page = page

    def check_status(self):
        """
        Evaluates the current state of the Gemini UI and returns a status JSON.
        Returns: dict with "status" key.
        Statuses: GENERATING, TRY_AGAIN, ERROR, LIMIT_REACHED, SUCCESS, UNKNOWN
        """
        try:
            # 1. Check for Limit Reached
            if self.page.locator("text='Limit reached'").is_visible() or \
               self.page.locator("text='You\\'ve reached the limit'").is_visible() or \
               self.page.locator("text='usage limit'").is_visible():
                return {"status": "LIMIT_REACHED"}
                
            # 2. Check for Generic Errors / Something went wrong
            if self.page.locator("text='Something went wrong'").is_visible() or \
               self.page.locator("text='An error occurred'").is_visible():
                return {"status": "ERROR"}
                
            # 3. Check for Try Again button
            if self.page.locator("text='Try again'").is_visible() or \
               self.page.locator("button:has-text('Try again')").is_visible():
                return {"status": "TRY_AGAIN"}
                
            # 4. Check for Download button (SUCCESS)
            download_button = self.page.locator("button[aria-label*='Download'], a[download]").last
            if download_button.is_visible():
                return {"status": "SUCCESS"}
                
            # 5. Check for Generating state
            if self.page.locator("text='Generating'").is_visible() or \
               self.page.locator("text='Creating'").is_visible() or \
               self.page.locator("mat-progress-spinner").is_visible() or \
               self.page.locator("text='Working on it'").is_visible():
                return {"status": "GENERATING"}

            # If nothing else matches
            return {"status": "UNKNOWN"}

        except Exception as e:
            logger.error(f"Error checking Gemini status: {e}")
            return {"status": "ERROR"}

    def wait_for_completion(self, timeout_minutes=15):
        """
        Polls the UI until a terminal state is reached.
        """
        start_time = time.time()
        logger.info(f"Monitoring Gemini UI for up to {timeout_minutes} minutes...")
        
        while (time.time() - start_time) < timeout_minutes * 60:
            result = self.check_status()
            status = result["status"]
            
            if status in ["SUCCESS", "LIMIT_REACHED", "ERROR", "TRY_AGAIN"]:
                logger.info(f"Terminal status reached: {status}")
                return result
                
            if status == "GENERATING":
                logger.info("Status: Generating...")
            elif status == "UNKNOWN":
                logger.debug("Status: Unknown (waiting for UI update)...")
                
            time.sleep(5)
            
        logger.warning("Monitoring timed out.")
        return {"status": "TIMEOUT"}

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Gemini UI Monitoring Agent...")
    print("This module is designed to be imported and passed a Playwright page object.")
    print("Example usage:")
    print("  from agents.gemini_monitor import GeminiMonitor")
    print("  monitor = GeminiMonitor(playwright_page)")
    print("  result = monitor.wait_for_completion()")
    print("  print(json.dumps(result))")
