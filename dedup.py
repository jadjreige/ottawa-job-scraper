"""
Tracks which job postings have already been emailed, so the daily digest
only contains new listings. State is stored in a JSON file committed back
to the repo by the GitHub Actions workflow after each run.
"""
import json
import hashlib
import os
from datetime import datetime, timedelta
from config import SEEN_JOBS_FILE, SEEN_JOBS_RETENTION_DAYS


def _job_id(job):
    # URL is the most reliable unique key; fall back to title+source if missing
    key = job.get("url") or f"{job['source']}::{job['title']}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def load_seen():
    if not os.path.exists(SEEN_JOBS_FILE):
        return {}
    try:
        with open(SEEN_JOBS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_seen(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def prune_old(seen):
    cutoff = datetime.utcnow() - timedelta(days=SEEN_JOBS_RETENTION_DAYS)
    pruned = {}
    for job_id, date_str in seen.items():
        try:
            seen_date = datetime.fromisoformat(date_str)
        except ValueError:
            continue
        if seen_date >= cutoff:
            pruned[job_id] = date_str
    return pruned


def mark_new_and_seen(jobs):
    """Tags each job with is_new=True/False instead of dropping seen ones,
    so the email can show ALL current postings while highlighting new ones.
    Updates and saves the seen-jobs file."""
    seen = prune_old(load_seen())
    now_str = datetime.utcnow().isoformat()

    for job in jobs:
        job_id = _job_id(job)
        if job_id in seen:
            job["is_new"] = False
        else:
            job["is_new"] = True
            seen[job_id] = now_str

    save_seen(seen)
    return jobs


def filter_new(jobs):
    """Returns only jobs not seen in previous runs, and updates+saves the seen-jobs file.
    Kept for backwards compatibility; mark_new_and_seen is now preferred."""
    seen = prune_old(load_seen())
    new_jobs = []
    now_str = datetime.utcnow().isoformat()

    for job in jobs:
        job_id = _job_id(job)
        if job_id not in seen:
            new_jobs.append(job)
            seen[job_id] = now_str

    save_seen(seen)
    return new_jobs


def collapse_duplicate_titles(jobs):
    """Greenhouse (and some Workday tenants) post the same role once per
    location, each with its own job ID and URL. URL-based dedup can't catch
    these, so collapse on (source, lowercased title) and keep the first.
    Preserves input order, so call this AFTER relevance sorting."""
    seen_keys = set()
    collapsed = []
    dropped = 0

    for job in jobs:
        key = (job["source"], job["title"].strip().lower())
        if key in seen_keys:
            dropped += 1
            continue
        seen_keys.add(key)
        collapsed.append(job)

    if dropped:
        print(f"Collapsed {dropped} duplicate title(s) across sources")
    return collapsed
