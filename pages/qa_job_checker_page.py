import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

@dataclass
class CheckResult:
    base_url: str
    careers_url: str | None
    has_qa_job: bool
    notes: str
    job_links: list[str] = field(default_factory=list)


class QaJobCheckerPage:
    CAREERS_TEXT_RE = re.compile(
        r"(careers?|jobs?|join\s+us|work\s+with\s+us|open\s+positions?|vacancies|we'?re\s+hiring|hiring)",
        re.IGNORECASE,
    )

    QA_RE = re.compile(
        r"(\bqa\b|quality\s*assurance|\btester\b|\btesting\b|\bsdet\b|automation\s*test)",
        re.IGNORECASE,
    )

    COMMON_CAREER_PATHS = [
        "/careers", "/career", "/jobs", "/job", "/join-us", "/join",
        "/about/careers", "/company/careers", "/work-with-us",
    ]

    def __init__(
        self,
        page,
        base_url: str,
        timeout_ms: int = 20000,
        allow_external_careers_domain: bool = False,
    ):
        self.page = page
        self.base_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc.lower()
        self.timeout_ms = timeout_ms
        self.allow_external = allow_external_careers_domain

    def run_check(self) -> CheckResult:
        try:
            self._goto(self.base_url)
        except Exception as e:
            return CheckResult(self.base_url, None, False, f"FAIL: Could not open base url. Error: {e}")

        careers_url = self._navigate_to_careers()
        if not careers_url:
            return CheckResult(
                self.base_url,
                None,
                False,
                "FAIL: Could not reach a Careers/Jobs page (no link found, common paths failed).",
            )

        careers_domain = urlparse(careers_url).netloc.lower()
        if careers_domain != self.base_domain and not self.allow_external:
            return CheckResult(
                self.base_url,
                careers_url,
                False,
                f"FAIL: Careers page moved to external domain ({careers_domain}). "
                f"Set allow_external_careers_domain=True to allow it.",
            )

        self._try_use_search("qa")
        has_qa = self._detect_qa()
        # Debug quick hint in notes:
        if has_qa:
            try:
                sample = (self.page.inner_text("body") or "")[:400]
                return CheckResult(self.base_url, careers_url, True, f"FAIL: QA job detected (sample): {sample}")
            except Exception:
                pass
        return CheckResult(
            self.base_url,
            careers_url,
            has_qa,
            ("FAIL: QA job detected" if has_qa else "PASS: No QA job detected"),
        )

    def _navigate_to_careers(self) -> str | None:
        # 1) try clicking link
        if self._click_careers_link():
            if self._looks_like_careers_page():
                return self.page.url

        # 2) fallback: common paths
        for p in self.COMMON_CAREER_PATHS:
            candidate = urljoin(self.base_url.rstrip("/") + "/", p.lstrip("/"))
            if self._try_open_non_404(candidate) and self._looks_like_careers_page():
                return self.page.url

        return None

    def _looks_like_careers_page(self) -> bool:
        """
        נוודא שזה באמת עמוד קריירה ולא נשארנו בהום פייג'.
        """
        url = (self.page.url or "").lower()
        if any(k in url for k in ["/careers", "/jobs", "/job", "careers", "jobs"]):
            return True

        try:
            body = (self.page.inner_text("body") or "").lower()
        except Exception:
            return False

        # מילים שמופיעות כמעט תמיד בעמוד משרות
        signals = ["open positions", "job", "careers", "vacancies", "apply", "positions"]
        return any(s in body for s in signals)

    def _click_careers_link(self) -> bool:
        links = self.page.locator("a:visible")
        count = links.count()

        for i in range(min(count, 120)):
            a = links.nth(i)
            try:
                txt = (a.inner_text(timeout=400) or "").strip()
            except Exception:
                continue

            if txt and self.CAREERS_TEXT_RE.search(txt):
                try:
                    a.click(timeout=3000)
                    self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout_ms)
                    self.page.wait_for_timeout(600)
                    return True
                except Exception:
                    continue

        return False

    def _try_use_search(self, query: str) -> None:
        selectors = [
            "input[type='search']",
            "input[placeholder*='Search' i]",
            "input[aria-label*='search' i]",
            "input[name*='search' i]",
            "input[id*='search' i]",
        ]

        for sel in selectors:
            box = self.page.locator(sel).first
            try:
                if box.count() == 0 or not box.is_visible():
                    continue
                box.click(timeout=1000)
                box.fill(query, timeout=2000)
                box.press("Enter", timeout=1000)
                self.page.wait_for_timeout(800)
                return
            except Exception:
                continue

    def _detect_qa(self) -> bool:
        """
        מחפש QA בצורה שמפחיתה False Positives:
        1) קודם כל מנסה למצוא אזורים שנראים כמו רשימת משרות
        2) אם אין - מחפש טקסט QA רק אם יש גם מילה של משרה/Apply בסביבה
        """

        # נסה לתפוס כרטיסי משרה נפוצים
        job_like_selectors = [
            "[data-testid*='job' i]",
            "[class*='job' i]",
            "[class*='position' i]",
            "a[href*='job' i]",
            "a[href*='careers' i]",
            "a[href*='positions' i]",
        ]

        text_chunks = []

        for sel in job_like_selectors:
            loc = self.page.locator(sel)
            try:
                count = min(loc.count(), 80)
            except Exception:
                count = 0

            for i in range(count):
                try:
                    t = (loc.nth(i).inner_text(timeout=300) or "").strip()
                    if t:
                        text_chunks.append(t)
                except Exception:
                    continue

        # אם מצאנו משהו "דמוי משרות" – נבדוק שם QA
        joined = "\n".join(text_chunks)
        if joined and self.QA_RE.search(joined):
            return True

        # fallback: חיפוש ב-body אבל רק אם יש גם אינדיקציה של Job/Apply
        try:
            body = self.page.inner_text("body") or ""
        except Exception:
            return False

        if not self.QA_RE.search(body):
            return False

        job_context_re = re.compile(r"(apply|position|role|opening|job|vacanc|career)", re.IGNORECASE)
        return bool(job_context_re.search(body))

    def _goto(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        self.page.wait_for_timeout(600)

    def _try_open_non_404(self, url: str) -> bool:
        try:
            self._goto(url)
        except Exception:
            return False

        try:
            content = (self.page.content() or "").lower()
            title = (self.page.title() or "").lower()
        except Exception:
            return True

        if "404" in content or "page not found" in content or "not found" in title:
            return False

        return True

    @staticmethod
    def _normalize_url(u: str) -> str:
        u = u.strip()
        if not u.startswith(("http://", "https://")):
            u = "https://" + u
        return u

    def _extract_job_links(self) -> list[str]:
        """
        מחלץ עד 10 לינקים שנראים כמו משרות/Apply מתוך עמוד הקריירה.
        """
        link_hints = re.compile(r"(apply|job|position|careers|opening|vacanc)", re.IGNORECASE)
        qa_hints = self.QA_RE

        links = self.page.locator("a[href]")
        results: list[str] = []

        try:
            count = min(links.count(), 300)
        except Exception:
            return results

        for i in range(count):
            a = links.nth(i)
            try:
                href = a.get_attribute("href") or ""
                text = (a.inner_text(timeout=200) or "").strip()
            except Exception:
                continue

            if not href:
                continue

            # בנה URL מלא אם זה יחסי
            full = urljoin(self.page.url, href)

            # סינון: לינק "דמוי משרה"
            if not link_hints.search(full) and not link_hints.search(text):
                continue

            # אם יש QA בטקסט/לינק – מעדיפים אותם
            if qa_hints.search(text) or qa_hints.search(full):
                if full not in results:
                    results.append(full)

            # עצירה אם כבר יש מספיק
            if len(results) >= 10:
                break

        return results

    def _extract_job_links(self) -> list[str]:
        """
        מחלץ לינקים שנראים כמו משרה/Apply. נותן עד 10.
        """
        link_hints = re.compile(r"(apply|job|position|careers|opening|vacanc)", re.IGNORECASE)

        links = self.page.locator("a[href]")
        results: list[str] = []

        try:
            count = min(links.count(), 400)
        except Exception:
            return results

        for i in range(count):
            a = links.nth(i)
            try:
                href = a.get_attribute("href") or ""
                text = (a.inner_text(timeout=200) or "").strip()
            except Exception:
                continue

            if not href:
                continue

            full = urljoin(self.page.url, href)

            # חייב להיראות קשור למשרות/Apply
            if not link_hints.search(full) and not link_hints.search(text):
                continue

            # מעדיפים כאלה שקשורים ל-QA
            if self.QA_RE.search(text) or self.QA_RE.search(full):
                if full not in results:
                    results.append(full)

            if len(results) >= 10:
                break

        return results