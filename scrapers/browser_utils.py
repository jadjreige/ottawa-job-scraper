"""
Helper for scraping JS-rendered career pages (Workday, Avature, etc.)
using a headless browser via Playwright.

Includes stealth measures to reduce automation fingerprinting for sites
(like njoyn) that serve bots a stripped-down or empty result set:
  - masks navigator.webdriver
  - sets realistic user-agent, viewport, locale, timezone
  - spoofs plugins/languages that headless Chromium otherwise leaves empty
  - waits for network idle so async-loaded content settles

Only import/use this in scrapers that actually need it - it's much
slower and heavier than plain requests.
"""
from playwright.sync_api import sync_playwright

DEFAULT_WAIT_MS = 4000

# Injected before any page script runs, to hide common automation tells.
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = { runtime: {} };
"""

REAL_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def get_rendered_html(url, wait_selector=None, wait_ms=DEFAULT_WAIT_MS, scroll=False,
                      stealth=False, wait_networkidle=False):
    """
    Loads a URL in headless Chromium and returns the fully rendered HTML.
    wait_selector: CSS selector to wait for before grabbing HTML (preferred over wait_ms when known)
    scroll: set True for infinite-scroll job boards that lazy-load more postings
    stealth: set True to apply anti-fingerprinting measures (for anti-bot sites)
    wait_networkidle: set True to wait for network to go idle (async-heavy sites)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent=REAL_UA,
            viewport={"width": 1366, "height": 900},
            locale="en-CA",
            timezone_id="America/Toronto",
            extra_http_headers={
                "Accept-Language": "en-CA,en;q=0.9",
                "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                           "image/avif,image/webp,*/*;q=0.8"),
            },
        )
        if stealth:
            context.add_init_script(STEALTH_JS)

        page = context.new_page()

        wait_until = "networkidle" if wait_networkidle else "load"
        page.goto(url, timeout=45000, wait_until=wait_until)

        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=15000)
            except Exception:
                pass  # fall through and grab whatever loaded - caller should handle empty results
        else:
            page.wait_for_timeout(wait_ms)

        if scroll:
            for _ in range(5):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(1000)

        html = page.content()
        browser.close()
        return html
