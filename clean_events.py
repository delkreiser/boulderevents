"""
Clean Events Script
Deduplicates recurring events and fixes venue names
Run this after scrapers complete
"""

import json


def deduplicate_recurring_events(events):
    """Remove duplicate recurring events - keep only one instance"""
    
    seen_recurring = set()
    cleaned_events = []
    
    for event in events:
        # If it's a recurring event, check if we've seen it before
        if event.get('recurring'):
            # Create a unique key from venue + title + recurring pattern
            key = f"{event.get('venue')}|{event.get('title')}|{event.get('recurring')}"
            
            if key in seen_recurring:
                continue  # Skip duplicate
            
            seen_recurring.add(key)
        
        cleaned_events.append(event)
    
    return cleaned_events


def fix_venue_names(events):
    """Fix venue names to match desired display names"""
    
    name_fixes = {
        'Mountain Sun Pub on Pearl': 'Mountain Sun Pub',
    }
    
    for event in events:
        if event.get('venue') in name_fixes:
            event['venue'] = name_fixes[event['venue']]
    
    return events


def process_file(filename):
    """Process a single JSON file"""
    print(f"Processing {filename}...")
    
    try:
        with open(filename, 'r') as f:
            events = json.load(f)
        
        if not events:
            print(f"  No events in {filename}")
            return
        
        original_count = len(events)
        
        # Deduplicate recurring events
        events = deduplicate_recurring_events(events)
        
        # Fix venue names
        events = fix_venue_names(events)
        
        # Save back
        with open(filename, 'w') as f:
            json.dump(events, f, indent=2)
        
        removed = original_count - len(events)
        if removed > 0:
            print(f"  ✅ Removed {removed} duplicate recurring events")
        else:
            print(f"  ✅ No duplicates found")
        
    except FileNotFoundError:
        print(f"  ⚠️  File not found: {filename}")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def main():
    """Clean all event JSON files"""
    print("Cleaning Event Data")
    print("=" * 60)
    
    files_to_clean = [
        'mountain_sun_events.json',  # Has duplicates
        'junkyard_events.json',
        'velvet_elk_events.json',
        'st_julien_events.json',
        'license_no1_events.json',
        'trident_events.json',
    ]
    
    for filename in files_to_clean:
        process_file(filename)
    
    print("\n" + "=" * 60)
    print("Cleaning complete!")


if __name__ == "__main__":
    main()
