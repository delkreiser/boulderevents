"""
License No 1 Event Scraper
URL: https://www.license1boulderado.com/events-1

This scraper extracts events from License No 1 in Boulder, CO.
License No 1 appears to be a bar/nightlife venue.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


def scrape_license_no1_events():
    """
    Scrape events from License No 1 using Playwright
    
    Returns:
        List of event dictionaries
    """
    events = []
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to events page
            print("Loading License No 1 events page...")
            page.goto('https://www.license1boulderado.com/events-1', wait_until='networkidle')
            
            # Wait for events to load (Squarespace typically needs this)
            page.wait_for_timeout(3000)
            
            # Get the rendered HTML
            html_content = page.content()
            browser.close()
            
            # Parse with BeautifulSoup
            events = parse_license_no1_html(html_content)
    
    except Exception as e:
        print(f"Error with Playwright: {e}")
        print("This scraper needs to be run in an environment with network access.")
    
    return events


def parse_license_no1_html(html_content):
    """Parse events from License No 1 HTML"""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Squarespace event selectors
    event_selectors = [
        'article.eventlist-event',
        'div.eventlist-event',
        'li.eventlist-event',
        'div.summary-item',
        'article.summary-item',
        'div[class*="event"]',
    ]
    
    event_elements = []
    for selector in event_selectors:
        found = soup.select(selector)
        if found:
            print(f"Found {len(found)} events using selector: {selector}")
            event_elements = found
            break
    
    # If no events found with standard selectors, try broader search
    if not event_elements:
        event_elements = soup.find_all(['article', 'div', 'li'], 
                                      class_=re.compile(r'event|summary', re.I))
    
    print(f"Total event elements found: {len(event_elements)}")
    
    # Parse each event
    for element in event_elements:
        try:
            event = parse_license_no1_event(element)
            if event and event.get('title'):
                event['venue'] = 'License No 1'
                event['category'] = 'Nightlife'
                event['source_url'] = 'https://www.license1boulderado.com/events-1'
                events.append(event)
        except Exception as e:
            print(f"Error parsing event: {e}")
            continue
    
    return events


def parse_license_no1_event(element):
    """Parse a single event element"""
    
    event = {}
    
    # Title - Squarespace often uses specific classes
    title_elem = element.find(['h1', 'h2', 'h3', 'h4'], 
                              class_=re.compile(r'title|name|heading', re.I))
    if not title_elem:
        title_elem = element.find('a', class_=re.compile(r'title|name', re.I))
    if not title_elem:
        title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
    
    if title_elem:
        event['title'] = title_elem.get_text(strip=True)
    
    # Link
    link_elem = element.find('a', href=True)
    if link_elem:
        link = link_elem.get('href', '')
        if link and not link.startswith('http'):
            link = f"https://www.license1boulderado.com{link}"
        event['link'] = link
    
    # Date and Time - Squarespace has specific date classes
    date_elem = element.find(class_=re.compile(r'date|time|when', re.I))
    if date_elem:
        event['date'] = date_elem.get_text(strip=True)
    
    # Try to find time separately
    time_elem = element.find(class_=re.compile(r'time', re.I))
    if time_elem and time_elem != date_elem:
        event['time'] = time_elem.get_text(strip=True)
    
    # Description
    desc_elem = element.find(['p', 'div'], 
                            class_=re.compile(r'desc|excerpt|summary|content', re.I))
    if desc_elem:
        event['description'] = desc_elem.get_text(strip=True)
    
    # Image
    img_elem = element.find('img')
    if img_elem and img_elem.get('src'):
        event['image'] = img_elem['src']
    elif img_elem and img_elem.get('data-src'):  # Lazy-loaded images
        event['image'] = img_elem['data-src']
    
    return event


def scrape_license_no1_simple(html_content):
    """
    Simple scraper that works with pre-fetched HTML
    Useful if you already have the HTML content
    """
    return parse_license_no1_html(html_content)


if __name__ == "__main__":
    print("License No 1 Event Scraper")
    print("=" * 60)
    print("\nNote: This site uses JavaScript (Squarespace).")
    print("Run this script locally with Playwright installed:")
    print("  pip install playwright beautifulsoup4")
    print("  playwright install chromium")
    print("  python license_no1.py")
    print("\n" + "=" * 60)
    
    # Try to scrape
    events = scrape_license_no1_events()
    
    if events:
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
        output_file = './license_no1_events.json'
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"\n\nEvents saved to {output_file}")
    else:
        print("\nNo events found. This scraper needs network access to work properly.")
