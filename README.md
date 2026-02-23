QA Job Hunt Watchdog 🚨
Automated QA job monitoring tool built with Playwright + Python.
Sends email alerts via Gmail API when new QA / Test / Automation-related positions are detected.
🔎 What It Does
Scans a list of tech company websites
Automatically finds Careers / Jobs pages
Detects QA / Test / Automation related positions
Extracts relevant job links
Sends email alerts only for new jobs
Prevents duplicate notifications across runs
🛠 Tech Stack
Python 3.11+
Playwright (Chromium)
Gmail API
Pytest
Logging
JSON-based state management (deduplication)
📂 Project Structure
QA_Job_Hunt/
│
├── run_watchdog.py
├── run_and_email.py
├── gmail_service.py
├── requirements.txt
├── sites.example.txt
│
├── pages/
│   └── qa_job_checker_page.py
│
├── tests/
│   ├── conftest.py
│   └── test_qa_jobs.py
│
└── seen_jobs.json (generated locally)
🚀 How To Run
1️⃣ Install Dependencies
pip install -r requirements.txt
playwright install
2️⃣ Setup Gmail API
Create a project in Google Cloud Console
Enable Gmail API
Create OAuth credentials
Download client_secret.json
Place it in the project root
On first run, token.json will be generated automatically.
3️⃣ Configure Sites
sites.example.txt → sites.txt
Add one company URL per line in sites.txt.
4️⃣ Run
python run_watchdog.py
If new QA-related jobs are detected, an email alert will be sent.
🧠 Smart Features
Deduplicates job links across runs
Prevents repeated alerts for the same position
Handles navigation failures gracefully
Detects QA keywords dynamically
Extracts job links intelligently
Modular Page Object structure
Pytest test coverage included
Logging for traceability and debugging
🧪 Running Tests
pytest
🔐 Security
The following files are intentionally excluded from version control:
token.json
client_secret.json
seen_jobs.json
sites.txt
👨‍💻 Author
Yehuda Gutmann
Junior QA | Automation in Progress
