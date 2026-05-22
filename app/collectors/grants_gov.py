# app/collectors/grants_gov.py
import requests
import json
import os
from datetime import datetime

def fetch():
    # Load keywords from the central config file
    try:
        with open("app/config/keywords.json", "r") as f:
            keywords_data = json.load(f)
            keywords = keywords_data.get("keywords", [])
            # Create a search term by joining keywords with 'OR'
            search_term = " OR ".join(keywords)
    except Exception as e:
        print(f"Error loading keywords: {e}. Using fallback term.")
        search_term = "genomics"

    # API Endpoint
    url = "https://api.grants.gov/v1/api/search2"

    # Payload to get the latest grants, sorted by open date, only 'posted' ones
    payload = {
        "rows": 20,                # Number of results to fetch
        "sortBy": "openDate|desc", # Sort by open date, newest first
        "oppStatuses": "posted",   # Only fetch active opportunities
        "keyword": search_term     # Search for your keywords
    }

    print(f"🔍 Fetching from Grants.gov API with keywords: {search_term}")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        return []

    # Process the results
    opportunities = data.get("data", {}).get("oppHits", [])
    print(f"  → Received {len(opportunities)} opportunities from API")

    formatted_grants = []
    for opp in opportunities:
        formatted_grants.append({
            "id": opp.get("id"),               # Unique ID for de-duplication
            "title": opp.get("title", ""),
            "description": opp.get("summary", ""),
            "link": f"https://www.grants.gov/opportunity/{opp.get('id')}",  # Full, correct link
            "source": "Grants.gov",
            "openDate": opp.get("openDate", ""),
            "closeDate": opp.get("closeDate", "N/A"),
            "agencyName": opp.get("agencyName", ""),
            "opportunityStatus": opp.get("oppStatus", "")
        })
    
    return formatted_grants
