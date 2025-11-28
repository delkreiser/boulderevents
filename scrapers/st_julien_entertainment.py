"""
St Julien Hotel & Spa - Entertainment Events Scraper
URL: https://stjulien.com/boulder-colorado-events/category/entertainment-events/

This scraper extracts entertainment events from St Julien's events calendar.
Note: This site uses a JavaScript calendar widget, so we may need Selenium/Playwright
for full functionality.
"""

from bs4 import BeautifulSoup
from datetime import datetime
import re
import json


def scrape_st_julien_entertainment(html_content):
    """
    Scrape entertainment events from St Julien
    
    Args:
        html_content: Raw HTML content from the events page
        
    Returns:
        List of event dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Look for The Events Calendar (Tribe) structure
    # Common class patterns: tribe-events-list, tribe-events-event, etc.
    
    # Try multiple selectors
    event_selectors = [
        'article.tribe-events-calendar-list__event',
        'div.tribe-events-calendar-list__event',
        'article[class*="tribe-event"]',
        'div[class*="event-item"]',
        '.type-tribe_events',
    ]
    
    event_elements = []
    for selector in event_selectors:
        found = soup.select(selector)
        if found:
            event_elements = found
            print(f"Found {len(found)} events using selector: {selector}")
            break
    
    # If no events found with specific selectors, try broader search
    if not event_elements:
        event_elements = soup.find_all('article', class_=lambda x: x and 'event' in str(x).lower())
    
    for element in event_elements:
        try:
            event = extract_event_data(element)
            if event:
                event['venue'] = 'St Julien Hotel & Spa'
                event['category'] = 'Entertainment'
                event['source_url'] = 'https://stjulien.com/boulder-colorado-events/category/entertainment-events/'
                events.append(event)
        except Exception as e:
            print(f"Error parsing event: {e}")
            continue
    
    return events


def extract_event_data(element):
    """Extract event data from a single event element"""
    
    # Title
    title_elem = element.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name|heading', re.I))
    if not title_elem:
        title_elem = element.find('a', class_=re.compile(r'title|name', re.I))
    if not title_elem:
        # Look for any heading
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
    
    title = title_elem.get_text(strip=True) if title_elem else None
    
    if not title:
        return None
    
    # Link
    link_elem = element.find('a', href=True)
    link = None
    if link_elem:
        link = link_elem.get('href', '')
        if link and not link.startswith('http'):
            link = f"https://stjulien.com{link}"
    
    # Date and Time
    date_text = None
    time_text = None
    
    # Look for date elements
    date_elem = element.find(class_=re.compile(r'date|time|when', re.I))
    if date_elem:
        date_text = date_elem.get_text(strip=True)
    
    # Try to find separate time element
    time_elem = element.find(class_=re.compile(r'time', re.I))
    if time_elem and time_elem != date_elem:
        time_text = time_elem.get_text(strip=True)
    
    # Description
    desc_elem = element.find(['p', 'div'], class_=re.compile(r'desc|excerpt|summary|content', re.I))
    description = desc_elem.get_text(strip=True) if desc_elem else None
    
    # If no description found, try to get any paragraph
    if not description:
        desc_elem = element.find('p')
        description = desc_elem.get_text(strip=True) if desc_elem else None
    
    return {
        'title': title,
        'date': date_text,
        'time': time_text,
        'description': description,
        'link': link,
    }


def scrape_with_selenium(url):
    """
    Alternative scraper using Selenium for JavaScript-rendered content
    This would be used if the basic scraper doesn't work well
    
    Note: Requires selenium and a webdriver to be installed
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        
        # Set up headless browser
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for events to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tribe-events-calendar-list__event"))
        )
        
        # Get the rendered HTML
        html_content = driver.page_source
        driver.quit()
        
        return scrape_st_julien_entertainment(html_content)
        
    except ImportError:
        print("Selenium not installed. Install with: pip install selenium")
        return []
    except Exception as e:
        print(f"Error with Selenium scraper: {e}")
        return []


if __name__ == "__main__":
    import json
    from playwright.sync_api import sync_playwright
    
    print("St Julien Entertainment Scraper")
    print("=" * 60)
    
    events = []
    
    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            page.set_default_timeout(30000)
            
            print("Loading St Julien events page...")
            page.goto('https://stjulien.com/boulder-colorado-events/category/entertainment-events/', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(5000)
            
            html_content = page.content()
            browser.close()
            
            print("Parsing events...")
            events = scrape_st_julien_entertainment(html_content)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nFound {len(events)} events")
    
    # Save to JSON
    output_file = 'st_julien_events.json'
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)
    
    if events:
        print(f"✅ Events saved to {output_file}")
        for i, event in enumerate(events[:3], 1):
            print(f"\nEvent {i}: {event.get('title', 'N/A')}")
    else:
        print(f"⚠️  No events found - created empty {output_file}")
