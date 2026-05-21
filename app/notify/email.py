import smtplib
from email.mime.text import MIMEText

def send_email(results):
    body = ""

    for r in results:
        body += f"{r['title']}\n{r['link']}\n{r['analysis']}\n\n"

    msg = MIMEText(body)
    msg['Subject'] = "🧬 AI Grant Alerts (Genomics & Infectious Disease)"
    msg['From'] = "your_email@gmail.com"
    msg['To'] = "your_email@gmail.com"

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login("your_email@gmail.com", "APP_PASSWORD")
    server.send_message(msg)
    server.quit()
