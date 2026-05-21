import requests

def fetch():
    url = "https://api.reporter.nih.gov/v2/projects/search"

    payload = {
        "criteria": {
            "text_search": "genomics"
        },
        "limit": 10
    }

    r = requests.post(url, json=payload)
    data = r.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "title": item.get("project_title"),
            "summary": item.get("abstract_text", ""),
            "link": "https://reporter.nih.gov/"
        })

    return results
