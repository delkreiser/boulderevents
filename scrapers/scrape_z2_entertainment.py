#!/usr/bin/env python3
"""
Z2 Entertainment Events Scraper
Scrapes events from Boulder Theater, Fox Theatre, and Aggie Theatre
Uses direct API calls to get all events without Selenium
Downloads event images locally to avoid hotlinking
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from pathlib import Path
import hashlib

# Venue mappings
VENUE_INFO = {
    "Boulder Theater": {
        "location": "Boulder",
        "image": "images/bouldertheater.jpg",
        "include": True  # Show in Boulder Events
    },
    "Fox Theatre": {
        "location": "Boulder",
        "image": "images/foxtheatre.jpg",
        "include": True  # Show in Boulder Events
    },
    "Aggie Theatre": {
        "location": "Fort Collins",
        "image": "images/aggietheatre.jpg",
        "include": False  # Don't show yet (future expansion)
    },
    "10 Mile Music Hall": {
        "location": "Frisco",
        "image": "images/default.jpg",
        "include": False  # Skip this venue
    }
}

# Image download settings
IMAGE_DOWNLOAD_DIR = Path("images/z2")
DOWNLOAD_IMAGES = True  # Set to False to use venue default images instead

def scrape_events():
    """Scrape all events using Z2's AJAX endpoint"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.z2ent.com/events'
    }
    
    all_events = []
    seen_event_ids = set()  # Track unique events by ID
    offset = 0
    per_page = 12
    max_pages = 50  # Safety limit
    
    print("Scraping Z2 Entertainment events using events_ajax endpoint...")
    
    # First, get initial page
    print(f"\nFetching initial page...")
    try:
        response = requests.get("https://www.z2ent.com/events", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        event_items = soup.find_all('div', class_='eventItem')
        print(f"  Found {len(event_items)} events on initial page")
        
        # Parse initial events
        for item in event_items:
            try:
                event = parse_event_card(item)
                if event:
                    event_id = f"{event['venue']}|{event['title']}|{event['date']}"
                    if event_id not in seen_event_ids:
                        seen_event_ids.add(event_id)
                        all_events.append(event)
            except Exception as e:
                print(f"  Error parsing event: {e}")
                continue
        
        print(f"  Parsed {len(all_events)} unique events from initial page")
        
    except Exception as e:
        print(f"Error fetching initial page: {e}")
        return []
    
    # Now load more using AJAX endpoint
    offset = per_page  # Start at 12 (since we got 0-11 already)
    
    for page in range(1, max_pages):
        print(f"\nFetching page {page + 1} (offset: {offset})...")
        
        # Use the actual AJAX endpoint Z2 uses
        ajax_url = f"https://www.z2ent.com/events/events_ajax/{offset}"
        params = {
            'category': '0',
            'venue': '0',
            'team': '0',
            'exclude': '',
            'per_page': str(per_page),
            'came_from_page': 'event-list-page'
        }
        
        try:
            response = requests.get(ajax_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"  Status {response.status_code}, stopping")
                break
            
            # The response is a JSON string (wrapped in quotes) containing escaped HTML
            try:
                # Parse as JSON to get the HTML string
                html_string = response.json()
                
                # Check if we got an empty string
                if not html_string or len(html_string) < 100:
                    print("  Empty HTML string, stopping")
                    break
                
                # Now parse the HTML string with BeautifulSoup
                soup = BeautifulSoup(html_string, 'html.parser')
                
            except json.JSONDecodeError:
                # Fallback: try parsing response content directly as HTML
                if len(response.content) < 100:
                    print("  Empty response, stopping")
                    break
                soup = BeautifulSoup(response.content, 'html.parser')
            
            event_items = soup.find_all('div', class_='eventItem')
            
            if not event_items:
                print(f"  No more events found")
                break
            
            print(f"  Found {len(event_items)} events on this page")
            
            # Parse events and check for duplicates
            new_events_count = 0
            for item in event_items:
                try:
                    event = parse_event_card(item)
                    if event:
                        event_id = f"{event['venue']}|{event['title']}|{event['date']}"
                        
                        if event_id not in seen_event_ids:
                            seen_event_ids.add(event_id)
                            all_events.append(event)
                            new_events_count += 1
                        else:
                            print(f"  ⚠ Duplicate skipped: {event['title']}")
                except Exception as e:
                    print(f"  Error parsing event: {e}")
                    continue
            
            print(f"  New unique events from this page: {new_events_count}")
            
            # If we got no new events, stop
            if new_events_count == 0:
                print("  All events were duplicates, stopping")
                break
            
            # If we got fewer events than per_page, we're on the last page
            if len(event_items) < per_page:
                print(f"  Reached last page (got {len(event_items)} < {per_page})")
                break
            
            offset += per_page
            
        except Exception as e:
            print(f"  Error fetching page: {e}")
            break
    
    print(f"\n{'='*60}")
    print(f"Total unique events scraped: {len(all_events)}")
    print(f"{'='*60}")
    
    return all_events

def download_event_image(image_url, title, venue):
    """
    Download event image and save locally
    Returns local path if successful, None if failed
    """
    if not DOWNLOAD_IMAGES or not image_url or image_url == VENUE_INFO.get(venue, {}).get('image'):
        return None
    
    try:
        # Create images/z2 directory if it doesn't exist
        IMAGE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename from title
        # Use hash to keep filename length reasonable
        safe_title = re.sub(r'[^a-z0-9]+', '-', title.lower())[:50]
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
        
        # Determine file extension from URL
        ext = '.jpg'
        if '.png' in image_url.lower():
            ext = '.png'
        elif '.gif' in image_url.lower():
            ext = '.gif'
        elif '.webp' in image_url.lower():
            ext = '.webp'
        
        filename = f"{safe_title}-{url_hash}{ext}"
        filepath = IMAGE_DOWNLOAD_DIR / filename
        
        # Skip if already downloaded
        if filepath.exists():
            print(f"    Image already exists: {filepath}")
            return str(filepath)
        
        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.z2ent.com/'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # Save image
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"    Downloaded image: {filepath}")
        return str(filepath)
        
    except Exception as e:
        print(f"    Failed to download image: {e}")
        return None

