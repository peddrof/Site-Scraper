import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time

# Base URL of the site you want to download
BASE_URL = "https://example.com"
DOWNLOAD_DIR = "site_copy"

# Set to keep track of visited URLs to avoid duplicates
visited_urls = set()

# Headers to mimic a browser (some sites block default requests)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def ensure_dir(file_path):
    """Create directory if it doesn't exist."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_file(url, folder):
    """Download a file from a URL and save it locally."""
    try:
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        # Get the file path from the URL
        parsed_url = urlparse(url)
        file_path = os.path.join(folder, parsed_url.path.lstrip("/"))
        if not file_path.endswith((".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".woff", ".woff2", ".ttf")):
            file_path = os.path.join(file_path, "index.html")
        
        ensure_dir(file_path)
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return None

def extract_assets(soup, base_url, folder):
    """Extract and download CSS, JS, images, and fonts from an HTML page."""
    # CSS
    for link in soup.find_all("link", rel="stylesheet"):
        css_url = urljoin(base_url, link.get("href"))
        download_file(css_url, folder)
    
    # JS
    for script in soup.find_all("script", src=True):
        js_url = urljoin(base_url, script.get("src"))
        download_file(js_url, folder)
    
    # Images
    for img in soup.find_all("img", src=True):
        img_url = urljoin(base_url, img.get("src"))
        download_file(img_url, folder)
    
    # Fonts (from CSS or direct links might need additional parsing)
    for link in soup.find_all("link", href=True):
        if link["href"].endswith((".woff", ".woff2", ".ttf")):
            font_url = urljoin(base_url, link.get("href"))
            download_file(font_url, folder)

def crawl_site(url, folder):
    """Recursively crawl and download the site."""
    if url in visited_urls or not url.startswith(BASE_URL):
        return
    
    visited_urls.add(url)
    print(f"Crawling: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Download the HTML page
        html_path = download_file(url, folder)
        if not html_path:
            return
        
        # Extract and download assets
        extract_assets(soup, url, folder)
        
        # Find all links and crawl them
        for a_tag in soup.find_all("a", href=True):
            next_url = urljoin(url, a_tag.get("href"))
            if next_url.startswith(BASE_URL):
                crawl_site(next_url, folder)
    
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")

# Start the crawl
if __name__ == "__main__":
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    crawl_site(BASE_URL, DOWNLOAD_DIR)
    print("Download complete!")
