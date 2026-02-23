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
