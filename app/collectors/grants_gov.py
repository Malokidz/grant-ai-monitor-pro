# app/collectors/grants_gov.py
import requests
import json
import os

def fetch():
    # Load keywords from config
    try:
        with open("app/config/keywords.json", "r") as f:
            keywords_data = json.load(f)
            keywords = keywords_data.get("keywords", [])
            # Join keywords with OR for API search
            search_term = " OR ".join(keywords)
    except Exception as e:
        print(f"⚠️ Could not load keywords: {e}. Using fallback.")
        search_term = "genomics"
    
    url = "https://api.grants.gov/v1/api/search2"
    payload = {
        "rows": 20,                       # Number of results
        "sortBy": "openDate|desc",        # Newest first
        "oppStatuses": "posted",          # Only active opportunities
        "keyword": search_term            # Search by your keywords
    }
    
    print(f"🔍 Searching Grants.gov for: {search_term}")
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return []
    
    opportunities = data.get("data", {}).get("oppHits", [])
    print(f"  → Found {len(opportunities)} grants matching keywords")
    
    grants = []
    for opp in opportunities:
        # Extract basic info – the API already matched keywords, so we don't need description
        grant = {
            "id": opp.get("id"),
            "title": opp.get("title", ""),
            "link": f"https://www.grants.gov/opportunity/{opp.get('id')}",
            "source": "Grants.gov",
            "closeDate": opp.get("closeDate", "N/A"),
            "agencyName": opp.get("agencyName", ""),
            "description": ""   # Not needed because API did keyword search
        }
        grants.append(grant)
    
    return grants
