#!/usr/bin/env python3
"""
Google Sheets Scraper for Boulder Summer Concert Series
Scrapes event data from a Google Sheet and appends to all_boulder_events.json
"""

import json
import csv
import urllib.request
from datetime import datetime
from pathlib import Path

# Google Sheet URL (export as CSV)
SHEET_ID = "18zRuXOk4JB4Z8uMbJJuQ5TdBNurhtrWTFtw0RxAfyEw"
CSV_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Venue to image mapping
VENUE_IMAGES = {
    "Bands on the Bricks": "images/bandsonthebricks.jpg",
    "Rock & Rails": "images/rocknrails.jpg",
    "Louisville Street Faire": "images/streetfaire.jpg",
    "Village at The Peaks - Summer Concert Series": "images/village.jpg"
}

# City to location mapping
CITY_LOCATIONS = {
    "Niwot": "Niwot",
    "Louisville": "Louisville",
    "Lafayette": "Lafayette",
    "Boulder": "Boulder"
}

def download_sheet_as_csv():
    """Download Google Sheet as CSV"""
    print(f"Downloading sheet from Google Sheets...")
    with urllib.request.urlopen(CSV_EXPORT_URL) as response:
        csv_data = response.read().decode('utf-8')
    return csv_data

def parse_date(date_str):
    """Convert mm/dd/yyyy to 'Month DD, YYYY' format"""
    try:
        date_obj = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return date_obj.strftime("%B %d, %Y")
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return date_str

def scrape_events():
    """Scrape events from Google Sheet"""
    csv_data = download_sheet_as_csv()
    
    events = []
    reader = csv.DictReader(csv_data.splitlines())
    
    for row in reader:
        # Skip empty rows
        if not row.get('Event') or not row.get('Venue'):
            continue
        
        event_name = row['Event'].strip()
        venue = row['Venue'].strip()
        city = row['City'].strip()
        day = row.get('Day', '').strip()
        date_raw = row['Date'].strip()
        time = row['Time'].strip()
        info = row.get('Info', '').strip()
        url = row.get('url', '').strip()
        
        # Format date
        formatted_date = parse_date(date_raw)
        
        # Get location
        location = CITY_LOCATIONS.get(city, city)
        
        # Get venue image
        image = VENUE_IMAGES.get(venue, "images/default.jpg")
        
        # Create event object
        event = {
            "name": event_name,
            "venue": venue,
            "location": location,
            "date": formatted_date,
            "time": time,
            "image": image,
            "url": url,
            "tags": ["Live Music", "All Ages", "Free"],
            "normalized_date": datetime.strptime(date_raw, "%m/%d/%Y").strftime("%Y-%m-%d")
        }
        
        # Add info if present
        if info:
            event["info"] = info
        
        # Add day if present
        if day:
            event["day"] = day
        
        events.append(event)
        print(f"✓ Added: {event_name} at {venue} on {formatted_date}")
    
    return events

def merge_with_existing(new_events):
    """Merge new events with existing all_boulder_events.json"""
    json_file = Path("all_boulder_events.json")
    
    # Load existing events
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing_events = data.get('events', [])
    else:
        existing_events = []
        data = {}
    
    print(f"\nExisting events: {len(existing_events)}")
    print(f"New events: {len(new_events)}")
    
    # Create set of existing event identifiers to avoid duplicates
    existing_ids = set()
    for event in existing_events:
        event_id = f"{event.get('name', '')}|{event.get('venue', '')}|{event.get('normalized_date', '')}"
        existing_ids.add(event_id)
    
    # Add new events that don't exist
    added_count = 0
    for event in new_events:
        event_id = f"{event['name']}|{event['venue']}|{event['normalized_date']}"
        if event_id not in existing_ids:
            existing_events.append(event)
            added_count += 1
        else:
            print(f"⊘ Skipped duplicate: {event['name']} at {event['venue']}")
    
    # Sort by normalized_date
    existing_events.sort(key=lambda x: x.get('normalized_date', ''))
    
    # Update data
    data['events'] = existing_events
    
    # Save back to file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Added {added_count} new events")
    print(f"✓ Total events: {len(existing_events)}")
    print(f"✓ Saved to {json_file}")

def main():
    """Main function"""
    print("=" * 60)
    print("Boulder Summer Concert Series Scraper")
    print("=" * 60)
    
    try:
        # Scrape events from Google Sheet
        events = scrape_events()
        
        if not events:
            print("\n⚠ No events found in sheet")
            return
        
        # Merge with existing events
        merge_with_existing(events)
        
        print("\n" + "=" * 60)
        print("✓ Scraping completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
