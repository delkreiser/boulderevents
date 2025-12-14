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
            
            # Find only the TOP-LEVEL event containers, not nested ones
            # Look for elements that have BOTH h2 and Event Info link as direct children
            all_containers = soup.find_all(['article', 'div'], class_=re.compile(r'event|post', re.I))
            
            # Filter to only parent containers (not nested)
            event_containers = []
            seen_titles = set()  # Track titles to avoid duplicates
            
            for container in all_containers:
                # Check if this container has an h2 (title)
                h2 = container.find('h2')
                if not h2:
                    continue
                
                title = h2.get_text(strip=True)
                
                # Skip if we've already seen this title
                if title in seen_titles:
                    continue
                
                # Check if this container has Event Info link
                event_link = container.find('a', string=re.compile(r'Event Info', re.I))
                if not event_link:
                    event_link = container.find('a', href=re.compile(r'/event/|/product/|/drop-in-event/', re.I))
                
                if event_link:
                    event_containers.append(container)
                    seen_titles.add(title)
            
            print(f"Found {len(event_containers)} unique event containers")
            
            for idx, event_card in enumerate(event_containers, 1):
                try:
                    event = parse_junkyard_event_card(event_card)
                    if event and event.get('title'):
                        event['venue'] = 'Junkyard Social Club'
                        event['source_url'] = 'https://junkyardsocialclub.org/events/'
                        
                        # Add default image if none exists
                        if not event.get('image'):
                            event['image'] = 'junkyard.jpg'
                        
                        events.append(event)
                        print(f"  ✓ Event {idx}: {event['title']}")
                    else:
                        if idx <= 30:
                            print(f"  ✗ Event {idx}: Failed to parse (missing title)")
                except Exception as e:
                    if idx <= 30:
                        print(f"  ✗ Event {idx}: Error - {e}")
                    continue
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_junkyard_event_card(card):
    """Parse a single Junkyard event card"""
    
    event = {}
    
    # Find the event title (h2 heading)
    title_elem = card.find('h2')
    if title_elem:
        event['title'] = title_elem.get_text(strip=True)
    else:
        # Skip if no title found
        return None
    
    # Get all list items which contain date, time, categories, age info
    list_items = card.find_all('li')
    
    for li in list_items:
        text = li.get_text(strip=True)
        
        # Check if this is the date
        if re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', text, re.I):
            event['date'] = text
        
        # Check if this is the time (contains PM/AM or "Doors")
        elif re.search(r'\d{1,2}:\d{2}|Doors|POSTPONED|Closed', text, re.I):
            event['time'] = text
        
        # Check if this is categories (contains commas or known category words)
        elif any(cat in text for cat in ['Community', 'Dance/Music', 'Educational', 'Performance', 'Family Fun']):
            event['categories'] = text
        
        # Check if this is age restriction
        elif 'age' in text.lower() or 'family friendly' in text.lower():
            event['age_restriction'] = text
    
    # Find the "Event Info" link - search broadly in the container
    link_elem = card.find('a', string=re.compile(r'Event Info', re.I))
    if not link_elem:
        # Try finding any link with 'event' in the href
        link_elem = card.find('a', href=re.compile(r'/event/|/product/|/drop-in-event/', re.I))
    
    if link_elem and link_elem.get('href'):
        href = link_elem['href']
        if href.startswith('http'):
            event['link'] = href
        elif href.startswith('/'):
            event['link'] = f"https://junkyardsocialclub.org{href}"
        else:
            event['link'] = f"https://junkyardsocialclub.org/{href}"
    
    # Get the event image
    img_elem = card.find('img')
    if img_elem and img_elem.get('src'):
        event['image'] = img_elem['src']
    
    return event if event.get('title') else None  # Only require title, date is optional


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
