"""
Roots Music Project - Events Scraper
URL: https://www.eventbrite.com/o/roots-music-project-28110994095

Scrapes events from Roots Music Project's Eventbrite organizer page
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date
import pytz


def scrape_roots_music_events():
    """Scrape Roots Music Project events using Playwright"""
    
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
            
            print("Loading Roots Music Project Eventbrite page...")
            page.goto('https://www.eventbrite.com/cc/roots-music-project-168639', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(5000)  # Wait for JS to load events
            
            # Scroll to load all events
            print("Scrolling to load all events...")
            for i in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(2000)
            
            print("Parsing events...")
            html = page.content()
            events = parse_eventbrite_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_eventbrite_html(html):
    """Parse the Eventbrite HTML to extract event data from JSON-LD"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find JSON-LD script tags
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    print(f"Found {len(json_ld_scripts)} JSON-LD script tags")
    
    events = []
    mountain_tz = pytz.timezone('America/Denver')
    today = datetime.now(mountain_tz).date()
    seen_titles = set()  # Track titles to avoid duplicates
    
    for script in json_ld_scripts:
        try:
            json_data = json.loads(script.string)
            
            # Check if this is an ItemList with events
            if isinstance(json_data, dict) and json_data.get('@type') == 'ItemList':
                items = json_data.get('itemListElement', [])
                print(f"Found ItemList with {len(items)} items")
                
                for item_wrapper in items:
                    # Extract the actual event from the ListItem
                    item = item_wrapper.get('item', {})
                    
                    if item.get('@type') == 'Event':
                        event = parse_json_ld_event(item)
                        
                        if event and event.get('title'):
                            # Skip duplicates based on title + date
                            event_key = f"{event.get('title')}|{event.get('date', '')}"
                            if event_key in seen_titles:
                                print(f"  ✗ Skipped duplicate: {event.get('title')}")
                                continue
                            
                            seen_titles.add(event_key)
                            
                            # Add venue info
                            event['venue'] = 'Roots Music Project'
                            event['location'] = 'Boulder'
                            event['category'] = 'Music'
                            event['source_url'] = 'https://www.eventbrite.com/cc/roots-music-project-168639'
                            event['event_type_tags'] = ['Live Music']
                            event['venue_type_tags'] = ['Live Music', 'Community']
                            
                            # Default to 21+ unless specified as All Ages
                            if not event.get('age_restriction'):
                                event['age_restriction'] = '21+'
                            
                            # Use roots.jpg as fallback if no image
                            if not event.get('image'):
                                event['image'] = 'roots.jpg'
                            
                            # Filter: Only include today and future events
                            if event.get('date_obj'):
                                if event['date_obj'] >= today:
                                    del event['date_obj']  # Remove before adding to list
                                    events.append(event)
                                    print(f"  ✓ {event['title']} - {event['date']}")
                                else:
                                    print(f"  ✗ Skipped past event: {event.get('title')} - {event.get('date')}")
                            else:
                                # Skip events without parseable dates
                                print(f"  ✗ Skipped (no date): {event['title']}")
                                
        except json.JSONDecodeError as e:
            print(f"  Error parsing JSON-LD: {e}")
            continue
        except Exception as e:
            print(f"  Error processing event: {e}")
            continue
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_json_ld_event(event_data):
    """
    Parse event from JSON-LD structure
    
    Example:
    {
        "@type": "Event",
        "name": "Open Mic with Steve Koppe at Roots Music Project",
        "startDate": "2025-12-15T18:00:00-0700",
        "endDate": "2025-12-15T20:30:00-0700",
        "description": "...",
        "url": "https://www.eventbrite.com/e/...",
        "image": "https://img.evbuc.com/..."
    }
    """
    
    event = {}
    
    # Title
    if event_data.get('name'):
        event['title'] = event_data['name']
    
    # Description
    if event_data.get('description'):
        desc = event_data['description']
        # Limit to 300 characters
        if len(desc) > 300:
            desc = desc[:300] + "..."
        event['description'] = desc
        
        # Check for "All Ages" in description
        if 'all ages' in desc.lower() or 'family friendly' in desc.lower():
            event['age_restriction'] = 'All Ages'
    
    # URL
    if event_data.get('url'):
        event['link'] = event_data['url']
    
    # Image
    if event_data.get('image'):
        event['image'] = event_data['image']
    
    # Start Date/Time
    if event_data.get('startDate'):
        parsed = parse_iso_datetime(event_data['startDate'])
        if parsed:
            event.update(parsed)
    
    # End Time (just extract the time portion)
    if event_data.get('endDate'):
        try:
            end_dt = datetime.fromisoformat(event_data['endDate'])
            end_time = end_dt.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')
            
            # Add end time to existing time if we have start time
            if event.get('time'):
                event['time'] = f"{event['time']} - {end_time}"
        except:
            pass
    
    return event


def parse_iso_datetime(datetime_str):
    """
    Parse ISO datetime string like:
    "2025-12-20T19:00:00-07:00"
    """
    
    result = {}
    
    try:
        # Parse the ISO format
        dt = datetime.fromisoformat(datetime_str)
        
        # Format date: "December 20, 2025"
        result['date'] = dt.strftime('%B %d, %Y')
        
        # Format time: "7:00 PM"
        time_str = dt.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')
        result['time'] = time_str
        
        # Store date object for filtering
        result['date_obj'] = dt.date()
        
    except Exception as e:
        print(f"    Error parsing datetime '{datetime_str}': {e}")
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("ROOTS MUSIC PROJECT EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_roots_music_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'roots_music_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
            print(f"   Age: {event.get('age_restriction', 'N/A')}")
            print(f"   Image: {event.get('image', 'N/A')[:60]}...")
            print(f"   Link: {event.get('link', 'N/A')[:60]}...")
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
        all_ages = sum(1 for e in events if e.get('age_restriction') == 'All Ages')
        print(f"   All Ages events: {all_ages}")
        print(f"   21+ events: {len(events) - all_ages}")
