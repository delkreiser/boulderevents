"""
300 Suns Brewing - Events Scraper
URL: https://300sunsbrewing.com/events/

Scrapes events from 300 Suns Brewing's events page in Longmont
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date


def scrape_300_suns_events():
    """Scrape 300 Suns Brewing events using Playwright"""
    
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
            
            print("Loading 300 Suns Brewing events page...")
            page.goto('https://300sunsbrewing.com/events/', 
                     wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Scroll to load all content
            print("Scrolling to load all events...")
            for i in range(3):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
            
            print("Parsing events...")
            html = page.content()
            events = parse_300_suns_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_300_suns_html(html):
    """Parse the HTML to extract event data"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all event list items (li elements with class containing "wp-block-post")
    event_items = soup.find_all('li', class_=re.compile(r'wp-block-post'))
    print(f"Found {len(event_items)} event items")
    
    events = []
    today = date.today()
    
    for item in event_items:
        try:
            event = parse_300_suns_event(item)
            
            if event and event.get('title'):
                # Add venue info
                event['venue'] = '300 Suns Brewing'
                event['location'] = 'Longmont'
                event['category'] = 'Music'
                event['source_url'] = 'https://300sunsbrewing.com/events/'
                event['image'] = '300suns.jpg'
                event['age_restriction'] = 'All Ages'
                event['event_type_tags'] = ['Live Music', 'Brewery', 'Family Friendly']
                event['venue_type_tags'] = ['Brewery', 'Live Music', 'Family Friendly']
                
                # Filter: Only include today and future events
                if event.get('date_obj'):
                    if event['date_obj'] >= today:
                        del event['date_obj']  # Remove before adding to list
                        events.append(event)
                        print(f"  ✓ {event['title']} - {event['date']}")
                    else:
                        print(f"  ✗ Skipped past event: {event.get('title')} - {event.get('date')}")
                else:
                    # Skip events where we can't parse the date
                    print(f"  ✗ Skipped (no date): {event['title']}")
                    
        except Exception as e:
            print(f"  Error parsing event: {e}")
            continue
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_300_suns_event(item):
    """
    Parse a single event from a list item
    
    Structure:
    - h2.wp-block-post-title > a: Event title and link
    - h2.wp-block-heading: Date/time like "Sat • Dec 6 • 6:00-8:00 PM"
    - div.entry-content > p: Description
    """
    
    event = {}
    
    # Get title and link from h2.wp-block-post-title
    title_elem = item.find('h2', class_='wp-block-post-title')
    if title_elem:
        link_elem = title_elem.find('a')
        if link_elem:
            event['title'] = link_elem.get_text(strip=True)
            href = link_elem.get('href', '')
            if href:
                event['link'] = href
    
    if not event.get('title'):
        return None
    
    # Get date/time from h2.wp-block-heading
    heading_elem = item.find('h2', class_='wp-block-heading')
    if heading_elem:
        datetime_text = heading_elem.get_text(strip=True)
        parsed_datetime = parse_date_time(datetime_text)
        if parsed_datetime:
            event.update(parsed_datetime)
    
    # Get description from div.entry-content > p
    entry_content = item.find('div', class_='entry-content')
    if entry_content:
        desc_p = entry_content.find('p')
        if desc_p:
            desc_text = desc_p.get_text(strip=True)
            # Limit to 300 characters
            if len(desc_text) > 300:
                desc_text = desc_text[:300] + "..."
            event['description'] = desc_text
    
    return event


def parse_date_time(datetime_text):
    """
    Parse date and time from text like:
    "Sat • Dec 6 • 6:00-8:00 PM"
    "Th • Dec 18 • 6-8 PM" (without colons)
    "Sun • Jan 12 • 7:00-9:00 PM"
    """
    
    result = {}
    
    # Try pattern with colons first: "Weekday • Month Day • HH:MM-HH:MM PM/AM"
    match = re.search(
        r'(\w{2,3})\s*•\s*(\w{3})\s+(\d{1,2})\s*•\s*(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})\s*(AM|PM)',
        datetime_text,
        re.IGNORECASE
    )
    
    if match:
        weekday_abbr = match.group(1)
        month_abbr = match.group(2)
        day = match.group(3)
        start_hour = match.group(4)
        start_min = match.group(5)
        end_hour = match.group(6)
        end_min = match.group(7)
        meridiem = match.group(8).upper()
        
        # Format time with meridiem
        time_str = f"{start_hour}:{start_min} - {end_hour}:{end_min} {meridiem}"
        result['time'] = time_str
        
        # Parse the date
        result.update(parse_month_day_to_date(month_abbr, day))
    else:
        # Try pattern without colons: "Weekday • Month Day • H-H PM/AM"
        match = re.search(
            r'(\w{2,3})\s*•\s*(\w{3})\s+(\d{1,2})\s*•\s*(\d{1,2})-(\d{1,2})\s*(AM|PM)',
            datetime_text,
            re.IGNORECASE
        )
        
        if match:
            weekday_abbr = match.group(1)
            month_abbr = match.group(2)
            day = match.group(3)
            start_hour = match.group(4)
            end_hour = match.group(5)
            meridiem = match.group(6).upper()
            
            # Format time with meridiem (assume :00 for minutes)
            time_str = f"{start_hour}:00 - {end_hour}:00 {meridiem}"
            result['time'] = time_str
            
            # Parse the date
            result.update(parse_month_day_to_date(month_abbr, day))
    
    return result


def parse_month_day_to_date(month_abbr, day):
    """Convert month abbreviation and day to full date with year"""
    
    result = {}
    
    # Map abbreviated months to full names
    month_map = {
        'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 
        'Apr': 'April', 'May': 'May', 'Jun': 'June',
        'Jul': 'July', 'Aug': 'August', 'Sep': 'September',
        'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
    }
    
    month_full = month_map.get(month_abbr, month_abbr)
    
    # Try to create a full date
    try:
        current_year = datetime.now().year
        current_date = date.today()
        
        date_str = f"{month_full} {day}, {current_year}"
        parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
        
        print(f"    Parsed: {date_str} -> {parsed_date}, Today: {current_date}")
        
        # If the date is in the past, use next year
        if parsed_date < current_date:
            print(f"    Date {parsed_date} is in past, using next year")
            date_str = f"{month_full} {day}, {current_year + 1}"
            parsed_date = datetime.strptime(date_str, '%B %d, %Y').date()
        
        result['date'] = date_str
        result['date_obj'] = parsed_date
        
    except Exception as e:
        print(f"    Error parsing date '{month_full} {day}': {e}")
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("300 SUNS BREWING EVENT SCRAPER")
    print("=" * 70)
    
    events = scrape_300_suns_events()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = '300_suns_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
            print(f"   Link: {event.get('link', 'N/A')[:60]}...")
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
