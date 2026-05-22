# app/collectors/grants_gov.py
import requests
from bs4 import BeautifulSoup
import re

def fetch():
    url = "https://www.grants.gov/rss/GG_NewOpp.xml"
    print("🔍 Fetching Grants.gov RSS feed with tolerant parser...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GrantBot/1.0)"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        # Use BeautifulSoup with XML parser (tolerant of some errors)
        soup = BeautifulSoup(resp.content, "lxml-xml")
    except Exception as e:
        print(f"❌ Failed to fetch or parse RSS feed: {e}")
        return []
    
    # Find all <item> tags
    items = soup.find_all("item")
    print(f"  → Found {len(items)} opportunities in RSS feed")
    
    formatted_grants = []
    for item in items:
        title = item.find("title")
        title_text = title.get_text(strip=True) if title else ""
        
        link = item.find("link")
        link_text = link.get_text(strip=True) if link else ""
        
        # Extract description (full text)
        desc = item.find("description")
        desc_text = desc.get_text(strip=True) if desc else ""
        # Remove HTML tags (description often contains <p>, <br>, etc.)
        desc_text = re.sub(r'<[^>]+>', '', desc_text)
        
        # Try to get closeDate from <closeDate> or <opportunityCloseDate>
        close_date = ""
        close_tag = item.find("closeDate")
        if not close_tag:
            close_tag = item.find("opportunityCloseDate")
        if close_tag:
            close_date = close_tag.get_text(strip=True)
        
        # Opportunity ID from <opportunityId> or <id>
        opp_id = ""
        id_tag = item.find("opportunityId")
        if not id_tag:
            id_tag = item.find("id")
        if id_tag:
            opp_id = id_tag.get_text(strip=True)
        else:
            # Fallback: extract from link
            if link_text and "opportunity/" in link_text:
                opp_id = link_text.split("opportunity/")[-1].split("/")[0]
        
        formatted_grants.append({
            "id": opp_id,
            "title": title_text,
            "description": desc_text,
            "link": link_text,
            "source": "Grants.gov",
            "openDate": "",  # Not always in RSS
            "closeDate": close_date,
            "agencyName": ""  # Not in RSS item; can be fetched separately if needed
        })
    
    return formatted_grants
