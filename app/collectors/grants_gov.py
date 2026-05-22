import requests
import json

def fetch():
    # Load keywords from config
    try:
        with open("app/config/keywords.json", "r") as f:
            keywords_data = json.load(f)
            keywords = keywords_data.get("keywords", [])
            search_term = " OR ".join(keywords)
    except Exception as e:
        print(f"⚠️ Could not load keywords: {e}. Using fallback.")
        search_term = "genomics"
    
    url = "https://api.grants.gov/v1/api/search2"
    payload = {
        "rows": 20,
        "sortBy": "openDate|desc",
        "oppStatuses": "posted",
        "keyword": search_term
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
        grant = {
            "id": opp.get("id"),
            "title": opp.get("title", ""),
            "link": f"https://simpler.grants.gov/opportunity/{opp.get('id')}",   # 👈 FIXED DOMAIN
            "source": "Grants.gov",
            "closeDate": opp.get("closeDate", "N/A"),
            "agencyName": opp.get("agencyName", ""),
            "description": ""
        }
        grants.append(grant)
    
    return grants
