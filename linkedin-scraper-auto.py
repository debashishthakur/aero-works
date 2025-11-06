"""
LinkedIn Profile Scraper with Automatic ChromeDriver Download
==============================================================
This script demonstrates comprehensive LinkedIn scraping techniques including:
- Automatic ChromeDriver download and version matching
- Selenium WebDriver automation
- Cookie management and session persistence
- User-agent rotation
- Proxy rotation support
- Stealth techniques to avoid detection
- HTML parsing for profile data extraction

Requirements:
pip install selenium beautifulsoup4 lxml requests webdriver-manager

Note: ChromeDriver is now automatically downloaded and managed!
"""

import json
import time
import random
import pickle
import os
import sys
from typing import List, Dict, Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Automatic ChromeDriver management
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print("✓ webdriver_manager is installed - ChromeDriver will be auto-managed")
except ImportError:
    print("⚠ webdriver_manager not found. Installing...")
    os.system("pip install webdriver-manager")
    from webdriver_manager.chrome import ChromeDriverManager
    print("✓ webdriver_manager installed successfully")


class LinkedInScraper:
    """
    Advanced LinkedIn Profile Scraper with automatic ChromeDriver management
    """
    
    def __init__(self, email: str, password: str, use_proxy: bool = False, proxy: Optional[str] = None):
        """
        Initialize the LinkedIn scraper
        
        Args:
            email: LinkedIn account email
            password: LinkedIn account password
            use_proxy: Whether to use a proxy
            proxy: Proxy address in format "ip:port" or "username:password@ip:port"
        """
        self.email = email
        self.password = password
        self.use_proxy = use_proxy
        self.proxy = proxy
        self.driver = None
        self.cookies_file = "linkedin_cookies.pkl"
        
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)
    
    def _get_chrome_version(self) -> str:
        """
        Get the installed Chrome version
        Works on Windows, macOS, and Linux
        """
        import subprocess
        import re
        
        try:
            if sys.platform == 'win32':
                # Windows
                result = subprocess.run(
                    ['powershell', '-Command', 
                     'Get-Item -Path "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" | ForEach-Object {$_.VersionInfo.FileVersion}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"✓ Found Chrome version: {version}")
                    return version
            elif sys.platform == 'darwin':
                # macOS
                result = subprocess.run(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split()[-1]
                    print(f"✓ Found Chrome version: {version}")
                    return version
            else:
                # Linux
                result = subprocess.run(
                    ['google-chrome', '--version'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split()[-1]
                    print(f"✓ Found Chrome version: {version}")
                    return version
        except Exception as e:
            print(f"⚠ Could not detect Chrome version: {str(e)}")
            print("→ webdriver-manager will handle version matching automatically")
        
        return None
    
    def _setup_driver(self):
        """Setup Chrome driver with automatic ChromeDriver management and stealth options"""
        print("→ Setting up ChromeDriver with automatic version matching...")
        
        chrome_options = Options()
        
        # Add user agent
        chrome_options.add_argument(f'user-agent={self._get_random_user_agent()}')
        
        # Stealth options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        
        # Disable notifications
        chrome_options.add_argument('--disable-notifications')
        
        # Disable extensions
        chrome_options.add_argument('--disable-extensions')
        
        # Disable images for faster loading (optional - uncomment to enable)
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", prefs)
        
        # Add proxy if provided
        if self.use_proxy and self.proxy:
            print(f"→ Using proxy: {self.proxy}")
            chrome_options.add_argument(f'--proxy-server={self.proxy}')
        
        try:
            # Automatic ChromeDriver download and setup
            print("→ Downloading matching ChromeDriver version...")
            service = Service(ChromeDriverManager().install())
            print(f"✓ ChromeDriver service initialized successfully")
            
            # Initialize driver with service
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            print(f"✗ Error initializing ChromeDriver: {str(e)}")
            print("→ Attempting fallback method...")
            try:
                # Fallback: Try to use ChromeDriver from PATH
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                print(f"✗ Fallback also failed: {str(e2)}")
                raise Exception("Could not initialize ChromeDriver. Please ensure Chrome is installed.")
        
        # Execute script to mask webdriver property
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            print("✓ Stealth mode activated")
        except Exception as e:
            print(f"⚠ Could not activate full stealth mode: {str(e)}")
        
        self.driver.implicitly_wait(10)
        print("✓ ChromeDriver setup complete!\n")
        
    def _random_sleep(self, min_sec: float = 2, max_sec: float = 5):
        """Sleep for a random duration to mimic human behavior"""
        sleep_time = random.uniform(min_sec, max_sec)
        time.sleep(sleep_time)
        
    def _human_like_typing(self, element, text: str):
        """Type text in a human-like manner with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
    
    def _scroll_slowly(self):
        """Scroll the page slowly to mimic human behavior"""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            current_position = 0
            while current_position < total_height:
                # Random scroll distance
                scroll_distance = random.randint(200, 400)
                current_position += scroll_distance
                
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                self._random_sleep(0.5, 1.5)
                
                # Recalculate total height as content might have loaded
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if current_position >= total_height:
                    break
        except Exception as e:
            print(f"⚠ Error during scrolling: {str(e)}")
    
    def save_cookies(self):
        """Save cookies to file for session persistence"""
        try:
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(self.driver.get_cookies(), f)
            print(f"✓ Cookies saved to {self.cookies_file}")
        except Exception as e:
            print(f"⚠ Error saving cookies: {str(e)}")
    
    def load_cookies(self) -> bool:
        """Load cookies from file"""
        cookies_path = Path(self.cookies_file)
        if cookies_path.exists():
            try:
                self.driver.get("https://www.linkedin.com")
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            # Some cookies might fail, continue with others
                            continue
                print("✓ Cookies loaded successfully")
                return True
            except Exception as e:
                print(f"⚠ Error loading cookies: {str(e)}")
                return False
        return False
    
    def login(self, force_login: bool = False):
        """
        Login to LinkedIn
        
        Args:
            force_login: Force login even if cookies exist
        """
        if not self.driver:
            self._setup_driver()
        
        # Try loading cookies first
        if not force_login and self.load_cookies():
            self.driver.refresh()
            self._random_sleep(2, 3)
            
            # Check if still logged in
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                print("✓ Already logged in using saved cookies\n")
                return
        
        print("→ Logging in to LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        self._random_sleep(2, 4)
        
        try:
            # Find and fill email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            self._human_like_typing(email_field, self.email)
            self._random_sleep(1, 2)
            
            # Find and fill password
            password_field = self.driver.find_element(By.ID, "password")
            self._human_like_typing(password_field, self.password)
            self._random_sleep(1, 2)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            print("→ Login button clicked, waiting for page load...")
            self._random_sleep(5, 7)
            
            # Check for security verification
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                print("⚠ Security verification required!")
                print("Please complete the verification manually in the browser window.")
                input("Press Enter after completing verification...")
            
            # Save cookies after successful login
            self.save_cookies()
            print("✓ Login successful!\n")
            
        except TimeoutException:
            print("✗ Login failed: Timeout waiting for elements")
            raise
        except Exception as e:
            print(f"✗ Login failed: {str(e)}")
            raise
    
    def scrape_profile(self, profile_url: str) -> Dict:
        """
        Scrape a LinkedIn profile
        
        Args:
            profile_url: URL of the LinkedIn profile
            
        Returns:
            Dictionary containing profile data
        """
        print(f"→ Scraping profile: {profile_url}")
        
        try:
            self.driver.get(profile_url)
            self._random_sleep(3, 5)
            
            # Scroll to load all content
            print("  → Scrolling to load content...")
            self._scroll_slowly()
            self._random_sleep(2, 3)
            
            # Get page source
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Extract profile data
            profile_data = {
                'url': profile_url,
                'name': self._extract_name(soup),
                'headline': self._extract_headline(soup),
                'location': self._extract_location(soup),
                'about': self._extract_about(soup),
                'experience': self._extract_experience(soup),
                'education': self._extract_education(soup),
                'skills': self._extract_skills(soup)
            }
            
            print(f"✓ Successfully scraped profile: {profile_data.get('name', 'Unknown')}")
            return profile_data
            
        except Exception as e:
            print(f"✗ Error scraping profile {profile_url}: {str(e)}")
            return {'url': profile_url, 'error': str(e)}
    
    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Extract name from profile"""
        try:
            # Try multiple selectors
            name_element = soup.find('h1', class_=lambda x: x and 'text-heading-xlarge' in x)
            if name_element:
                return name_element.get_text().strip()
            
            # Alternative selector
            name_element = soup.find('h1', class_='pv-text-details__left-panel')
            if name_element:
                return name_element.get_text().strip()
                
        except Exception as e:
            pass
        return "N/A"
    
    def _extract_headline(self, soup: BeautifulSoup) -> str:
        """Extract headline/title from profile"""
        try:
            headline = soup.find('div', class_=lambda x: x and 'text-body-medium' in x)
            if headline:
                return headline.get_text().strip()
        except Exception as e:
            pass
        return "N/A"
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract location from profile"""
        try:
            location = soup.find('span', class_=lambda x: x and 'text-body-small' in x)
            if location:
                return location.get_text().strip()
        except Exception as e:
            pass
        return "N/A"
    
    def _extract_about(self, soup: BeautifulSoup) -> str:
        """Extract about section from profile"""
        try:
            about_section = soup.find('div', class_=lambda x: x and 'pv-about' in x if x else False)
            if about_section:
                about_text = about_section.find('div', class_=lambda x: x and 'inline-show-more-text' in x if x else False)
                if about_text:
                    return about_text.get_text().strip()
        except Exception as e:
            pass
        return "N/A"
    
    def _extract_experience(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract experience section from profile"""
        experiences = []
        try:
            exp_section = soup.find('section', {'id': lambda x: x and 'experience' in x if x else False})
            if exp_section:
                exp_items = exp_section.find_all('li', class_=lambda x: x and 'profile-section-card' in x if x else False)
                for item in exp_items[:5]:  # Limit to first 5
                    try:
                        title = item.find('div', class_=lambda x: x and 'mr1' in x if x else False)
                        company = item.find('span', class_=lambda x: x and 't-14' in x if x else False)
                        
                        exp_data = {
                            'title': title.get_text().strip() if title else 'N/A',
                            'company': company.get_text().strip() if company else 'N/A'
                        }
                        experiences.append(exp_data)
                    except:
                        continue
        except Exception as e:
            pass
        return experiences
    
    def _extract_education(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract education section from profile"""
        education = []
        try:
            edu_section = soup.find('section', {'id': lambda x: x and 'education' in x if x else False})
            if edu_section:
                edu_items = edu_section.find_all('li', class_=lambda x: x and 'profile-section-card' in x if x else False)
                for item in edu_items[:3]:  # Limit to first 3
                    try:
                        school = item.find('div', class_=lambda x: x and 'mr1' in x if x else False)
                        degree = item.find('span', class_=lambda x: x and 't-14' in x if x else False)
                        
                        edu_data = {
                            'school': school.get_text().strip() if school else 'N/A',
                            'degree': degree.get_text().strip() if degree else 'N/A'
                        }
                        education.append(edu_data)
                    except:
                        continue
        except Exception as e:
            pass
        return education
    
    def _extract_skills(self, soup: BeautifulSoup) -> List[str]:
        """Extract skills from profile"""
        skills = []
        try:
            skills_section = soup.find('section', {'id': lambda x: x and 'skills' in x if x else False})
            if skills_section:
                skill_items = skills_section.find_all('div', class_=lambda x: x and 'mr1' in x if x else False)
                for item in skill_items[:10]:  # Limit to first 10
                    skill_text = item.get_text().strip()
                    if skill_text:
                        skills.append(skill_text)
        except Exception as e:
            pass
        return skills
    
    def scrape_multiple_profiles(self, profile_urls: List[str], output_file: str = "linkedin_profiles.csv"):
        """
        Scrape multiple profiles and save to CSV
        
        Args:
            profile_urls: List of profile URLs to scrape
            output_file: Output CSV filename
        """
        all_profiles = []
        successful = 0
        failed = 0
        
        for i, url in enumerate(profile_urls, 1):
            print(f"\n{'='*70}")
            print(f"Processing profile {i}/{len(profile_urls)}")
            print(f"{'='*70}")
            
            profile_data = self.scrape_profile(url)
            all_profiles.append(profile_data)
            
            if 'error' in profile_data:
                failed += 1
            else:
                successful += 1
            
            # Random delay between profiles
            if i < len(profile_urls):
                delay = random.uniform(5, 10)
                print(f"→ Waiting {delay:.1f} seconds before next profile...")
                time.sleep(delay)
        
        # Save to CSV
        self._save_to_csv(all_profiles, output_file)
        
        print(f"\n{'='*70}")
        print(f"Scraping Complete!")
        print(f"{'='*70}")
        print(f"Total profiles processed: {len(profile_urls)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/len(profile_urls)*100):.1f}%")
        
        return all_profiles
    
    def _save_to_csv(self, profiles: List[Dict], filename: str):
        """Save profile data to CSV file"""
        import csv
        
        if not profiles:
            print("✗ No profiles to save")
            return
        
        # Define CSV columns
        columns = ['url', 'name', 'headline', 'location', 'about']
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                
                for profile in profiles:
                    # Flatten experience and education
                    row = {
                        'url': profile.get('url', ''),
                        'name': profile.get('name', ''),
                        'headline': profile.get('headline', ''),
                        'location': profile.get('location', ''),
                        'about': profile.get('about', '')[:500] if profile.get('about') else ''
                    }
                    writer.writerow(row)
            
            print(f"\n✓ Successfully saved {len(profiles)} profiles to {filename}")
            
        except Exception as e:
            print(f"✗ Error saving to CSV: {str(e)}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("\n✓ Browser closed")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("="*70)
    print("LinkedIn Profile Scraper - Auto ChromeDriver Version")
    print("="*70 + "\n")
    
    # Configuration
    LINKEDIN_EMAIL = "debsthakur@gmail.com"  # Replace with your test account email
    LINKEDIN_PASSWORD = "@May211999"  # Replace with your test account password
    
    # List of profile URLs to scrape (19 profiles as provided)
    PROFILE_URLS = [
        "https://www.linkedin.com/in/mario-hesham-207660242/",
        "https://www.linkedin.com/in/mahmoud-el-kady-6b01b5220/",
        "https://www.linkedin.com/in/ibrahim-madany-038426354/",
        "https://www.linkedin.com/in/abdalla-gamal-2b58a8196/",
        "https://www.linkedin.com/in/debashishthakur/",
        "https://www.linkedin.com/in/avijayvargia/",
        "https://www.linkedin.com/in/ramit-kundu-b3b91014a/",
        "https://www.linkedin.com/in/tarun29061990/",
        "https://www.linkedin.com/in/gunnu13/",
        "https://www.linkedin.com/in/ayushi-sharma-8a285a185/",
        "https://www.linkedin.com/in/komalpandey152/",
        "https://www.linkedin.com/in/swati-jha2906/",
        "https://www.linkedin.com/in/dimple-sharma-465301144/",
        "https://www.linkedin.com/in/tarun-khandagare/",
        "https://www.linkedin.com/in/eswarbhageerathkesari/",
        "https://www.linkedin.com/in/srikomm/",
        "https://www.linkedin.com/in/vramesh-50/",
        "https://www.linkedin.com/in/peter-sujan/",
        "https://www.linkedin.com/in/nathantung/"
    ]
    
    # Optional: Proxy configuration
    USE_PROXY = False
    PROXY = None  # Format: "ip:port" or "username:password@ip:port"
    
    # Initialize scraper
    scraper = LinkedInScraper(
        email=LINKEDIN_EMAIL,
        password=LINKEDIN_PASSWORD,
        use_proxy=USE_PROXY,
        proxy=PROXY
    )
    
    try:
        # Login
        scraper.login()
        
        # Scrape profiles
        profiles = scraper.scrape_multiple_profiles(PROFILE_URLS)
        
        # Also save as JSON for reference
        with open('linkedin_profiles.json', 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        print("✓ Also saved to linkedin_profiles.json")
        
    except KeyboardInterrupt:
        print("\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
