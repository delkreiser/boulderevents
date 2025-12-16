"""
Bricks on Main - Events Scraper
URL: https://www.bricksretail.com/events-calendar

Scrapes events from Bricks on Main's events calendar in Longmont
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
import re


def scrape_bricks_events():
    """Scrape Bricks on Main events using Playwright"""
    
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
            
            print("Loading Bricks on Main events page...")
            page.goto('https://www.bricksretail.com/events-calendar', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(5000)  # Wait for events to load
            
            # Scroll to load all content
            print("Scrolling to load all events...")
            for i in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1500)
            
            print("Parsing events...")
            html = page.content()
            events = parse_bricks_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_bricks_html(html):
    """Parse the HTML to extract event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all event items using data-hook attributes
    event_elements = soup.find_all(attrs={'data-hook': 'ev-list-item'})
    
    if not event_elements:
        # Try alternative selector
        event_elements = soup.find_all('li', class_=re.compile(r'event', re.I))
    
    print(f"Found {len(event_elements)} event elements")
    
    events = []
    today = date.today()
    
    for element in event_elements:
        try:
            event = parse_bricks_event(element)
            
            if event and event.get('title'):
                # Add venue info
                event['venue'] = 'Bricks on Main'
                event['location'] = 'Longmont'
                event['category'] = 'Community'
                event['source_url'] = 'https://www.bricksretail.com/events-calendar'
                event['event_type_tags'] = ['Community', 'Entertainment']
                event['venue_type_tags'] = ['Community', 'Retail', 'Entertainment']
                
                # Default image if none found
                if not event.get('image'):
                    event['image'] = 'bricks.jpg'
                
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


def parse_bricks_event(element):
    """Parse a single event element from Bricks on Main"""
    
    event = {}
    
    # Title - data-hook="ev-list-item-title"
    title_elem = element.find(attrs={'data-hook': 'ev-list-item-title'})
    if title_elem:
        title = title_elem.get_text(strip=True)
        if title and len(title) < 200:
            event['title'] = title
        else:
            return None
    else:
        return None
    
    # Date - data-hook="date"
    # Format: "Jan 30, 2026, 6:00 PM – 9:00 PM"
    date_elem = element.find(attrs={'data-hook': 'date'})
    if date_elem:
        date_text = date_elem.get_text(strip=True)
        parsed = parse_date_time(date_text)
        if parsed:
            event.update(parsed)
    
    # Link - data-hook="ev-rsvp-button"
    link_elem = element.find(attrs={'data-hook': 'ev-rsvp-button'})
    if link_elem and link_elem.get('href'):
        link = link_elem['href']
        if link and not link.startswith('http'):
            link = f"https://www.bricksretail.com{link}"
        event['link'] = link
    
    # Image - data-hook="image-background"
    img_elem = element.find(attrs={'data-hook': 'image-background'})
    if img_elem:
        # Check for background-image style
        style = img_elem.get('style', '')
        if 'background-image' in style:
            # Extract URL from background-image: url(...)
            match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
            if match:
                img_url = match.group(1)
                event['image'] = img_url
        
        # Also check for src attribute on img tags inside
        img_tag = img_elem.find('img')
        if img_tag and img_tag.get('src'):
            event['image'] = img_tag['src']
    
    # Description - try to find any description text
    desc_elem = element.find(attrs={'data-hook': re.compile(r'description|excerpt', re.I)})
    if not desc_elem:
        # Try finding any paragraph
        desc_elem = element.find('p')
    
    if desc_elem:
        desc = desc_elem.get_text(strip=True)
        if len(desc) > 300:
            desc = desc[:300] + "..."
        event['description'] = desc
    
    return event


def parse_date_time(date_text):
    """
    Parse date/time from format like:
    "Jan 30, 2026, 6:00 PM – 9:00 PM"
    "Dec 15, 2025, 7:00 PM"
    """
    
    result = {}
    
    try:
        # Clean up the text
        date_text = date_text.strip()
        
        # Pattern: "Month Day, Year, Time – Time"
        match = re.search(
            r'([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4}),\s+(\d{1,2}:\d{2}\s+[AP]M)(?:\s*[–—-]\s*(\d{1,2}:\d{2}\s+[AP]M))?',
            date_text,
            re.IGNORECASE
        )
        
        if match:
            month_str = match.group(1)
            day_str = match.group(2)
            year_str = match.group(3)
            start_time = match.group(4)
            end_time = match.group(5)
            
            # Map month abbreviations
            month_map = {
                'Jan': 'January', 'Feb': 'February', 'Mar': 'March',
                'Apr': 'April', 'May': 'May', 'Jun': 'June',
                'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
                'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
            }
            
            month_full = month_map.get(month_str, month_str)
            
            # Create date string
            date_str = f"{month_full} {day_str}, {year_str}"
            parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            result['date'] = date_str
            result['date_obj'] = parsed_date
            
            # Format time
            if end_time:
                result['time'] = f"{start_time} - {end_time}"
            else:
                result['time'] = start_time
        
    except Exception as e:
        print(f"    Error parsing date '{date_text}': {e}")
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("BRICKS ON MAIN EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_bricks_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'bricks_events.json'
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
