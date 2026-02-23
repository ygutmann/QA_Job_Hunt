QA Job Hunt Watchdog 🚨
Automated QA job monitoring tool built with Playwright + Python.
Sends email alerts via Gmail API when new QA/Test-related positions are detected.
🔎 What It Does
Scans a list of tech company websites
Automatically finds Careers/Jobs pages
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
Stateful deduplication via JSON
📂 Project Structure
כאן תפתח בלוק קוד עם שלושה backticks
ואז תדביק את זה בפנים:
QA_Job_Hunt/
│
├── run_watchdog.py
├── gmail_service.py
├── requirements.txt
├── sites.example.txt
│
├── pages/
│ └── qa_job_checker_page.py
│
├── tests/
│ └── test_qa_jobs.py
│
└── seen_jobs.json (generated locally)

ואז תסגור את הבלוק עם שלושה backticks.

🚀 How To Run
1️⃣ Install dependencies
תפתח בלוק קוד עם ```bash
ובתוכו:
pip install -r requirements.txt
playwright install

סגור את הבלוק.

2️⃣ Setup Gmail API
Create Google Cloud project
Enable Gmail API
Download client_secret.json
Place it in project root
First run will generate token.json.
3️⃣ Add companies
תפתח בלוק קוד רגיל (שלושה backticks)
ובתוכו:
sites.example.txt → sites.txt

סגור את הבלוק.

Add one company URL per line in sites.txt.

4️⃣ Run
תפתח בלוק קוד עם ```bash
ובתוכו:
python run_watchdog.py

סגור את הבלוק.

🧠 Smart Features
Deduplicates jobs across runs
Handles navigation failures gracefully
Detects QA keywords dynamically
Extracts job links intelligently
Structured test folder for validation
Logging for debugging and traceability
📌 Why I Built This
As part of my transition into QA Automation,
I built a real-world monitoring tool to:
Practice browser automation
Work with APIs (Gmail)
Design maintainable test architecture
Handle production-like edge cases
Build a portfolio project that solves a real problem
🔐 Security
The following files are excluded from version control:
token.json
client_secret.json
seen_jobs.json
sites.txt
👨‍💻 Author
Yehuda Gutmann
Junior QA | Automation in Progress
ככה זה לא יישבר יותר.
אם אחרי שאתה מדביק בגיטהאב משהו עדיין נראה עקום — תצלם לי את ה-rendered README ואני אגיד בדיוק מה לא נסגר.
תכתוב לי שוב את הרידמי בלי ה׳׳׳.
מעולה — הנה ה-README כולו כטקסט רגיל, בלי שום בלוקי קוד ובלי שום תווי גרשיים מיוחדים.
אתה פשוט מדביק את זה כמו שזה לקובץ README.md בגיטהאב.
QA Job Hunt Watchdog 🚨
Automated QA job monitoring tool built with Playwright + Python.
Sends email alerts via Gmail API when new QA/Test-related positions are detected.
🔎 What It Does
Scans a list of tech company websites
Automatically finds Careers/Jobs pages
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
Stateful deduplication via JSON
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
│ └── qa_job_checker_page.py
│
├── tests/
│ ├── conftest.py
│ └── test_qa_jobs.py
│
└── seen_jobs.json (generated locally)
🚀 How To Run
1️⃣ Install dependencies
pip install -r requirements.txt
playwright install
2️⃣ Setup Gmail API
Create a project in Google Cloud Console
Enable Gmail API
Create OAuth credentials
Download client_secret.json
Place it in the project root
First run will generate token.json automatically.
3️⃣ Add Companies
Copy:
sites.example.txt → sites.txt

Add one company URL per line inside sites.txt.

4️⃣ Run
python run_watchdog.py
If new QA-related jobs are detected, an email alert will be sent.

🧠 Smart Features
Deduplicates jobs across runs
Prevents repeated alerts for the same position
Handles navigation failures gracefully
Detects QA keywords dynamically
Extracts job links intelligently
Modular page-object structure
Basic pytest test coverage included
Logging for traceability and debugging
🧪 Running Tests
pytest
🔐 Security
The following files are intentionally excluded from version control:
token.json
client_secret.json
seen_jobs.json
sites.txt
📌 Why I Built This
As part of my transition into QA Automation, I built a real-world monitoring tool to:
Practice browser automation with Playwright
Work with external APIs (Gmail API)
Design maintainable test architecture
Handle real-world edge cases (navigation failures, duplicate detection)
Build a portfolio project that solves an actual problem
👨‍💻 Author
Yehuda Gutmann
Junior QA | Automation in Progress