def parse_event_card(card):
    """Parse individual event card based on Z2 Entertainment HTML structure"""
    
    # Extract venue name from div.location
    location_elem = card.find('div', class_='location')
    if not location_elem:
        return None
    
    venue_name = location_elem.get_text(strip=True)
    
    # Check if this is a venue we care about
    if venue_name not in VENUE_INFO:
        return None
    
    venue_config = VENUE_INFO[venue_name]
    
    # Skip if we're not including this venue yet
    if not venue_config['include']:
        print(f"Skipping {venue_name} event (not included yet)")
        return None
    
    # Extract event title from h3.title a
    title_elem = card.find('h3', class_='title')
    if not title_elem:
        return None
    
    title_link = title_elem.find('a')
    if not title_link:
        return None
    
    title = title_link.get_text(strip=True)
    
    # Extract link
    link = title_link.get('href', '')
    if link and not link.startswith('http'):
        link = f"https://www.z2ent.com{link}"
    
    # Extract date from span.m-date__singleDate structure
    date_container = card.find('span', class_='m-date__singleDate')
    if not date_container:
        return None
    
    # Parse date parts
    weekday = date_container.find('span', class_='m-date__weekday')
    month = date_container.find('span', class_='m-date__month')
    day = date_container.find('span', class_='m-date__day')
    year = date_container.find('span', class_='m-date__year')
    
    if not all([month, day, year]):
        return None
    
    # Build date string
    month_text = month.get_text(strip=True).replace(',', '').strip()
    day_text = day.get_text(strip=True)
    year_text = year.get_text(strip=True).replace(',', '').strip()
    
    date_str = f"{month_text} {day_text}, {year_text}"
    formatted_date = parse_date(date_str)
    
    # Extract time if available (not in provided HTML, but check)
    time_elem = card.find('div', class_='time') or card.find('span', class_='time')
    time = time_elem.get_text(strip=True) if time_elem else ""
    
    # Extract image from div.thumb
    thumb_elem = card.find('div', class_='thumb')
    remote_image_url = None
    if thumb_elem:
        img = thumb_elem.find('img')
        if img and img.get('src'):
            img_src = img['src']
            if img_src.startswith('http'):
                remote_image_url = img_src
            elif img_src.startswith('//'):
                remote_image_url = f"https:{img_src}"
            elif img_src.startswith('/'):
                remote_image_url = f"https://www.z2ent.com{img_src}"
    
    # Download image locally (or use venue default)
    local_image_path = download_event_image(remote_image_url, title, venue_name)
    final_image = local_image_path if local_image_path else venue_config['image']
    
    # Check ticket status
    ticket_elem = card.find('a', class_='tickets')
    ticket_status = ""
    if ticket_elem:
        ticket_text = ticket_elem.get_text(strip=True)
        if "FREE" in ticket_text.upper():
            ticket_status = "Free Event"
        elif "SOLD OUT" in ticket_text.upper():
            ticket_status = "Sold Out"
    
    event = {
        "title": title,
        "venue": venue_name,
        "location": venue_config['location'],
        "date": formatted_date,
        "time": time,
        "image": final_image,  # Use downloaded local image
        "link": link,
        "description": "",
        "additional_info": ticket_status,
        "event_type_tags": ["Live Music", "Concert"]
    }
    
    print(f"✓ {title} at {venue_name} on {formatted_date}")
    return event

def parse_date(date_str):
    """Parse date string to 'Month DD, YYYY' format"""
    try:
        # Z2 Entertainment format: "Jan 11, 2026"
        date_str = date_str.strip()
        
        # Try to parse as-is first
        try:
            date_obj = datetime.strptime(date_str, "%b %d, %Y")
            return date_obj.strftime("%B %d, %Y")
        except ValueError:
            pass
        
        # Other common formats to try
        formats = [
            "%B %d, %Y",       # "January 10, 2025"
            "%m/%d/%Y",        # "01/10/2025"
            "%m-%d-%Y",        # "01-10-2025"
            "%Y-%m-%d",        # "2025-01-10"
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%B %d, %Y")
            except ValueError:
                continue
        
        # If none of the formats work, return original
        print(f"Warning: Could not parse date '{date_str}'")
        return date_str
        
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return date_str

def save_events(events):
    """Save events to JSON file"""
    output_file = "z2_entertainment_events.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(events)} events to {output_file}")

def main():
    print("=" * 60)
    print("Z2 Entertainment Events Scraper")
    print("=" * 60)
    print("\nVenues:")
    print("  • Boulder Theater (Boulder) - INCLUDED")
    print("  • Fox Theatre (Boulder) - INCLUDED")
    print("  • Aggie Theatre (Fort Collins) - SCRAPED, NOT SHOWN")
    print("  • 10 Mile Music Hall - SKIPPED")
    print()
    
    events = scrape_events()
    
    if events:
        save_events(events)
        print(f"\n✓ Successfully scraped {len(events)} events")
    else:
        print("\n✗ No events found")
        print("\nTroubleshooting:")
        print("1. Check if the website structure has changed")
        print("2. Update CSS selectors in parse_event_card()")
        print("3. Verify the events page URL is correct")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
