"""
License No 1 Event Scraper - Improved Version
URL: https://www.license1boulderado.com/events-1

This version has better error handling and debugging for GitHub Actions.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import sys


def scrape_license_no1_events():
    """
    Scrape events from License No 1 using Playwright
    
    Returns:
        List of event dictionaries
    """
    events = []
    
    try:
        with sync_playwright() as p:
            # Launch browser with specific args for GitHub Actions
            print("Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Set longer timeout
            page.set_default_timeout(30000)
            
            # Navigate to events page
            print("Loading License No 1 events page...")
            try:
                response = page.goto(
                    'https://www.license1boulderado.com/events-1',
                    wait_until='domcontentloaded',
                    timeout=30000
                )
                print(f"Page loaded with status: {response.status}")
            except PlaywrightTimeout:
                print("Warning: Page load timeout, but continuing...")
            
            # Wait for content to load
            print("Waiting for dynamic content...")
            page.wait_for_timeout(5000)
            
            # Try to find any event-related elements
            print("Looking for event elements...")
            
            # Debug: Save screenshot
            try:
                page.screenshot(path='license_no1_debug.png')
                print("Screenshot saved for debugging")
            except:
                pass
            
            # Get the rendered HTML
            html_content = page.content()
            
            # Debug: Print page title and first bit of content
            print(f"Page title: {page.title()}")
            print(f"HTML length: {len(html_content)} characters")
            
            # Save HTML for debugging
            with open('license_no1_debug.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("HTML saved for debugging")
            
            browser.close()
            
            # Parse with BeautifulSoup
            events = parse_license_no1_html(html_content)
            
            print(f"Found {len(events)} events")
    
    except Exception as e:
        print(f"Error with Playwright: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_license_no1_html(html_content):
    """Parse events from License No 1 HTML"""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    print("Parsing HTML for events...")
    
    # Try multiple Squarespace event selectors
    selectors_to_try = [
        'article.eventlist-event',
        'div.eventlist-event',
        'li.eventlist-event',
        'div.summary-item',
        'article.summary-item',
        '.eventlist',
        '[class*="event"]',
        '[class*="Event"]',
    ]
    
    event_elements = []
    for selector in selectors_to_try:
        found = soup.select(selector)
        if found:
            print(f"Found {len(found)} elements with selector: {selector}")
            event_elements = found
            break
    
    if not event_elements:
        print("No event elements found with standard selectors")
        print("Trying broader search...")
        
        # Look for any text that might indicate events
        text = soup.get_text()
        if 'event' in text.lower() or 'upcoming' in text.lower():
            print("Found event-related text but couldn't parse structure")
        else:
            print("No event-related content found on page")
    
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
    
    # Title
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
    
    # Date/Time
    date_elem = element.find(class_=re.compile(r'date|time|when', re.I))
    if date_elem:
        event['date'] = date_elem.get_text(strip=True)
    
    # Description
    desc_elem = element.find(['p', 'div'], 
                            class_=re.compile(r'desc|excerpt|summary|content', re.I))
    if desc_elem:
        event['description'] = desc_elem.get_text(strip=True)
    
    # Image
    img_elem = element.find('img')
    if img_elem and img_elem.get('src'):
        event['image'] = img_elem['src']
    elif img_elem and img_elem.get('data-src'):
        event['image'] = img_elem['data-src']
    
    return event


if __name__ == "__main__":
    print("License No 1 Event Scraper - Improved")
    print("=" * 60)
    
    events = scrape_license_no1_events()
    
    if events:
        print(f"\n✅ Successfully scraped {len(events)} events")
        
        # Save to JSON
        output_file = 'license_no1_events.json'
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"✅ Events saved to {output_file}")
        
        # Print sample
        for i, event in enumerate(events[:3], 1):
            print(f"\nEvent {i}:")
            print(f"  Title: {event.get('title', 'N/A')}")
            print(f"  Date: {event.get('date', 'N/A')}")
    else:
        print("\n⚠️  No events found")
        print("Check license_no1_debug.html and license_no1_debug.png for details")
        
        # Create empty JSON file so aggregator doesn't fail
        with open('license_no1_events.json', 'w') as f:
            json.dump([], f)
        print("Created empty license_no1_events.json")
