"""
Bricks on Main - Events Scraper
URL: https://www.bricksretail.com/events-calendar

Scrapes events from Bricks on Main's events calendar in Longmont
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
import pytz
import re


def scrape_bricks_events():
    """Scrape Bricks on Main events using requests"""
    
    events = []
    
    try:
        print("Fetching Bricks on Main events page...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(
            'https://www.bricksretail.com/events-calendar',
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        print("Parsing events...")
        events = parse_bricks_html(response.text)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_bricks_html(html):
    """Parse the HTML to extract event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the "Upcoming Events" list section
    # Events are in <li> elements with links to /event-details/
    event_links = soup.find_all('a', href=re.compile(r'/event-details/'))
    
    print(f"Found {len(event_links)} event links")
    
    events = []
    mountain_tz = pytz.timezone('America/Denver')
    today = datetime.now(mountain_tz).date()
    seen_titles = set()  # Avoid duplicates
    
    for link in event_links:
        try:
            # Get the container with event info
            event_container = link.find_parent('li')
            if not event_container:
                continue
            
            event = parse_bricks_event_item(link, event_container)
            
            if event and event.get('title'):
                # Check for duplicates
                title_key = event['title'].lower().strip()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)
                
                # Add venue info
                event['venue'] = 'Bricks on Main'
                event['location'] = 'Longmont'
                event['category'] = 'Music'
                event['source_url'] = 'https://www.bricksretail.com/events-calendar'
                
                # Add tags based on event type
                if 'open mic' in event['title'].lower():
                    event['event_type_tags'] = ['Open Mic', 'Music', 'Community']
                elif 'karaoke' in event['title'].lower():
                    event['event_type_tags'] = ['Karaoke', 'Music', 'Entertainment']
                elif 'jazz' in event['title'].lower() or 'jazz' in event.get('description', '').lower():
                    event['event_type_tags'] = ['Jazz', 'Live Music']
                elif 'comedy' in event['title'].lower() or 'comedy' in event.get('description', '').lower():
                    event['event_type_tags'] = ['Comedy', 'Entertainment']
                elif 'market' in event['title'].lower():
                    event['event_type_tags'] = ['Market', 'Community', 'Family Friendly']
                else:
                    event['event_type_tags'] = ['Live Music', 'Entertainment']
                
                event['venue_type_tags'] = ['Music Venue', 'Bar', 'Restaurant']
                
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


def parse_bricks_event_item(link, container):
    """Parse a single event from the list view"""
    
    event = {}
    
    # Get event URL
    href = link.get('href', '')
    if href:
        if not href.startswith('http'):
            href = f"https://www.bricksretail.com{href}"
        event['link'] = href
    
    # Get all text from container
    all_text = container.get_text(separator='\n', strip=True)
    lines = [l.strip() for l in all_text.split('\n') if l.strip()]
    
    # Find title - it's usually in a line with " / " separators
    # Format: "Event Name / Location / Venue"
    title_text = None
    for line in lines:
        # Look for lines with " / " that aren't dates
        if ' / ' in line and not re.search(r'\d{1,2}:\d{2}\s+[AP]M', line):
            # Split by " / " and take the first part
            parts = [p.strip() for p in line.split(' / ')]
            # Filter out location names
            for part in parts:
                if part.lower() not in ['bricks on main', 'miss krissy\'s bistro', 'longmont', '']:
                    title_text = part
                    break
            if title_text:
                break
    
    # If no title found with " / ", try other methods
    if not title_text:
        for line in lines:
            # Skip known non-title lines
            if (line.lower() in ['learn more', 'multiple dates', 'longmont', 'bricks on main'] 
                or re.search(r'[A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4}', line)  # Date pattern
                or re.search(r'\d{1,2}:\d{2}\s+[AP]M', line)  # Time pattern
                or re.search(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),', line)  # Day of week
                or len(line) < 3 or len(line) > 200):
                continue
            title_text = line
            break
    
    if title_text and len(title_text) < 200:
        # Clean up trailing slash and whitespace
        title_text = re.sub(r'\s*/\s*$', '', title_text).strip()
        event['title'] = title_text
    else:
        return None
    
    # Get all text from container to parse date and description
    all_text = container.get_text(separator='\n', strip=True)
    lines = [l.strip() for l in all_text.split('\n') if l.strip()]
    
    # Date - Look for pattern like "Dec 16, 2025, 6:00 PM – 8:00 PM"
    for line in lines:
        if re.search(r'[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}', line):
            parsed = parse_date_time(line)
            if parsed:
                event.update(parsed)
                break
    
    # Description - Get longer text blocks
    for line in lines:
        if len(line) > 40 and line not in [event.get('title', ''), event.get('date', '')]:
            desc = line
            if len(desc) > 300:
                desc = desc[:300] + "..."
            event['description'] = desc
            break
    
    # Image - Look for img tags in container
    img = container.find('img')
    if img:
        # Try to get the full-resolution image
        # Wix uses data-pin-url or look for URLs without blur parameters
        img_url = None
        
        # Check for data-pin-url (often has full res)
        if img.get('data-pin-url'):
            img_url = img['data-pin-url']
        # Check src
        elif img.get('src'):
            img_url = img['src']
        # Check data-src
        elif img.get('data-src'):
            img_url = img['data-src']
        
        if img_url:
            # Remove Wix blur parameters and get high-res version
            # Remove blur_2, blur_3, etc.
            img_url = re.sub(r',blur_\d+', '', img_url)
            # Remove usm parameters that reduce quality
            img_url = re.sub(r',usm_[\d.]+_[\d.]+_[\d.]+', '', img_url)
            # Change size parameters to get larger image
            # Replace w_56 or w_147 with w_400 for better quality
            img_url = re.sub(r'/fill/w_\d+,h_\d+', '/fill/w_400,h_400', img_url)
            # Remove /v1/fill entirely to get original
            # img_url = re.sub(r'/v1/fill/[^/]+/', '/v1/', img_url)
            
            event['image'] = img_url
    
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
