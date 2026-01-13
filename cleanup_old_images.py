#!/usr/bin/env python3
"""
Clean up old Z2 event images
Removes images for events that have already passed
Run this after aggregate_events.py in the workflow
"""

import json
from datetime import datetime
from pathlib import Path

# Try to use pytz for Mountain Time, fall back to UTC if not available
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    print("Note: pytz not installed, using UTC time")

def cleanup_old_images():
    """Remove images for past events"""
    
    # Load aggregated events
    events_file = Path("all_boulder_events.json")
    if not events_file.exists():
        print("No all_boulder_events.json found, skipping cleanup")
        return
    
    with open(events_file, 'r') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    
    # Get today's date
    if PYTZ_AVAILABLE:
        mountain_tz = pytz.timezone('America/Denver')
        today = datetime.now(mountain_tz).date()
    else:
        today = datetime.now().date()
    
    print(f"Today's date: {today}")
    print(f"Total events in JSON: {len(events)}")
    
    # Track which images are still in use
    active_images = set()
    
    for event in events:
        # Get normalized date, or try to parse from date field if missing
        normalized_date = event.get('normalized_date')
        
        if not normalized_date:
            # Try to parse from date field (e.g., "Jan 15, 2026")
            date_str = event.get('date')
            if date_str:
                try:
                    # Try parsing "Jan 15, 2026" format
                    from datetime import datetime
                    parsed_date = datetime.strptime(date_str, "%b %d, %Y")
                    normalized_date = parsed_date.strftime("%Y-%m-%d")
                except:
                    try:
                        # Try parsing "January 15, 2026" format
                        parsed_date = datetime.strptime(date_str, "%B %d, %Y")
                        normalized_date = parsed_date.strftime("%Y-%m-%d")
                    except:
                        print(f"  ⚠ Could not parse date for {event.get('title')}: {date_str}")
                        continue
            else:
                continue
        
        try:
            event_date = datetime.fromisoformat(normalized_date).date()
            
            # If event is today or in the future, keep its image
            if event_date >= today:
                image_path = event.get('image')
                if image_path and image_path.startswith('images/z2/'):
                    active_images.add(image_path)
                    print(f"  Active event: {event.get('title')} ({event_date}) - Image: {image_path}")
        except Exception as e:
            print(f"Error parsing date for {event.get('title')}: {e}")
            continue
    
    print(f"\nTotal active Z2 images in JSON: {len(active_images)}")
    if active_images:
        print("Active image paths:")
        for img in sorted(active_images):
            print(f"  - {img}")
    
    # Find all Z2 images in directory
    z2_image_dir = Path("images/z2")
    if not z2_image_dir.exists():
        print("\nNo images/z2 directory found, nothing to clean up")
        return
    
    all_z2_images = set()
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']:
        all_z2_images.update(z2_image_dir.glob(ext))
    
    print(f"\nTotal Z2 images in folder: {len(all_z2_images)}")
    if all_z2_images:
        print("Images in folder:")
        for img in sorted(all_z2_images):
            print(f"  - {str(img).replace(chr(92), '/')}")  # Show with forward slashes
    
    # Delete images that are no longer in use
    deleted_count = 0
    kept_count = 0
    
    for image_path in all_z2_images:
        # Convert Path object to string with forward slashes (matches JSON format)
        relative_path = str(image_path).replace('\\', '/')
        
        print(f"\nChecking: {relative_path}")
        print(f"  In active_images? {relative_path in active_images}")
        
        if relative_path not in active_images:
            try:
                image_path.unlink()
                print(f"  ✗ DELETED (not in active list)")
                deleted_count += 1
            except Exception as e:
                print(f"  ✗ Error deleting: {e}")
        else:
            kept_count += 1
            print(f"  ✓ KEPT (active event)")
    
    print(f"\n{'='*60}")
    print(f"Image Cleanup Complete")
    print(f"{'='*60}")
    print(f"Active images kept: {kept_count}")
    print(f"Old images deleted: {deleted_count}")
    print(f"{'='*60}")

def main():
    print("="*60)
    print("Z2 Event Images Cleanup")
    print("="*60)
    print()
    
    cleanup_old_images()

if __name__ == "__main__":
    main()
