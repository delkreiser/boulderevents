"""
Fix Dates Script
This script fixes date/time parsing issues in the event JSON files
Run this after scrapers complete to clean up the data
"""

import json
import re
from datetime import datetime


def fix_date_time_fields(event):
    """
    Fix events where times are in date field, or dates are missing
    """
    date_field = event.get('date', '')
    time_field = event.get('time')
    
    # If date field only contains time (like "7:30 PM" or "6:00 pm-9:00 pm")
    if date_field:
        # Check if it's just a time (no month/day/year)
        is_just_time = bool(re.match(r'^\d{1,2}:\d{2}\s*(AM|PM|am|pm)', date_field) or 
                           re.match(r'^\d{1,2}:\d{2}.*\d{1,2}:\d{2}', date_field))
        
        if is_just_time:
            # Move to time field
            event['time'] = date_field
            event['date'] = None
    
    return event


def process_file(filename):
    """Process a single JSON file"""
    print(f"\nProcessing {filename}...")
    
    try:
        with open(filename, 'r') as f:
            events = json.load(f)
        
        if not events:
            print(f"  No events in {filename}")
            return
        
        fixed_count = 0
        for event in events:
            original_date = event.get('date')
            event = fix_date_time_fields(event)
            if event.get('date') != original_date:
                fixed_count += 1
        
        # Save back
        with open(filename, 'w') as f:
            json.dump(events, f, indent=2)
        
        print(f"  ✅ Fixed {fixed_count} events in {filename}")
        
    except FileNotFoundError:
        print(f"  ⚠️  File not found: {filename}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    """Fix all event JSON files"""
    print("Fixing Date/Time Fields in Event JSONs")
    print("=" * 60)
    
    files_to_fix = [
        'st_julien_events.json',
        'license_no1_events.json',
        'trident_events.json',
        'velvet_elk_events.json',
        'junkyard_events.json',
        'mountain_sun_events.json',
        'etown_events.json',
    ]
    
    for filename in files_to_fix:
        process_file(filename)
    
    print("\n" + "=" * 60)
    print("Date fixing complete! Now run aggregate_events.py")


if __name__ == "__main__":
    main()
