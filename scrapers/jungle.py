"""
Jungle Rum Bar - Recurring Events
Since Jungle doesn't have an events page, this creates their recurring weekly event
"""

import json
from datetime import datetime, timedelta


def generate_jungle_events():
    """Generate recurring events for Jungle Rum Bar"""
    
    events = []
    
    # Live Jazz - Every Wednesday
    jazz_event = {
        'title': 'Live Jazz',
        'venue': 'Jungle',
        'location': 'Boulder',
        'recurring': 'Every Wednesday',
        'time': '7:00 PM - 9:00 PM',
        'description': 'Live Jazz with Max Moore, Zach Ritchie, and William George Kuepper V',
        'link': 'https://junglerumbar.com/',
        'source_url': 'https://junglerumbar.com/',
        'image': 'jungle.jpg',
        'category': 'Music',
        'age_restriction': '21+',
        'event_type_tags': ['Live Music', 'Jazz'],
        'venue_type_tags': ['Music', 'Live Music', 'Bar', 'Nightlife']
    }
    
    events.append(jazz_event)
    
    return events


if __name__ == "__main__":
    print("=" * 70)
    print("JUNGLE RUM BAR - RECURRING EVENTS")
    print("=" * 70)
    
    events = generate_jungle_events()
    
    print(f"\nGenerated {len(events)} recurring event(s)")
    print("=" * 70)
    
    # Save to JSON
    output_file = 'jungle_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved to {output_file}\n")
    
    # Display events
    for i, event in enumerate(events, 1):
        print(f"{i}. {event['title']}")
        print(f"   Venue: {event['venue']}")
        print(f"   Recurring: {event['recurring']}")
        print(f"   Time: {event['time']}")
        print(f"   Description: {event['description']}")
        print(f"   Tags: {', '.join(event['event_type_tags'])}")
        print(f"   Age: {event['age_restriction']}")
