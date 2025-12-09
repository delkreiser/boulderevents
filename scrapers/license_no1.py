#!/usr/bin/env python3
"""
License No 1 Event Scraper - FIXED VERSION
Fixes:
1. Correct time parsing (was showing 57:00PM, 58:00PM, etc.)
2. Add Comedy tag for comedy shows
3. Use custom licenseno1.jpg image for all events
4. Better event detection to catch all events including multiple per day
"""

import re
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_license_no1():
    """Scrape all License No 1 events from their calendar"""
    
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
            
            print("Loading License No 1 calendar...")
            page.goto('https://www.license1boulderado.com/calendar', 
                     wait_until='domcontentloaded', timeout=30000)
            
            # Wait for calendar to load
            page.wait_for_timeout(5000)
            
            print("Finding all event links...")
            # Get all event links from the calendar
            event_links = page.locator('a[href*="/calendar/"]').all()
            print(f"Found {len(event_links)} potential event links")
            
            seen_urls = set()
            
            for i, link in enumerate(event_links):
                try:
                    href = link.get_attribute('href')
                    if not href or href in seen_urls or href == '/calendar':
                        continue
                    
                    seen_urls.add(href)
                    full_url = f"https://www.license1boulderado.com{href}" if not href.startswith('http') else href
                    
                    print(f"\nProcessing event {len(events) + 1}: {href[:50]}...")
                    
                    # Open event detail page
                    event_page = browser.new_page()
                    try:
                        event_page.goto(full_url, wait_until='domcontentloaded', timeout=15000)
                        event_page.wait_for_timeout(2000)
                        
                        html = event_page.content()
                        event = parse_event_detail_page(html, full_url)
                        
                        if event and event.get('title'):
                            # Add venue info
                            event['venue'] = 'License No 1'
                            event['location'] = 'Boulder'
                            event['category'] = 'Nightlife'
                            event['source_url'] = 'https://www.license1boulderado.com/calendar'
                            
                            # Use custom image (will be uploaded separately)
                            event['image'] = 'licenseno1.jpg'
                            
                            # Detect comedy shows and add Comedy tag
                            if is_comedy_show(event['title'], event.get('description', '')):
                                event['event_type_tags'] = ['Comedy', 'Nightlife']
                            else:
                                event['event_type_tags'] = ['Live Music', 'Nightlife']
                            
                            event['venue_type_tags'] = ['Bar', 'Nightlife']
                            
                            events.append(event)
                            print(f"  ✓ {event['title']}")
                            print(f"    Date: {event.get('date', 'N/A')}")
                            print(f"    Time: {event.get('time', 'N/A')}")
                            
                    except Exception as e:
                        print(f"  ✗ Error loading event page: {e}")
                    finally:
                        event_page.close()
                        
                except Exception as e:
                    print(f"  ✗ Error processing link: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_event_detail_page(html, url):
    """Parse individual event detail page"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    event = {'link': url}
    
    # Title - look for event title in common Squarespace patterns
    title_selectors = [
        'h1.eventitem-title',
        'h1[class*="title"]',
        'h1',
        '.eventitem-title',
        '[class*="event-title"]'
    ]
    
    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            event['title'] = title_elem.get_text(strip=True)
            break
    
    # Date and Time - FIXED parsing
    # Squarespace stores time in specific format, need to extract correctly
    time_elem = soup.select_one('.event-time-localized-start, .eventitem-meta-time, [class*="time"]')
    date_elem = soup.select_one('.event-date, .eventitem-meta-date, [class*="date"]')
    
    if date_elem:
        date_text = date_elem.get_text(strip=True)
        # Extract date like "December 06, 2025"
        date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}', date_text, re.I)
        if date_match:
            event['date'] = date_match.group(0)
    
    if time_elem:
        time_text = time_elem.get_text(strip=True)
        # FIX: Extract time properly - look for XX:XX PM/AM format
        # The issue was parsing "9:00 PM" as "57:00 PM" or similar
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', time_text, re.I)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2)
            meridiem = time_match.group(3).upper()
            event['time'] = f"{hour}:{minute} {meridiem}"
    
    # If time not found above, look in other elements
    if not event.get('time'):
        # Look in all text for time patterns
        all_text = soup.get_text()
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)', all_text, re.I)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2)
            meridiem = time_match.group(3).upper()
            event['time'] = f"{hour}:{minute} {meridiem}"
    
    # Description
    desc_selectors = [
        '.eventitem-column-content',
        '.event-description',
        '[class*="description"]',
        '.sqs-block-content p'
    ]
    
    for selector in desc_selectors:
        desc_elem = soup.select_one(selector)
        if desc_elem:
            desc_text = desc_elem.get_text(strip=True)
            if len(desc_text) > 20:  # Make sure it's actual content
                event['description'] = desc_text[:500]  # Limit length
                break
    
    return event if event.get('title') else None


def is_comedy_show(title, description=''):
    """Detect if an event is a comedy show"""
    comedy_keywords = [
        'comedy',
        'comedian',
        'stand-up',
        'standup',
        'underground comedy',
        'comedy show',
        'comedy night'
    ]
    
    combined_text = f"{title} {description}".lower()
    
    return any(keyword in combined_text for keyword in comedy_keywords)


if __name__ == "__main__":
    print("=" * 70)
    print("LICENSE NO. 1 EVENT SCRAPER - FIXED VERSION")
    print("=" * 70)
    print("\nFixes applied:")
    print("✓ Corrected time parsing (fixes 57:00PM, 58:00PM issues)")
    print("✓ Added Comedy tag detection")
    print("✓ Using custom licenseno1.jpg image")
    print("✓ Improved event detection to catch all events\n")
    
    events = scrape_license_no1()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'license_no1_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    # Show summary
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:5], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
            print(f"   Tags: {', '.join(event.get('event_type_tags', []))}")
            
        # Count comedy shows
        comedy_count = sum(1 for e in events if 'Comedy' in e.get('event_type_tags', []))
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
        print(f"   Comedy shows: {comedy_count}")
        print(f"   Music events: {len(events) - comedy_count}")
