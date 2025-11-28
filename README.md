# Boulder Events Calendar

A comprehensive event aggregation system for Boulder and Longmont, Colorado.

## 📊 Current Status

**Working Scrapers: 3/6**
- ✅ Velvet Elk Lounge (9 events)
- ✅ Junkyard Social Club (19 events)
- ✅ Mountain Sun Pub & Sister Locations (8 events across 4 venues)
- ⚠️ St Julien Hotel & Spa (needs Playwright)
- ⚠️ Trident Booksellers & Cafe (needs Playwright)
- ⚠️ License No 1 (needs Playwright)

**Total Events Available: 60 events**

## 🚀 Quick Start

### View the Calendar

1. Open `index.html` in any web browser
2. The calendar will automatically load events from `all_boulder_events.json`
3. Use filters to find events by venue, location, or type

### Update Events

Run the aggregator script to refresh all events:

```bash
python3 aggregate_events.py
```

This will:
- Load events from all scraper output files
- Add proper tags (venue, location, event type)
- Combine everything into `all_boulder_events.json`
- The web interface will automatically show the updates

## 📁 File Structure

```
/home/claude/
├── index.html                      # Web interface (open this in browser)
├── all_boulder_events.json         # Combined events database
├── aggregate_events.py             # Combines all events with tags
│
├── scrapers/                       # Individual venue scrapers
│   ├── velvet_elk.py              # ✅ Working
│   ├── junkyard_social_club.py    # ✅ Working
│   ├── mountain_sun_pub.py        # ✅ Working
│   ├── st_julien_entertainment.py # ⚠️ Needs Playwright
│   ├── trident_cafe.py            # ⚠️ Needs Playwright
│   └── license_no1.py             # ⚠️ Needs Playwright
│
└── Individual JSON outputs
    ├── velvet_elk_events.json
    ├── junkyard_events.json
    └── mountain_sun_events.json
```

## 🏷️ Tagging System

Each event has multiple tags for filtering:

### Venue Tags
- Exact venue name (e.g., "Velvet Elk Lounge", "Mountain Sun Pub on Pearl")

### Location Tags
- **Boulder** - Events in Boulder
- **Longmont** - Events in Longmont (Longs Peak Pub)

### Venue Type Tags
- Music, Live Music, Bar, Nightlife, Pub, Food & Drink
- Community, Arts, Dance, Performance
- Games, All Ages, 21+, Upscale, Books, Literary, Cafe

### Event Type Tags
- Music, Community, Performance, Educational
- All Ages, Family Friendly, 21+

## 🎯 Features

### Current Features
✅ Event aggregation from multiple sources
✅ Comprehensive tagging system
✅ Search functionality
✅ Filter by venue, location, and event type
✅ Clean, modern web interface
✅ Responsive design (mobile-friendly)
✅ Support for recurring events
✅ Event images

### Potential Future Features
- Date range filtering
- Calendar view (month/week/day)
- Sort by date
- Add to calendar (iCal export)
- Email notifications for new events
- User submissions via Google Form

## 🔧 Running the Full System

### Option 1: Simple (Current Working Venues Only)

The scrapers for Velvet Elk, Junkyard, and Mountain Sun work without any special setup:

```bash
# Run individual scrapers
python3 scrapers/velvet_elk.py
python3 scrapers/junkyard_social_club.py
python3 scrapers/mountain_sun_pub.py

# Aggregate all events
python3 aggregate_events.py

# Open index.html in your browser
open index.html  # Mac
# or
xdg-open index.html  # Linux
# or just double-click index.html
```

### Option 2: Full System (All Venues with Playwright)

For venues that use JavaScript (St Julien, Trident, License No 1):

1. **Install dependencies:**
```bash
pip install playwright beautifulsoup4 requests
playwright install chromium
```

2. **Run all scrapers:**
```bash
# Working scrapers (no Playwright needed)
python3 scrapers/velvet_elk.py
python3 scrapers/junkyard_social_club.py
python3 scrapers/mountain_sun_pub.py

# Playwright scrapers (run on your M2 Mac)
python3 scrapers/st_julien_entertainment.py
python3 scrapers/trident_cafe.py
python3 scrapers/license_no1.py
```

3. **Aggregate and view:**
```bash
python3 aggregate_events.py
open index.html
```

