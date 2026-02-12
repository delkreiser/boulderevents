#!/usr/bin/env python3
"""
eTown Hall Events Scraper
Scrapes events from eTown Hall in Boulder
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from pathlib import Path

# Configuration
BASE_URL = "https://www.etown.org/etown-hall/all-events/"
OUTPUT_FILE = "etown_events.json"
MAX_PAGES = 5  # Maximum pages to scrape (adjust if needed)

def scrape_page(page_num=1):
    """Scrape a single page of events"""
    if page_num == 1:
        url = BASE_URL
    else:
        url = f"{BASE_URL}?pno={page_num}"
    
    print(f"Scraping page {page_num}: {url}")
    
    # Add headers to look like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all event items (they use class "event-wrapper")
        event_items = soup.find_all('div', class_='event-wrapper')
        
        print(f"  DEBUG: Found {len(event_items)} event-wrapper divs")
        
        if not event_items:
            # Check if the content is there at all
            if "eTown Presents" in response.text:
                print(f"  DEBUG: Content IS in HTML but wrapper not found")
                print(f"  DEBUG: Trying to find any div with 'event' in class name...")
                event_divs = soup.find_all('div', class_=lambda x: x and 'event' in x.lower())
                print(f"  DEBUG: Found {len(event_divs)} divs with 'event' in class")
                if event_divs:
                    print(f"  DEBUG: First event div classes: {event_divs[0].get('class')}")
            print(f"  No events found on page {page_num}")
            return []
        
        events = []
        for item in event_items:
            event = parse_event(item)
            if event:
                events.append(event)
        
        print(f"  Found {len(events)} events on page {page_num}")
        return events
        
    except requests.RequestException as e:
        print(f"  Error scraping page {page_num}: {e}")
        return []

def parse_event(item):
    """Parse individual event item"""
    try:
        # Extract image from event-image div
        image_div = item.find('div', class_='event-image')
        image_url = None
        if image_div:
            img_tag = image_div.find('img')
            if img_tag:
                image_url = img_tag.get('src', '')
        
        # Extract event data from event-data div
        event_data_div = item.find('div', class_='event-data')
        if not event_data_div:
            return None
        
        # Extract title and URL
        title_elem = event_data_div.find('h2')
        if not title_elem:
            return None
        
        title_link = title_elem.find('a')
        if not title_link:
            return None
        
        title = title_link.get_text(strip=True)
        url = title_link.get('href', '')
        
        # Extract date/time and other data from event-data-block divs
        data_blocks = event_data_div.find_all('div', class_='event-data-block')
        
        date_str = None
        time_str = None
        venue = None
        categories = []
        
        for block in data_blocks:
            block_text = block.get_text(strip=True)
            
            # Check if this block contains date/time (has " - " pattern with times)
            if ' - ' in block_text and ('am' in block_text.lower() or 'pm' in block_text.lower()):
                # Parse date and time
                # Format: "February 14, 2026 - 7:00 pm - 9:30 pm"
                parts = block_text.split(' - ')
                if len(parts) >= 2:
                    date_str = parts[0].strip()  # "February 14, 2026"
                    if len(parts) == 3:
                        time_str = f"{parts[1].strip()} - {parts[2].strip()}"  # "7:00 pm - 9:30 pm"
                    else:
                        time_str = parts[1].strip()  # Just start time
            
            # Check for venue (typically "eTOWN HALL")
            elif block_text.upper() == block_text and len(block_text) > 3:
                venue = block_text
            
            # Check for categories
            elif block.find('ul', class_='event-categories'):
                cat_links = block.find_all('a')
                categories = [link.get_text(strip=True) for link in cat_links]
        
        # Default venue if not found
        if not venue:
            venue = "eTown Hall"
        
        # Parse date into normalized format
        normalized_date = None
        if date_str:
            try:
                # Try parsing "February 14, 2026" format
                parsed_date = datetime.strptime(date_str, "%B %d, %Y")
                normalized_date = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    # Try "Feb 14, 2026" format
                    parsed_date = datetime.strptime(date_str, "%b %d, %Y")
                    normalized_date = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        # Try "March 05, 2026" format (with leading zero)
                        parsed_date = datetime.strptime(date_str, "%B %d, %Y")
                        normalized_date = parsed_date.strftime("%Y-%m-%d")
                    except ValueError:
                        print(f"  Could not parse date: {date_str}")
        
        event = {
            "title": title,
            "venue": venue,
            "location": "Boulder",
            "date": date_str,
            "normalized_date": normalized_date,
            "time": time_str,
            "image": image_url,
            "url": url,
            "categories": categories,
            "tags": ["music", "live music", "concert"]  # eTown is primarily music venue
        }
        
        print(f"  ✓ Parsed: {title}")
        return event
        
    except Exception as e:
        print(f"  ✗ Error parsing event: {e}")
        return None

def scrape_all_events():
    """Scrape all pages of events"""
    all_events = []
    
    print("="*60)
    print("eTown Hall Events Scraper")
    print("="*60)
    
    for page_num in range(1, MAX_PAGES + 1):
        events = scrape_page(page_num)
        
        if not events:
            print(f"No events found on page {page_num}, stopping")
            break
        
        all_events.extend(events)
    
    return all_events

def save_events(events):
    """Save events to JSON file"""
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(events, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Saved {len(events)} events to {OUTPUT_FILE}")
    print(f"{'='*60}")

def main():
    events = scrape_all_events()
    
    if events:
        save_events(events)
        
        # Show event summary
        print(f"\nEvents Summary:")
        print(f"  Total events: {len(events)}")
        
        # Count by month
        months = {}
        for event in events:
            if event.get('date'):
                month = event['date'].split()[0]  # Get month name
                months[month] = months.get(month, 0) + 1
        
        if months:
            print(f"\nEvents by month:")
            for month, count in sorted(months.items()):
                print(f"    {month}: {count} events")
    else:
        print("\nNo events found")

if __name__ == "__main__":
    main()
