# app/collectors/grants_gov.py
import requests
from bs4 import BeautifulSoup
import re
import time

def fetch():
    # Try RSS first (with tolerant parser)
    url = "https://www.grants.gov/rss/GG_NewOpp.xml"
    print("🔍 Fetching Grants.gov RSS feed...")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        if items:
            print(f"  → Found {len(items)} opportunities in RSS feed")
            return parse_rss_items(items)
    except Exception as e:
        print(f"RSS parsing failed: {e}")

    # Fallback: scrape HTML search results
    print("Falling back to scraping Grants.gov search page...")
    search_url = "https://www.grants.gov/search-grants.html"
    params = {
        "keywords": "genomics OR bioinformatics OR parasite OR infectious disease",
        "sortBy": "openDate",
        "page": 1
    }
    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Find grant rows - the actual selector may vary; we need to inspect.
        # Let's look for common patterns: div with class 'search-result-item' or 'grants-result'
        results = soup.select(".search-result-item")  # tentative
        if not results:
            results = soup.select(".grant-result")
        if not results:
            # Try to find all links that look like /opportunity/...
            links = soup.find_all("a", href=re.compile(r"/opportunity/\d+"))
            # This is rough; better to get the surrounding text.
            print(f"Found {len(links)} potential opportunity links")
            # Extract info from parent elements
            grants = []
            for link in links:
                title = link.get_text(strip=True)
                opp_id = re.search(r"/opportunity/(\d+)", link['href']).group(1)
                grants.append({
                    "id": opp_id,
                    "title": title,
                    "description": "",  # Would need to fetch detail page
                    "link": f"https://www.grants.gov{link['href']}",
                    "source": "Grants.gov",
                    "closeDate": ""
                })
            return grants
        # More robust parsing would go here
    except Exception as e:
        print(f"Scraping failed: {e}")

    return []

def parse_rss_items(items):
    grants = []
    for item in items:
        title = item.find("title")
        desc = item.find("description")
        link = item.find("link")
        close = item.find("closeDate") or item.find("opportunityCloseDate")
        opp_id = item.find("opportunityId") or item.find("id")
        grants.append({
            "id": opp_id.get_text(strip=True) if opp_id else "",
            "title": title.get_text(strip=True) if title else "",
            "description": re.sub(r'<[^>]+>', '', desc.get_text(strip=True)) if desc else "",
            "link": link.get_text(strip=True) if link else "",
            "source": "Grants.gov",
            "closeDate": close.get_text(strip=True) if close else ""
        })
    return grants
