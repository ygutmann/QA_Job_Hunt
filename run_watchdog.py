from __future__ import annotations

import json
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

from smtp_mailer import send_email  # <-- SMTP sender (GitHub Secrets)

# -----------------------
# Config
# -----------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SITES_FILE = PROJECT_ROOT / "sites.txt"
SEEN_FILE = PROJECT_ROOT / "seen_jobs.json"

HEADLESS = True
NAV_TIMEOUT_MS = 25_000
WAIT_AFTER_NAV_MS = 500  # קצת יציבות אחרי ניווט

# Allow careers pages on common ATS / external domains (whitelist)
ALLOWED_CAREERS_DOMAINS = {
    "boards.greenhouse.io",
    "api.greenhouse.io",
    "jobs.lever.co",
    "api.lever.co",
    "apply.workable.com",
    "jobs.ashbyhq.com",
    "jobs.smartrecruiters.com",
    "myworkdayjobs.com",
    "careers.microsoft.com",
    "jobs.nvidia.com",
}

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
    "career",
    "jobs",
    "join us",
    "open positions",
    "vacancies",
    "work with us",
    "talent",
    "positions",
    "recruit",
    "we're hiring",
    "hiring",
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
    "workday",
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
def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def sha_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_sites() -> list[str]:
    if not SITES_FILE.exists():
        return []
    lines = [l.strip() for l in SITES_FILE.read_text(encoding="utf-8").splitlines()]
    sites: list[str] = []
    for l in lines:
        if not l or l.startswith("#"):
            continue
        sites.append(normalize_url(l))

    # remove duplicates while preserving order
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


def build_email_html(
    new_results: list[SiteResult],
    could_not_verify: list[SiteResult],
    total_sites_scanned: int,
) -> str:
    total_links = sum(len(r.job_links) for r in new_results)
    html = f"""
    <h2>QA Watchdog results</h2>
    <p><b>Run time:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    <p><b>Scanned:</b> {total_sites_scanned} site(s)</p>
    <p><b>New items:</b> {total_links} link(s) across {len(new_results)} site(s)</p>
    <hr/>
    """

    if new_results:
        html += "<h3>🚨 New QA-related links</h3>"
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
# Navigation helpers
# -----------------------
def safe_goto(page, url: str, timeout_ms: int) -> tuple[bool, str]:
    """
    Retry navigation a few times to reduce flaky failures in CI.
    Returns (ok, error_string).
    """
    last_err = ""
    for attempt in range(3):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # Often improves reliability on JS-heavy pages:
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
            page.wait_for_timeout(WAIT_AFTER_NAV_MS)
            return True, ""
        except PWTimeoutError:
            last_err = "timeout"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        time.sleep(0.7 * (attempt + 1))
    return False, last_err


def is_allowed_external_careers(base_url: str, abs_url: str) -> bool:
    base_netloc = urlparse(base_url).netloc.lower()
    careers_netloc = urlparse(abs_url).netloc.lower()
    if careers_netloc == base_netloc:
        return True
    return careers_netloc in ALLOWED_CAREERS_DOMAINS


# -----------------------
# Scraping logic
# -----------------------
def find_careers_link(page, base_url: str) -> Optional[str]:
    anchors = page.locator("a")
    try:
        count = anchors.count()
    except Exception:
        count = 0

    for i in range(min(count, 300)):
        try:
            a = anchors.nth(i)
            text = (a.inner_text() or "").strip().lower()
            href = (a.get_attribute("href") or "").strip()
            if not href:
                continue

            abs_url = urljoin(base_url, href)
            hay = (text + " " + href).lower()

            if any(h in hay for h in CAREERS_HINTS):
                if not is_allowed_external_careers(base_url, abs_url):
                    continue
                return abs_url
        except Exception:
            continue

    return None


def page_has_qa_signal(page) -> bool:
    try:
        content = (page.content() or "").lower()
    except Exception:
        return False
    return any(k in content for k in QA_KEYWORDS)


def extract_job_links(page, careers_url: str) -> list[str]:
    anchors = page.locator("a")
    try:
        count = anchors.count()
    except Exception:
        count = 0

    found: list[str] = []

    for i in range(min(count, 800)):
        try:
            a = anchors.nth(i)
            href = (a.get_attribute("href") or "").strip()
            if not href:
                continue

            abs_url = urljoin(careers_url, href)
            text = (a.inner_text() or "").strip().lower()
            hay = (text + " " + href).lower()

            qa_hit = any(k in hay for k in QA_KEYWORDS)
            jobish = (
                any(h in hay for h in JOB_LINK_HINTS)
                or "/job" in hay
                or "/careers" in hay
                or "/positions" in hay
            )

            if qa_hit and jobish:
                found.append(abs_url)
        except Exception:
            continue

    # de-dup preserve order
    seen = set()
    uniq = []
    for u in found:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq


def check_site(page, base_url: str) -> SiteResult:
    r = SiteResult(base_url=base_url)

    ok, err = safe_goto(page, base_url, NAV_TIMEOUT_MS)
    if not ok:
        r.notes = f"FAIL: error opening base url: {err}"
        return r

    careers_url = find_careers_link(page, base_url)
    r.careers_url = careers_url

    if not careers_url:
        r.has_qa_signal = page_has_qa_signal(page)
        r.notes = "No careers link found; scanned base page"
        return r

    ok, err = safe_goto(page, careers_url, NAV_TIMEOUT_MS)
    if not ok:
        r.notes = f"FAIL: error opening careers page: {err}"
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

        context = browser.new_context(
            ignore_https_errors=True,
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9,he;q=0.8"},
        )

        page = context.new_page()
        page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
        page.set_default_timeout(NAV_TIMEOUT_MS)

        for base_url in sites:
            logging.info(f"Checking: {base_url}")
            res = check_site(page, base_url)

            if res.notes.startswith("FAIL:"):
                could_not_verify.append(res)
                continue

            # Dedup:
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
                    res.notes += " (No job links extracted; first time notifying)"
                    new_results.append(res)
                    seen.add(site_flag)

        page.close()
        context.close()
        browser.close()

    save_seen(seen)

    if new_results or could_not_verify:
        total_links = sum(len(r.job_links) for r in new_results)
        subject = f"QA Watchdog 🚨 {total_links} new link(s) on {len(new_results)} site(s)"
        body_html = build_email_html(new_results, could_not_verify, total_sites_scanned=len(sites))
        send_email(subject, body_html)
        logging.info("Email sent.")
        logging.info(f"Run finished. New sites: {len(new_results)}, New links: {total_links}")
        return 0

    logging.info("No new QA items found.")
    logging.info("Run finished. New: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())