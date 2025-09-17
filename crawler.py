from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from collections import deque

# Import the scraping function from our main scrape module
try:
    from scrape_enhanced import scrape_website
except ImportError:
    try:
        from scrape_playwright import scrape_website_playwright as scrape_website
    except ImportError:
        from scrape import scrape_website

# Configuration
EXCLUDED_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.rar', '.tar', '.gz', '.exe', '.dmg', '.pkg',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.css', '.js', '.xml', '.json'
]

EXCLUDED_URL_KEYWORDS = [
    'logout', 'login', 'signin', 'signup', 'register',
    'admin', 'dashboard', 'profile', 'settings',
    'cart', 'checkout', 'payment', 'billing',
    'download', 'upload', 'api', 'feed'
]


class WebCrawler:
    def __init__(self, max_pages=10, delay=2, same_domain_only=True, progress_callback=None):
        self.max_pages = max_pages
        self.delay = delay
        self.same_domain_only = same_domain_only
        self.visited_urls = set()
        self.scraped_content = {}
        self.url_queue = deque()
        self.found_links = set()
        self.progress_callback = progress_callback  # Callback for progress updates
        
    def get_domain(self, url):
        """Extract domain from URL"""
        return urlparse(url).netloc
    
    def is_valid_url(self, url, base_domain):
        """Check if URL is valid for crawling"""
        if not url or url.startswith('#') or url.startswith('mailto:') or url.startswith('tel:'):
            return False
        
        # Check for excluded file extensions
        url_lower = url.lower()
        if any(url_lower.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            return False
        
        # Check for excluded keywords
        if any(keyword in url_lower for keyword in EXCLUDED_URL_KEYWORDS):
            return False
        
        # Check domain restriction
        if self.same_domain_only:
            return self.get_domain(url) == base_domain
        
        return True
    
    def extract_links(self, html_content, base_url):
        """Extract all valid links from HTML content"""
        soup = BeautifulSoup(html_content, "html.parser")
        links = set()
        base_domain = self.get_domain(base_url)
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            if self.is_valid_url(absolute_url, base_domain):
                links.add(absolute_url)
        
        return list(links)
    
    def scrape_single_page(self, url):
        """Scrape a single page and return HTML content"""
        try:
            print(f"🕷️ Crawling: {url}")
            # Use the same scraping function as the main app
            html_content = scrape_website(url)
            return html_content
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def update_progress(self, message, current_url=None, links_found=0):
        """Update progress via callback"""
        if self.progress_callback:
            progress_data = {
                'message': message,
                'current_url': current_url,
                'visited_count': len(self.visited_urls),
                'queue_size': len(self.url_queue),
                'total_links_found': len(self.found_links),
                'links_on_current_page': links_found,
                'max_pages': self.max_pages,
                'progress_percentage': min((len(self.visited_urls) / self.max_pages) * 100, 100)
            }
            self.progress_callback(progress_data)

    def crawl_website(self, start_url):
        """Enhanced crawl with recursive link discovery and progress tracking"""
        print(f"🚀 Starting recursive crawl from: {start_url}")
        
        # Initialize
        self.url_queue = deque([start_url])
        base_domain = self.get_domain(start_url)
        self.found_links.add(start_url)
        
        self.update_progress("🔍 Starting crawl...", start_url)
        
        while self.url_queue and len(self.visited_urls) < self.max_pages:
            current_url = self.url_queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            # Update progress
            self.update_progress(f"🕷️ Scraping page...", current_url)
            
            # Scrape the page
            html_content = self.scrape_single_page(current_url)
            
            if html_content:
                # Mark as visited and store content
                self.visited_urls.add(current_url)
                self.scraped_content[current_url] = html_content
                
                # Extract ALL links from this page (recursive discovery)
                page_links = self.extract_links(html_content, current_url)
                new_links_count = 0
                
                # Add new links to queue and tracking
                for link in page_links:
                    if link not in self.found_links:
                        self.found_links.add(link)
                        new_links_count += 1
                        
                        # Add to queue if not visited and not already queued
                        if link not in self.visited_urls and link not in self.url_queue:
                            self.url_queue.append(link)
                
                # Update progress with link discovery info
                self.update_progress(
                    f"✅ Found {new_links_count} new links", 
                    current_url, 
                    len(page_links)
                )
                
                print(f"📄 Page: {current_url}")
                print(f"🔗 Links on page: {len(page_links)} | New: {new_links_count}")
                print(f"📊 Progress: {len(self.visited_urls)}/{self.max_pages} pages | Queue: {len(self.url_queue)} | Total links found: {len(self.found_links)}")
                print("-" * 80)
                
                # Delay between requests
                if self.delay > 0:
                    time.sleep(self.delay)
            else:
                self.update_progress(f"❌ Failed to scrape", current_url)
        
        # Final progress update
        final_message = f"Crawling completed! Scraped {len(self.visited_urls)} pages, found {len(self.found_links)} total links"
        self.update_progress(final_message)
        print(final_message)
        
        return self.scraped_content
    
    def get_crawl_stats(self):
        """Get detailed crawling statistics"""
        return {
            'pages_scraped': len(self.visited_urls),
            'total_links_discovered': len(self.found_links),
            'pages_in_queue': len(self.url_queue),
            'max_pages': self.max_pages,
            'completion_percentage': min((len(self.visited_urls) / self.max_pages) * 100, 100),
            'visited_urls': list(self.visited_urls),
            'remaining_queue': list(self.url_queue)
        }

    def get_all_content(self):
        """Get all scraped content as a single string"""
        all_content = []
        for i, (url, html) in enumerate(self.scraped_content.items(), 1):
            all_content.append(f"=== PAGE {i}: {url} ===\n")
            
            # Extract and clean body content
            soup = BeautifulSoup(html, "html.parser")
            body = soup.body
            
            if body:
                # Remove scripts and styles
                for script_or_style in body(["script", "style"]):
                    script_or_style.extract()
                
                # Get clean text
                text = body.get_text(separator="\n")
                cleaned_text = "\n".join(
                    line.strip() for line in text.splitlines() if line.strip()
                )
                all_content.append(cleaned_text)
            
            all_content.append("\n" + "="*80 + "\n")
        
        return "\n".join(all_content)