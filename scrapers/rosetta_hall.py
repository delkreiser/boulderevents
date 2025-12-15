"""
Rosetta Hall - Live Music Events Scraper
URL: https://rosettahall.com/live-music/

Scrapes events from Rosetta Hall's live music schedule page
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date


def scrape_rosetta_hall_events():
    """Scrape Rosetta Hall events using Playwright"""
    
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
            
            print("Loading Rosetta Hall live music page...")
            page.goto('https://rosettahall.com/live-music/', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Scroll to load all content
            print("Scrolling to load all events...")
            for i in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
            
            print("Parsing events...")
            html = page.content()
            events = parse_rosetta_hall_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_rosetta_hall_html(html):
    """Parse the HTML to extract event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all h2 headings with class elementor-heading-title (event titles)
    title_elements = soup.find_all('h2', class_='elementor-heading-title')
    print(f"Found {len(title_elements)} potential event titles")
    
    events = []
    today = date.today()
    
    for title_elem in title_elements:
        try:
            event = parse_rosetta_event(title_elem)
            
            if event and event.get('title'):
                # Add venue info
                event['venue'] = 'Rosetta Hall'
                event['location'] = 'Boulder'
                event['category'] = 'Music'
                event['source_url'] = 'https://rosettahall.com/live-music/'
                event['link'] = 'https://rosettahall.com/live-music/'
                event['image'] = 'rosettahall.jpg'
                event['age_restriction'] = '21+'
                event['event_type_tags'] = ['Music', 'Nightlife', 'Dance', 'DJ']
                event['venue_type_tags'] = ['Music', 'Nightlife', 'Dance', 'DJ', '21+']
                
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


def parse_rosetta_event(title_elem):
    """
    Parse a single event starting from the h2 title element
    
    Pattern:
    1. h2.elementor-heading-title = Event Title
    2. Next text-editor widget = Genre/Type
    3. Next text-editor widget = Date/Time
    """
    
    event = {}
    
    # Get title
    title = title_elem.get_text(strip=True)
    if not title or len(title) < 2:
        return None
    
    event['title'] = title
    
    # Find the parent container
    container = title_elem.find_parent('div', class_='elementor-widget-heading')
    if not container:
        return None
    
    # Find the next siblings (looking for text-editor widgets)
    current = container
    text_widgets = []
    
    # Get the next 3 siblings to find genre and date/time
    for _ in range(5):
        current = current.find_next_sibling('div')
        if current and 'elementor-widget-text-editor' in current.get('class', []):
            text_widgets.append(current)
            if len(text_widgets) >= 2:
                break
    
    # Extract genre (first text widget)
    if len(text_widgets) > 0:
        genre_elem = text_widgets[0].find('p')
        if genre_elem:
            genre = genre_elem.get_text(strip=True)
            if genre:
                event['description'] = genre
    
    # Extract date/time (second text widget)
    if len(text_widgets) > 1:
        datetime_elem = text_widgets[1].find('p')
        if datetime_elem:
            datetime_text = datetime_elem.get_text(strip=True)
            parsed = parse_date_time(datetime_text)
            if parsed:
                event.update(parsed)
    
    return event


def parse_date_time(datetime_text):
    """
    Parse date and time from text like:
    "thursday december 11th, 10 pm"
    "friday january 3rd, 9 pm"
    """
    
    result = {}
    
    # Pattern: "weekday month day, time"
    # Example: "thursday december 11th, 10 pm"
    match = re.search(
        r'(\w+day)\s+(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{1,2}(?::\d{2})?)\s*(am|pm)',
        datetime_text,
        re.IGNORECASE
    )
    
    if match:
        weekday = match.group(1)
        month = match.group(2)
        day = match.group(3)
        time_num = match.group(4)
        meridiem = match.group(5).upper()
        
        # Format time
        if ':' in time_num:
            time_str = f"{time_num} {meridiem}"
        else:
            time_str = f"{time_num}:00 {meridiem}"
        
        result['time'] = time_str
        
        # Try to create a full date
        try:
            current_year = datetime.now().year
            
            # Capitalize the month name
            month_capitalized = month.capitalize()
            
            # Start with current year
            date_str = f"{month_capitalized} {day}, {current_year}"
            parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            # If the date is in the past, use next year
            if parsed_date < date.today():
                date_str = f"{month_capitalized} {day}, {current_year + 1}"
                parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
            
            result['date'] = date_str
            result['date_obj'] = parsed_date
            
        except Exception as e:
            print(f"    Error parsing date '{month} {day}': {e}")
            # Store what we have with capitalized month
            result['date'] = f"{month.capitalize()} {day}"
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("ROSETTA HALL EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_rosetta_hall_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'rosetta_hall_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Genre: {event.get('description', 'N/A')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
