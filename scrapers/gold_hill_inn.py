"""
Gold Hill Inn - Music Events Scraper
URL: https://www.goldhillinn.com/music/

Scrapes music events from Gold Hill Inn's music schedule page
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date


def scrape_gold_hill_inn_events():
    """Scrape Gold Hill Inn events using Playwright"""
    
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
            
            print("Loading Gold Hill Inn music page...")
            try:
                page.goto('https://www.goldhillinn.com/music/', 
                         wait_until='domcontentloaded', timeout=45000)  # Increased to 45s
                page.wait_for_timeout(3000)
            except Exception as nav_error:
                print(f"Navigation error (trying to continue anyway): {nav_error}")
                # Try to get whatever content is there
                page.wait_for_timeout(2000)
            
            # Scroll to load all content
            print("Scrolling to load all events...")
            for i in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
            
            print("Parsing events...")
            html = page.content()
            events = parse_gold_hill_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_gold_hill_html(html):
    """Parse the HTML to extract event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all event containers with class "showcontainer"
    event_containers = soup.find_all('div', class_='showcontainer')
    print(f"Found {len(event_containers)} event containers")
    
    events = []
    today = date.today()
    
    for container in event_containers:
        try:
            event = parse_gold_hill_event(container)
            
            if event and event.get('title'):
                # Add venue info
                event['venue'] = 'Gold Hill Inn'
                event['location'] = 'Gold Hill'
                event['category'] = 'Music'
                event['source_url'] = 'https://www.goldhillinn.com/music/'
                event['link'] = 'https://www.goldhillinn.com/music/'
                event['image'] = 'goldhillinn.jpg'
                event['age_restriction'] = '21+'
                event['event_type_tags'] = ['Live Music']
                event['venue_type_tags'] = ['Live Music', 'Restaurant', 'Historic']
                
                # Filter: Only include today and future events
                if event.get('date_obj'):
                    if event['date_obj'] >= today:
                        del event['date_obj']  # Remove before adding to list
                        events.append(event)
                        print(f"  ✓ {event['title']} - {event['date']}")
                    else:
                        print(f"  ✗ Skipped past event: {event.get('title')} - {event.get('date')}")
                else:
                    # Skip events where we can't parse the date
                    print(f"  ✗ Skipped (no date): {event['title']}")
                    
        except Exception as e:
            print(f"  Error parsing event: {e}")
            continue
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_gold_hill_event(container):
    """
    Parse a single event from a showcontainer div
    
    Structure:
    - li.showdate: "Sunday, December 14, 2025 | 07:30 pm"
    - li.artistname: "Moors & McCumber"
    - Next li: Genre "(Folk/Americana)"
    - p: Description
    """
    
    event = {}
    
    # Find the ul element that contains the event details
    ul = container.find('ul')
    if not ul:
        return None
    
    list_items = ul.find_all('li')
    
    # Extract date and time from first li with class "showdate"
    showdate_li = ul.find('li', class_='showdate')
    if showdate_li:
        datetime_text = showdate_li.get_text(strip=True)
        parsed_datetime = parse_date_time(datetime_text)
        if parsed_datetime:
            event.update(parsed_datetime)
    
    # Extract artist name from li with class "artistname"
    artistname_li = ul.find('li', class_='artistname')
    if artistname_li:
        artist_name = artistname_li.get_text(strip=True)
        event['title'] = artist_name
    
    # Extract genre (usually in parentheses in a li after artist name)
    for li in list_items:
        text = li.get_text(strip=True)
        # Look for genre in parentheses like "(Folk/Americana)"
        if text.startswith('(') and text.endswith(')'):
            genre = text.strip('()')
            event['genre'] = genre
            break
    
    # Extract description from p tag
    desc_p = container.find('p')
    if desc_p:
        # Get text but limit length
        desc_text = desc_p.get_text(strip=True)
        # Remove HTML entities and extra whitespace
        desc_text = re.sub(r'\s+', ' ', desc_text)
        # Limit to first 300 characters
        if len(desc_text) > 300:
            desc_text = desc_text[:300] + "..."
        event['description'] = desc_text
    
    # Combine title with genre if available
    if event.get('genre'):
        event['description'] = f"{event.get('genre')} - {event.get('description', '')}" if event.get('description') else event.get('genre')
    
    return event


def parse_date_time(datetime_text):
    """
    Parse date and time from text like:
    "Sunday, December 14, 2025 | 07:30 pm"
    "Friday, January 3, 2026 | 08:00 pm"
    """
    
    result = {}
    
    # Pattern: "Weekday, Month Day, Year | HH:MM pm/am"
    match = re.search(
        r'(\w+day),\s+(\w+)\s+(\d{1,2}),\s+(\d{4})\s*\|\s*(\d{1,2}):(\d{2})\s*(am|pm)',
        datetime_text,
        re.IGNORECASE
    )
    
    if match:
        weekday = match.group(1)
        month = match.group(2)
        day = match.group(3)
        year = match.group(4)
        hour = match.group(5)
        minute = match.group(6)
        meridiem = match.group(7).upper()
        
        # Format time (remove leading zero from hour if present)
        time_str = f"{int(hour)}:{minute} {meridiem}"
        result['time'] = time_str
        
        # Create full date
        try:
            date_str = f"{month} {day}, {year}"
            parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            result['date'] = date_str
            result['date_obj'] = parsed_date
            
        except Exception as e:
            print(f"    Error parsing date '{month} {day}, {year}': {e}")
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("GOLD HILL INN EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_gold_hill_inn_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'gold_hill_inn_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Genre: {event.get('genre', 'N/A')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
