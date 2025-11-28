"""
Junkyard Social Club Event Scraper
URL: https://junkyardsocialclub.org/events/

This scraper extracts community events from Junkyard Social Club in Boulder, CO.
"""

from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


def scrape_junkyard_events(html_content):
    """
    Scrape events from Junkyard Social Club
    
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
        'article.event',
        'div.tribe-events-list-event',
        'div[class*="event"]',
        'article[class*="event"]',
    ]
    
    event_elements = []
    for selector in event_selectors:
        found = soup.select(selector)
        if found:
            print(f"Found {len(found)} events using selector: {selector}")
            event_elements = found
            break
    
    # If no specific containers, look for image-based event structure
    if not event_elements:
        # Look for images with event info nearby
        images = soup.find_all('img', src=re.compile(r'junkyardsocialclub\.org/wp-content/uploads'))
        print(f"Found {len(images)} event images")
        
        # Each image likely has event details following it
        for img in images:
            # Find the parent container that holds the event info
            event_container = img.find_parent(['div', 'article', 'section'])
            if event_container:
                event_elements.append(event_container)
    
    print(f"Total event elements found: {len(event_elements)}")
    
    # Parse each event
    for element in event_elements:
        try:
            event = parse_junkyard_event(element)
            if event and event.get('title'):
                event['venue'] = 'Junkyard Social Club'
                event['source_url'] = 'https://junkyardsocialclub.org/events/'
                events.append(event)
        except Exception as e:
            print(f"Error parsing event: {e}")
            continue
    
    return events


def parse_junkyard_event(element):
    """Parse a single event element"""
    
    event = {}
    
    # Get all text
    text = element.get_text(separator='|', strip=True)
    
    # Title - usually the largest/first heading
    title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
    if title_elem:
        title = title_elem.get_text(strip=True)
        # Clean up title (remove image alt text if present)
        event['title'] = title
    
    # Link
    link_elem = element.find('a', href=True)
    if link_elem:
        link = link_elem.get('href', '')
        if link and not link.startswith('http'):
            link = f"https://junkyardsocialclub.org{link}"
        event['link'] = link
    
    # Categories - look for category tags
    category_text = element.find(class_=re.compile(r'categor', re.I))
    if category_text:
        event['categories'] = category_text.get_text(strip=True)
    else:
        # Try to extract from list items
        list_items = element.find_all('li')
        if list_items:
            categories = [li.get_text(strip=True) for li in list_items if len(li.get_text(strip=True)) < 50]
            if categories:
                event['categories'] = ', '.join(categories)
    
    # Date - look for date patterns
    date_patterns = [
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            event['date'] = match.group(0)
            break
    
    # Time - look for time patterns
    time_patterns = [
        r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
        r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
        r'Doors\s+\d{1,2}:\d{2}',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            event['time'] = match.group(0)
            break
    
    # Age restriction
    age_patterns = [
        r'All Ages?(?:\s+are\s+Welcome)?',
        r'Must be age \d+\+?',
        r'Ages? \d+\+',
        r'Family Friendly',
        r'\d+\+',
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            event['age_restriction'] = match.group(0)
            break
    
    # Image
    img_elem = element.find('img')
    if img_elem and img_elem.get('src'):
        event['image'] = img_elem['src']
    
    # Description - get remaining text that's not title/date/time
    desc_elem = element.find(['p', 'div'], class_=re.compile(r'desc|excerpt|summary|content', re.I))
    if desc_elem:
        event['description'] = desc_elem.get_text(strip=True)
    
    return event


def parse_junkyard_simple(text_content):
    """
    Parse events from simple text format
    Based on the web_fetch output we received
    """
    events = []
    lines = text_content.split('\n')
    
    current_event = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a title line (no date pattern, substantial text)
        if len(line) > 15 and not re.match(r'^\d|^-', line):
            # Save previous event if exists
            if current_event.get('title'):
                events.append(current_event.copy())
            
            # Start new event
            current_event = {
                'title': line,
                'venue': 'Junkyard Social Club',
                'source_url': 'https://junkyardsocialclub.org/events/'
            }
        
        # Check if this is a date line
        elif re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|January|February|March|April|May|June|July|August|September|October|November|December)', line, re.I):
            if current_event:
                current_event['date'] = line.replace('- ', '')
        
        # Check if this is a time line
        elif re.search(r'\d{1,2}:\d{2}', line):
            if current_event:
                current_event['time'] = line.replace('- ', '')
        
        # Check for categories
        elif re.search(r'(Dance/Music|Community|Educational|Performance|Family Fun)', line, re.I):
            if current_event:
                current_event['categories'] = line.replace('- ', '')
        
        # Check for age restrictions
        elif re.search(r'(All Ages|Must be age|Family Friendly|\d+\+)', line, re.I):
            if current_event:
                current_event['age_restriction'] = line.replace('- ', '')
    
    # Add the last event
    if current_event.get('title'):
        events.append(current_event)
    
    return events


if __name__ == "__main__":
    # Test with sample data
    sample_text = """
    Good Music Medicine Student Open Mic
    - Sunday, October 5, 2025
    - 3:00 - 7:00 PM
    - Dance/Music
    - All Ages are Welcome
    
    Embody Yo Body
    - Monday, October 6, 2025
    - Cancelled this month - see you next month!
    - Community, Dance/Music, Educational
    - All Ages are Welcome
    
    Pop-Up Bachata night
    - Monday, October 6, 2025
    - 7:00 PM - 9:00 PM
    - Community, Dance/Music, Educational, Family Fun
    - All Ages are Welcome
    
    Junkyard Game Night
    - Thursday, October 9, 2025
    - 6:00 - 9:00 PM
    - Community, Family Fun
    - All Ages are Welcome
    
    Fusion Partner Dance
    - Thursday, October 9, 2025
    - Doors 6:30 | Class 6:45 PM | Social Dance 7:15
    - Community, Dance/Music
    - All Ages are Welcome
    
    SPEAK UP STUDIO: NO KING'S DAY
    - Wednesday, October 15, 2025
    - 4:00 - 6:00 PM
    - Community
    - All Ages are Welcome
    
    House of Fire – Grave Rave
    - Friday, October 17, 2025
    - 8:00 PM Doors | Ends at 1 AM
    - Dance/Music
    - All Ages are Welcome
    
    CreativeMornings: SOFT with textile artist Steven Frost
    - Friday, October 17, 2025
    - 8:00 am doors | 9:00 am talk | 10:00 am off to work
    - Community
    - Family Friendly
    
    Masquerade Mermaid Ball
    - Saturday, October 18, 2025
    - 6:00 - 10:00 PM
    - Community, Dance/Music, Educational
    - All Ages are Welcome
    
    Salsa Sunday
    - Sunday, October 19, 2025
    - 5:00 PM - 7:30 PM
    - Community, Dance/Music, Family Fun
    - Family Friendly
    
    DANCE AND DREAM: Uplevel Your reality
    - Tuesday, October 21, 2025
    - 6:00 - 9:00 PM
    - Community, Dance/Music, Educational
    - 13+ for workshop | All ages for dance
    
    Rocky Horror Picture Show
    - Thursday, October 23, 2025
    - 7:00 PM Door | 8:00 PM Movie
    - Community
    - Ages 13+
    
    Salsaton Events
    - Friday, October 24, 2025
    - 7:30 - 11:00 PM
    - Community, Dance/Music, Family Fun, Performance
    - Family Friendly
    
    Queer Art Organics Open Mic
    - Sunday, October 26, 2025
    - 4:30 - 8:00 PM
    - Community, Performance
    
    Ghosts of the Junkyard
    - Sunday, October 26, 2025
    - 3:00 - 6:00 PM
    - Community, Family Fun, Performance
    - All Ages are Welcome
    
    Rocky Mountain Synthesizer Meet: Halloween Groovebox Invasion
    - Wednesday, October 29, 2025
    - 7:00 - 9:00 PM
    - Community, Dance/Music, Performance
    - Must be age 18+
    
    La Muerta: A Salsa, Samba, and Zouk Party
    - Saturday, November 1, 2025
    - 6:00 PM - Midnight
    - Community, Dance/Music, Family Fun
    - All Ages are Welcome
    
    Stage Party
    - Thursday, November 6, 2025
    - 7:00 PM Doors | 8:00 PM Show
    - Community, Dance/Music, Performance
    - All Ages are Welcome
    
    Story Collective: Boundaries
    - Saturday, November 8, 2025
    - 7:00 PM Doors | 7:45 PM Show
    - Community, Performance
    - 16+ (mature content)
    
    Speed Dating with The Big Dream
    - Sunday, November 9, 2025
    - 6:00 - 8:30 PM
    - Community
    - Must be age 18+
    
    Simon Shackleton – Open To Close – CHPTR 004
    - Saturday, November 22, 2025
    - 7:00 PM - Midnight
    - Dance/Music
    - Must be age 18+
    
    Christmas Movie the Play: The Beginning
    - Sunday, December 7, 2025
    - 6:30 Doors | 7:00 Show
    - Performance
    - Must be age 18+
    
    THE DOSE: A Psychedelic Comedy Experience
    - Saturday, December 13, 2025
    - 7pm Doors/Preshow DJ Set | 8pm Comedy Show | End time 10pm
    - Dance/Music, Performance
    - Must be age 18+
    """
    
    print("Junkyard Social Club Event Scraper")
    print("=" * 60)
    
    events = parse_junkyard_simple(sample_text)
    
    print(f"\nFound {len(events)} events")
    print("=" * 60)
    
    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Title: {event['title']}")
        print(f"  Date: {event.get('date', 'N/A')}")
        print(f"  Time: {event.get('time', 'N/A')}")
        print(f"  Categories: {event.get('categories', 'N/A')}")
        print(f"  Age: {event.get('age_restriction', 'N/A')}")
    
    # Save to JSON
    output_file = '/home/claude/junkyard_events.json'
    with open(output_file, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"\n\nEvents saved to {output_file}")
