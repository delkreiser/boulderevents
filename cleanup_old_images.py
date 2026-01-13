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
    
    # Track which images are still in use
    active_images = set()
    
    for event in events:
        # Check if event has passed
        normalized_date = event.get('normalized_date')
        if not normalized_date:
            continue
        
        try:
            event_date = datetime.fromisoformat(normalized_date).date()
            
            # If event is today or in the future, keep its image
            if event_date >= today:
                image_path = event.get('image')
                if image_path and image_path.startswith('images/z2/'):
                    active_images.add(image_path)
        except Exception as e:
            print(f"Error parsing date for {event.get('title')}: {e}")
            continue
    
    # Find all Z2 images in directory
    z2_image_dir = Path("images/z2")
    if not z2_image_dir.exists():
        print("No images/z2 directory found, nothing to clean up")
        return
    
    all_z2_images = set()
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']:
        all_z2_images.update(z2_image_dir.glob(ext))
    
    # Delete images that are no longer in use
    deleted_count = 0
    for image_path in all_z2_images:
        # Convert Path object to string with forward slashes (matches JSON format)
        relative_path = str(image_path).replace('\\', '/')
        
        if relative_path not in active_images:
            try:
                image_path.unlink()
                print(f"  Deleted old image: {relative_path}")
                deleted_count += 1
            except Exception as e:
                print(f"  Error deleting {relative_path}: {e}")
        else:
            print(f"  Keeping active image: {relative_path}")
    
    print(f"\n{'='*60}")
    print(f"Image Cleanup Complete")
    print(f"{'='*60}")
    print(f"Active images: {len(active_images)}")
    print(f"Deleted images: {deleted_count}")
    print(f"{'='*60}")

def main():
    print("="*60)
    print("Z2 Event Images Cleanup")
    print("="*60)
    print()
    
    cleanup_old_images()

if __name__ == "__main__":
    main()
