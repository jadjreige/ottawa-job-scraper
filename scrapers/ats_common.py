"""
Reusable scrapers for common ATS (Applicant Tracking System) platforms.

Several of the target companies use standard ATS platforms that expose
clean JSON APIs - far more reliable than HTML scraping. This module provides
generic functions each company-specific scraper can call with its own slug.

Platforms covered:
- Lever      (jobs.lever.co)      -> public JSON API at api.lever.co
- Greenhouse (boards.greenhouse.io) -> public JSON API at boards-api.greenhouse.io
- iCIMS      (careers-X.icims.com) -> HTML, needs careful parsing (no clean public API)
"""
from .utils import get_json, make_job, clean_text


def scrape_lever(company_slug, source_name, location_filter=None):
    """
    Lever's public API: https://api.lever.co/v0/postings/<slug>?mode=json
    Returns a clean list of postings. location_filter (list of lowercase
    strings) optionally restricts to matching locations.
    """
    jobs = []
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    try:
        data = get_json(url)
    except Exception as e:
        print(f"[{source_name}] Lever API fetch failed: {e}")
        return jobs

    for posting in data:
        title = clean_text(posting.get("text", ""))
        href = posting.get("hostedUrl", "")
        location = ""
        categories = posting.get("categories", {})
        if categories:
            location = clean_text(categories.get("location", ""))

        if not title or not href:
            continue

        if location_filter:
            loc_lower = location.lower()
            if not any(f in loc_lower for f in location_filter):
                continue

        jobs.append(make_job(title=title, url=href, source=source_name,
                             location=location or "See posting"))
    return jobs


def scrape_greenhouse(company_slug, source_name, location_filter=None):
    """
    Greenhouse public API:
    https://boards-api.greenhouse.io/v1/boards/<slug>/jobs
    """
    jobs = []
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    try:
        data = get_json(url)
    except Exception as e:
        print(f"[{source_name}] Greenhouse API fetch failed: {e}")
        return jobs

    for posting in data.get("jobs", []):
        title = clean_text(posting.get("title", ""))
        href = posting.get("absolute_url", "")
        location = clean_text(posting.get("location", {}).get("name", ""))

        if not title or not href:
            continue

        if location_filter:
            loc_lower = location.lower()
            if not any(f in loc_lower for f in location_filter):
                continue

        jobs.append(make_job(title=title, url=href, source=source_name,
                             location=location or "See posting"))
    return jobs


def scrape_bamboohr(company_slug, source_name, location_filter=None):
    """
    BambooHR public jobs feed:
    https://<slug>.bamboohr.com/careers/list
    Returns JSON with a 'result' list of postings. Each has id, jobOpeningName,
    location {city, state}, etc. Detail URL is /careers/<id>.
    """
    jobs = []
    url = f"https://{company_slug}.bamboohr.com/careers/list"
    try:
        data = get_json(url)
    except Exception as e:
        print(f"[{source_name}] BambooHR API fetch failed: {e}")
        return jobs

    for posting in data.get("result", []):
        title = clean_text(posting.get("jobOpeningName", ""))
        job_id = posting.get("id")
        if not title or not job_id:
            continue

        loc = posting.get("location") or {}
        city = clean_text(loc.get("city", "")) if isinstance(loc, dict) else ""
        state = clean_text(loc.get("state", "")) if isinstance(loc, dict) else ""
        location = clean_text(f"{city} {state}").strip()
        if not location and isinstance(posting.get("location"), str):
            location = clean_text(posting.get("location"))
        if posting.get("isRemote"):
            location = (location + " (Remote)").strip()

        href = f"https://{company_slug}.bamboohr.com/careers/{job_id}"

        if location_filter and location:
            loc_lower = location.lower()
            # keep empty-location postings (over-include); filter clear non-matches
            if not any(f in loc_lower for f in location_filter):
                continue

        jobs.append(make_job(title=title, url=href, source=source_name,
                             location=location or "See posting"))
    return jobs