## 🔄 Automation Options

### Daily Updates (Recommended)

Create a script to run daily:

```bash
#!/bin/bash
# update_events.sh

cd /path/to/boulder-events

# Run all scrapers
python3 scrapers/velvet_elk.py
python3 scrapers/junkyard_social_club.py
python3 scrapers/mountain_sun_pub.py
python3 scrapers/st_julien_entertainment.py
python3 scrapers/trident_cafe.py
python3 scrapers/license_no1.py

# Aggregate
python3 aggregate_events.py

echo "Events updated at $(date)"
```

Then set up a cron job (Mac/Linux):
```bash
# Run daily at 6 AM
0 6 * * * /path/to/update_events.sh
```

Or use macOS Automator to schedule it.

## 🌐 Deployment Options

### Option 1: Local (Current)
- Open `index.html` directly in browser
- No server needed
- Best for personal use

### Option 2: GitHub Pages (Free Hosting)
1. Create a GitHub repository
2. Push these files to the repo
3. Enable GitHub Pages in settings
4. Your calendar will be live at `username.github.io/repo-name`

### Option 3: Web Server
- Upload to any web hosting
- Works with Netlify, Vercel, AWS S3, etc.
- Just upload `index.html` and `all_boulder_events.json`

## 📝 Adding New Venues

1. **Find the venue's events page**

2. **Check if it works with web_fetch:**
   - If you can see event data in plain text → Easy to scrape!
   - If you see "Loading..." or empty → Needs Playwright

3. **Create a scraper** (use existing ones as templates):
```python
# scrapers/new_venue.py
def scrape_new_venue_events(html_content):
    # Parse HTML and extract events
    # Return list of event dictionaries
    pass
```

4. **Add to aggregator** in `aggregate_events.py`:
```python
'New Venue Name': {
    'location': 'Boulder',  # or 'Longmont'
    'tags': ['Music', 'Bar', 'etc'],
    'scraper_output': '/home/claude/new_venue_events.json'
}
```

5. **Run and test:**
```bash
python3 scrapers/new_venue.py
python3 aggregate_events.py
```

## 🎨 Customizing the Web Interface

The web interface is in `index.html` - it's a single file with HTML, CSS, and JavaScript all together. You can customize:

- **Colors:** Change the gradient in the `<style>` section
- **Layout:** Modify the grid in `.events-grid`
- **Filters:** Add/remove filter sections
- **Card design:** Update `.event-card` styles

## 🐛 Troubleshooting

**"No events found"**
- Check that `all_boulder_events.json` is in the same folder as `index.html`
- Run `python3 aggregate_events.py` to regenerate the JSON

**"Error loading events"**
- Open browser console (F12) to see the error
- Make sure you're opening `index.html` (not viewing the raw HTML)

**Scraper returns no events**
- Check if the website structure changed
- For JavaScript sites, make sure Playwright is installed
- Check network restrictions (some sites may block automated access)

## 📊 Event Data Format

Each event in the JSON has this structure:

```json
{
  "id": "unique_event_id",
  "title": "Event Title",
  "venue": "Venue Name",
  "location": "Boulder",
  "date": "November 28, 2024",
  "normalized_date": "2024-11-28T00:00:00",
  "recurring": "Every Thursday",
  "time": "7:30 - 9:30 pm",
  "description": "Event description...",
  "link": "https://venue.com/event",
  "image": "https://venue.com/image.jpg",
  "age_restriction": "All Ages",
  
  "venue_tag": "Venue Name",
  "location_tag": "Boulder",
  "venue_type_tags": ["Music", "Bar", "Nightlife"],
  "event_type_tags": ["Music", "All Ages"]
}
```

## 🤝 Contributing

To add more venues or improve the system:

1. Find Boulder event venues
2. Create scrapers following the existing patterns
3. Test thoroughly
4. Update this README with new venues

## 📜 License

This is a personal project for aggregating public event information. Please respect the terms of service of each venue website when scraping.

## 🙋 Support

Questions or issues? Check:
- Individual scraper files for comments
- `aggregate_events.py` for tagging logic
- `index.html` for web interface code

---

**Last Updated:** November 28, 2024
**Total Events:** 60 events from 6 venues
**Working Scrapers:** 3/6
