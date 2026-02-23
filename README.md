# QA Job Hunt Watchdog 🚨

Automated QA job monitoring tool built with **Playwright + Python**.  
Sends email alerts via **Gmail API** when new QA / Test / Automation-related positions are detected.

---

## 🔎 What It Does

- Scans a list of tech company websites  
- Automatically finds Careers / Jobs pages  
- Detects QA / Test / Automation related positions  
- Extracts relevant job links  
- Sends email alerts **only for new jobs**  
- Prevents duplicate notifications across runs  

---

## 🛠 Tech Stack

- Python 3.11+
- Playwright (Chromium)
- Gmail API
- Pytest
- Logging
- JSON-based state management (deduplication)

---

## 📂 Project Structure
# QA Job Hunt Watchdog 🚨

Automated QA job monitoring tool built with **Playwright + Python**.  
Sends email alerts via **Gmail API** when new QA / Test / Automation-related positions are detected.

---

## 🔎 What It Does

- Scans a list of tech company websites  
- Automatically finds Careers / Jobs pages  
- Detects QA / Test / Automation related positions  
- Extracts relevant job links  
- Sends email alerts **only for new jobs**  
- Prevents duplicate notifications across runs  

---

## 🛠 Tech Stack

- Python 3.11+
- Playwright (Chromium)
- Gmail API
- Pytest
- Logging
- JSON-based state management (deduplication)

---

## 📂 Project Structure
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


---

## 🚀 How To Run

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
playwright install
## 2️⃣ Setup Gmail API

1. Create a project in Google Cloud Console  
2. Enable Gmail API  
3. Create OAuth credentials  
4. Download client_secret.json  
5. Place it in the project root  

On first run, token.json will be generated automatically.

---

## 3️⃣ Configure Sites

cp sites.example.txt sites.txt

Edit sites.txt and add one company URL per line:

https://company1.com
https://company2.com
https://company3.io

```
---

## 4️⃣ Run the Watchdog

python run_watchdog.py

If new QA-related jobs are detected, an email alert will be sent.


---

## 🧠 Smart Features

- Deduplicates job links across runs  
- Prevents repeated alerts for the same position  
- Handles navigation failures gracefully  
- Detects QA keywords dynamically  
- Extracts job links intelligently  
- Modular Page Object structure  
- Pytest test coverage included  
- Logging for traceability and debugging  

---

## 🧪 Running Tests

pytest

---

## 🔐 Security

The following files are intentionally excluded from version control:

- token.json  
- client_secret.json  
- seen_jobs.json  
- sites.txt  

---

## 📌 Why I Built This

As part of my transition into QA Automation,  
I built a real-world monitoring tool to:

- Practice browser automation with Playwright  
- Work with external APIs (Gmail API)  
- Design maintainable test architecture  
- Handle real-world edge cases (timeouts, duplicate detection)  
- Build a portfolio project that solves an actual problem  

---

## 👨‍💻 Author

Yehuda Gutmann  
Junior QA | Automation in Progress  
