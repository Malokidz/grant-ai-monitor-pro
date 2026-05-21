import feedparser

def fetch():
    feed = feedparser.parse("https://www.grants.gov/rss/GG_NewOpp.xml")
    return [{"title": e.title, "summary": e.summary, "link": e.link} for e in feed.entries]
