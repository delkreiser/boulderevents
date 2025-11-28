"""
License No 1 Event Scraper - Improved with Calendar URL
URL: https://www.license1boulderado.com/calendar

This version uses the calendar page and clicks through to individual events to get dates.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


def scrape_license_no1_calendar():
    """Scrape License No 1 events from calendar page"""
    
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
            
            print("Loading License No 1 calendar...")
            page.goto('https://www.license1boulderado.com/calendar', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Scroll down to load more events
            print("Scrolling to load all events...")
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
            
            # Click "Load More" button if it exists
            try:
                load_more = page.locator('button:has-text("Load More")').first
                for i in range(3):
                    if load_more.is_visible(timeout=2000):
                        load_more.click()
                        page.wait_for_timeout(2000)
            except:
                print("No 'Load More' button found")
            
            # Find all event links (but exclude Google Calendar links)
            print("Finding event links...")
            event_links = page.locator('a[href*="/calendar/"]').all()
            print(f"Found {len(event_links)} potential event links")
            
            seen_urls = set()
            skipped_count = 0
            
            for i, link in enumerate(event_links):
                try:
                    href = link.get_attribute('href')
                    if not href or href in seen_urls:
                        continue
                    
                    # Skip Google Calendar export links
                    if 'google.com/calendar' in href or 'action=TEMPLATE' in href:
                        skipped_count += 1
                        continue
                    
                    # Skip if it's not a proper event URL
                    if not href.startswith('/calendar/') or href == '/calendar' or href == '/calendar/':
                        continue
                    
                    seen_urls.add(href)
                    full_url = f"https://www.license1boulderado.com{href}"
                    
                    print(f"Event {len(events)+1}: Fetching...")
                    
                    # Visit event page
                    event_page = browser.new_page()
                    event_page.goto(full_url, wait_until='domcontentloaded', timeout=15000)
                    event_page.wait_for_timeout(2000)
                    
                    event_html = event_page.content()
                    event = parse_license_event_page(event_html, full_url)
                    
                    if event and event.get('title'):
                        # Skip if title is "Sign in" or other navigation text
                        if event['title'].lower() in ['sign in', 'log in', 'login', 'sign up', 'calendar']:
                            skipped_count += 1
                            event_page.close()
                            continue
                        
                        event['venue'] = 'License No 1'
                        event['category'] = 'Nightlife'
                        event['source_url'] = 'https://www.license1boulderado.com/calendar'
                        events.append(event)
                        print(f"  ✓ {event['title'][:60]}")
                    
                    event_page.close()
                    
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    continue
            
            print(f"\nSkipped {skipped_count} non-event links (Google Calendar exports, etc.)")
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_license_event_page(html, url):
    """Parse individual event page for details"""
    
    soup = BeautifulSoup(html, 'html.parser')
    event = {'link': url}
    
    # Title
    title_elem = soup.find(['h1', 'h2'], class_=re.compile(r'title|event', re.I))
    if not title_elem:
        title_elem = soup.find('h1')
    if title_elem:
        event['title'] = title_elem.get_text(strip=True)
    
    # Date/Time - look in multiple places
    # 1. Look for datetime attribute in time element
    time_elem = soup.find('time')
    if time_elem:
        datetime_attr = time_elem.get('datetime')
        if datetime_attr:
            try:
                dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                event['date'] = dt.strftime('%B %d, %Y')
                event['time'] = dt.strftime('%I:%M %p')
            except:
                # Fallback to text content
                time_text = time_elem.get_text(strip=True)
                if time_text:
                    # Try to separate date and time
                    date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', time_text, re.I)
                    if date_match:
                        event['date'] = date_match.group(0)
                    
                    time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)', time_text, re.I)
                    if time_match:
                        event['time'] = time_match.group(0)
    
    # 2. Look for date/time in class names
    if not event.get('date'):
        date_time_elem = soup.find(class_=re.compile(r'date|time|when', re.I))
        if date_time_elem:
            text = date_time_elem.get_text(strip=True)
            
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', text, re.I)
            if date_match:
                event['date'] = date_match.group(0)
            
            if not event.get('time'):
                time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)', text, re.I)
                if time_match:
                    event['time'] = time_match.group(0)
    
    # Description
    desc_elem = soup.find(class_=re.compile(r'description|content|excerpt', re.I))
    if desc_elem:
        event['description'] = desc_elem.get_text(strip=True)[:300]
    
    # Image
    img_elem = soup.find('img')
    if img_elem:
        img_src = img_elem.get('src') or img_elem.get('data-src')
        if img_src and 'http' in img_src:
            event['image'] = img_src
    
    return event if event.get('title') else None


if __name__ == "__main__":
    print("License No 1 Calendar Scraper")
    print("=" * 60)
    
    events = scrape_license_no1_calendar()
    
    print(f"\n{'='*60}")
    print(f"Found {len(events)} events")
    print(f"{'='*60}")
    
    # Save to JSON
    with open('license_no1_events.json', 'w') as f:
        json.dump(events, f, indent=2)
    
    if events:
        print(f"✅ Saved to license_no1_events.json\n")
        for i, event in enumerate(events[:5], 1):
            print(f"Event {i}:")
            print(f"  Title: {event.get('title')}")
            print(f"  Date: {event.get('date', 'N/A')}")
            print(f"  Time: {event.get('time', 'N/A')}\n")
    else:
        print("⚠️  No events found - created empty JSON")
