# crawler.py
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Configuration ---
# You can change this to any starting URL
START_URL = 'https://en.wikipedia.org/wiki/Search_engine'
MAX_PAGES = 20  # Limit the crawl to 20 pages
DB_NAME = 'search.db'
# ---------------------

def init_db():
    """Creates the database and 'pages' table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Drop table if it exists to start fresh
    c.execute('DROP TABLE IF EXISTS pages')
    # Create table
    c.execute('''
        CREATE TABLE pages (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized.")

def crawl():
    """Crawls web pages and stores their text content in the database."""
    print(f"Starting crawl from: {START_URL}")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    pages_to_visit = [START_URL]
    visited_pages = set()
    pages_crawled = 0
    
    # Get the base domain to stay on the same site
    base_domain = urlparse(START_URL).netloc

    while pages_to_visit and pages_crawled < MAX_PAGES:
        current_url = pages_to_visit.pop(0)
        
        if current_url in visited_pages:
            continue
        
        try:
            # Add this headers dictionary
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            }
            
            # Add headers=headers to the request
            response = requests.get(current_url, headers=headers, timeout=5)
            
            # Raise an error for bad responses (4xx, 5xx)
            response.raise_for_status()
            
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue  # Skip non-HTML pages
                
            visited_pages.add(current_url)
            pages_crawled += 1
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text (IMPROVED version)
            # Find the specific div for main content on Wikipedia
            main_content = soup.find('div', id='mw-content-text')

            if main_content:
                # Remove navigation bars, footers, etc., that are *inside* the main content div
                for element in main_content.find_all(['nav', 'table', '.noprint', '.mw-editsection']):
                    element.decompose() # This removes the element

                # Get the cleaned text
                text_content = ' '.join(main_content.get_text().split())
            else:
                # If we can't find the main content, skip this page
                print(f"Could not find main content for {current_url}, skipping.")
                continue # This skips the rest of the loop and goes to the next page
            # Save to database
            try:
                c.execute('INSERT INTO pages (url, content) VALUES (?, ?)', (current_url, text_content))
                conn.commit()
                print(f"[{pages_crawled}/{MAX_PAGES}] Crawled and saved: {current_url}")
            except sqlite3.IntegrityError:
                print(f"URL already in database: {current_url}")
            
            # Find new links to visit
            if main_content:
                for link in main_content.find_all('a', href=True):
                    href = link['href']
                    new_url = urljoin(current_url, href)
                    
                    # Clean URL (remove fragments)
                    new_url = new_url.split('#')[0]
                    
                    # Stay on the same domain and avoid visited links
                    if urlparse(new_url).netloc == base_domain and \
                       new_url not in visited_pages and \
                       new_url not in pages_to_visit:
                        
                        pages_to_visit.append(new_url)

        except requests.RequestException as e:
            print(f"Failed to fetch {current_url}: {e}")
        except Exception as e:
            print(f"Error processing {current_url}: {e}")

    conn.close()
    print(f"\nCrawl complete. {pages_crawled} pages saved to '{DB_NAME}'.")

if __name__ == '__main__':
    init_db()
    crawl()