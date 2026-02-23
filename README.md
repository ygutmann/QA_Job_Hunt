# QA Job Hunt Watchdog 🚨

Automated QA job monitoring tool built with **Playwright + Python**  
Sends email alerts via **Gmail API** when new QA/Test-related positions are detected.

---

## 🔎 What It Does

- Scans a list of tech company websites
- Automatically finds Careers/Jobs pages
- Detects QA / Test / Automation related positions
- Extracts relevant job links
- Sends email alerts **only for new jobs** (deduplication supported)
- Prevents duplicate notifications across runs

---

## 🛠 Tech Stack

- Python 3.11+
- Playwright (Chromium)
- Gmail API
- Pytest
- Logging
- Stateful deduplication via JSON

---

## 📂 Project Structure
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

---

## 🚀 How To Run

### 1️⃣ Install dependencies

```bash
pip install -r requirements.txt
playwright install
2️⃣ Setup Gmail API
Create Google Cloud project
Enable Gmail API
Download client_secret.json
Place it in project root
First run will generate token.json.
3️⃣ Add companies
Copy:
sites.example.txt → sites.txt
Add one company URL per line.
4️⃣ Run
python run_watchdog.py

---

##🧠 Smart Features
Deduplicates jobs across runs
Handles navigation failures gracefully
Detects QA keywords dynamically
Extracts job links intelligently
Structured test folder for validation
Logging for debugging and traceability

---

##📌 Why I Built This
As part of my transition into QA Automation,
I built a real-world monitoring tool to:
Practice browser automation
Work with APIs (Gmail)
Design maintainable test architecture
Handle production-like edge cases
Build a portfolio project that solves a real problem

---

##🔐 Security
The following files are excluded from version control:
token.json
client_secret.json
seen_jobs.json

---

##👨‍💻 Author
Yehuda Gutmann
Junior QA | Automation in Progress
