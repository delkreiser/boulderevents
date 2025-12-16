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
            page.goto('https://www.eventbrite.com/o/roots-music-project-28110994095', 
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
    """Parse the Eventbrite HTML to extract event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all event cards - Eventbrite uses various patterns
    # Try multiple selectors
    event_cards = soup.find_all('div', class_=re.compile(r'discover-search-desktop-card|event-card|Card-sc'))
    
    if not event_cards:
        # Try finding by article tag
        event_cards = soup.find_all('article', class_=re.compile(r'event|card'))
    
    if not event_cards:
        # Try finding links to /e/ (event pages)
        links = soup.find_all('a', href=re.compile(r'/e/'))
        # Get parent containers
        event_cards = [link.find_parent(['div', 'article']) for link in links if link.find_parent(['div', 'article'])]
        # Remove duplicates
        event_cards = list(set(event_cards))
    
    print(f"Found {len(event_cards)} event cards")
    
    events = []
    today = date.today()
    
    for card in event_cards:
        try:
            event = parse_eventbrite_event(card)
            
            if event and event.get('title'):
                # Add venue info
                event['venue'] = 'Roots Music Project'
                event['location'] = 'Boulder'
                event['category'] = 'Music'
                event['source_url'] = 'https://www.eventbrite.com/o/roots-music-project-28110994095'
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
                    # If no date parsed, still include it
                    events.append(event)
                    print(f"  ⚠️  {event['title']} - no date parsed, including anyway")
                    
        except Exception as e:
            print(f"  Error parsing event: {e}")
            continue
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_eventbrite_event(card):
    """Parse a single Eventbrite event card"""
    
    event = {}
    
    # Find event link and title
    link_elem = card.find('a', href=re.compile(r'/e/'))
    if link_elem:
        href = link_elem.get('href', '')
        if href:
            # Make sure it's a full URL
            if href.startswith('http'):
                event['link'] = href
            elif href.startswith('/'):
                event['link'] = f"https://www.eventbrite.com{href}"
            else:
                event['link'] = f"https://www.eventbrite.com/{href}"
        
        # Try to get title from the link or nearby heading
        title = link_elem.get('aria-label') or link_elem.get_text(strip=True)
        if not title or len(title) < 3:
            # Look for h2, h3 nearby
            heading = card.find(['h1', 'h2', 'h3', 'h4'])
            if heading:
                title = heading.get_text(strip=True)
        
        if title:
            event['title'] = title
    
    # Find image
    img = card.find('img')
    if img and img.get('src'):
        img_src = img['src']
        # Skip placeholder/default images
        if 'default' not in img_src.lower() and 'placeholder' not in img_src.lower():
            event['image'] = img_src
    
    # Find date/time - Eventbrite formats vary
    # Look for time elements or date text
    time_elem = card.find('time')
    if time_elem:
        datetime_attr = time_elem.get('datetime')
        if datetime_attr:
            # Parse ISO format datetime
            parsed = parse_iso_datetime(datetime_attr)
            if parsed:
                event.update(parsed)
        
        # Also get the human-readable text
        date_text = time_elem.get_text(strip=True)
        if date_text and not event.get('date'):
            event['date'] = date_text
    
    # Look for "All Ages" in the card text
    card_text = card.get_text().lower()
    if 'all ages' in card_text or 'family friendly' in card_text:
        event['age_restriction'] = 'All Ages'
    
    # Try to extract description
    # Look for paragraphs or divs with description-like text
    desc_elem = card.find('p')
    if desc_elem:
        desc_text = desc_elem.get_text(strip=True)
        if desc_text and len(desc_text) > 20:
            # Limit to 300 chars
            if len(desc_text) > 300:
                desc_text = desc_text[:300] + "..."
            event['description'] = desc_text
    
    return event if event.get('title') else None


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
