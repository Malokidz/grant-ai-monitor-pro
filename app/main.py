import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

# ========================
# CONFIG (YOUR PROFILE)
# ========================
KEYWORDS = [
    "genomics",
    "bioinformatics",
    "microbes",
    "parasite",
    "infectious disease"
]

GRANT_TYPES = ["K99", "R21"]

# ========================
# SCRAPE GRANTS (example)
# ========================
def scrape_grants():
    url = "https://www.grants.gov/search-results-detail/"

    # Dummy example (replace later with real API)
    grants = [
        {
            "title": "NIH K99 Genomics Research",
            "description": "Focus on infectious disease genomics",
            "url": "https://example.com"
        },
        {
            "title": "R21 Microbiology Study",
            "description": "Microbes and host interaction",
            "url": "https://example.com"
        }
    ]

    return grants

# ========================
# FILTER
# ========================
def filter_grants(grants):
    filtered = []

    for g in grants:
        text = (g["title"] + " " + g["description"]).lower()

        if any(k in text for k in KEYWORDS):
            if any(gt in g["title"] for gt in GRANT_TYPES):
                filtered.append(g)

HEAD
if results:
    send_email(results)

import smtplib
from email.mime.text import MIMEText

def send_email(subject, body):
    sender = "your_email@gmail.com"
    receiver = "your_email@gmail.com"

    msg = MIMEText(body)
    msg["Subject"] = subject
=======
    return filtered

# ========================
# EMAIL
# ========================
def send_email(grants):
    if not grants:
        print("No relevant grants found")
        return

    sender = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    receiver = sender

    body = "🔥 Matching Grants:\n\n"

    for g in grants:
        body += f"{g['title']}\n{g['url']}\n\n"

    msg = MIMEText(body)
    msg["Subject"] = "Grant Alerts"
 08bb289 (Fix main pipeline for GitHub Actions)
    msg["From"] = sender
    msg["To"] = receiver

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
 HEAD
    server.login(sender, os.environ["EMAIL_PASS"])
    server.send_message(msg)
    server.quit()
=======
    server.login(sender, password)
    server.send_message(msg)
    server.quit()

    print("Email sent!")

# ========================
# MAIN
# ========================
def main():
    print("Starting pipeline...")

    grants = scrape_grants()
    filtered = filter_grants(grants)

    print(f"Found {len(filtered)} matching grants")

    send_email(filtered)

if __name__ == "__main__":
    main()
 08bb289 (Fix main pipeline for GitHub Actions)
