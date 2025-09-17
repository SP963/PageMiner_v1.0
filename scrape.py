from selenium import webdriver
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Configuration
SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")
SCRAPING_MODE = os.getenv("SCRAPING_MODE", "local")


def get_chrome_options():
    """Get Chrome options with basic anti-detection"""
    options = ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return options


def scrape_website(website):
    """Scrape website using configured method"""
    print(f"🌐 Scraping: {website}")
    
    options = get_chrome_options()
    driver = None
    
    try:
        if SCRAPING_MODE == "remote" and SBR_WEBDRIVER:
            # Use remote browser service
            print("📡 Using remote browser service...")
            sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
            driver = Remote(sbr_connection, options=options)
            
            driver.get(website)
            
            # Handle CAPTCHA for remote service
            try:
                solve_res = driver.execute(
                    "executeCdpCommand",
                    {
                        "cmd": "Captcha.waitForSolve",
                        "params": {"detectTimeout": 10000},
                    },
                )
                print("Captcha solve status:", solve_res["value"]["status"])
            except Exception as e:
                print(f"CAPTCHA handling: {e}")
        
        else:
            # Use local ChromeDriver
            print("💻 Using local ChromeDriver...")
            
            if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
                service = Service(CHROMEDRIVER_PATH)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                # Try to use ChromeDriver from PATH
                driver = webdriver.Chrome(options=options)
            
            driver.get(website)
            time.sleep(2)  # Wait for page to load
        
        html = driver.page_source
        print("✅ Scraping successful")
        return html
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()


def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""


def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")

    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()

    # Get text or further process the content
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)
    ]


def extract_links_from_content(html_content, base_url):
    """Extract all links from HTML content for crawling"""
    from urllib.parse import urljoin, urlparse
    
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        links.append({
            'url': absolute_url,
            'text': link.get_text(strip=True),
            'title': link.get('title', '')
        })
    
    return links
