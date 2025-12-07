"""
Mountain Sun Pub Event Scraper - Hybrid Approach
URL: https://www.mountainsunpub.com/events/

This scraper combines:
1. Static recurring events (manually maintained)
2. Dynamic scraping of special one-off events from page text
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


# ============================================================
# STATIC RECURRING EVENTS - Update these manually as needed
# ============================================================

RECURRING_EVENTS = [
    {
        'title': 'Vinyl Night',
        'venue': 'Vine Street Pub',
        'location': 'Denver',
        'recurring': 'Every Monday',
        'time': '5:00 PM - 9:00 PM',
        'description': 'Join us every Monday for an intentional listening experience. Share your favorite tunes and discover new music while enjoying house-made beer and snacks. Bring in a record from your collection and in exchange, we will play it for the pub and give you a free beer to sip on while you sit back and listen.',
        'link': 'https://www.mountainsunpub.com/events/',
        'image': 'https://raw.githubusercontent.com/delkreiser/boulderevents/main/images/vinestreetpub.jpg',
        'source_url': 'https://www.mountainsunpub.com/events/',
    },
    {
        'title': 'Music Night',
        'venue': 'Vine Street Pub',
        'location': 'Denver',
        'recurring': 'Every Saturday',
        'time': '8:00 PM',
        'description': 'In collaboration with Stir Fry Sessions, a Denver based artist collective, we showcase local talent while offering a community space to dance and mingle.',
        'link': 'https://www.mountainsunpub.com/events/',
        'image': 'https://raw.githubusercontent.com/delkreiser/boulderevents/main/images/vinestreetpub.jpg',
        'source_url': 'https://www.mountainsunpub.com/events/',
    },
    {
        'title': 'Game Night',
        'venue': 'Longs Peak Pub',
        'location': 'Longmont',
        'recurring': 'Every Monday',
        'time': '5:00 PM - 10:00 PM',
        'description': 'Monday Nights from 5pm-10pm. Free Fries and Happy Hour prices for all game tables!',
        'link': 'https://www.mountainsunpub.com/events/',
        'image': 'https://raw.githubusercontent.com/delkreiser/boulderevents/main/images/longspeakpub.jpg',
        'source_url': 'https://www.mountainsunpub.com/events/',
    },
    {
        'title': 'The Bluegrass Pick',
        'venue': 'Southern Sun Pub',
        'location': 'Boulder',
        'recurring': 'Every Thursday',
        'time': '7:30 PM - 9:30 PM',
        'description': 'The Bluegrass Pick is back, hosted by Max Kabat of Bowregard! Join us every Thursday from 7:30pm – 9:30pm for free live music, toe-tappin\' energy, and the cozy pub vibe you already love.',
        'link': 'https://www.mountainsunpub.com/events/',
        'image': 'https://raw.githubusercontent.com/delkreiser/boulderevents/main/images/southernsunpub.jpg',
        'source_url': 'https://www.mountainsunpub.com/events/',
    },
    {
        'title': 'Live Music',
        'venue': 'Mountain Sun Pub',
        'location': 'Boulder',
        'recurring': 'Friday Nights',
        'time': '9:00 PM - 12:00 AM',
        'description': 'Join us every Friday night for live music at Mountain Sun Pub on Pearl Street.',
        'link': 'https://www.mountainsunpub.com/events/',
        'image': 'https://raw.githubusercontent.com/delkreiser/boulderevents/main/images/mountainsunpub.jpg',
        'source_url': 'https://www.mountainsunpub.com/events/',
    },
]


def scrape_mountain_sun_events():
    """Scrape Mountain Sun events - combines static recurring + dynamic special events"""
    
    events = []
    
    # Add static recurring events
    print("Adding static recurring events...")
    for event in RECURRING_EVENTS:
        events.append(event.copy())
        print(f"  ✓ {event['title']} at {event['venue']}")
    
    # Try to scrape special one-off events from page text
    print("\nSearching for special events on website...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            print("Loading Mountain Sun events page...")
            page.goto('https://www.mountainsunpub.com/events/', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Get page text
            page_text = page.inner_text('body')
            
            browser.close()
            
            # Look for special events in the text
            special_events = extract_special_events(page_text)
            
            if special_events:
                print(f"Found {len(special_events)} special event(s):")
                for event in special_events:
                    events.append(event)
                    print(f"  ✓ {event['title']} at {event['venue']}")
            else:
                print("  No special events found in text")
                
    except Exception as e:
        print(f"Error scraping special events: {e}")
        print("Continuing with static events only...")
    
    return events


def extract_special_events(page_text):
    """Extract special one-off events from unstructured page text"""
    
    special_events = []
    
    # Pattern to find events with dates like "12/23/25" or "December 23, 2025"
    # Looking for patterns like: "Event Name, Venue, Date, Time"
    
    # Split text into lines
    lines = page_text.split('\n')
    
    for i, line in enumerate(lines):
        # Look for date patterns
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', line)
        
        if date_match:
            # Found a date, try to extract event info from this line and surrounding lines
            event = parse_special_event_line(line, lines[max(0, i-2):min(len(lines), i+3)])
            if event:
                special_events.append(event)
    
    return special_events


def parse_special_event_line(line, context_lines):
    """Parse a line containing a special event"""
    
    # Combine context for better parsing
    text = ' '.join(context_lines)
    
    # Extract date
    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', text)
    if not date_match:
        return None
    
    date_str = date_match.group(1)
    
    # Try to normalize date to full format
    try:
        parts = date_str.split('/')
        if len(parts[2]) == 2:
            year = '20' + parts[2]
        else:
            year = parts[2]
        normalized_date = f"{parts[0]}/{parts[1]}/{year}"
    except:
        normalized_date = date_str
    
    # Extract time (look for patterns like "6:00 pm" or "6:00 pm - 9:00 pm")
    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm)(?:\s*-\s*\d{1,2}:\d{2}\s*(?:am|pm))?)', text, re.I)
    time_str = time_match.group(1) if time_match else None
    
    # Extract venue (look for known venue names)
    venue_name = None
    location = None
    
    if 'Longs Peak' in text:
        venue_name = 'Longs Peak Pub'
        location = 'Longmont'
    elif 'Vine Street' in text:
        venue_name = 'Vine Street Pub'
        location = 'Denver'
    elif 'Southern Sun' in text:
        venue_name = 'Southern Sun Pub'
        location = 'Boulder'
    elif 'Mountain Sun' in text or 'Pearl' in text:
        venue_name = 'Mountain Sun Pub'
        location = 'Boulder'
    
    if not venue_name:
        return None
    
    # Extract title (look for text in quotes or bold, or beginning of line)
    title_match = re.search(r'["""]([^"""]+)["""]', text)
    if title_match:
        title = title_match.group(1)
    else:
        # Try to get first substantial text before the venue name
        before_venue = text.split(venue_name)[0].strip()
        # Take last 2-5 words as potential title
        words = before_venue.split()
        if len(words) >= 2:
            title = ' '.join(words[-5:]) if len(words) >= 5 else ' '.join(words[-2:])
        else:
            title = f"Special Event at {venue_name}"
    
    # Clean up title
    title = re.sub(r'^[__\*\-\s]+|[__\*\-\s]+$', '', title)
    title = title.strip()
    
    if not title or len(title) < 3:
        return None
    
    return {
        'title': title,
        'venue': venue_name,
        'location': location,
        'date': normalized_date,
        'time': time_str,
        'description': text.strip()[:200],  # First 200 chars as description
        'link': 'https://www.mountainsunpub.com/events/',
        'source_url': 'https://www.mountainsunpub.com/events/',
    }


if __name__ == "__main__":
    print("Mountain Sun Pub Event Scraper")
    print("=" * 60)
    
    events = scrape_mountain_sun_events()
    
    print(f"\n{'='*60}")
    print(f"Total events: {len(events)}")
    print(f"{'='*60}")
    
    # Save to JSON
    with open('mountain_sun_events.json', 'w') as f:
        json.dump(events, f, indent=2)
    
    print(f"\n✅ Saved to mountain_sun_events.json")
    
    # Show summary
    print("\nEvent Summary:")
    for event in events:
        recurring_tag = f" [{event['recurring']}]" if event.get('recurring') else ""
        print(f"  • {event['title']} - {event['venue']}{recurring_tag}")
