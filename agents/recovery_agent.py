import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger

class RecoveryAgent:
    def __init__(self, page=None):
        """
        Initializes the Recovery Agent.
        Optionally takes a Playwright page object to perform direct browser actions (like clicking or reloading).
        """
        self.page = page

    def handle_failure(self, status):
        """
        Determines the recovery action based on the failure status from the GeminiMonitor.
        Actions: RETRY, REFRESH, WAIT, REQUEUE
        """
        logger.info(f"Recovery Agent analyzing failure status: {status}")
        
        if status == "TRY_AGAIN":
            logger.info("Action decided: RETRY (Will attempt to click 'Try again' button)")
            self._perform_retry()
            return "RETRY"
            
        elif status == "ERROR":
            logger.info("Action decided: REFRESH (Will attempt to refresh the page)")
            self._perform_refresh()
            return "REFRESH"
            
        elif status == "LIMIT_REACHED":
            logger.warning("Action decided: WAIT (Usage limit reached, suggesting a wait period)")
            self._perform_wait()
            return "WAIT"
            
        elif status in ["TIMEOUT", "UNKNOWN"]:
            logger.warning("Action decided: REQUEUE (Unable to resolve in current session, sending back to queue)")
            return "REQUEUE"
            
        else:
            logger.info(f"No recovery needed for status: {status}")
            return "NONE"

    def _perform_retry(self):
        """Attempts to click the 'Try again' button if a page is provided."""
        if not self.page:
            return
            
        try:
            retry_button = self.page.locator("text='Try again'")
            if retry_button.is_visible():
                retry_button.click()
                time.sleep(2)
                logger.info("Clicked 'Try again' successfully.")
            else:
                logger.warning("'Try again' button not visible to click.")
        except Exception as e:
            logger.error(f"Failed to perform retry click: {e}")

    def _perform_refresh(self):
        """Refreshes the current page if a page is provided."""
        if not self.page:
            return
            
        try:
            self.page.reload()
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
            logger.info("Page refreshed successfully.")
        except Exception as e:
            logger.error(f"Failed to perform page refresh: {e}")

    def _perform_wait(self, minutes=60):
        """
        Logs a wait action. The orchestrator is expected to read the 'WAIT' return
        value and pause the main job execution.
        """
        logger.info(f"System must wait for {minutes} minutes before trying again.")

if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("Testing Recovery Agent...")
    agent = RecoveryAgent()
    
    print(f"\nEvaluating Status: TRY_AGAIN")
    print(f"Action Returned: {agent.handle_failure('TRY_AGAIN')}")
    
    print(f"\nEvaluating Status: ERROR")
    print(f"Action Returned: {agent.handle_failure('ERROR')}")
    
    print(f"\nEvaluating Status: LIMIT_REACHED")
    print(f"Action Returned: {agent.handle_failure('LIMIT_REACHED')}")
    
    print(f"\nEvaluating Status: TIMEOUT")
    print(f"Action Returned: {agent.handle_failure('TIMEOUT')}")
