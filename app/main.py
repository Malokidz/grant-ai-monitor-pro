import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# =========================
# CONFIG (EDIT THIS)
# =========================
import os

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")


# =========================
# MOCK GRANTS (replace later with real scraper/API)
# =========================
def fetch_new_grants():
    # Replace this with real scraping/API logic
    return [
        {
            "title": "AI Research Grant 2026",
            "organization": "Open Science Fund",
            "deadline": "2026-09-01",
            "link": "https://example.com/grant1",
        },
        {
            "title": "Startup Innovation Grant",
            "organization": "Tech Future Org",
            "deadline": "2026-08-15",
            "link": "https://example.com/grant2",
        },
    ]


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

    grants = fetch_new_grants()

    print(f"Found {len(grants)} grants")

    email_body = format_email(grants)

    send_email(
        subject=f"Grant Monitor Update - {datetime.now().strftime('%Y-%m-%d')}",
        body=email_body,
    )


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
