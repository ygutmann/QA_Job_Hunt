import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject: str, html_body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]          # e.g. smtp.gmail.com
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]          # your email
    smtp_pass = os.environ["SMTP_PASS"]          # app password
    to_email = os.environ["TO_EMAIL"]            # destination

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_email], msg.as_string())