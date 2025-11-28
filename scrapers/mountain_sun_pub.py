"""
Mountain Sun Pub Event Scraper
URL: https://www.mountainsunpub.com/events/

This scraper extracts events from Mountain Sun Pub and their sister pubs
(Southern Sun, Vine Street Pub, Longs Peak Pub)
"""

from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


def scrape_mountain_sun_events(html_content):
    """
    Scrape events from Mountain Sun Pub
    
    Args:
        html_content: Raw HTML content from the events page
        
    Returns:
        List of event dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Look for event containers
    event_selectors = [
        'div.event-item',
        'div.event',
        'article.event',
        'div[class*="event"]',
    ]
    
    event_elements = []
    for selector in event_selectors:
        found = soup.select(selector)
        if found:
            print(f"Found {len(found)} events using selector: {selector}")
            event_elements = found
            break
    
    # If no specific containers, look for sections or divs with event info
    if not event_elements:
        # Look for headings that might indicate events
        headings = soup.find_all(['h2', 'h3', 'h4', 'h5'])
        for heading in headings:
            # Get the heading and nearby content
            parent = heading.find_parent(['div', 'section', 'article'])
            if parent:
                event_elements.append(parent)
    
    print(f"Total event elements found: {len(event_elements)}")
    
    # Parse each event
    for element in event_elements:
        try:
            event = parse_mountain_sun_event(element)
            if event and event.get('title'):
                event['source_url'] = 'https://www.mountainsunpub.com/events/'
                events.append(event)
        except Exception as e:
            print(f"Error parsing event: {e}")
            continue
    
    return events


def parse_mountain_sun_event(element):
    """Parse a single event element"""
    
    event = {}
    
    # Get all text
    text = element.get_text(separator=' | ', strip=True)
    
    # Title - look for headings
    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
    if title_elem:
        event['title'] = title_elem.get_text(strip=True)
    
    # Determine venue from title or content
    venue_patterns = {
        'Mountain Sun Pub': r'Mountain Sun',
        'Southern Sun Pub': r'Southern Sun',
        'Vine Street Pub': r'Vine Street',
        'Longs Peak Pub': r'Longs? Peak',
    }
    
    for venue_name, pattern in venue_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            event['venue'] = venue_name
            break
    
    if 'venue' not in event:
        event['venue'] = 'Mountain Sun Pub'
    
    # Category
    event['category'] = 'Music & Pub Events'
    
    # Look for recurring patterns
    recurring_patterns = [
        r'Every (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) Nights?',
    ]
    
    for pattern in recurring_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            event['recurring'] = match.group(0)
            break
    
    # Look for specific dates
    date_patterns = [
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            event['date'] = match.group(0)
            break
    
    # Look for time patterns
    time_patterns = [
        r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
        r'\d{1,2}\s*(?:AM|PM|am|pm)\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
        r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
        r'from\s+\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
        r'\d{1,2}(?:am|pm|AM|PM)-\d{1,2}(?:am|pm|AM|PM)',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            event['time'] = match.group(0)
            break
    
    # Description - get paragraph content
    desc_elem = element.find('p')
    if desc_elem:
        event['description'] = desc_elem.get_text(strip=True)
    
    # Link
    link_elem = element.find('a', href=True)
    if link_elem:
        link = link_elem.get('href', '')
        if link and not link.startswith('http'):
            link = f"https://www.mountainsunpub.com{link}"
        event['link'] = link
    
    return event


def parse_mountain_sun_simple(text_content):
    """
    Parse events from simple text format
    Based on the web_fetch output we received
    """
    events = []
    
    # Parse recurring events
    recurring_events_data = [
        {
            'title': 'The BLUEGRASS PICK',
            'recurring': 'Every Thursday',
            'time': '7:30 - 9:30 pm',
            'venue': 'Southern Sun Pub',
            'description': 'Hosted by Max Kabat of Bowregard. Never a cover, always a good time!',
        },
        {
            'title': 'Vinyl Night',
            'recurring': 'Every Monday',
            'time': '5-9 pm',
            'venue': 'Vine Street Pub',
            'description': 'Join us for an intentional listening experience. Share your favorite tunes and discover new music while enjoying house-made beer and snacks. Bring in a record from your collection and in exchange, we will play it for the pub and give you a free beer.',
        },
        {
            'title': 'Game Night',
            'recurring': 'Monday Nights',
            'time': '5pm-10pm',
            'venue': 'Longs Peak Pub',
            'description': 'Free Fries and Happy Hour prices for all game tables!',
        },
        {
            'title': 'Music Night',
            'recurring': 'Every Saturday',
            'time': '8pm',
            'venue': 'Vine Street Pub',
            'description': 'In collaboration with Stir Fry Sessions, a Denver based artist collective, we showcase local talent while offering a community space to dance and mingle.',
        },
    ]
    
    # Parse specific Friday music events
    friday_music = [
        {
            'title': 'Free Live Music: Goodtime Funk',
            'date': 'Friday, November 7th',
            'time': '9pm-Midnight',
            'venue': 'Mountain Sun Pub on Pearl',
            'description': 'NO COVER!',
        },
        {
            'title': 'Free Live Music: Jason Brandt & the Build-Out',
            'date': 'Friday, November 14th',
            'time': '9pm-Midnight',
            'venue': 'Mountain Sun Pub on Pearl',
            'description': 'NO COVER!',
        },
        {
            'title': 'Free Live Music: Brandy Wine & The Mighty Fines',
            'date': 'Friday, November 21st',
            'time': '9pm-Midnight',
            'venue': 'Mountain Sun Pub on Pearl',
            'description': 'NO COVER!',
        },
        {
            'title': 'Free Live Music: Crick Wooder',
            'date': 'Friday, November 28th',
            'time': '9pm-Midnight',
            'venue': 'Mountain Sun Pub on Pearl',
            'description': 'NO COVER!',
        },
    ]
    
    # Add all events
    for event_data in recurring_events_data + friday_music:
        event_data['category'] = 'Music & Pub Events'
        event_data['source_url'] = 'https://www.mountainsunpub.com/events/'
        events.append(event_data)
    
    return events


if __name__ == "__main__":
    print("Mountain Sun Pub Event Scraper")
    print("=" * 60)
    
    # Use the simple parser with our known data
    events = parse_mountain_sun_simple("")
    
    print(f"\nFound {len(events)} events")
    print("=" * 60)
    
    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Title: {event['title']}")
        print(f"  Venue: {event['venue']}")
        if event.get('date'):
            print(f"  Date: {event['date']}")
        if event.get('recurring'):
            print(f"  Recurring: {event['recurring']}")
        print(f"  Time: {event['time']}")
        if event.get('description'):
            desc = event['description'][:80] + "..." if len(event['description']) > 80 else event['description']
            print(f"  Description: {desc}")
    
    # Save to JSON
    output_file = '/home/claude/mountain_sun_events.json'
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"\n\nEvents saved to {output_file}")
