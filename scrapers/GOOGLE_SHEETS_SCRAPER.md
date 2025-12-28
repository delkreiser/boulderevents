# Google Sheets Scraper - Summer Concert Series

## Overview
Scrapes summer concert series events from a Google Sheet and merges them into `all_boulder_events.json`.

## Google Sheet Structure

**Sheet URL:** https://docs.google.com/spreadsheets/d/18zRuXOk4JB4Z8uMbJJuQ5TdBNurhtrWTFtw0RxAfyEw/edit?usp=sharing

**Columns (Row 1 Headers):**
1. **Event** - Band/performer name (e.g., "Hazel Miller")
2. **Venue** - Series name (e.g., "Bands on the Bricks")
3. **City** - City name (e.g., "Niwot", "Louisville")
4. **Day** - Day of week (e.g., "Thursday")
5. **Date** - Date in mm/dd/yyyy format (e.g., "06/15/2024")
6. **Time** - Event time (e.g., "7:00 PM - 9:00 PM")
7. **Info** - Additional event information (optional)
8. **url** - Link to more info (optional)

---

## Venue Image Mapping

| Venue | Image File |
|-------|-----------|
| Bands on the Bricks | `images/bandsonthebricks.jpg` |
| Rock & Rails | `images/rocknrails.jpg` |
| Louisville Street Faire | `images/streetfaire.jpg` |
| Village at The Peaks - Summer Concert Series | `images/village.jpg` |

**Default:** `images/default.jpg` (if venue not recognized)

---

## Location Mapping

| City | Location Filter |
|------|----------------|
| Niwot | Niwot |
| Louisville | Louisville |
| Lafayette | Lafayette |
| Boulder | Boulder |

**New Location Added:** Niwot (automatically appears in location filter)

---

## Event Tags

All events are automatically tagged with:
- `Live Music`
- `All Ages`
- `Free`

---

## Date Formatting

**Input:** mm/dd/yyyy (e.g., `06/15/2024`)
**Output:** Month DD, YYYY (e.g., `June 15, 2024`)
**Normalized:** YYYY-MM-DD for sorting (e.g., `2024-06-15`)

---

## Event Card Format

```
┌─────────────────────────────┐
│ [Venue Image]               │
├─────────────────────────────┤
│ Hazel Miller                │ ← Event Name (band)
│ 📍 Bands on the Bricks      │ ← Venue
│ Niwot                        │ ← Location
│ Thursday, June 15, 2024      │ ← Day, Date
│ 🕐 7:00 PM - 9:00 PM        │ ← Time
│ ℹ️ Special guest appearance  │ ← Info (if present)
│ [More Info →]               │ ← URL link
│ 🎵 Live Music 👨‍👩‍👧‍👦 All Ages 💰 Free │
└─────────────────────────────┘
```

---

## How to Run

### Prerequisites
- Python 3.7+
- Internet connection (to download sheet)

### Run the Scraper
```bash
python3 scrape_summer_series.py
```

### What It Does
1. Downloads Google Sheet as CSV
2. Parses each row into event objects
3. Formats dates (mm/dd/yyyy → Month DD, YYYY)
4. Maps venues to images
5. Maps cities to locations
6. Adds tags: Live Music, All Ages, Free
7. Checks for duplicates (by name + venue + date)
8. Merges new events into `all_boulder_events.json`
9. Sorts all events by date

---

## Output Example

```json
{
  "events": [
    {
      "name": "Hazel Miller",
      "venue": "Bands on the Bricks",
      "location": "Niwot",
      "date": "June 15, 2024",
      "time": "7:00 PM - 9:00 PM",
      "image": "images/bandsonthebricks.jpg",
      "url": "https://example.com/event",
      "tags": ["Live Music", "All Ages", "Free"],
      "normalized_date": "2024-06-15",
      "day": "Thursday",
      "info": "Special guest appearance"
    }
  ]
}
```

---

## Duplicate Prevention

The scraper checks for duplicates using:
```
event_id = "{name}|{venue}|{normalized_date}"
```

**Example:** `Hazel Miller|Bands on the Bricks|2024-06-15`

If an event with the same name, venue, and date already exists, it will be skipped.

---

## Google Sheet Access

**Requirement:** Sheet must be set to "Anyone with the link can view"

**How to Check:**
1. Open sheet
2. Click "Share" button
3. Ensure "General access" is set to "Anyone with the link"
4. Viewer access is sufficient

---

## Adding New Venues

To add a new venue image:

1. Add image to `/images/` folder
2. Update `VENUE_IMAGES` dictionary in scraper:

```python
VENUE_IMAGES = {
    "Bands on the Bricks": "images/bandsonthebricks.jpg",
    "Rock & Rails": "images/rocknrails.jpg",
    "Louisville Street Faire": "images/streetfaire.jpg",
    "Village at The Peaks - Summer Concert Series": "images/village.jpg",
    "New Venue Name": "images/newvenue.jpg"  # Add here
}
```

---

## Adding New Locations

To add a new location:

1. Update `CITY_LOCATIONS` dictionary in scraper:

```python
CITY_LOCATIONS = {
    "Niwot": "Niwot",
    "Louisville": "Louisville",
    "Lafayette": "Lafayette",
    "Boulder": "Boulder",
    "Longmont": "Longmont"  # Add here
}
```

2. Location will automatically appear in filter dropdown

---

## Troubleshooting

### "No events found in sheet"
- Check that sheet has data in rows 2+
- Verify Row 1 headers match exactly
- Ensure sheet is publicly accessible

### "Error parsing date"
- Verify dates are in mm/dd/yyyy format
- Check for extra spaces or invalid dates

### Images not showing
- Verify image files exist in `/images/` folder
- Check venue names match exactly (case-sensitive)
- Ensure filenames match `VENUE_IMAGES` dictionary

### Duplicate events not being caught
- Verify event name, venue, and date are identical
- Check for extra spaces or capitalization differences

---

## Integration with Website

The scraper appends to `all_boulder_events.json`, which is automatically loaded by `index.html`.

**No code changes needed!** The website will automatically:
- Display new events
- Add "Niwot" to location filter
- Show venue images
- Apply tags for filtering

---

## Schedule Automation (Optional)

To run scraper automatically:

### Using cron (Linux/Mac)
```bash
# Run daily at 6 AM
0 6 * * * cd /path/to/project && python3 scrape_summer_series.py
```

### Using Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6 AM
4. Action: Run `python3 scrape_summer_series.py`

---

## Summary

✅ **Scrapes:** Google Sheet with 8 columns
✅ **Outputs:** Merged into all_boulder_events.json
✅ **Tags:** Live Music, All Ages, Free
✅ **Images:** 4 venue images mapped
✅ **Locations:** Niwot, Louisville, Lafayette, Boulder
✅ **Duplicates:** Automatically prevented
✅ **Sorting:** By date (earliest first)
✅ **Integration:** Automatic with existing website

Ready to use! 🎉
