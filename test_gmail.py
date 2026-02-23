import os
import pytest

# Skip this test module in GitHub Actions (CI) only
if os.getenv("GITHUB_ACTIONS") == "true":
    pytest.skip("Skipping Gmail integration test in CI", allow_module_level=True)

from gmail_service import send_gmail

send_gmail(
    subject="QA Watchdog Test 🚀",
    body_html="<h2>It works!</h2><p>Gmail API connected successfully.</p>",
    to_email="ygutmann@gmail.com"  # תחליף למייל שלך
)