#!/usr/bin/env python3
"""
Z2 Entertainment Events Scraper
Scrapes events from Boulder Theater, Fox Theatre, and Aggie Theatre
Uses Selenium to handle dynamic JavaScript content and click "Load More" buttons
Downloads event images locally to avoid hotlinking
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from pathlib import Path
import hashlib
import requests
import time

# Venue mappings
VENUE_INFO = {
    "Boulder Theater": {
        "location": "Boulder",
        "image": "images/bouldertheater.jpg",
        "include": True  # Show in Boulder Events
    },
    "Fox Theatre": {
        "location": "Boulder",
        "image": "images/foxtheatre.jpg",
        "include": True  # Show in Boulder Events
    },
    "Aggie Theatre": {
        "location": "Fort Collins",
        "image": "images/aggietheatre.jpg",
        "include": False  # Don't show yet (future expansion)
    },
    "10 Mile Music Hall": {
        "location": "Frisco",
        "image": "images/default.jpg",
        "include": False  # Skip this venue
    }
}

# Image download settings
IMAGE_DOWNLOAD_DIR = Path("images/z2")
DOWNLOAD_IMAGES = True  # Set to False to use venue default images instead

def scrape_events():
    """Scrape all events using Selenium (real browser automation)"""
    
    # Set up Chrome options for headless operation
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run without visible window
    chrome_options.add_argument('--no-sandbox')  # Required for Linux/GitHub Actions
    chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
    chrome_options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
    chrome_options.add_argument('--window-size=1920,1080')  # Set window size
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    all_events = []
    seen_event_ids = set()  # Track unique events by ID
    
    driver = None
    
    try:
        # Create Chrome driver
        print("Initializing Chrome browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("Scraping Z2 Entertainment events using Selenium...")
        print(f"\n{'='*60}")
        print("Venues:")
        for venue, info in VENUE_INFO.items():
            status = "INCLUDED" if info['include'] else ("SCRAPED, NOT SHOWN" if venue == "Aggie Theatre" else "SKIPPED")
            print(f" • {venue} ({info['location']}) - {status}")
        print(f"{'='*60}\n")
        
        # Load main page
        print("Loading main Z2 Entertainment events page...")
        driver.get("https://www.z2ent.com/events")
        
        # Wait for initial events to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "eventItem")))
        print("✓ Page loaded successfully")
        
        # Parse initial page events
        print("\nParsing initial page events...")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        event_items = soup.find_all('div', class_='eventItem')
        
        for item in event_items:
            event = parse_event_card(item, driver)
            if event:
                event_id = f"{event['venue']}|{event['title']}|{event['date']}"
                if event_id not in seen_event_ids:
                    seen_event_ids.add(event_id)
                    all_events.append(event)
                    print(f"  + {event['venue']}: {event['title']} ({event['date']})")
        
        print(f"\n✓ Initial page: {len(all_events)} events captured")
        
        # Click "Load More" button 4 times to get January + February events
        # (Extra clicks account for other venues in the list)
        print("\nClicking 'Load More' button to get additional events...")
        
        # Wait a moment for the page to fully render the button
        time.sleep(2)
        
        for click_num in range(1, 5):  # Click 4 times
            try:
                print(f"\n--- Load More Click #{click_num} ---")
                
                # Scroll to bottom to ensure button is visible
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Give button time to render
                
                # Find and click the Load More button
                # The button has id="loadMoreEvents" and class="eventList__showMore"
                load_more_button = None
                selectors = [
                    "#loadMoreEvents",  # Primary selector - the actual ID
                    "button.eventList__showMore",  # Class-based backup
                    "button[data-options='events']",  # Data attribute backup
                ]
                
                for selector in selectors:
                    try:
                        load_more_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if load_more_button and load_more_button.is_displayed():
                            print(f"  ✓ Found button using selector: {selector}")
                            break
                    except NoSuchElementException:
                        continue
                
                if not load_more_button:
                    print("  ✗ Load More button not found - reached end of events")
                    break
                
                # Click using JavaScript to avoid click interception
                driver.execute_script("arguments[0].click();", load_more_button)
                print("  ✓ Clicked Load More button")
                
                # Wait for new events to load (wait for AJAX response)
                time.sleep(3)
                
                # Parse newly loaded events
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                event_items = soup.find_all('div', class_='eventItem')
                
                events_before = len(all_events)
                
                for item in event_items:
                    event = parse_event_card(item, driver)
                    if event:
                        event_id = f"{event['venue']}|{event['title']}|{event['date']}"
                        if event_id not in seen_event_ids:
                            seen_event_ids.add(event_id)
                            all_events.append(event)
                            print(f"    + {event['venue']}: {event['title']} ({event['date']})")
                
                new_events = len(all_events) - events_before
                print(f"  ✓ Found {new_events} new events (total: {len(all_events)})")
                
                # Continue clicking even if no new Boulder/Fox events (might be other venues)
                    
            except TimeoutException:
                print(f"  ✗ Timeout waiting for new events to load")
                break
            except Exception as e:
                print(f"  ✗ Error clicking Load More: {e}")
                break
        
        print(f"\n{'='*60}")
        print(f"Total unique events scraped: {len(all_events)}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always close the browser
        if driver:
            print("\nClosing browser...")
            driver.quit()
    
    return all_events

def download_event_image(driver, image_url, title, venue):
    """
    Download event image using Selenium (bypasses 406 blocks)
    Returns local path if successful, None if failed
    """
    if not DOWNLOAD_IMAGES or not image_url or image_url == VENUE_INFO.get(venue, {}).get('image'):
        return None
    
    try:
        # Create images/z2 directory if it doesn't exist
        IMAGE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename from title
        # Use hash to keep filename length reasonable
        safe_title = re.sub(r'[^a-z0-9]+', '-', title.lower())[:50]
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
        
        # Determine file extension from URL
        ext = '.jpg'
        if '.png' in image_url.lower():
            ext = '.png'
        elif '.gif' in image_url.lower():
            ext = '.gif'
        elif '.webp' in image_url.lower():
            ext = '.webp'
        
        filename = f"{safe_title}-{url_hash}{ext}"
        filepath = IMAGE_DOWNLOAD_DIR / filename
        
        # Skip if already downloaded
        if filepath.exists():
            print(f"    Image already exists: {filepath}")
            return str(filepath)
        
        # Download image using Selenium (bypasses 406 blocks)
        print(f"    Downloading with Selenium: {image_url}")
        
        # Navigate to the image URL
        driver.get(image_url)
        time.sleep(1)  # Brief wait for image to load
        
        # Take a screenshot of the image element
        # Find the img tag on the page
        try:
            img_element = driver.find_element(By.TAG_NAME, "img")
            
            # Get the image as PNG bytes
            image_bytes = img_element.screenshot_as_png
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            print(f"    ✓ Downloaded image: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"    ✗ Could not find image element: {e}")
            return None
        
    except Exception as e:
        print(f"    ✗ Failed to download image: {e}")
        return None

def parse_event_card(card, driver):
    """Parse individual event card based on Z2 Entertainment HTML structure"""
    
    # Extract venue name from div.location
    location_elem = card.find('div', class_='location')
    if not location_elem:
        return None
    
    venue_name = location_elem.get_text(strip=True)
    
    # Check if this is a venue we care about
    if venue_name not in VENUE_INFO:
        return None
    
    venue_config = VENUE_INFO[venue_name]
    
    # Skip if we're not including this venue yet
    if not venue_config['include']:
        print(f"Skipping {venue_name} event (not included yet)")
        return None
    
    # Extract event title from h3.title a
    title_elem = card.find('h3', class_='title')
    if not title_elem:
        return None
    
    title_link = title_elem.find('a')
    if not title_link:
        return None
    
    title = title_link.get_text(strip=True)
    event_url = title_link.get('href', '')
    if event_url and not event_url.startswith('http'):
        event_url = f"https://www.z2ent.com{event_url}"
    
    # Extract date - handle both single dates and date ranges
    date_container = card.find('span', class_='m-date__singleDate')
    
    if date_container:
        # Single date format: "Wed, Jan 15, 2026"
        weekday_elem = date_container.find('span', class_='m-date__weekday')
        month_elem = date_container.find('span', class_='m-date__month')
        day_elem = date_container.find('span', class_='m-date__day')
        year_elem = date_container.find('span', class_='m-date__year')
        
        if not all([month_elem, day_elem, year_elem]):
            return None
        
        month_text = month_elem.get_text(strip=True)
        day_text = day_elem.get_text(strip=True).strip()
        year_text = year_elem.get_text(strip=True).replace(',', '').strip()
        
        # Format: "January 15, 2026"
        date_str = f"{month_text} {day_text}, {year_text}"
        
    else:
        # Date range format: "Jan 15 - 17, 2026"
        range_first = card.find('span', class_='m-date__rangeFirst')
        range_last = card.find('span', class_='m-date__rangeLast')
        
        if not range_first or not range_last:
            return None
        
        # Extract start date components
        month_elem = range_first.find('span', class_='m-date__month')
        start_day_elem = range_first.find('span', class_='m-date__day')
        
        # Extract end day and year
        end_day_elem = range_last.find('span', class_='m-date__day')
        year_elem = range_last.find('span', class_='m-date__year')
        
        if not all([month_elem, start_day_elem, year_elem]):
            return None
        
        month_text = month_elem.get_text(strip=True)
        start_day_text = start_day_elem.get_text(strip=True).strip()
        year_text = year_elem.get_text(strip=True).replace(',', '').strip()
        
        # Use start date for display/sorting
        date_str = f"{month_text} {start_day_text}, {year_text}"
    
    # Parse and normalize the date
    try:
        parsed_date = datetime.strptime(date_str, "%B %d, %Y")
        normalized_date = parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Try abbreviated month format
            parsed_date = datetime.strptime(date_str, "%b %d, %Y")
            normalized_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            print(f"  Could not parse date: {date_str}")
            return None
    
    # Extract image URL
    image_elem = card.find('img')
    image_url = None
    if image_elem and image_elem.get('src'):
        image_url = image_elem['src']
        if image_url and not image_url.startswith('http'):
            image_url = f"https://www.z2ent.com{image_url}"
    
    # Download image if available
    local_image_path = None
    if image_url:
        local_image_path = download_event_image(driver, image_url, title, venue_name)
    
    # Use local image path if downloaded, otherwise use default venue image
    final_image = local_image_path if local_image_path else venue_config['image']
    
    # Extract ticket link from buttons section
    ticket_link = None
    buttons_div = card.find('div', class_='buttons')
    if buttons_div:
        ticket_elem = buttons_div.find('a', class_='tickets')
        if ticket_elem and ticket_elem.get('href'):
            ticket_link = ticket_elem['href']
    
    print(f"✓ {title} at {venue_name} on {date_str}")
    
    return {
        "title": title,
        "venue": venue_name,
        "location": venue_config['location'],
        "date": date_str,
        "normalized_date": normalized_date,
        "time": None,  # Z2 doesn't show times on event cards
        "image": final_image,
        "url": event_url,
        "ticket_link": ticket_link,
        "tags": ["music", "concert"],
        "description": None
    }

def main():
    """Main execution function"""
    
    print(f"\n{'='*60}")
    print("Z2 Entertainment Events Scraper")
    print(f"{'='*60}")
    
    # Scrape events
    events = scrape_events()
    
    if not events:
        print("\n⚠ No events scraped!")
        return
    
    # Save to JSON file
    output_file = "z2_entertainment_events.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved {len(events)} events to {output_file}")
        
        # Print summary by venue
        print("\nEvents by venue:")
        venue_counts = {}
        for event in events:
            venue = event['venue']
            venue_counts[venue] = venue_counts.get(venue, 0) + 1
        
        for venue, count in sorted(venue_counts.items()):
            print(f"  • {venue}: {count} events")
        
        print(f"\n✓ Successfully scraped {len(events)} events")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ Error saving to file: {e}")

if __name__ == "__main__":
    main()
