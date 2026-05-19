import os
import time
import random
import logging

logger = logging.getLogger(__name__)

# Try to import playwright, if not installed, we'll log warnings
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class HsoubBidder:
    def __init__(self, data_dir="."):
        self.data_dir = data_dir
        self.profile_dir = os.path.join(data_dir, "playwright_profile")
        os.makedirs(self.profile_dir, exist_ok=True)

    def is_available(self):
        return PLAYWRIGHT_AVAILABLE

    def run_login_session(self, site="mostaql"):
        """Launch headed browser so user can log in manually to save session context."""
        if not PLAYWRIGHT_AVAILABLE:
            return False, "Playwright is not installed. Run 'pip install playwright && playwright install'"
        
        site_profile_dir = os.path.join(self.profile_dir, site)
        os.makedirs(site_profile_dir, exist_ok=True)
        
        url = "https://mostaql.com/login" if site == "mostaql" else "https://khamsat.com/login"
        
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    site_profile_dir,
                    headless=False,
                    viewport=None,
                    args=["--start-maximized"]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(url)
                
                logger.info(f"Opened login window for {site}. Waiting for user to close browser...")
                
                # Wait until window is closed
                while len(context.pages) > 0:
                    try:
                        page.wait_for_timeout(1000)
                    except Exception:
                        break
                context.close()
            return True, f"Session saved successfully for {site}."
        except Exception as e:
            logger.error(f"Error during manual login session: {e}")
            return False, str(e)

    def check_session_status(self, site="mostaql"):
        """Check if we have an active session cookie/storage."""
        site_profile_dir = os.path.join(self.profile_dir, site)
        if not os.path.exists(site_profile_dir):
            return False, "No profile directory exists. Login first."
            
        if not PLAYWRIGHT_AVAILABLE:
            return False, "Playwright not installed."
            
        url = "https://mostaql.com/projects" if site == "mostaql" else "https://khamsat.com/community/requests"
        
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    site_profile_dir,
                    headless=True
                )
                page = context.new_page()
                page.goto(url, timeout=20000)
                
                # Check if logged in. If logged in, page should not have a login link but will show user menu/profile
                is_logged_in = False
                if site == "mostaql":
                    is_logged_in = page.locator("a[href*='/login']").count() == 0
                else: # khamsat
                    is_logged_in = page.locator("a[href*='/login']").count() == 0
                    
                context.close()
                return is_logged_in, "Active session found." if is_logged_in else "Session expired or not logged in."
        except Exception as e:
            return False, f"Error checking session: {str(e)}"

    def submit_bid(self, site, project_url, proposal_text, budget=None, duration=None):
        """Submit a bid/comment to Mostaql or Khamsat in the background."""
        if not PLAYWRIGHT_AVAILABLE:
            return False, "Playwright is not installed.", None
            
        site_profile_dir = os.path.join(self.profile_dir, site)
        screenshot_path = os.path.join(self.data_dir, f"{site}_submit_error.png")
        
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    site_profile_dir,
                    headless=True
                )
                page = context.new_page()
                page.goto(project_url, timeout=25000)
                
                # Add delay to look natural
                time.sleep(random.uniform(2.0, 4.0))
                
                if site == "mostaql":
                    desc_selector = "textarea[name='description']"
                    if page.locator(desc_selector).count() == 0:
                        page.screenshot(path=screenshot_path)
                        context.close()
                        return False, "Proposal description textarea not found. Check if logged in or if project is closed.", screenshot_path
                    
                    # Fill description
                    page.fill(desc_selector, proposal_text)
                    
                    # Fill budget (if present)
                    if budget:
                        amount_sel = "input[name='amount']"
                        if page.locator(amount_sel).count() > 0:
                            page.fill(amount_sel, str(budget))
                            
                    # Fill duration
                    if duration:
                        dur_sel = "input[name='duration']"
                        if page.locator(dur_sel).count() > 0:
                            page.fill(dur_sel, str(duration))
                            
                    # Jitter before clicking submit
                    time.sleep(random.uniform(1.5, 3.0))
                    
                    # Click Submit
                    submit_btn = page.locator("button[type='submit']")
                    if submit_btn.count() > 0:
                        submit_btn.first.click()
                        page.wait_for_timeout(4000)
                        
                        success = page.locator(desc_selector).count() == 0 or "proposals" in page.url
                        if not success:
                            page.screenshot(path=screenshot_path)
                            context.close()
                            return False, "Failed to submit: Form is still present or submission error occurred.", screenshot_path
                            
                        context.close()
                        return True, "Bid submitted successfully!", None
                    else:
                        page.screenshot(path=screenshot_path)
                        context.close()
                        return False, "Submit button not found.", screenshot_path
                        
                else: # khamsat
                    comment_sel = "textarea[name='comment']"
                    if page.locator(comment_sel).count() == 0:
                        comment_sel = "textarea[name='content']"
                    if page.locator(comment_sel).count() == 0:
                        comment_sel = "textarea"
                        
                    if page.locator(comment_sel).count() == 0:
                        page.screenshot(path=screenshot_path)
                        context.close()
                        return False, "Reply textarea not found. The post might be closed or session expired.", screenshot_path
                        
                    page.fill(comment_sel, proposal_text)
                    time.sleep(random.uniform(2.0, 4.0))
                    
                    submit_btn = page.locator("button[type='submit']")
                    if submit_btn.count() == 0:
                        submit_btn = page.locator("input[type='submit']")
                        
                    if submit_btn.count() > 0:
                        submit_btn.first.click()
                        page.wait_for_timeout(4000)
                        context.close()
                        return True, "Reply submitted successfully!", None
                    else:
                        page.screenshot(path=screenshot_path)
                        context.close()
                        return False, "Submit button not found on Khamsat.", screenshot_path
                        
        except Exception as e:
            logger.error(f"Error submitting bid: {e}")
            return False, f"Exception occurred: {str(e)}", screenshot_path
