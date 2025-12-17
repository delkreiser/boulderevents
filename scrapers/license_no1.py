#!/usr/bin/env python3
"""
License No 1 Event Scraper - PRODUCTION VERSION
Scrapes directly from calendar page HTML - simple and fast!
"""

import re
import json
from datetime import datetime, date
import pytz
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def scrape_license_no1():
    """Scrape License No 1 events from calendar page"""
    
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
            page.wait_for_timeout(3000)
            
            # Scroll to load all events (Squarespace uses lazy loading)
            print("Scrolling to load all events...")
            for i in range(5):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1500)
            
            # Scroll back to top
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(1000)
            
            print("Parsing calendar HTML...")
            html = page.content()
            events = parse_calendar_html(html)
            
            browser.close()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return events


def parse_calendar_html(html):
    """Parse the calendar HTML to extract all events"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all event items
    event_items = soup.find_all(class_=re.compile(r'eventlist-event', re.I))
    print(f"Found {len(event_items)} total events in HTML")
    
    # Also try the specific class you mentioned
    upcoming_items = soup.find_all('article', class_='eventlist-event--upcoming')
    print(f"Found {len(upcoming_items)} events with 'eventlist-event--upcoming' class")
    
    # Use whichever finds more events
    if len(upcoming_items) > len(event_items):
        event_items = upcoming_items
        print(f"Using upcoming_items instead")
    
    events = []
    mountain_tz = pytz.timezone('America/Denver')
    today = datetime.now(mountain_tz).date()
    
    print(f"\nProcessing {len(event_items)} event items...")
    
    for idx, item in enumerate(event_items, 1):
        event = parse_event_item(item)
        
        if event and event.get('title'):
            print(f"\n  Event {idx}: {event.get('title')}")
            print(f"    Date: {event.get('date')}")
            print(f"    Start datetime: {event.get('start_datetime')}")
            print(f"    Time: {event.get('time_start')}")
            
            # Filter: Only include today and future events
            if event.get('start_date_obj'):
                print(f"    Date object: {event['start_date_obj']}")
                print(f"    Today: {today}")
                print(f"    Is future/today: {event['start_date_obj'] >= today}")
                
                if event['start_date_obj'] >= today:
                    # Add metadata
                    event['venue'] = 'License No 1'
                    event['location'] = 'Boulder'
                    event['category'] = 'Nightlife'
                    event['source_url'] = 'https://www.license1boulderado.com/calendar'
                    event['image'] = 'licenseno1.jpg'
                    
                    # Detect comedy shows
                    if is_comedy_show(event['title']):
                        event['event_type_tags'] = ['Comedy', 'Nightlife']
                    else:
                        event['event_type_tags'] = ['Live Music', 'Nightlife']
                    
                    event['venue_type_tags'] = ['Bar', 'Nightlife']
                    
                    # Remove internal date object (not JSON serializable)
                    del event['start_date_obj']
                    if 'end_date_obj' in event:
                        del event['end_date_obj']
                    
                    events.append(event)
                    print(f"    ✓ ADDED to output")
                else:
                    print(f"    ✗ SKIPPED (past event)")
            else:
                print(f"    ✗ SKIPPED (no date object)")
        else:
            print(f"\n  Event {idx}: SKIPPED (no title or failed to parse)")
    
    # Sort by start date/time (earliest first)
    events.sort(key=lambda e: (e.get('start_datetime', ''), e.get('time_start', '')))
    
    print(f"\nFiltered to {len(events)} current/future events")
    
    return events


def parse_event_item(item):
    """Parse a single event item from the calendar"""
    
    event = {}
    
    # Title and Link
    title_elem = item.find('h1', class_='eventlist-title')
    if title_elem:
        link_elem = title_elem.find('a', class_='eventlist-title-link')
        if link_elem:
            event['title'] = link_elem.get_text(strip=True)
            href = link_elem.get('href', '')
            event['link'] = f"https://www.license1boulderado.com{href}" if href.startswith('/') else href
    
    # Find all date and time elements
    date_elems = item.find_all('time', class_='event-date')
    time_elems = item.find_all('time', class_=re.compile(r'event-time-localized'))
    
    # Start date and time
    if len(date_elems) > 0:
        event['date'] = date_elems[0].get_text(strip=True)
        event['start_datetime'] = date_elems[0].get('datetime', '')
        
        # Parse date for filtering
        try:
            event['start_date_obj'] = datetime.fromisoformat(event['start_datetime']).date()
        except:
            pass
    
    if len(time_elems) > 0:
        # Find start time specifically
        time_start_elem = item.find('time', class_='event-time-localized-start')
        if time_start_elem:
            event['time_start'] = time_start_elem.get_text(strip=True)
        else:
            # Fallback to first time element
            event['time_start'] = time_elems[0].get_text(strip=True)
    
    # End date and time (for multi-day events like NYE)
    if len(date_elems) > 1:
        event['end_date'] = date_elems[1].get_text(strip=True)
        event['end_datetime'] = date_elems[1].get('datetime', '')
        
        try:
            event['end_date_obj'] = datetime.fromisoformat(event['end_datetime']).date()
        except:
            pass
    
    if len(time_elems) > 1:
        # Find end time specifically
        time_end_elem = item.find('time', class_='event-time-localized-end')
        if time_end_elem:
            event['time_end'] = time_end_elem.get_text(strip=True)
        else:
            # Fallback to second time element for multi-day events
            event['time_end'] = time_elems[1].get_text(strip=True)
    
    # Create combined time field for display
    if event.get('time_start') and event.get('time_end'):
        # Check if it's a multi-day event
        if event.get('end_date') and event.get('end_date') != event.get('date'):
            event['time'] = f"{event['time_start']} ({event['date']}) - {event['time_end']} ({event['end_date']})"
        else:
            event['time'] = f"{event['time_start']} - {event['time_end']}"
    elif event.get('time_start'):
        event['time'] = event['time_start']
    else:
        event['time'] = 'TBD'
    
    return event if event.get('title') else None


def is_comedy_show(title):
    """Detect if an event is a comedy show"""
    comedy_keywords = [
        'comedy', 'comedian', 'stand-up', 'standup',
        'underground comedy', 'comedy show', 'comedy night'
    ]
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in comedy_keywords)


if __name__ == "__main__":
    print("=" * 70)
    print("LICENSE NO. 1 EVENT SCRAPER - PRODUCTION VERSION")
    print("=" * 70)
    
    events = scrape_license_no1()
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS: Found {len(events)} current/future events")
    print(f"{'=' * 70}\n")
    
    # Save to JSON
    output_file = 'license_no1_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to {output_file}\n")
    
    if events:
        print("Sample events:")
        for i, event in enumerate(events[:10], 1):
            print(f"\n{i}. {event.get('title')}")
            print(f"   Date: {event.get('date', 'N/A')}")
            print(f"   Time: {event.get('time', 'N/A')}")
            print(f"   Tags: {', '.join(event.get('event_type_tags', []))}")
            print(f"   Link: {event.get('link', 'N/A')[:60]}...")
        
        # Statistics
        comedy_count = sum(1 for e in events if 'Comedy' in e.get('event_type_tags', []))
        music_count = len(events) - comedy_count
        
        print(f"\n📊 Statistics:")
        print(f"   Total events: {len(events)}")
        print(f"   Comedy shows: {comedy_count}")
        print(f"   Music events: {music_count}")
        
        # Check for multi-day events
        multiday = [e for e in events if e.get('end_date')]
        if multiday:
            print(f"   Multi-day events: {len(multiday)}")
            for e in multiday:
                print(f"     - {e['title']}: {e['time']}")
