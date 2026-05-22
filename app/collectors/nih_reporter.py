import requests
import json

def fetch():
    try:
        with open("app/config/keywords.json") as f:
            kw = json.load(f)["keywords"]
        search_term = " OR ".join(kw[:5])
    except:
        search_term = "genomics"

    url = "https://api.reporter.nih.gov/v2/projects/search"
    payload = {
        "criteria": {"text_search": search_term},
        "limit": 20
    }
    r = requests.post(url, json=payload)
    data = r.json()
    results = []
    for item in data.get("results", []):
        # Extract project ID from various possible field names
        project_id = (item.get("project_id") or 
                      item.get("appl_id") or 
                      item.get("projectId") or 
                      item.get("id"))
        if project_id:
            link = f"https://reporter.nih.gov/project-detail/{project_id}"
        else:
            # Fallback: create a search URL using title (not perfect but clickable)
            title_part = item.get("project_title", "").replace(" ", "+")
            link = f"https://reporter.nih.gov/search?term={title_part}"
        
        results.append({
            "title": item.get("project_title", "No title"),
            "summary": item.get("abstract_text", ""),
            "link": link,
            "deadline": "N/A"
        })
    return results
