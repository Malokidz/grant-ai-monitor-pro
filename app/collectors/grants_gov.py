# app/collectors/grants_gov.py
import feedparser
import requests
import time
import re

def fetch():
    # First, try RSS feed (which contains full descriptions)
    print("🔍 Fetching from Grants.gov RSS feed...")
    try:
        feed = feedparser.parse("https://www.grants.gov/rss/GG_NewOpp.xml")
        if feed.bozo:
            print(f"⚠️ Feed parsing warning: {feed.bozo_exception}")
        entries = feed.entries
        if entries:
            print(f"  → RSS feed returned {len(entries)} opportunities")
            formatted = []
            for entry in entries:
                desc = entry.get("summary", "")
                # Remove HTML tags
                desc = re.sub(r'<[^>]+>', '', desc)
                formatted.append({
                    "id": entry.get("id", ""),
                    "title": entry.get("title", ""),
                    "description": desc,
                    "link": entry.get("link", ""),
                    "source": "Grants.gov",
                    "openDate": entry.get("openDate", ""),
                    "closeDate": entry.get("closeDate", "N/A"),
                    "agencyName": entry.get("agencyName", "")
                })
            return formatted
        else:
            print("  → RSS feed returned 0 entries. Falling back to API...")
    except Exception as e:
        print(f"  ❌ RSS fetch failed: {e}. Falling back to API...")
    
    # Fallback: use search2 API to get opportunity IDs, then fetch each detail
    print("🔍 Using API fallback: fetching 50 recent opportunities...")
    search_url = "https://api.grants.gov/v1/api/search2"
    payload = {
        "rows": 50,
        "sortBy": "openDate|desc",
        "oppStatuses": "posted"
    }
    try:
        resp = requests.post(search_url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        opportunities = data.get("data", {}).get("oppHits", [])
        print(f"  → API returned {len(opportunities)} opportunity IDs")
    except Exception as e:
        print(f"  ❌ API search failed: {e}")
        return []
    
    formatted_grants = []
    for opp in opportunities:
        opp_id = opp.get("id")
        if not opp_id:
            continue
        # Fetch full opportunity details
        detail_url = f"https://api.grants.gov/v1/api/opportunity/{opp_id}"
        try:
            detail_resp = requests.get(detail_url, timeout=10)
            detail_resp.raise_for_status()
            detail = detail_resp.json()
            # The description might be in 'synopsis' or 'description' field
            description = detail.get("synopsis", "") or detail.get("description", "") or ""
            formatted_grants.append({
                "id": opp_id,
                "title": opp.get("title", ""),
                "description": description,
                "link": f"https://www.grants.gov/opportunity/{opp_id}",
                "source": "Grants.gov",
                "openDate": opp.get("openDate", ""),
                "closeDate": opp.get("closeDate", "N/A"),
                "agencyName": opp.get("agencyName", "")
            })
            time.sleep(0.5)  # be polite to the API
        except Exception as e:
            print(f"  ⚠️ Failed to fetch details for opportunity {opp_id}: {e}")
            continue
    
    print(f"  → Successfully fetched details for {len(formatted_grants)} grants")
    return formatted_grants
