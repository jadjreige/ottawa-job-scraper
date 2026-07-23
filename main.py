"""
Entry point - run by GitHub Actions every morning.
Scrapes all active sources, filters for relevance, dedups against
previous runs, and emails the digest via SendGrid.

Also tracks per-source health: a scraper that returns far fewer postings
than its baseline is flagged in the digest, so a silently-broken source
doesn't just look like a quiet job market.
"""
from scrapers import ACTIVE_SCRAPERS
from relevance import filter_relevant
from dedup import mark_new_and_seen, collapse_duplicate_titles
from emailer import send_digest
from config import SOURCE_HEALTH_BASELINE


def run():
    all_jobs = []
    health = []  # list of (source_name, status, detail)

    for scraper in ACTIVE_SCRAPERS:
        source_name = getattr(scraper, "SOURCE_NAME", scraper.__name__)
        baseline = SOURCE_HEALTH_BASELINE.get(source_name, 0)

        try:
            jobs = scraper.scrape()
        except Exception as e:
            # one broken scraper should never take down the whole run
            print(f"[{source_name}] scraper CRASHED: {e}")
            health.append((source_name, "crashed", str(e)[:200]))
            continue

        count = len(jobs)
        print(f"[{source_name}] found {count} raw postings")
        if jobs:
            print(f"[{source_name}] sample titles: {[j['title'] for j in jobs[:5]]}")

        if count == 0 and baseline > 0:
            print(f"[{source_name}] *** RETURNED 0, expected >= {baseline} - likely broken ***")
            health.append((source_name, "down", f"0 postings (expected >= {baseline})"))
        elif count < baseline:
            print(f"[{source_name}] *** only {count}, expected >= {baseline} - possibly degraded ***")
            health.append((source_name, "degraded", f"{count} postings (expected >= {baseline})"))

        all_jobs.extend(jobs)

    print(f"{len(all_jobs)} raw postings across all sources")

    relevant = filter_relevant(all_jobs)
    relevant = collapse_duplicate_titles(relevant)
    print(f"{len(relevant)} postings passed the relevance filter (after title-collapse)")

    all_postings = mark_new_and_seen(relevant)
    new_count = sum(1 for j in all_postings if j["is_new"])
    print(f"{new_count} are new since the last run ({len(all_postings)} total shown)")

    if health:
        print(f"HEALTH: {len(health)} source(s) need attention: "
              f"{', '.join(s for s, _, _ in health)}")

    jobs_by_tier = {"Primary": all_postings}

    send_digest(jobs_by_tier, new_count=new_count, health=health)


if __name__ == "__main__":
    run()
