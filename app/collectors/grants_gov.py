# app/collectors/grants_gov.py
import feedparser
import time

def fetch():
    url = "https://www.grants.gov/rss/GG_NewOpp.xml"
    print(f"🔍 Fetching from Grants.gov RSS feed...")
    
    try:
        feed = feedparser.parse(url)
        if feed.bozo:  # Check for parsing errors
            print(f"⚠️ Feed parsing warning: {feed.bozo_exception}")
    except Exception as e:
        print(f"❌ RSS fetch failed: {e}")
        return []
    
    entries = feed.entries
    print(f"  → Received {len(entries)} opportunities from RSS feed")
    
    formatted_grants = []
    for entry in entries:
        # Extract description (full text)
        description = entry.get("summary", "")
        # Remove HTML tags if present (often RSS descriptions contain HTML)
        import re
        description = re.sub(r'<[^>]+>', '', description)
        
        formatted_grants.append({
            "id": entry.get("id", ""),
            "title": entry.get("title", ""),
            "description": description,
            "link": entry.get("link", ""),
            "source": "Grants.gov",
            "openDate": entry.get("openDate", ""),
            "closeDate": entry.get("closeDate", "N/A"),
            "agencyName": entry.get("agencyName", ""),
            "opportunityStatus": "posted"  # RSS feed only contains posted opportunities
        })
    
    return formatted_grants
