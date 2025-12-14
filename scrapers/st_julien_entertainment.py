"""
St Julien Hotel & Spa - Entertainment Events Scraper
URL: https://stjulien.com/boulder-colorado-events/month/?tribe_eventcategory%5B0%5D=83

This scraper extracts entertainment events from St Julien's JSON-LD structured data.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date


def scrape_st_julien_events():
    """Scrape St Julien events using Playwright"""
    
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
            page.goto('https://stjulien.com/boulder-colorado-events/month/?tribe_eventcategory%5B0%5D=83', 
                     wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Scroll to load all events
            print("Scrolling to load all events...")
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1500)
            
            print("Parsing events...")
            html = page.content()
            events = parse_st_julien_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_st_julien_html(html):
    """Parse the HTML to extract JSON-LD event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all script tags with type="application/ld+json"
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    print(f"Found {len(json_ld_scripts)} JSON-LD script tags")
    
    events = []
    today = date.today()
    
    for script in json_ld_scripts:
        try:
            # Parse the JSON content
            json_data = json.loads(script.string)
            
            # Check if this is an Event type
            if isinstance(json_data, dict) and json_data.get('@type') == 'Event':
                event = parse_event_json(json_data)
                
                if event and event.get('title'):
                    # Filter: Only include today and future events
                    if event.get('date_obj'):
                        if event['date_obj'] >= today:
                            # Add venue info
                            event['venue'] = 'St Julien Hotel & Spa'
                            event['location'] = 'Boulder'
                            event['category'] = 'Entertainment'
                            event['source_url'] = 'https://stjulien.com/boulder-colorado-events/month/?tribe_eventcategory%5B0%5D=83'
                            event['event_type_tags'] = ['Entertainment', 'Hotel Events']
                            event['venue_type_tags'] = ['Hotel', 'Upscale']
                            event['image'] = 'stjulien.jpg'  # Default image
                            
                            del event['date_obj']  # Remove before adding to list
                            events.append(event)
                            print(f"  ✓ {event['title']} - {event['date']}")
                        else:
                            print(f"  ✗ Skipped past event: {event.get('title')}")
            
        except json.JSONDecodeError as e:
            print(f"  Error parsing JSON-LD: {e}")
            continue
        except Exception as e:
            print(f"  Error processing event: {e}")
            continue
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_event_json(json_data):
    """
    Parse event data from JSON-LD structure
    
    Example structure:
    {
        "@type": "Event",
        "name": "Ron Legualt's Charlie Brown Goes to the Nutcracker",
        "description": "",
        "url": "https://stjulien.com/event/...",
        "startDate": "2025-12-06T18:00:00-07:00",
        "endDate": "2025-12-06T21:00:00-07:00",
        "location": {...}
    }
    """
    
    event = {}
    
    # Title
    if json_data.get('name'):
        # Unescape any escaped characters (like \')
        title = json_data['name'].replace("\\'", "'").replace('\\"', '"')
        event['title'] = title
    
    # Description
    if json_data.get('description'):
        desc = json_data['description'].replace("\\'", "'").replace('\\"', '"')
        if desc and desc.strip():
            event['description'] = desc
    
    # URL
    if json_data.get('url'):
        event['link'] = json_data['url']
    
    # Start Date and Time
    if json_data.get('startDate'):
        start_datetime_str = json_data['startDate']
        try:
            # Parse ISO format: "2025-12-06T18:00:00-07:00"
            start_dt = datetime.fromisoformat(start_datetime_str)
            
            # Format date: "December 6, 2025"
            event['date'] = start_dt.strftime('%B %d, %Y')
            
            # Format start time: "6:00 PM"
            start_time = start_dt.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')
            event['time_start'] = start_time
            
            # Store date object for filtering
            event['date_obj'] = start_dt.date()
            
        except Exception as e:
            print(f"    Error parsing start date: {e}")
    
    # End Time
    if json_data.get('endDate'):
        end_datetime_str = json_data['endDate']
        try:
            # Parse ISO format
            end_dt = datetime.fromisoformat(end_datetime_str)
            
            # Format end time: "9:00 PM"
            end_time = end_dt.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')
            event['time_end'] = end_time
            
        except Exception as e:
            print(f"    Error parsing end date: {e}")
    
    # Create combined time field
    if event.get('time_start') and event.get('time_end'):
        event['time'] = f"{event['time_start']} - {event['time_end']}"
    elif event.get('time_start'):
        event['time'] = event['time_start']
    
    # Location details (optional - for additional info)
    if json_data.get('location'):
        location = json_data['location']
        if isinstance(location, dict) and location.get('name'):
            # Store venue location name (e.g., "The Great Room Lobby")
            event['venue_location'] = location['name']
    
    return event


if __name__ == "__main__":
    print("=" * 70)
    print("ST JULIEN HOTEL & SPA EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_st_julien_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'st_julien_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
            if event.get('venue_location'):
                print(f"   Location: {event.get('venue_location')}")
            print(f"   Link: {event.get('link', 'N/A')[:60]}...")
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
