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
        # Skip empty rows - use "Event Name" as the column header
        if not row.get('Event Name') or not row.get('Venue'):
            continue
        
        event_name = row['Event Name'].strip()
        venue = row['Venue'].strip()
        city = row['City'].strip()
        day = row.get('Day', '').strip()
        date_raw = row['Date'].strip()
        time = row['Time'].strip()
        info = row.get('Info', '').strip()
        url = row.get('url', '').strip()
        
        # Format date to match aggregator format
        formatted_date = parse_date(date_raw)
        
        # Get location
        location = CITY_LOCATIONS.get(city, city)
        
        # Get venue image
        image = VENUE_IMAGES.get(venue, "images/default.jpg")
        
        # Create event object in aggregator format
        event = {
            "title": event_name,
            "venue": venue,
            "location": location,
            "date": formatted_date,
            "time": time,
            "image": image,
            "link": url if url else None,
            "description": "",
            "additional_info": info if info else "",
            "event_type_tags": ["Live Music", "All Ages", "Free"]
        }
        
        events.append(event)
        print(f"✓ Added: {event_name} at {venue} on {formatted_date}")
    
    return events

def save_events(events):
    """Save events to summer_series_events.json for aggregator to process"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    output_file = script_dir / "summer_series_events.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(events)} events to {output_file}")
    print(f"✓ Run aggregate_events.py to merge into all_boulder_events.json")

def main():
    """Main function"""
    print("=" * 60)
    print("Boulder Summer Concert Series Scraper")
    print("=" * 60)
    print(f"Script location: {Path(__file__).parent}")
    print(f"Sheet ID: {SHEET_ID}")
    print(f"CSV URL: {CSV_EXPORT_URL}")
    
    try:
        print("\n1. Downloading Google Sheet...")
        # Scrape events from Google Sheet
        events = scrape_events()
        
        print(f"\n2. Found {len(events)} events")
        
        if not events:
            print("\n⚠ No events found in sheet")
            print("   - Check that sheet has data in rows 2+")
            print("   - Verify headers match: Event | Venue | City | Day | Date | Time | Info | url")
            print("   - Ensure sheet is publicly accessible")
            return
        
        print("\n3. Saving events...")
        # Save to intermediate JSON file
        save_events(events)
        
        print("\n" + "=" * 60)
        print("✓ Scraping completed successfully!")
        print("=" * 60)
        
    except urllib.error.HTTPError as e:
        print(f"\n✗ HTTP Error accessing Google Sheet: {e}")
        print(f"   Status Code: {e.code}")
        print("   - Check that sheet is set to 'Anyone with link can view'")
    except urllib.error.URLError as e:
        print(f"\n✗ URL Error: {e}")
        print("   - Check your internet connection")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
