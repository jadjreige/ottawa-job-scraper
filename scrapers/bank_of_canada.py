"""
Bank of Canada careers - SuccessFactors career site
(careers.bankofcanada.ca). Unlike most SuccessFactors deployments this
list page is fully SERVER-RENDERED HTML - plain requests works, no JS
needed. Verified live: ~20 postings, all with /job/ URL pattern.

One of Ottawa's best-paying stable employers with junior-friendly IT
postings (e.g. "DevOps Analyst", "Analyst, Cyber Security (Recent
Graduates)", "QA Systems Testing Analyst").
"""
from .utils import get_soup, clean_text, make_job

SOURCE_NAME = "Bank of Canada"
URL = "https://careers.bankofcanada.ca/go/All-Job-Opportunities/2400817/"
BASE = "https://careers.bankofcanada.ca"


def scrape():
    jobs = []
    try:
        soup = get_soup(URL)
    except Exception as e:
        print(f"[{SOURCE_NAME}] fetch failed: {e}")
        return jobs

    seen_urls = set()
    for link in soup.select("a[href*='/job/']"):
        href = link.get("href", "")
        title = clean_text(link.get_text())
        if not title or not href:
            continue
        if not href.startswith("http"):
            href = BASE + href
        # the page renders each job link twice; dedupe by URL
        if href in seen_urls:
            continue
        seen_urls.add(href)

        # location is embedded in the URL slug (e.g. Ottawa-%28Downtown%29-...)
        location = "Ottawa, ON"
        if "Toronto" in href and "Ottawa" not in href:
            location = "Toronto, ON"
        elif "Ottawa-or-Toronto" in href:
            location = "Ottawa or Toronto, ON"

        jobs.append(make_job(title=title, url=href, source=SOURCE_NAME,
                             location=location))

    if not jobs:
        print(f"[{SOURCE_NAME}] no job links found - markup may have changed")
    return jobs
