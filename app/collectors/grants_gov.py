import feedparser

def fetch():
    feed = feedparser.parse("https://www.grants.gov/rss/GG_NewOpp.xml")
    results = []
    for e in feed.entries:
        results.append({
            "title": e.title,
            "summary": e.summary,
            "link": e.link,
            "deadline": getattr(e, "closeDate", "N/A")
        })
    return results
