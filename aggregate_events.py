"""
Boulder Events Aggregator
Combines all venue scrapers and creates a unified events database with tags
"""

import json
from datetime import datetime
import re
from pathlib import Path

# Try to use pytz for Mountain Time, fall back to UTC if not available
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    print("Note: pytz not installed, using UTC time (may cause timezone issues)")
    print("Install with: pip install pytz")


class EventAggregator:
    """Aggregates events from multiple venues with proper tagging"""
    
    def __init__(self):
        self.events = []
        self.venue_configs = {
            'Velvet Elk Lounge': {
                'location': 'Boulder',
                'tags': ['Music', 'Live Music', 'Bar', 'Nightlife'],
                'scraper_output': 'velvet_elk_events.json'
            },
            'Junkyard Social Club': {
                'location': 'Boulder',
                'tags': ['Community', 'Arts', 'Performance', 'All Ages'],  # Removed 'Dance' - not all events involve dancing
                'scraper_output': 'junkyard_events.json'
            },
            'Mountain Sun Pubs': {
                'location': 'Boulder',  # Default location, actual location in each event
                'tags': ['Music', 'Pub', 'Bar', 'Food & Drink'],
                'scraper_output': 'mountain_sun_events.json'
            },
            'St Julien Hotel & Spa': {
                'location': 'Boulder',
                'tags': ['Entertainment', 'Hotel', 'Upscale'],
                'scraper_output': 'st_julien_events.json'
            },
            'Trident Booksellers & Cafe': {
                'location': 'Boulder',
                'tags': ['Books', 'Literary', 'Cafe', 'Arts'],
                'scraper_output': 'trident_events.json'
            },
            'License No 1': {
                'location': 'Boulder',
                'tags': ['Nightlife', 'Bar', '21+'],  # Removed Music, will use event-specific tags
                'scraper_output': 'license_no1_events.json'
            },
            'Jungle': {
                'location': 'Boulder',
                'tags': ['Music', 'Live Music', 'Bar', 'Nightlife'],
                'scraper_output': 'jungle_events.json'
            },
            'Rosetta Hall': {
                'location': 'Boulder',
                'tags': ['Music', 'Nightlife', 'Dance', 'DJ', '21+'],
                'scraper_output': 'rosetta_hall_events.json'
            },
            'Gold Hill Inn': {
                'location': 'Gold Hill',
                'tags': ['Live Music', 'Restaurant', 'Historic'],
                'scraper_output': 'gold_hill_inn_events.json'
            },
            '300 Suns Brewing': {
                'location': 'Longmont',
                'tags': ['Brewery', 'Live Music', 'Family Friendly'],
                'scraper_output': '300_suns_events.json'
            },
            'Bricks on Main': {
                'location': 'Longmont',
                'tags': ['Community', 'Retail', 'Entertainment'],
                'scraper_output': 'bricks_events.json'
            },
            'Roots Music Project': {
                'location': 'Boulder',
                'tags': ['Live Music', 'Community'],
                'scraper_output': 'roots_music_events.json'
            },
        }
    
    def load_events_from_file(self, filepath):
        """Load events from a JSON file"""
        if not Path(filepath).exists():
            print(f"Warning: {filepath} does not exist, skipping...")
            return []
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return []
    
    def extract_event_type_tags(self, event):
        """Extract event type tags from event data"""
        tags = set()
        
        # Check categories field (can be list or string)
        if event.get('categories'):
            categories = event['categories']
            # Handle both list and string formats
            if isinstance(categories, list):
                cat_list = categories
            else:
                cat_list = [categories]
            
            for cat in cat_list:
                if 'Dance' in cat or 'Music' in cat:
                    tags.add('Music')
                if 'Community' in cat:
                    tags.add('Community')
                if 'Performance' in cat:
                    tags.add('Performance')
                if 'Educational' in cat:
                    tags.add('Educational')
                if 'Family Fun' in cat:
                    tags.add('Family Friendly')
        
        # Check category field (singular)
        if event.get('category'):
            category = event['category']
            if 'Music' in category:
                tags.add('Music')
            if 'Entertainment' in category:
                tags.add('Entertainment')
            if 'Books' in category or 'Literary' in category:
                tags.add('Books & Literary')
            if 'Nightlife' in category:
                tags.add('Nightlife')
            if 'Community' in category:
                tags.add('Community')
        
        # Check age restrictions
        if event.get('age_restriction'):
            age = event['age_restriction']
            if 'All Ages' in age or 'Family' in age:
                tags.add('All Ages')
            elif '21+' in age or '18+' in age:
                tags.add('21+')
        
        return list(tags)
    
    def normalize_date(self, event):
        """Normalize date format for better sorting and filtering"""
        date_str = event.get('date', '')
        
        if not date_str:
            return None
        
        # Try to parse various date formats
        date_patterns = [
            (r'(\w+day),\s+(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})', '%A, %B %d, %Y'),
            (r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})', '%B %d, %Y'),
            (r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?', '%B %d'),
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),
        ]
        
        for pattern, date_format in date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    # Clean up the matched string
                    matched_str = match.group(0)
                    # Remove ordinal suffixes
                    cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', matched_str)
                    
                    # Parse the date
                    if '%Y' not in date_format:
                        # Add current year if not specified
                        cleaned += f", {datetime.now().year}"
                        date_format += ", %Y"
                    
                    parsed_date = datetime.strptime(cleaned, date_format)
                    return parsed_date.isoformat()
                except Exception as e:
                    print(f"Error parsing date '{date_str}': {e}")
                    continue
        
        return None
    
    def aggregate_all_events(self):
        """Load and aggregate all events from all venues"""
        all_events = []
        
        # Use Mountain Time for Colorado events if pytz is available
        if PYTZ_AVAILABLE:
            mountain_tz = pytz.timezone('America/Denver')
            today = datetime.now(mountain_tz).date()
        else:
            today = datetime.now().date()  # Fall back to system time
        
        for venue_name, config in self.venue_configs.items():
            print(f"\nProcessing {venue_name}...")
            
            # Load events from file
            events = self.load_events_from_file(config['scraper_output'])
            
            for event in events:
                # Get the venue name from the event or use the config key
                event_venue = event.get('venue', venue_name)
                
                # Get venue config (handle cases where event venue might be more specific)
                venue_config = self.venue_configs.get(event_venue, config)
                
                # Normalize the date first
                normalized_date = self.normalize_date(event)
                
                # Skip past events (before today, but include today's events)
                if normalized_date:
                    try:
                        event_date = datetime.fromisoformat(normalized_date).date()
                        if event_date < today:
                            print(f"  Skipping past event: {event.get('title', 'Unknown')} ({event.get('date')})")
                            continue  # Skip events before today
                    except Exception as e:
                        print(f"  Error parsing date for {event.get('title')}: {e}")
                        pass  # If parsing fails, include the event anyway
                
                # Get location from event first, fall back to venue config
                event_location = event.get('location', venue_config['location'])
                
                # Create enriched event
                enriched_event = {
                    'id': self.generate_event_id(event),
                    'title': event.get('title', 'Untitled Event'),
                    'venue': event_venue,
                    'location': event_location,
                    'date': event.get('date'),
                    'normalized_date': normalized_date,
                    'recurring': event.get('recurring'),
                    'time': event.get('time'),
                    'description': event.get('description', ''),
                    'additional_info': event.get('additional_info', ''),  # NEW: Additional notes
                    'link': event.get('link'),
                    'image': event.get('image'),
                    'source_url': event.get('source_url'),
                    'age_restriction': event.get('age_restriction'),
                    
                    # Tags
                    'venue_tag': event_venue,
                    'location_tag': event_location,
                    'venue_type_tags': venue_config['tags'],
                    # Use event's tags if available, otherwise extract
                    'event_type_tags': event.get('event_type_tags', self.extract_event_type_tags(event)),
                }
                
                all_events.append(enriched_event)
            
            print(f"  Loaded {len(events)} events from {venue_name}")
        
        self.events = all_events
        return all_events
    
    def generate_event_id(self, event):
        """Generate a unique ID for each event"""
        # Create ID from venue + title + date + time (to handle multiple events per day)
        venue = event.get('venue', 'unknown')
        title = event.get('title', 'untitled')
        date = event.get('date', event.get('recurring', 'recurring'))
        time = event.get('time', event.get('time_start', ''))  # Include time for uniqueness
        
        id_string = f"{venue}_{title}_{date}_{time}".lower()
        # Clean up the string
        id_string = re.sub(r'[^a-z0-9]+', '_', id_string)
        id_string = re.sub(r'_+', '_', id_string).strip('_')
        
        return id_string
    
    def get_all_tags(self):
        """Get all unique tags from events"""
        venue_tags = set()
        location_tags = set()
        venue_type_tags = set()
        event_type_tags = set()
        
        for event in self.events:
            venue_tags.add(event['venue_tag'])
            location_tags.add(event['location_tag'])
            venue_type_tags.update(event['venue_type_tags'])
            event_type_tags.update(event['event_type_tags'])
        
        return {
            'venues': sorted(list(venue_tags)),
            'locations': sorted(list(location_tags)),
            'venue_types': sorted(list(venue_type_tags)),
            'event_types': sorted(list(event_type_tags))
        }
    
    def save_aggregated_events(self, output_file='all_boulder_events.json'):
        """Save all aggregated events to a single JSON file"""
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'total_events': len(self.events),
            'tags': self.get_all_tags(),
            'events': self.events
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Saved {len(self.events)} events to {output_file}")
        print(f"{'='*60}")
        
        return output_file


def main():
    """Main aggregation function"""
    print("Boulder Events Aggregator")
    print("="*60)
    
    aggregator = EventAggregator()
    events = aggregator.aggregate_all_events()
    
    print(f"\n{'='*60}")
    print(f"Total events aggregated: {len(events)}")
    print(f"{'='*60}")
    
    # Show tag summary
    tags = aggregator.get_all_tags()
    print(f"\nAvailable Tags:")
    print(f"  Venues: {', '.join(tags['venues'])}")
    print(f"  Locations: {', '.join(tags['locations'])}")
    print(f"  Venue Types: {', '.join(tags['venue_types'])}")
    print(f"  Event Types: {', '.join(tags['event_types'])}")
    
    # Save to file
    output_file = aggregator.save_aggregated_events()
    
    return output_file


if __name__ == "__main__":
    main()
