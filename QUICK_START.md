# 🎉 Boulder Events Calendar - Quick Start

## What You Have

✅ **Complete event aggregation system** with 60 events from 6 Boulder/Longmont venues
✅ **Beautiful web interface** with filtering and search
✅ **Comprehensive tagging system** (venue, location, event type)
✅ **Working scrapers** for 3 venues (3 more need Playwright on your M2 Mac)

## 🚀 How to Use It RIGHT NOW

### Step 1: Download Everything
All files are in the `/mnt/user-data/outputs/boulder-events/` folder. Download it to your computer.

### Step 2: Open the Calendar
Simply double-click `index.html` or drag it into your web browser.

**That's it!** You'll see all 60 events with:
- 🔍 Search by keyword
- 🏷️ Filter by venue
- 📍 Filter by location (Boulder/Longmont)
- 🎵 Filter by event type (Music, Community, etc.)

## 📂 What's Inside

```
boulder-events/
├── index.html                    ← Open this to view events!
├── all_boulder_events.json       ← All 60 events combined
├── aggregate_events.py           ← Run to update events
├── README.md                     ← Full documentation
│
├── scrapers/                     ← Individual venue scrapers
│   ├── velvet_elk.py
│   ├── junkyard_social_club.py
│   ├── mountain_sun_pub.py
│   ├── st_julien_entertainment.py
│   ├── trident_cafe.py
│   └── license_no1.py
│
└── Individual event files
    ├── velvet_elk_events.json
    ├── junkyard_events.json
    └── mountain_sun_events.json
```

## 🔄 To Update Events

### Currently Working (No setup needed):
```bash
python3 scrapers/velvet_elk.py
python3 scrapers/junkyard_social_club.py
python3 scrapers/mountain_sun_pub.py
python3 aggregate_events.py
```
Then refresh your browser!

### To Enable ALL Venues (Needs Playwright):
```bash
# One-time setup on your M2 Mac
pip install playwright beautifulsoup4
playwright install chromium

# Then run ALL scrapers
python3 scrapers/st_julien_entertainment.py
python3 scrapers/trident_cafe.py
python3 scrapers/license_no1.py
python3 aggregate_events.py
```

## 🎨 Customization

### Change Colors/Design
Edit `index.html` - all the CSS is in the `<style>` section at the top.

### Add More Venues
1. Create a new scraper in `scrapers/` folder (copy an existing one as template)
2. Add venue to `aggregate_events.py`
3. Run the scraper and aggregator
4. Refresh browser!

## 🌐 Want to Host It Online?

### Option 1: GitHub Pages (Free & Easy)
1. Create a GitHub repo
2. Upload these files
3. Enable GitHub Pages in settings
4. Your calendar is now live!

### Option 2: Any Web Host
Just upload `index.html` and `all_boulder_events.json` - that's all you need!

## 📊 Current Events Breakdown

**Venues:**
- Velvet Elk Lounge (9 events) - Music & nightlife
- Junkyard Social Club (19 events) - Community & arts
- Mountain Sun Pub on Pearl (4 events) - Live music
- Southern Sun Pub (recurring events)
- Vine Street Pub (recurring events)  
- Longs Peak Pub in Longmont (recurring events)

**Categories:**
- 🎵 Music & Live Music
- 🎭 Performance & Arts
- 🎉 Community Events
- 🎲 Game Nights
- 🍺 Pub Events
- 💃 Dance Parties

**Locations:**
- Boulder (most events)
- Longmont (Longs Peak Pub)

## 💡 Tips

- **Filter tip:** Click multiple tags to narrow down results
- **Search tip:** Search works on title, venue, and description
- **Mobile friendly:** Works great on phones and tablets
- **No internet needed:** Everything works offline once you open it

## ❓ Questions?

Check the full `README.md` for:
- Detailed documentation
- Troubleshooting guide
- How to add new venues
- Automation options

## 🎯 Next Steps

1. **Try it now** - Open `index.html` and explore!
2. **Run scrapers** - Update with the latest events
3. **Add venues** - Find more Boulder event sources
4. **Customize** - Make it your own!
5. **Host it** - Share with friends!

---

**Enjoy your Boulder Events Calendar!** 🎉