def scrape_workday(tenant, wd_instance, site, source_name, location_filter=None,
                   search_text="", max_jobs=100):
    """
    Workday's public CxS API - the same JSON endpoint Workday career pages
    call internally:
    POST https://<tenant>.<wd_instance>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs
    Body: {"appliedFacets": {}, "limit": N, "offset": N, "searchText": ""}
    Returns {"total": N, "jobPostings": [{title, externalPath, locationsText, ...}]}
    """
    from .utils import post_json

    jobs = []
    base = f"https://{tenant}.{wd_instance}.myworkdayjobs.com"
    api_url = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    job_base = f"{base}/en-US/{site}"

    offset = 0
    page_size = 20  # Workday CxS max per request
    while offset < max_jobs:
        try:
            data = post_json(api_url, {
                "appliedFacets": {},
                "limit": page_size,
                "offset": offset,
                "searchText": search_text,
            })
        except Exception as e:
            print(f"[{source_name}] Workday CxS fetch failed at offset {offset}: {e}")
            break

        postings = data.get("jobPostings", [])
        if not postings:
            break

        for posting in postings:
            title = clean_text(posting.get("title", ""))
            path = posting.get("externalPath", "")
            location = clean_text(posting.get("locationsText", ""))

            if not title or not path:
                continue

            if location_filter and location:
                loc_lower = location.lower()
                if not any(f in loc_lower for f in location_filter):
                    continue

            jobs.append(make_job(title=title, url=job_base + path,
                                 source=source_name,
                                 location=location or "See posting"))

        offset += page_size
        if offset >= data.get("total", 0):
            break

    return jobs


def scrape_ultipro(company_code, board_id, source_name, location_filter=None,
                   base_host="recruiting.ultipro.ca", top=50):
    """
    UltiPro/UKG job board public search endpoint - the same JSON endpoint the
    job board page calls internally:
    POST https://<host>/<code>/JobBoard/<board_id>/JobBoardView/LoadSearchResults
    Returns {"opportunities": [{Title, Id, Locations, ...}], "totalCount": N}
    """
    from .utils import post_json

    jobs = []
    api_url = f"https://{base_host}/{company_code}/JobBoard/{board_id}/JobBoardView/LoadSearchResults"
    payload = {
        "opportunitySearch": {
            "Top": top,
            "Skip": 0,
            "QueryString": "",
            "OrderBy": [{"Value": "postedDateDesc", "PropertyName": "PostedDate",
                         "Ascending": False}],
            "Filters": [
                {"t": "TermsSearchFilterDto", "fieldName": 4, "extra": None, "values": []},
                {"t": "TermsSearchFilterDto", "fieldName": 5, "extra": None, "values": []},
                {"t": "TermsSearchFilterDto", "fieldName": 6, "extra": None, "values": []},
            ],
        },
        "matchCriteria": {
            "PreferredJobs": [], "Educations": [], "LicenseAndCertifications": [],
            "Skills": [], "hasNoLicenses": False, "SkippedSkills": [],
        },
    }

    try:
        data = post_json(api_url, payload,
                         extra_headers={"X-Requested-With": "XMLHttpRequest"})
    except Exception as e:
        print(f"[{source_name}] UltiPro fetch failed: {e}")
        return jobs

    for opp in data.get("opportunities", []):
        title = clean_text(opp.get("Title", ""))
        opp_id = opp.get("Id", "")
        if not title or not opp_id:
            continue

        # Locations is a list of dicts with nested Address info
        location = ""
        locs = opp.get("Locations") or []
        if locs and isinstance(locs, list):
            addr = (locs[0] or {}).get("Address") or {}
            city = clean_text((addr.get("City") or ""))
            state_obj = addr.get("State") or {}
            state = clean_text(state_obj.get("Code", "") if isinstance(state_obj, dict) else "")
            location = ", ".join(p for p in [city, state] if p)

        if location_filter and location:
            loc_lower = location.lower()
            if not any(f in loc_lower for f in location_filter):
                continue

        href = (f"https://{base_host}/{company_code}/JobBoard/{board_id}/"
                f"OpportunityDetail?opportunityId={opp_id}")
        jobs.append(make_job(title=title, url=href, source=source_name,
                             location=location or "See posting"))

    return jobs


# Common Canadian/Ottawa location filters reused across sources
OTTAWA_LOCATION_FILTER = ["ottawa", "gatineau", "kanata", "remote", "canada", "ontario"]
