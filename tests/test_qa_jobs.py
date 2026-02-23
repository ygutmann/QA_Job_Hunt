import pytest
from pages.qa_job_checker_page import QaJobCheckerPage


SITES = [
    "https://wolt.com",
    "https://monday.com",
    "https://taboola.com",
]


@pytest.mark.parametrize("base_url", SITES)
def test_no_qa_job(base_url, page):
    checker = QaJobCheckerPage(page, base_url, allow_external_careers_domain=False)
    result = checker.run_check()

    assert result.has_qa_job is False, (
        f"{result.notes}\n"
        f"Base: {result.base_url}\n"
        f"Careers: {result.careers_url}\n"
    )