from __future__ import annotations

import json
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

from gmail_service import send_gmail  # צריך לספק את זה (ראה למטה)

# -----------------------
# Config
# -----------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SITES_FILE = PROJECT_ROOT / "sites.txt"
SEEN_FILE = PROJECT_ROOT / "seen_jobs.json"

TO_EMAIL = "ygutmann@gmail.com"

HEADLESS = True
NAV_TIMEOUT_MS = 25_000
WAIT_AFTER_NAV_MS = 500  # טיפה יציבות
ALLOW_EXTERNAL_CAREERS_DOMAIN = False

QA_KEYWORDS = [
    "qa",
    "quality assurance",
    "test engineer",
    "tester",
    "automation",
    "sdet",
    "software test",
    "בדיקות",
    "בודק",
]

CAREERS_HINTS = [
    "careers",
    "jobs",
    "join us",
    "open positions",
    "vacancies",
    "work with us",
    "talent",
    "positions",
    "recruit",
]

JOB_LINK_HINTS = [
    "apply",
    "job",
    "position",
    "opening",
    "requisition",
    "greenhouse",
    "lever",
    "workable",
    "ashby",
    "comeet",
    "smartrecruiters",
    "icims",
]


# -----------------------
# Models
# -----------------------
@dataclass
class SiteResult:
    base_url: str
    careers_url: Optional[str] = None
    has_qa_signal: bool = False
    job_links: list[str] = field(default_factory=list)
    notes: str = ""


# -----------------------
# Utilities
# -----------------------
def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def same_domain(a: str, b: str) -> bool:
    try:
        return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()
    except Exception:
        return False


def sha_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_sites() -> list[str]:
    if not SITES_FILE.exists():
        return []
    lines = [l.strip() for l in SITES_FILE.read_text(encoding="utf-8").splitlines()]
    sites = []
    for l in lines:
        if not l or l.startswith("#"):
            continue
        sites.append(normalize_url(l))
    # מסלק כפילויות תוך שמירה על סדר
    seen = set()
    unique = []
    for s in sites:
        if s not in seen:
            unique.append(s)
            seen.add(s)
    return unique


def load_seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    try:
        data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(str(x) for x in data)
    except Exception:
        pass
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")


def build_email_html(new_results: list[SiteResult], could_not_verify: list[SiteResult]) -> str:
    total_links = sum(len(r.job_links) for r in new_results)
    html = f"""
    <h2>QA Watchdog results</h2>
    <p><b>Run time:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    <p><b>New items:</b> {total_links} link(s) across {len(new_results)} site(s)</p>
    <hr/>
    """

    if new_results:
        html += f"<h3>🚨 New QA-related links</h3>"
        for r in new_results:
            html += f"""
            <h4>{r.base_url}</h4>
            <p><b>Careers:</b> {f'<a href="{r.careers_url}">{r.careers_url}</a>' if r.careers_url else 'N/A'}</p>
            <p><b>Status:</b> {r.notes}</p>
            """
            if r.job_links:
                html += "<p><b>New links:</b></p><ul>"
                for link in r.job_links:
                    html += f'<li><a href="{link}">{link}</a></li>'
                html += "</ul>"
            html += "<hr/>"

    if could_not_verify:
        html += f"<h3>Could not verify: {len(could_not_verify)}</h3><ul>"
        for r in could_not_verify:
            cu = r.careers_url or ""
            html += f"<li>{r.base_url} — {r.notes} {f'(Careers: {cu})' if cu else ''}</li>"
        html += "</ul>"

    return html


# -----------------------
# Scraping logic
# -----------------------
def find_careers_link(page, base_url: str) -> Optional[str]:
    # מחפש לינקים שנראים כמו careers/jobs בעמוד הבית
    anchors = page.locator("a")
    count = anchors.count()
    best = None

    for i in range(min(count, 250)):  # לא לסרוק אלפים
        try:
            a = anchors.nth(i)
            text = (a.inner_text() or "").strip().lower()
            href = (a.get_attribute("href") or "").strip()
            if not href:
                continue

            abs_url = urljoin(base_url, href)
            hay = (text + " " + href).lower()

            if any(h in hay for h in CAREERS_HINTS):
                # אם לא מאפשרים דומיין חיצוני – נוודא
                if not ALLOW_EXTERNAL_CAREERS_DOMAIN and not same_domain(base_url, abs_url):
                    continue
                best = abs_url
                break
        except Exception:
            continue

    return best


