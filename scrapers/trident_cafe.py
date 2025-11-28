"""
Trident Booksellers & Cafe Event Scraper
URL: https://www.tridentcafe.com/events

This scraper extracts events from Trident Cafe's events page using Playwright
for JavaScript rendering.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re


def scrape_trident_events():
    """
    Scrape events from Trident Cafe using Playwright
    
    Returns:
        List of event dictionaries
    """
    events = []
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to events page
        print("Loading Trident events page...")
        page.goto('https://www.tridentcafe.com/events', wait_until='networkidle')
        
        # Wait a bit for any dynamic content to load
        page.wait_for_timeout(2000)
        
        # Get the rendered HTML
        html_content = page.content()
        browser.close()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for event containers - try multiple selectors
        event_selectors = [
            'div.event-item',
            'div.eventlist-event',
            'article.event',
            'div[class*="event"]',
            'li.eventlist-event',
            '.sqs-block-summary-v2',
            'div.summary-item',
        ]
        
        event_elements = []
        for selector in event_selectors:
            found = soup.select(selector)
            if found:
                print(f"Found {len(found)} events using selector: {selector}")
                event_elements = found
                break
        
        # If still no events, try broader search
        if not event_elements:
            # Look for any container with "event" in class or id
            event_elements = soup.find_all(['div', 'article', 'li'], 
                                          attrs={'class': re.compile(r'event', re.I)})
        
        print(f"Total event elements found: {len(event_elements)}")
        
        # Parse each event
        for element in event_elements:
            try:
                event = parse_trident_event(element)
                if event and event.get('title'):
                    event['venue'] = 'Trident Booksellers & Cafe'
                    event['category'] = 'Books & Literary'
                    event['source_url'] = 'https://www.tridentcafe.com/events'
                    events.append(event)
            except Exception as e:
                print(f"Error parsing event: {e}")
                continue
    
    return events


def parse_trident_event(element):
    """Parse a single event element"""
    
    event = {}
    
    # Title
    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'], 
                              class_=re.compile(r'title|name|heading', re.I))
    if not title_elem:
        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
    
    if title_elem:
        event['title'] = title_elem.get_text(strip=True)
    
    # Link
    link_elem = element.find('a', href=True)
    if link_elem:
        link = link_elem.get('href', '')
        if link and not link.startswith('http'):
            link = f"https://www.tridentcafe.com{link}"
        event['link'] = link
    
    # Date/Time
    date_elem = element.find(class_=re.compile(r'date|time|when', re.I))
    if date_elem:
        event['date'] = date_elem.get_text(strip=True)
    
    # Description
    desc_elem = element.find(['p', 'div'], 
                            class_=re.compile(r'desc|excerpt|summary|content', re.I))
    if not desc_elem:
        desc_elem = element.find('p')
    
    if desc_elem:
        event['description'] = desc_elem.get_text(strip=True)
    
    return event


def scrape_trident_simple(html_content):
    """
    Simple scraper that works with pre-fetched HTML
    Useful if you already have the HTML content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Try to find events in the HTML
    # Look for common patterns
    event_containers = soup.find_all(['div', 'article'], 
                                    class_=re.compile(r'event', re.I))
    
    for container in event_containers:
        event = parse_trident_event(container)
        if event and event.get('title'):
            event['venue'] = 'Trident Booksellers & Cafe'
            event['category'] = 'Books & Literary'
            event['source_url'] = 'https://www.tridentcafe.com/events'
            events.append(event)
    
    return events


if __name__ == "__main__":
    print("Trident Cafe Event Scraper")
    print("=" * 60)
    
    events = scrape_trident_events()
    
    print(f"\nFound {len(events)} events")
    print("=" * 60)
    
    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Title: {event.get('title', 'N/A')}")
        print(f"  Date: {event.get('date', 'N/A')}")
        if event.get('description'):
            desc = event['description'][:100] + "..." if len(event['description']) > 100 else event['description']
            print(f"  Description: {desc}")
        print(f"  Link: {event.get('link', 'N/A')}")
    
    # Save to JSON
    output_file = '/home/claude/trident_events.json'
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"\n\nEvents saved to {output_file}")
