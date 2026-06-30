"""
CGI Canada careers, hosted on the njoyn ATS platform (cgi.njoyn.com).

njoyn applies anti-bot measures and loads its job table asynchronously,
so results can be inconsistent - sometimes the page is captured before the
table fully populates, yielding few/no rows. To harden this we:
  1. wait for actual populated job rows (not just the <table> element)
  2. retry the whole load a couple of times if we get suspiciously few rows
  3. use a longer settle time

Only page 1 (~50 most recent postings, globally) is scraped per run,
filtered to Canadian postings.
"""
import time
from .utils import clean_text, make_job
from .browser_utils import get_rendered_html
from bs4 import BeautifulSoup

SOURCE_NAME = "CGI"
URL = "https://cgi.njoyn.com/corp/xweb/xweb.asp?CLID=21001&page=joblisting&lang=1"

MIN_EXPECTED_CA_JOBS = 3
MAX_ATTEMPTS = 3


def _parse(html):
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("table tr")
    jobs = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        link = row.find("a", href=True)
        if not link:
            continue

        title = clean_text(cells[1].get_text()) if len(cells) > 1 else clean_text(link.get_text())
        city = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
        country = clean_text(cells[4].get_text()) if len(cells) > 4 else ""

        if not title or country.lower() != "canada":
            continue

        href = link["href"]
        if not href.startswith("http"):
            href = "https://cgi.njoyn.com/corp/xweb/" + href.lstrip("/")

        jobs.append(make_job(title=title, url=href, source=SOURCE_NAME,
                             location=f"{city}, {country}"))
    return jobs, len(rows)


def scrape():
    best_jobs = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # stealth mode + network idle to defeat njoyn's bot fingerprinting,
            # which otherwise serves automated traffic a stripped-down listing
            html = get_rendered_html(
                URL,
                wait_selector="table tr:nth-of-type(6)",
                wait_ms=8000,
                stealth=True,
                wait_networkidle=True,
            )
        except Exception as e:
            print(f"[{SOURCE_NAME}] attempt {attempt} browser fetch failed: {e}")
            continue

        jobs, row_count = _parse(html)
        if len(jobs) > len(best_jobs):
            best_jobs = jobs

        # retry if we got suspiciously few CANADIAN jobs - the tell that njoyn
        # served us a stripped-down result rather than the full listing
        if len(jobs) >= MIN_EXPECTED_CA_JOBS:
            return jobs

        print(f"[{SOURCE_NAME}] attempt {attempt}: {row_count} rows / "
              f"{len(jobs)} CA jobs - likely throttled, retrying")
        time.sleep(4)

    if len(best_jobs) < MIN_EXPECTED_CA_JOBS:
        print(f"[{SOURCE_NAME}] all attempts returned a stripped-down listing - "
              f"njoyn is fingerprinting this run. Returning what we got "
              f"({len(best_jobs)} job(s)); consider njoyn's native job alerts as backup.")
    return best_jobs
