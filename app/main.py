import feedparser
import json
from ai_filter import evaluate_grant
from database import already_seen, mark_seen
from emailer import send_email

feed = feedparser.parse("https://www.grants.gov/rss/GG_NewOpp.xml")

with open("keywords.json") as f:
    keywords = json.load(f)["keywords"]

results = []

for entry in feed.entries:
    if already_seen(entry.link):
        continue

    text = (entry.title + " " + entry.summary).lower()

    if any(k in text for k in keywords):
        ai_result = evaluate_grant(text)

        if "YES" in ai_result:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "analysis": ai_result
            })

        mark_seen(entry.link)

if results:
    send_email(results)
