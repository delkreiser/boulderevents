"""
Velvet Elk Lounge Event Scraper
URL: https://www.velvetelklounge.com/events/

This scraper extracts music events from Velvet Elk Lounge's events page.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date
import pytz


def scrape_velvet_elk_events():
    """Scrape events from Velvet Elk Lounge using Playwright"""
    
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
            
            print("Loading Velvet Elk events page...")
            page.goto('https://www.velvetelklounge.com/events/', 
                     wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            print("Parsing events...")
            html = page.content()
            events = parse_velvet_elk_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_velvet_elk_html(html):
    """Parse the HTML to extract all events"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all event cards with aria-label
    event_links = soup.find_all('a', class_='card__btn', attrs={'aria-label': True})
    print(f"Found {len(event_links)} event cards")
    
    events = []
    mountain_tz = pytz.timezone('America/Denver')
    today = datetime.now(mountain_tz).date()
    
    for link in event_links:
        aria_label = link.get('aria-label', '')
        href = link.get('href', '')
        
        if not aria_label:
            continue
        
        # Parse aria-label which has format: "Month Day, Event Title"
        # Example: "December 27, Rapidgrass"
        event = parse_aria_label(aria_label, href)
        
        if event and event.get('title'):
            # Get image from the card
            img_div = link.find('div', class_='card__image')
            if img_div:
                style = img_div.get('style', '')
                # Extract URL from background-image style
                img_match = re.search(r"url\('([^']+)'\)", style)
                if img_match:
                    event['image'] = img_match.group(1)
            
            # Add venue info
            event['venue'] = 'Velvet Elk Lounge'
            event['location'] = 'Boulder'
            event['category'] = 'Music'
            event['source_url'] = 'https://www.velvetelklounge.com/events/'
            event['event_type_tags'] = ['Live Music', 'Nightlife']
            event['venue_type_tags'] = ['Bar', 'Music Venue', 'Nightlife']
            
            # Build full link
            if href and not href.startswith('http'):
                event['link'] = f"https://www.velvetelklounge.com{href}"
            else:
                event['link'] = href
            
            # Filter: Only include today and future events
            if event.get('date_obj'):
                if event['date_obj'] >= today:
                    del event['date_obj']  # Remove before adding to list
                    events.append(event)
                    print(f"  ✓ {event['title']} - {event['date']}")
                else:
                    print(f"  ✗ Skipped past event: {event['title']}")
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_aria_label(aria_label, href=''):
    """
    Parse aria-label to extract date and title
    Format: "Month Day, Event Title" or "Month Day(th/st/nd/rd), Event Title"
    Examples: 
    - "December 27, Rapidgrass"
    - "December 18, LatkePalooza II: A Chanukah Celebration!"
    """
    
    event = {}
    
    # Pattern: "Month Day(optional suffix), Title"
    match = re.match(r'([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,\s*(.+)', aria_label, re.IGNORECASE)
    
    if match:
        month = match.group(1)
        day = match.group(2)
        title = match.group(3).strip()
        
        event['title'] = title
        event['date'] = f"{month} {day}"
        
        # Try to create a full date for filtering
        try:
            # Add current year
            mountain_tz = pytz.timezone('America/Denver')
            current_year = datetime.now(mountain_tz).year
            date_str = f"{month} {day}, {current_year}"
            parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            # If the date is in the past, try next year
            if parsed_date < datetime.now(mountain_tz).date():
                date_str = f"{month} {day}, {current_year + 1}"
                parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            event['date'] = date_str
            event['date_obj'] = parsed_date
        except:
            # If parsing fails, just use what we have
            pass
    
    return event


if __name__ == "__main__":
    print("=" * 70)
    print("VELVET ELK LOUNGE EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_velvet_elk_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'velvet_elk_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Link: {event.get('link', 'N/A')[:60]}...")
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