def page_has_qa_signal(page) -> bool:
    try:
        content = (page.content() or "").lower()
    except Exception:
        return False
    return any(k in content for k in QA_KEYWORDS)


def extract_job_links(page, careers_url: str) -> list[str]:
    # נחלץ לינקים ש”מריחים” כמו משרות/Apply + טקסט/URL שכולל QA/TEST
    anchors = page.locator("a")
    count = anchors.count()
    found: list[str] = []

    for i in range(min(count, 600)):
        try:
            a = anchors.nth(i)
            href = (a.get_attribute("href") or "").strip()
            if not href:
                continue
            abs_url = urljoin(careers_url, href)

            text = (a.inner_text() or "").strip().lower()
            hay = (text + " " + href).lower()

            qa_hit = any(k in hay for k in QA_KEYWORDS)
            jobish = any(h in hay for h in JOB_LINK_HINTS) or "/job" in hay or "/careers" in hay

            if qa_hit and jobish:
                found.append(abs_url)
        except Exception:
            continue

    # ננקה כפילויות ונשמור על סדר
    seen = set()
    uniq = []
    for u in found:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def check_site(page, base_url: str) -> SiteResult:
    r = SiteResult(base_url=base_url)

    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        page.wait_for_timeout(WAIT_AFTER_NAV_MS)
    except PWTimeoutError:
        r.notes = "FAIL: timeout opening base url"
        return r
    except Exception as e:
        r.notes = f"FAIL: error opening base url: {type(e).__name__}"
        return r

    careers_url = find_careers_link(page, base_url)
    r.careers_url = careers_url

    # אם לא מצאנו careers, עדיין נבדוק את העמוד עצמו (לפעמים יש listings בדף הבית)
    if not careers_url:
        r.has_qa_signal = page_has_qa_signal(page)
        r.notes = "No careers link found; scanned base page"
        return r

    # נווט לקריירות
    try:
        page.goto(careers_url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
        page.wait_for_timeout(WAIT_AFTER_NAV_MS)
    except PWTimeoutError:
        r.notes = "FAIL: timeout opening careers page"
        return r
    except Exception as e:
        r.notes = f"FAIL: error opening careers page: {type(e).__name__}"
        return r

    r.has_qa_signal = page_has_qa_signal(page)
    if r.has_qa_signal:
        r.job_links = extract_job_links(page, careers_url)
        r.notes = "QA/Test keywords detected on careers page"
    else:
        r.notes = "No QA/Test keywords detected"

    return r


# -----------------------
# Main
# -----------------------
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.info("Run started")

    sites = load_sites()
    if not sites:
        logging.warning("No sites found in sites.txt")
        logging.info("Run finished. New: 0")
        return 0

    seen = load_seen()

    new_results: list[SiteResult] = []
    could_not_verify: list[SiteResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()

        page = context.new_page()

        for base_url in sites:
            logging.info(f"Checking: {base_url}")
            res = check_site(page, base_url)

            if res.notes.startswith("FAIL:"):
                could_not_verify.append(res)
                continue

            # Dedup logic:
            # 1) אם יש job_links ספציפיים -> dedup ברמת לינק
            # 2) אם אין job_links אבל יש QA signal -> dedup “דגל באתר” כדי לא לספאמפ
            if res.has_qa_signal and res.job_links:
                only_new_links = []
                for link in res.job_links:
                    jid = sha_id(link)
                    if jid not in seen:
                        only_new_links.append(link)

                if only_new_links:
                    res.job_links = only_new_links
                    new_results.append(res)
                    for link in only_new_links:
                        seen.add(sha_id(link))

            elif res.has_qa_signal and not res.job_links:
                site_flag = sha_id(f"{res.base_url}::QA_SIGNAL")
                if site_flag not in seen:
                    # שולחים פעם אחת “יש QA אבל לא הצלחנו לחלץ לינקים”
                    res.job_links = []
                    res.notes += " (No job links extracted; first time notifying)"
                    new_results.append(res)
                    seen.add(site_flag)

        page.close()
        context.close()
        browser.close()

    save_seen(seen)

    if new_results:
        total_links = sum(len(r.job_links) for r in new_results)
        subject = f"QA Watchdog 🚨 {total_links} new link(s) on {len(new_results)} site(s)"
        body_html = build_email_html(new_results, could_not_verify)
        send_gmail(subject=subject, body_html=body_html, to_email=TO_EMAIL)
        logging.info("Email sent.")
        logging.info(f"Run finished. New sites: {len(new_results)}, New links: {total_links}")
        return 1

    logging.info("No new QA items found.")
    logging.info("Run finished. New: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())