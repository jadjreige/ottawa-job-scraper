"""
Shared helpers used by every per-site scraper module.
"""
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

TIMEOUT = 20


def get_soup(url, params=None):
    """Fetch a URL and return a BeautifulSoup object. Raises on failure -
    callers should catch exceptions so one broken source doesn't kill the whole run."""
    resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def get_json(url, params=None):
    resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def post_json(url, payload, extra_headers=None):
    """POST a JSON payload and return the JSON response. Used for ATS platforms
    (Workday, UltiPro) whose career pages fetch listings via POST endpoints."""
    headers = dict(HEADERS)
    headers["Content-Type"] = "application/json; charset=UTF-8"
    if extra_headers:
        headers.update(extra_headers)
    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def make_job(title, url, source, location="Ottawa, ON", salary=None):
    return {
        "title": clean_text(title),
        "url": url.strip() if url else "",
        "source": source,
        "location": clean_text(location),
        "salary": salary,
    }
