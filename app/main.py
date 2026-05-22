# app/main.py
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from db.database import init_db, already_seen, mark_seen
from collectors import grants_gov  # Only using Grants.gov now
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
# KEYWORD POST-FILTER (as a double-check)
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
    close_date = grant.get("closeDate") or "N/A"
    grant_text = f"Title: {title}\nDescription: {desc}\nDeadline: {close_date}"
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
    rule_score, _ = score_text(grant_text)
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
    rule_score, matched_kws = score_text(text)
    return {
        "relevant": True,
        "mechanism": "unknown",
        "eligible_pi": False,
        "role": "Co-I",
        "score": rule_score,
        "reason": f"AI unavailable. Matched keywords: {', '.join(matched_kws) if matched_kws else 'none'}"
    }

# =========================
# SEND EMAIL REPORT
# =========================
def send_email_report(new_grants_with_ai):
    if not new_grants_with_ai:
        return

    subject = f"🧬 Grant Alert – {datetime.now().strftime('%Y-%m-%d')}"
    body = "The following new grants match your profile and keywords:\n\n"

    for item in new_grants_with_ai:
        g = item["grant"]
        ai = item["ai"]
        body += f"""
Title: {g['title']}
Source: {g['source']}
Deadline: {g['closeDate']}
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
    summary = f"🧬 New grants ({datetime.now().strftime('%Y-%m-%d')})\n\n"
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
    print("🚀 Starting Grant Monitor...")

    # 1. Fetch all grants from Grants.gov API
    all_grants = grants_gov.fetch()
# Inside main(), after all_grants = grants_gov.fetch()
    print("\n--- DEBUG: First 5 grants from API ---")
    for i, grant in enumerate(all_grants[:5]):
    	print(f"{i+1}. Title: {grant.get('title', 'NO TITLE')}")
    	desc = grant.get('description', '')
    	print(f"   Description preview: {desc[:150] if desc else 'EMPTY'}")
    	print(f"   ID: {grant.get('id', 'NO ID')}")
    print("--------------------------------------\n")
    # 2. Double-check against your keywords
    keyword_relevant = keyword_filter(all_grants)

    # 3. Deduplicate using the new database (which uses opportunity_id)
    new_grants = []
    for g in keyword_relevant:
        opp_id = g.get("id")
        if opp_id and not already_seen(opp_id):
            new_grants.append(g)
            g["_dedup_key"] = opp_id  # Store the ID for later marking

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
        # Use the stored opportunity ID to mark as seen
        mark_seen(grant["_dedup_key"], grant.get("title", ""), ai_result["score"], ai_result["reason"])

    # Filter only those considered relevant (AI decides; in fallback mode all are kept)
    if ai_available:
        relevant_evaluated = [e for e in evaluated if e["ai"]["relevant"] is True]
    else:
        relevant_evaluated = evaluated

    print(f"🎯 After relevance filter: {len(relevant_evaluated)} grants")

    send_email_report(relevant_evaluated)
    send_telegram_summary(relevant_evaluated)

    print("✅ Done.")

if __name__ == "__main__":
    main()
