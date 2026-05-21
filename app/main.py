import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# =========================
# CONFIG (FROM GITHUB SECRETS)
# =========================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")


# =========================
# MOCK GRANTS (replace later with real scraper/API)
# =========================
import requests

def fetch_new_grants():
    print("🚀 USING API VERSION")

    url = "https://api.grants.gov/v1/api/search2"

    payload = {
        "rows": 10,
        "sortBy": "openDate|desc"
    }

    response = requests.post(url, json=payload)
    data = response.json()

    print("Found total:", data.get("data", {}).get("hitCount"))

    grants = []

    items = data.get("data", {}).get("oppHits", [])

    for item in items:
        grants.append({
            "title": item.get("opportunityTitle", "No title"),
            "organization": item.get("agencyName", "Unknown"),
            "deadline": item.get("closeDate", "N/A"),
            "link": f"https://www.grants.gov/search-results-detail/{item.get('opportunityNumber')}"
        })

    return grants
# =========================
# LOAD / SAVE SENT GRANTS
# =========================
def load_sent_grants():
    if not os.path.exists("sent_grants.json"):
        return []
    with open("sent_grants.json", "r") as f:
        return json.load(f)


def save_sent_grants(grants):
    with open("sent_grants.json", "w") as f:
        json.dump(grants, f, indent=2)


def filter_new_grants(all_grants, sent_grants):
    sent_titles = {g["title"] for g in sent_grants}
    return [g for g in all_grants if g["title"] not in sent_titles]


# =========================
# FORMAT EMAIL
# =========================
def format_email(grants):
    if not grants:
        return "No new grants found today."

    message = "🚀 New Grants Found:\n\n"

    for g in grants:
        message += f"""
Title: {g['title']}
Organization: {g['organization']}
Deadline: {g['deadline']}
Link: {g['link']}
-------------------------
"""

    return message


# =========================
# SEND EMAIL
# =========================
def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully!")

    except Exception as e:
        print("❌ Failed to send email:", e)


# =========================
# MAIN PIPELINE
# =========================
def main():
    print("🔍 Checking for new grants...")

    all_grants = fetch_new_grants()
    sent_grants = load_sent_grants()

    new_grants = filter_new_grants(all_grants, sent_grants)

    print(f"Found {len(new_grants)} NEW grants")

    if not new_grants:
        print("No new grants. Skipping email.")
        return

    email_body = format_email(new_grants)

    send_email(
        subject=f"New Grants - {datetime.now().strftime('%Y-%m-%d')}",
        body=email_body,
    )

    # Save updated list
    updated = sent_grants + new_grants
    save_sent_grants(updated)


# =========================
# RUN SCRIPT
# =========================
if __name__ == "__main__":
    main()
