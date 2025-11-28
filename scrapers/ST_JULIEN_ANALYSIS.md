# St Julien Entertainment Events Scraper - Analysis

## URL
https://stjulien.com/boulder-colorado-events/category/entertainment-events/

## Findings

### What We Can See
- **35 entertainment events** are listed on this page
- Events are displayed in a calendar grid format
- The site uses "The Events Calendar" (Tribe Events) WordPress plugin

### Category
- Entertainment

### Challenges
1. **JavaScript Rendering**: The calendar uses JavaScript to render events dynamically
2. **Limited HTML**: The web_fetch tool captures basic structure but not full event details
3. **Calendar Widget**: Events are in a calendar view rather than a simple list

### Solutions

#### Option 1: Selenium/Playwright (Recommended for JavaScript sites)
- Use a headless browser to render the page
- Extract full event details after JavaScript loads
- More reliable for dynamic content

#### Option 2: Find Alternative URLs
- List view: `/list/` suffix
- API endpoints: Look for JSON feeds
- RSS feeds: Check for `/feed/` endpoint

#### Option 3: Individual Event Pages
- Scrape the calendar to get event URLs
- Visit each event page for full details

### Event Data Structure
Each event should contain:
```json
{
  "title": "Event Title",
  "date": "December 5, 2024",
  "time": "7:00 PM - 9:00 PM",
  "description": "Event description...",
  "link": "https://stjulien.com/event/event-name/",
  "venue": "St Julien Hotel & Spa",
  "category": "Entertainment",
  "source_url": "https://stjulien.com/boulder-colorado-events/category/entertainment-events/"
}
```

### Next Steps
1. Test with Selenium to get full event data
2. Get 2-3 more venue URLs to build out the scraper collection
3. Build the aggregation system once we have multiple scrapers working

## Files Created
- `/home/claude/scrapers/st_julien_entertainment.py` - Scraper with both basic and Selenium options
