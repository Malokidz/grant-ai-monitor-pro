# app/collectors/grants_gov.py
import requests
import json

def fetch():
    url = "https://api.grants.gov/v1/api/search2"
    
    # Fetch recent posted opportunities without keyword filtering
    payload = {
        "rows": 50,                  # Get more results to increase chance of matches
        "sortBy": "openDate|desc",
        "oppStatuses": "posted"
    }
    
    print("🔍 Fetching from Grants.gov API (no API keyword filter)...")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return []
    
    opportunities = data.get("data", {}).get("oppHits", [])
    print(f"  → Received {len(opportunities)} opportunities")
    
    formatted_grants = []
    for opp in opportunities:
        formatted_grants.append({
            "id": opp.get("id"),
            "title": opp.get("title", ""),
            "description": opp.get("summary", ""),
            "link": f"https://www.grants.gov/opportunity/{opp.get('id')}",
            "source": "Grants.gov",
            "openDate": opp.get("openDate", ""),
            "closeDate": opp.get("closeDate", "N/A"),
            "agencyName": opp.get("agencyName", ""),
            "opportunityStatus": opp.get("oppStatus", "")
        })
    
    return formatted_grants
