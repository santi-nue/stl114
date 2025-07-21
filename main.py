import os
import sqlite3
import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import time

# Set up SQLite DB
conn = sqlite3.connect('images.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        url TEXT PRIMARY KEY,
        data BLOB
    )
''')
conn.commit()

visited = set()

def download_and_store(image_url):
    if image_url in visited:
        return
    visited.add(image_url)
    try:
        # Download image data
        with urllib.request.urlopen(image_url) as response:
            data = response.read()
            # Store in SQLite
            cursor.execute('INSERT OR IGNORE INTO images (url, data) VALUES (?, ?)', (image_url, data))
            conn.commit()
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")

def scrape_recursive(driver, root_url, current_url, domain):
    if current_url in visited:
        return
    visited.add(current_url)
    
    try:
        driver.get(current_url)
        time.sleep(1)  # Adjust if needed for JS content

        # Get all <img> tags
        images = driver.find_elements(By.TAG_NAME, 'img')
        for img in images:
            src = img.get_attribute('src')
            if src:
                src = urljoin(current_url, src)  # Handle relative URLs
                download_and_store(src)
        
        # Find and queue internal links
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            if href:
                href_parsed = urlparse(href)
                # Scrape only same-domain, http(s) links
                if href_parsed.scheme in ('http', 'https') and href_parsed.netloc == domain:
                    if href not in visited:
                        scrape_recursive(driver, root_url, href, domain)
    except Exception as e:
        print(f"Error scraping {current_url}: {e}")

def main(start_url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    domain = urlparse(start_url).netloc
    scrape_recursive(driver, start_url, start_url, domain)
    driver.quit()

    conn.close()
    print("Done. All images saved in images.db.")

if __name__ == '__main__':
    # Replace with your starting URL
    main("http://www.spanishbeercoasters.es")
