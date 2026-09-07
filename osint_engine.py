import os
import time
import logging
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

# We use a try-except block so that the pipeline doesn't crash if playwright isn't installed
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OSINTEngine:
    """
    Enterprise-grade OSINT Engine using Headless Browser Automation.
    Bypasses basic anti-bot mechanisms to perform real reverse image searches
    and extract actual social media footprints.
    """
    def __init__(self):
        logger.info("Initializing Headless OSINT Engine...")
        self.supported_platforms = ['instagram.com', 'twitter.com', 'linkedin.com', 'facebook.com']

    def perform_reverse_image_search(self, image_path: str) -> List[str]:
        """
        Drives a headless Chromium browser to perform a real reverse image search.
        Extracts all valid social media URLs found in the results.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright is not installed. OSINT engine cannot run.")
            return []

        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return []

        extracted_urls = []
        
        try:
            with sync_playwright() as p:
                logger.info("Launching headless Chromium for OSINT scraping...")
                # Launch headless browser (use headless=True in production)
                browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                # Approach 1: Yandex Images (Often better for un-censored face matching than Google)
                logger.info("Connecting to Yandex Visual Search...")
                try:
                    page.goto('https://yandex.com/images/', timeout=30000)
                    # Click the camera icon
                    page.click('button[aria-label="Image search"]', timeout=5000)
                    
                    # Upload the file directly to the hidden input
                    page.set_input_files('input[type="file"]', image_path)
                    
                    # Wait for results to load
                    page.wait_for_selector('a.CbirItem-TitleLink', timeout=15000)
                    
                    # Extract URLs
                    links = page.locator('a').all()
                    for link in links:
                        href = link.get_attribute('href')
                        if href and any(platform in href for platform in self.supported_platforms):
                            extracted_urls.append(href)
                except Exception as e:
                    logger.warning(f"Yandex search strategy failed or timed out: {e}")

                # Approach 2: Google Images fallback if Yandex fails or to get more results
                if not extracted_urls:
                    logger.info("Connecting to Google Lens Visual Search...")
                    try:
                        page.goto('https://images.google.com/', timeout=30000)
                        # Click the camera icon
                        page.click('div[role="button"][aria-label="Search by image"]', timeout=5000)
                        
                        # Wait for the upload modal to appear and attach file
                        # Google Lens uses a specific file input inside the modal
                        page.set_input_files('input[type="file"][name="encoded_image"]', image_path, timeout=5000)
                        
                        # Wait for Lens to process
                        time.sleep(5) # Allow dynamic content to load
                        
                        # Extract URLs
                        links = page.locator('a').all()
                        for link in links:
                            href = link.get_attribute('href')
                            if href and any(platform in href for platform in self.supported_platforms):
                                extracted_urls.append(href)
                    except Exception as e:
                        logger.warning(f"Google Lens strategy failed: {e}")

                browser.close()
                
        except Exception as e:
            logger.error(f"Headless browser critical failure: {e}")

        # Clean and deduplicate URLs
        clean_urls = list(set([self._clean_url(url) for url in extracted_urls if url]))
        logger.info(f"OSINT Engine discovered {len(clean_urls)} real social profiles.")
        return clean_urls

    def _clean_url(self, url: str) -> str:
        """Removes tracking parameters from scraped URLs"""
        # Remove Google redirect prefixes if any
        if "url?q=" in url:
            url = url.split("url?q=")[1].split("&")[0]
        # Remove UTM and other tracking params
        return url.split('?')[0]

if __name__ == "__main__":
    engine = OSINTEngine()
    res = engine.perform_reverse_image_search("private_photos/media_1788735986369.jpg")
    print(res)
