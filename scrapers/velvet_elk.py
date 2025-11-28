"""
Velvet Elk Lounge Event Scraper
URL: https://www.velvetelklounge.com/events/

This scraper extracts music events from Velvet Elk Lounge's events page.
"""

from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


def scrape_velvet_elk_events(html_content):
    """
    Scrape events from Velvet Elk Lounge
    
    Args:
        html_content: Raw HTML content from the events page
        
    Returns:
        List of event dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Look for event containers
    # Try multiple selector patterns
    event_selectors = [
        'div.event-item',
        'div.show-item',
        'li.event',
        'div[class*="event"]',
        'article.event',
        'div.bento-item',
        'div[class*="show"]',
    ]
    
    event_elements = []
    for selector in event_selectors:
        found = soup.select(selector)
        if found:
            print(f"Found {len(found)} events using selector: {selector}")
            event_elements = found
            break
    
    # If no specific event containers, look for a list structure
    if not event_elements:
        # Look for lists that might contain events
        event_lists = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'event|show|calendar', re.I))
        for event_list in event_lists:
            items = event_list.find_all(['li', 'div', 'article'])
            if items:
                event_elements = items
                print(f"Found {len(items)} items in event list")
                break
    
    print(f"Total event elements found: {len(event_elements)}")
    
    # Parse each event
    for element in event_elements:
        try:
            event = parse_velvet_elk_event(element)
            if event and event.get('title'):
                event['venue'] = 'Velvet Elk Lounge'
                event['category'] = 'Music'
                event['source_url'] = 'https://www.velvetelklounge.com/events/'
                events.append(event)
        except Exception as e:
            print(f"Error parsing event: {e}")
            continue
    
    return events


def parse_velvet_elk_event(element):
    """Parse a single event element"""
    
    event = {}
    
    # Get all text to analyze
    text = element.get_text(separator=' ', strip=True)
    
    # Title - look for headings or strong text
    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])
    if not title_elem:
        # Try to find a link that might be the title
        title_elem = element.find('a')
    
    if title_elem:
        event['title'] = title_elem.get_text(strip=True)
    else:
        # If no specific title element, use the first line of text
        lines = text.split('\n')
        if lines:
            event['title'] = lines[0].strip()
    
    # Link
    link_elem = element.find('a', href=True)
    if link_elem:
        link = link_elem.get('href', '')
        if link and not link.startswith('http'):
            link = f"https://www.velvetelklounge.com{link}"
        event['link'] = link
    
    # Date - look for date patterns in text
    date_elem = element.find(class_=re.compile(r'date|time|when', re.I))
    if date_elem:
        event['date'] = date_elem.get_text(strip=True)
    else:
        # Try to extract date from text using regex
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                event['date'] = match.group(0)
                break
    
    # Description
    desc_elem = element.find(['p', 'div'], class_=re.compile(r'desc|excerpt|summary|content', re.I))
    if desc_elem:
        event['description'] = desc_elem.get_text(strip=True)
    
    # Image
    img_elem = element.find('img')
    if img_elem and img_elem.get('src'):
        event['image'] = img_elem['src']
    
    return event


def parse_simple_event_list(text_content):
    """
    Parse events from simple text format
    Useful when HTML parsing doesn't work well
    
    Example format:
    - November 26, Event Name
    - November 28, Another Event
    """
    events = []
    
    # Split by lines or bullet points
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        # Remove leading bullets or dashes
        line = re.sub(r'^[-•*]\s*', '', line)
        
        # Try to extract date and title
        # Pattern: "Month Day, Title" or "Month Day - Title"
        match = re.match(r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?)[,\s-]+(.+)', line, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            title = match.group(2).strip()
            
            event = {
                'title': title,
                'date': date_str,
                'venue': 'Velvet Elk Lounge',
                'category': 'Music',
                'source_url': 'https://www.velvetelklounge.com/events/'
            }
            events.append(event)
    
    return events


if __name__ == "__main__":
    # Example usage with the text we can see
    sample_text = """
    - Nov 24 - Dec 31, Luxe Lounge
    - November 26, Home for the Holidaze featuring Los Cheesies
    - November 28, Black Sabbath Friday featuring Rat Salad a Black Sabbath Tribute
    - November 29th, Steve Knight Band
    - December 4th, Second Annual Ugly-er Sweater Party
    - December 18, LatkePalooza II: A Chanukah Celebration!
    - December 27, Rapidgrass
    - January 2, Kings of Prussia
    - January 24, JIMKATA with Terrawave
    """
    
    print("Velvet Elk Lounge Event Scraper")
    print("=" * 60)
    
    events = parse_simple_event_list(sample_text)
    
    print(f"\nFound {len(events)} events")
    print("=" * 60)
    
    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Title: {event['title']}")
        print(f"  Date: {event['date']}")
        print(f"  Venue: {event['venue']}")
        print(f"  Category: {event['category']}")
    
    # Save to JSON
    output_file = '/home/claude/velvet_elk_events.json'
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"\n\nEvents saved to {output_file}")
