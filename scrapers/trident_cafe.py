"""
Trident Booksellers & Cafe Event Scraper
URL: https://www.tridentcafe.com/events

Scrapes events from Trident Cafe's events page with proper date parsing and filtering.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
import pytz
import re


def scrape_trident_events():
    """Scrape events from Trident Cafe using Playwright"""
    
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
            
            print("Loading Trident events page...")
            page.goto('https://www.tridentcafe.com/events', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Scroll to load all content
            print("Scrolling to load all events...")
            for i in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
            
            print("Parsing events...")
            html = page.content()
            events = parse_trident_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_trident_html(html):
    """Parse the HTML to extract event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try multiple selectors for Squarespace event lists
    event_selectors = [
        'li.eventlist-event',
        'div.eventlist-event',
        'article.eventlist-event',
        '.sqs-block-summary-v2 .summary-item',
        'div.summary-item',
    ]
    
    event_elements = []
    for selector in event_selectors:
        found = soup.select(selector)
        if found:
            print(f"Found {len(found)} events using selector: {selector}")
            event_elements = found
            break
    
    print(f"Total event elements found: {len(event_elements)}")
    
    events = []
    mountain_tz = pytz.timezone('America/Denver')
    today = datetime.now(mountain_tz).date()
    
    for element in event_elements:
        try:
            event = parse_trident_event(element)
            
            if event and event.get('title'):
                # Add venue info
                event['venue'] = 'Trident Booksellers & Cafe'
                event['location'] = 'Boulder'
                event['category'] = 'Books & Literary'
                event['source_url'] = 'https://www.tridentcafe.com/events'
                event['image'] = 'trident.jpg'
                event['event_type_tags'] = ['Live Music', 'Books', 'Community']
                event['venue_type_tags'] = ['Cafe', 'Bookstore', 'Music Venue']
                
                # Filter: Only include today and future events
                if event.get('date_obj'):
                    if event['date_obj'] >= today:
                        del event['date_obj']  # Remove before adding to list
                        events.append(event)
                        print(f"  ✓ {event['title']} - {event.get('date', 'N/A')}")
                    else:
                        print(f"  ✗ Skipped past event: {event.get('title')} - {event.get('date')}")
                else:
                    # Skip events without parseable dates
                    print(f"  ✗ Skipped (no date): {event.get('title', 'Unknown')}")
                    
        except Exception as e:
            print(f"  Error parsing event: {e}")
            continue
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_trident_event(element):
    """Parse a single event element from Trident's Squarespace site"""
    
    event = {}
    
    # Title - look for h1 class="eventlist-title"
    title_elem = element.find(class_=re.compile(r'eventlist-title|summary-title', re.I))
    if not title_elem:
        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
    
    if title_elem:
        title = title_elem.get_text(strip=True)
        # Validate title - skip if it's actually a description
        if title and len(title) < 200 and not title.startswith('http'):
            event['title'] = title
        else:
            return None
    else:
        return None
    
    # Link
    link_elem = element.find('a', href=True)
    if link_elem:
        link = link_elem.get('href', '')
        if link and not link.startswith('http'):
            link = f"https://www.tridentcafe.com{link}"
        event['link'] = link
    
    # Date/Time - look for eventlist-datetag or eventlist-meta-date
    date_elem = element.find(class_=re.compile(r'eventlist-datetag|eventlist-meta-date|summary-metadata-item--date', re.I))
    if date_elem:
        date_text = date_elem.get_text(strip=True)
        parsed = parse_date_time(date_text)
        if parsed:
            event.update(parsed)
    
    # Time - separate time element
    time_elem = element.find(class_=re.compile(r'eventlist-meta-time|event-time-localized', re.I))
    if time_elem and not event.get('time'):
        event['time'] = time_elem.get_text(strip=True)
    
    # Description
    desc_elem = element.find(class_=re.compile(r'eventlist-description|summary-excerpt', re.I))
    if not desc_elem:
        desc_elem = element.find('p')
    
    if desc_elem:
        desc = desc_elem.get_text(strip=True)
        # Limit description length
        if len(desc) > 300:
            desc = desc[:300] + "..."
        event['description'] = desc
    
    return event


def parse_date_time(date_text):
    """
    Parse date/time from Squarespace format
    
    Examples:
    "Dec142:00 PM14:00" 
    "Dec 14 2:00 PM"
    "December 14, 2025"
    """
    
    result = {}
    
    try:
        # Clean up the text
        date_text = date_text.strip()
        
        # Try to extract date parts using regex
        # Pattern 1: "Dec142:00 PM14:00" or "Dec14"
        match = re.search(r'([A-Z][a-z]{2,8})\s*(\d{1,2})', date_text, re.I)
        if match:
            month_str = match.group(1)
            day_str = match.group(2)
            
            # Map month abbreviations
            month_map = {
                'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
                'Apr': 'April', 'May': 'May', 'Jun': 'June',
                'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
                'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
            }
            
            month_full = month_map.get(month_str[:3], month_str)
            
            # Get current year and determine if we need next year
            mountain_tz = pytz.timezone('America/Denver')
            current_year = datetime.now(mountain_tz).year
            mountain_tz = pytz.timezone('America/Denver')
            current_date = datetime.now(mountain_tz).date()
            
            date_str = f"{month_full} {day_str}, {current_year}"
            parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            # If date is in the past, try next year
            if parsed_date < current_date:
                date_str = f"{month_full} {day_str}, {current_year + 1}"
                parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            result['date'] = date_str
            result['date_obj'] = parsed_date
        
        # Try to extract time
        # Strategy: Trident includes both 12-hour and 24-hour times like "2:00 PM14:00"
        # Use the 24-hour time at the end for accuracy
        time_match_24 = re.search(r'(\d{2}):(\d{2})$', date_text.strip())
        if time_match_24:
            hour_int = int(time_match_24.group(1))
            minute = time_match_24.group(2)
            
            # Convert 24-hour to 12-hour
            if hour_int == 0:
                result['time'] = f"12:{minute} AM"
            elif hour_int < 12:
                result['time'] = f"{hour_int}:{minute} AM"
            elif hour_int == 12:
                result['time'] = f"12:{minute} PM"
            else:
                result['time'] = f"{hour_int - 12}:{minute} PM"
        else:
            # Fall back to AM/PM time search
            time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', date_text, re.I)
            if time_match:
                hour = time_match.group(1)
                minute = time_match.group(2)
                meridiem = time_match.group(3)
                result['time'] = f"{hour}:{minute} {meridiem.upper()}"
        
    except Exception as e:
        print(f"    Error parsing date '{date_text}': {e}")
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("TRIDENT BOOKSELLERS & CAFE EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_trident_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'trident_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
            if event.get('description'):
                desc = event['description'][:60] + "..." if len(event['description']) > 60 else event['description']
                print(f"   Description: {desc}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
