import requests
import json
import os

def fetch():
    # optionally load keywords dynamically
    with open("app/config/keywords.json") as f:
        kw = json.load(f)["keywords"]
    search_term = " OR ".join(kw[:5])  # keep query short

    url = "https://api.reporter.nih.gov/v2/projects/search"
    payload = {
        "criteria": {"text_search": search_term},
        "limit": 20
    }
    r = requests.post(url, json=payload)
    data = r.json()
    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("project_title"),
            "summary": item.get("abstract_text", ""),
            "link": f"https://reporter.nih.gov/project-detail/{item.get('project_id', '')}",
            "deadline": "N/A"
        })
    return results
