"""
CGI Canada careers, hosted on the njoyn ATS platform (cgi.njoyn.com).

njoyn applies bot fingerprinting, so we use stealth mode (see browser_utils)
to ensure we get the full job listing rather than a stripped-down one.
Confirmed working: we reliably receive the complete ~50-row global listing.

We then filter to Canadian postings only. The number of Canadian dev roles
varies run-to-run with what CGI has posted - some days many, some days few.
Only page 1 (~50 most recent postings, globally) is scraped per run.
"""
from .utils import clean_text, make_job
from .browser_utils import get_rendered_html
from bs4 import BeautifulSoup

SOURCE_NAME = "CGI"
URL = "https://cgi.njoyn.com/corp/xweb/xweb.asp?CLID=21001&page=joblisting&lang=1"


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
    # Stealth mode confirmed working: njoyn serves the full ~50-row listing.
    # The number of CANADIAN jobs simply varies with what's posted - some runs
    # there are many dev roles, other runs only a handful of non-dev Canadian
    # postings. No retry needed; we get the complete page on the first load.
    try:
        html = get_rendered_html(
            URL,
            wait_selector="table tr:nth-of-type(6)",
            wait_ms=8000,
            stealth=True,
            wait_networkidle=True,
        )
    except Exception as e:
        print(f"[{SOURCE_NAME}] browser fetch failed: {e}")
        return []

    jobs, row_count = _parse(html)
    print(f"[{SOURCE_NAME}] {row_count} rows on page, {len(jobs)} Canadian posting(s)")
    return jobs
