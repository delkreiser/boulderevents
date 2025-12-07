"""
Junkyard Social Club Event Scraper - Improved with Playwright
URL: https://junkyardsocialclub.org/events/

This version uses Playwright to scrape live events and includes event links.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


def scrape_junkyard_events():
    """Scrape Junkyard events using Playwright"""
    
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
            
            print("Loading Junkyard Social Club events page...")
            page.goto('https://junkyardsocialclub.org/events/', 
                     wait_until='networkidle', timeout=30000)
            
            # Scroll to load all events
            print("Scrolling to load all events...")
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
            
            # Get rendered HTML
            html_content = page.content()
            browser.close()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for event containers
            # Junkyard uses image-based event cards
            print("Finding event cards...")
            
            # Try to find event containers
            event_containers = soup.find_all('img', src=re.compile(r'junkyardsocialclub\.org/wp-content/uploads'))
            print(f"Found {len(event_containers)} event images")
            
            for img in event_containers:
                try:
                    # Find the parent container that holds the event info
                    event_card = img.find_parent(['div', 'article', 'section', 'li'])
                    if event_card:
                        event = parse_junkyard_event_card(event_card)
                        if event and event.get('title'):
                            event['venue'] = 'Junkyard Social Club'
                            event['source_url'] = 'https://junkyardsocialclub.org/events/'
                            events.append(event)
                            print(f"  ✓ {event['title']}")
                except Exception as e:
                    print(f"  ✗ Error parsing event: {e}")
                    continue
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_junkyard_event_card(card):
    """Parse a single Junkyard event card"""
    
    event = {}
    
    # Get all text from the card
    card_text = card.get_text(separator='|', strip=True)
    
    # Split by lines to parse
    lines = [line.strip() for line in card_text.split('|') if line.strip()]
    
    # First substantial line is usually the title
    for line in lines:
        if len(line) > 5 and line not in ['Dance/Music', 'Community', 'Educational', 'Performance', 'Family Fun', 'All Ages are Welcome', 'All Ages', 'Family Friendly']:
            if not line.startswith('-') and not re.match(r'^\d', line) and 'ages' not in line.lower():
                event['title'] = line
                break
    
    # Extract date
    date_patterns = [
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}',
    ]
    
    for line in lines:
        for pattern in date_patterns:
            match = re.search(pattern, line, re.I)
            if match:
                event['date'] = match.group(0)
                break
        if event.get('date'):
            break
    
    # Extract time
    for line in lines:
        time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)|Doors\s+\d{1,2}:\d{2}', line, re.I)
        if time_match:
            event['time'] = line  # Keep the full time description
            break
    
    # Extract categories
    categories = []
    category_keywords = ['Dance/Music', 'Community', 'Educational', 'Performance', 'Family Fun']
    for line in lines:
        for keyword in category_keywords:
            if keyword in line:
                categories.extend([k.strip() for k in line.split(',')])
                break
    if categories:
        event['categories'] = ', '.join(list(set(categories)))
    
    # Extract age restriction
    for line in lines:
        if 'age' in line.lower() or 'family friendly' in line.lower():
            event['age_restriction'] = line
            break
    
    # Look for event link
    link_elem = card.find('a', href=True)
    if link_elem:
        href = link_elem.get('href')
        if href:
            # Make sure it's a full URL
            if href.startswith('http'):
                event['link'] = href
            elif href.startswith('/'):
                event['link'] = f"https://junkyardsocialclub.org{href}"
    
    # Get image
    img_elem = card.find('img')
    if img_elem and img_elem.get('src'):
        event['image'] = img_elem['src']
    
    # Get description if available
    desc_elem = card.find('p')
    if desc_elem:
        desc_text = desc_elem.get_text(strip=True)
        # Filter out category/age info from description
        if len(desc_text) > 20 and not any(keyword in desc_text for keyword in category_keywords + ['All Ages', 'Family Friendly']):
            event['description'] = desc_text[:300]
    
    return event


if __name__ == "__main__":
    print("Junkyard Social Club Event Scraper")
    print("=" * 60)
    
    events = scrape_junkyard_events()
    
    print(f"\n{'='*60}")
    print(f"Found {len(events)} events")
    print(f"{'='*60}")
    
    # Save to JSON
    with open('junkyard_events.json', 'w') as f:
        json.dump(events, f, indent=2)
    
    if events:
        print(f"\n✅ Saved to junkyard_events.json\n")
        
        # Show December, January, February events
        future_events = [e for e in events if e.get('date') and any(month in e['date'] for month in ['December', 'January', 'February'])]
        print(f"December/January/February events: {len(future_events)}")
        
        for i, event in enumerate(events[:5], 1):
            print(f"\nEvent {i}:")
            print(f"  Title: {event.get('title')}")
            print(f"  Date: {event.get('date', 'N/A')}")
            print(f"  Time: {event.get('time', 'N/A')}")
            if event.get('link'):
                print(f"  Link: {event['link']}")
    else:
        print("⚠️  No events found")
