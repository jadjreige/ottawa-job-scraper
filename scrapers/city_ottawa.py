"""
City of Ottawa careers (Avature-based, JS-rendered).
Filters to the "Information Technology jobs" category.

Since exact CSS class names on Avature sites vary by tenant and can't be
verified without rendering JS live, this targets job links by URL pattern
instead of guessing class names - any <a> pointing to a job detail page
under /city-jobs/ with a longer text label is treated as a posting. This
is more resilient to markup/class-name changes than relying on exact
selectors, at the cost of occasionally picking up a stray non-job link
(harmless - it'll just get filtered out by the relevance scorer).
"""
from .utils import clean_text, make_job
from .browser_utils import get_rendered_html
from bs4 import BeautifulSoup

SOURCE_NAME = "City of Ottawa"
URL = "https://jobs-emplois.ottawa.ca/city-jobs/viewalljobs/?category=Information+Technology+jobs"

# Wait for ANY anchor tag to appear rather than a specific class, since we
# don't know the exact class name without live inspection.
WAIT_SELECTOR = "a[href]"


def scrape():
    jobs = []
    try:
        html = get_rendered_html(URL, wait_selector=WAIT_SELECTOR, wait_ms=6000)
    except Exception as e:
        print(f"[{SOURCE_NAME}] browser fetch failed: {e}")
        return jobs

    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all("a", href=True)

    seen_urls = set()
    for link in links:
        href = link["href"]
        # job detail pages on Avature career sites typically contain
        # "/job/" or a posting ID pattern in the URL
        if not any(marker in href.lower() for marker in ["/job/", "jobid", "joboffer", "/city-jobs/"]):
            continue

        title = clean_text(link.get_text())
        # filter out nav links, "Apply now" buttons, etc. by requiring a
        # reasonably descriptive title
        if not title or len(title) < 8 or title.lower() in ("apply now", "view job", "learn more"):
            continue

        if href.startswith("/"):
            href = "https://jobs-emplois.ottawa.ca" + href

        if href in seen_urls:
            continue
        seen_urls.add(href)

        jobs.append(make_job(title=title, url=href, source=SOURCE_NAME))

    if not jobs:
        print(f"[{SOURCE_NAME}] no job links found - page structure may differ from expected, needs live inspection")

    return jobs
