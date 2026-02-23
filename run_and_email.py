import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pytest


def send_email(subject: str, html_body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]          # למשל: smtp.gmail.com
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]          # המייל שלך
    smtp_pass = os.environ["SMTP_PASS"]          # app password
    to_email = os.environ["TO_EMAIL"]            # לאן לשלוח

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_email], msg.as_string())


def main():
    # מריץ pytest ומייצר קובץ תוצאות junit (אפשר לקרוא אותו אחר כך)
    junit_path = "report.xml"
    code = pytest.main(["-q", "-s", f"--junitxml={junit_path}"])

    # אם הכל עבר – לא שולחים מייל
    if code == 0:
        return

    # אם יש כשלון – שולחים מייל קצר עם הוראות לפתוח את הריצה
    # (בשלב הבא נשדרג לקרוא תוצאות ולשלוף לינקים)
    subject = "QA Watchdog: Found potential QA jobs (tests failed)"
    body = f"""
    <h2>QA Watchdog - Tests Failed</h2>
    <p>Some sites returned QA job detection.</p>
    <p>Open the project and run:</p>
    <pre>python3 -m pytest -q -s</pre>
    <p>Report file: <b>{junit_path}</b></p>
    """
    send_email(subject, body)


if __name__ == "__main__":
    main()