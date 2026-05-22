import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sqlite3

from collectors import grants_gov, nih_reporter
from ai.evaluator import evaluate_grant, has_available_quota
from ai.scorer import score_text

# =========================
# CONFIG (from environment)
# =========================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# LOAD LOCAL CONFIG
# =========================
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

PROFILE = load_json("app/config/profile.json")
KEYWORDS = load_json("app/config/keywords.json")["keywords"]

# =========================
# DATABASE (deduplication)
# =========================
DB_PATH = "grants.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS seen_grants (
            link TEXT PRIMARY KEY,
            title TEXT,
            first_seen TEXT,
            score INTEGER,
            ai_reason TEXT
        )
    """)
    conn.commit()
    conn.close()

def already_seen(link):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM seen_grants WHERE link = ?", (link,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def mark_seen(link, title, score, reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO seen_grants (link, title, first_seen, score, ai_reason)
        VALUES (?, ?, ?, ?, ?)
    """, (link, title, datetime.now().isoformat(), score, reason))
    conn.commit()
    conn.close()

# =========================
# FETCH GRANTS FROM ALL SOURCES
# =========================
def fetch_all_grants():
    print("🔍 Fetching from Grants.gov...")
    grants_gov_list = grants_gov.fetch()
    print(f"  → {len(grants_gov_list)} opportunities")

    print("🔍 Fetching from NIH Reporter...")
    nih_list = nih_reporter.fetch()
    print(f"  → {len(nih_list)} projects")

    all_grants = []
    for g in grants_gov_list:
        all_grants.append({
            "title": g.get("title", ""),
            "description": g.get("summary", ""),
            "link": g.get("link", ""),
            "source": "Grants.gov",
            "deadline": g.get("deadline", "N/A")
        })
    for n in nih_list:
        all_grants.append({
            "title": n.get("title", ""),
            "description": n.get("summary", ""),
            "link": n.get("link", ""),
            "source": "NIH Reporter",
            "deadline": n.get("deadline", "N/A")
        })
    return all_grants

# =========================
# KEYWORD PRE‑FILTER (cheap)
# =========================
def keyword_filter(grants):
    filtered = []
    for g in grants:
        title = g.get("title") or ""
        desc = g.get("description") or ""
        text = (title + " " + desc).lower()
        if any(kw.lower() in text for kw in KEYWORDS):
            filtered.append(g)
    print(f"🎯 After keyword filter: {len(filtered)} / {len(grants)} grants")
    return filtered

# =========================
# AI EVALUATION + SCORING (with fallback)
# =========================
def evaluate_grant_with_ai(grant):
    """Use OpenAI to evaluate a grant (assumes quota available)."""
    title = grant.get("title") or ""
    desc = grant.get("description") or ""
    deadline = grant.get("deadline") or "N/A"
    grant_text = f"Title: {title}\nDescription: {desc}\nDeadline: {deadline}"
    ai_output = evaluate_grant(grant_text, PROFILE)
    try:
        result = json.loads(ai_output)
    except json.JSONDecodeError:
        result = {
            "relevant": False,
            "mechanism": "unknown",
            "eligible_as_PI": False,
            "recommended_role": "Ignore",
            "score": 0,
            "reason": ai_output[:200]
        }
    rule_score = score_text(grant_text)
    final_score = result.get("score", rule_score)
    return {
        "relevant": result.get("relevant", False),
        "mechanism": result.get("mechanism", ""),
        "eligible_pi": result.get("eligible_as_PI", False),
        "role": result.get("recommended_role", "Ignore"),
        "score": final_score,
        "reason": result.get("reason", "No AI reason provided")
    }

def fallback_evaluate(grant):
    """Rule‑based fallback when AI quota is exhausted."""
    title = grant.get("title") or ""
    desc = grant.get("description") or ""
    text = title + " " + desc
    rule_score = score_text(text)
    return {
        "relevant": True,   # already passed keyword filter
        "mechanism": "unknown",
        "eligible_pi": False,
        "role": "Co-I",
        "score": rule_score,
        "reason": "AI unavailable – using keyword relevance only."
    }

# =========================
# SEND EMAIL REPORT
# =========================
def send_email_report(new_grants_with_ai):
    if not new_grants_with_ai:
        return

    subject = f"🧬 AI Grant Alert – {datetime.now().strftime('%Y-%m-%d')}"
    body = "The following new grants match your profile and keywords:\n\n"

    for item in new_grants_with_ai:
        g = item["grant"]
        ai = item["ai"]
        body += f"""
Title: {g['title']}
Source: {g['source']}
Deadline: {g['deadline']}
Link: {g['link']}
Score: {ai['score']}/10
Eligible as PI: {ai['eligible_pi']}
Recommended role: {ai['role']}
Reason: {ai['reason']}
----------------------------------------
"""
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully")
    except Exception as e:
        print(f"❌ Email failed: {e}")

# =========================
# SEND TELEGRAM (optional)
# =========================
def send_telegram_summary(new_grants_with_ai):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    if not new_grants_with_ai:
        return

    from notify.telegram import send as tg_send
    summary = f"🧬 New AI grants ({datetime.now().strftime('%Y-%m-%d')})\n\n"
    for item in new_grants_with_ai[:5]:
        g = item["grant"]
        ai = item["ai"]
        summary += f"• {g['title']} (score {ai['score']})\n{ai['reason'][:80]}...\n{g['link']}\n\n"
    tg_send(summary)

# =========================
# MAIN PIPELINE
# =========================
def main():
    init_db()
    print("🚀 Starting AI Grant Monitor...")

    all_grants = fetch_all_grants()
    keyword_relevant = keyword_filter(all_grants)
    new_grants = [g for g in keyword_relevant if not already_seen(g["link"])]
    print(f"✨ New unseen grants: {len(new_grants)}")

    if not new_grants:
        print("No new grants. Exiting.")
        return

    # Check OpenAI quota availability
    ai_available = has_available_quota()
    if not ai_available:
        print("🚫 AI evaluation disabled due to missing credits. Using rule‑based scoring only.")

    evaluated = []
    for grant in new_grants:
        if ai_available:
            print(f"🤖 AI evaluating: {grant['title'][:60]}...")
            ai_result = evaluate_grant_with_ai(grant)
        else:
            print(f"🔢 Rule‑based scoring: {grant['title'][:60]}...")
            ai_result = fallback_evaluate(grant)
        evaluated.append({"grant": grant, "ai": ai_result})
        mark_seen(grant["link"], grant["title"], ai_result["score"], ai_result["reason"])

    # Filter only those considered relevant (AI decides; in fallback mode all are kept)
    if ai_available:
        relevant_evaluated = [e for e in evaluated if e["ai"]["relevant"] is True]
    else:
        relevant_evaluated = evaluated   # keep all because fallback marks relevant=True

    print(f"🎯 After AI relevance filter: {len(relevant_evaluated)} grants")

    send_email_report(relevant_evaluated)
    send_telegram_summary(relevant_evaluated)

    print("✅ Done.")

if __name__ == "__main__":
    main()
