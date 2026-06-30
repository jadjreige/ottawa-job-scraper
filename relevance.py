"""
Keyword-weighted relevance scoring - approximates a "good enough fit"
filter without requiring an exact title/resume match. Also filters out
senior/lead/director-level postings that are above your current experience level.
"""
from config import KEYWORDS, RELEVANCE_THRESHOLD, EXCLUDED_SENIORITY_TERMS, JUNIOR_FRIENDLY_TERMS


def is_too_senior(job):
    title = job["title"].lower()

    # if it explicitly signals junior/intermediate/entry-level, never exclude it
    if any(term in title for term in JUNIOR_FRIENDLY_TERMS):
        return False

    return any(term in title for term in EXCLUDED_SENIORITY_TERMS)


def score_job(job):
    text = f"{job['title']} {job.get('location', '')}".lower()
    score = 0
    matched = []
    for keyword, weight in KEYWORDS.items():
        if keyword in text:
            score += weight
            matched.append(keyword)
    return score, matched


def is_relevant(job):
    if is_too_senior(job):
        return False
    score, _ = score_job(job)
    return score >= RELEVANCE_THRESHOLD


def filter_relevant(jobs):
    relevant = []
    excluded_senior_count = 0

    for job in jobs:
        if is_too_senior(job):
            excluded_senior_count += 1
            continue

        score, matched = score_job(job)
        if score >= RELEVANCE_THRESHOLD:
            job["score"] = score
            job["matched_keywords"] = matched
            relevant.append(job)

    if excluded_senior_count:
        print(f"Filtered out {excluded_senior_count} posting(s) as too senior")

    # highest relevance first
    relevant.sort(key=lambda j: j["score"], reverse=True)
    return relevant
