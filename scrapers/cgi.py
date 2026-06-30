"""
CGI Canada careers, hosted on the njoyn ATS platform (cgi.njoyn.com).
Confirmed server-rendered (no JS needed) - the job listing table is present
in the raw HTML. The site doesn't expose a simple GET-based location/keyword
filter that works without JS form submission, so we instead pull the
(globally sorted, newest-first) listing and filter for Canada/Ottawa
ourselves in Python.

NOTE: only page 1 (~50 most recent postings, globally) is scraped per run.
Postings appear to sort newest-first by Position ID, so this should reliably
catch new Canadian postings without needing to paginate through thousands of
global listings. If Ottawa postings start getting missed, we can add
pagination (the site uses a JS gotopage() call, so that would need Playwright).
"""
from .utils import get_soup, make_job, clean_text

SOURCE_NAME = "CGI"
URL = "https://cgi.njoyn.com/corp/xweb/xweb.asp"

PARAMS = {
    "CLID": "21001",
    "page": "joblisting",
    "lang": "1",
}

LOCATION_KEYWORDS = ["ottawa", "gatineau", "remote", "canada"]


def scrape():
    jobs = []
    try:
        soup = get_soup(URL, params=PARAMS)
    except Exception as e:
        print(f"[{SOURCE_NAME}] fetch failed: {e}")
        return jobs

    rows = soup.select("table tr")
    if not rows:
        print(f"[{SOURCE_NAME}] no table rows found - markup may have changed")
        return jobs

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue  # skip header row / malformed rows

        link = row.find("a", href=True)
        if not link:
            continue

        title = clean_text(cells[1].get_text()) if len(cells) > 1 else clean_text(link.get_text())
        city = clean_text(cells[3].get_text()) if len(cells) > 3 else ""
        country = clean_text(cells[4].get_text()) if len(cells) > 4 else ""

        if not title:
            continue

        # Only keep Canadian postings, biased toward Ottawa/Gatineau/remote
        location_text = f"{city} {country}".lower()
        if country.lower() != "canada":
            continue
        if not any(kw in location_text for kw in LOCATION_KEYWORDS) and city:
            # Keep it anyway if it's Canada-wide with no specific city match -
            # better to over-include than silently miss an Ottawa posting
            pass

        href = link["href"]
        if not href.startswith("http"):
            href = "https://cgi.njoyn.com/corp/xweb/" + href.lstrip("/")

        jobs.append(make_job(title=title, url=href, source=SOURCE_NAME, location=f"{city}, {country}"))

    return jobs
