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
                # Only set time from datetime if it's not midnight
                if not (dt.hour == 0 and dt.minute == 0):
                    event['time'] = dt.strftime('%I:%M %p').lstrip('0')
            except:
                pass
        
        # Always check text content for time (datetime might be midnight but text has actual time)
        time_text = time_elem.get_text(strip=True)
        if time_text and not event.get('time'):
            time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)', time_text, re.I)
            if time_match:
                event['time'] = time_match.group(0)
    
    # 2. Look for date/time in class names
    if not event.get('date') or not event.get('time'):
        date_time_elem = soup.find(class_=re.compile(r'date|time|when|schedule', re.I))
        if date_time_elem:
            text = date_time_elem.get_text(strip=True)
            
            if not event.get('date'):
                date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', text, re.I)
                if date_match:
                    event['date'] = date_match.group(0)
            
            if not event.get('time'):
                time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)', text, re.I)
                if time_match:
                    event['time'] = time_match.group(0)
    
    # 3. Search visible event details for time
    if not event.get('time'):
        # Look specifically in elements that typically contain event details
        detail_containers = soup.find_all(class_=re.compile(r'detail|info|meta|time|schedule', re.I))
        for container in detail_containers:
            text = container.get_text(strip=True)
            # Match proper time format with any kind of space (including Unicode spaces)
            # Use \s* to match any whitespace including \u202f
            time_match = re.search(r'\b([1-9]|1[0-2]):([0-5][0-9])\s*(?:AM|PM|am|pm)\b', text, re.I)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                # Validate hour and minute ranges
                if 1 <= hour <= 12 and 0 <= minute <= 59:
                    event['time'] = time_match.group(0)
                    break
    
    # 4. Last resort: look for time in visible text, but validate strictly
    if not event.get('time'):
        # Get only visible text (not scripts, styles, etc)
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        visible_text = soup.get_text(separator=' ', strip=True)
        
        # Find all potential times
        all_times = re.findall(r'\b([1-9]|1[0-2]):([0-5][0-9])\s*(?:AM|PM|am|pm)\b', visible_text, re.I)
        for hour, minute in all_times:
            hour_int = int(hour)
            minute_int = int(minute)
            # Only accept valid times
            if 1 <= hour_int <= 12 and 0 <= minute_int <= 59:
                # Format it properly
                event['time'] = f"{hour_int}:{minute:0>2} {'PM' if 'pm' in visible_text.lower() else 'AM'}"
                break
    
    # Description
    desc_elem = soup.find(class_=re.compile(r'description|content|excerpt', re.I))
    if desc_elem:
        desc_text = desc_elem.get_text(strip=True)[:300]
        # Filter out unwanted text
        unwanted_phrases = [
            'select "accept all"',
            'accept all',
            'use of cookies',
            'cookie',
            'browsing experience',
            'privacy policy',
            'terms of service',
            'join our email list',
            'get the latest news',
            'subscribe',
            'newsletter',
            'sign up',
        ]
        # Skip if description contains unwanted text
        if not any(phrase in desc_text.lower() for phrase in unwanted_phrases):
            event['description'] = desc_text
        else:
            # Try to find actual event description in a different element
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                p_text = p.get_text(strip=True)
                if len(p_text) > 50 and not any(phrase in p_text.lower() for phrase in unwanted_phrases):
                    event['description'] = p_text[:300]
                    break
    
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
