"""
Sends the daily job digest via the SendGrid API (plain requests call,
no SDK dependency needed).

The email shows ALL current matching postings (grouped by source/category),
visually flags which ones are new since the last run, and the subject line
counts only the new ones.
"""
import os
import requests
from datetime import date
from collections import defaultdict


SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


def build_health_html(health):
    """Renders the scraper-health banner. Empty string when all sources are OK."""
    if not health:
        return ""

    rows = []
    for source, status, detail in health:
        colour = "#c0392b" if status in ("down", "crashed") else "#b8860b"
        rows.append(
            f"<li><strong style='color:{colour}'>{source} - {status.upper()}</strong>"
            f" <span style='color:#666'>({detail})</span></li>"
        )

    return (
        "<div style='border:2px solid #c0392b;background:#fff5f5;"
        "padding:10px 14px;margin:12px 0;border-radius:4px'>"
        "<strong style='color:#c0392b'>Scraper health warning</strong>"
        "<p style='margin:6px 0;color:#555;font-size:13px'>These sources returned "
        "fewer postings than expected. A quiet job market and a broken scraper look "
        "identical in this digest - check these before assuming there is nothing new.</p>"
        "<ul style='margin:6px 0'>" + "".join(rows) + "</ul></div>"
    )


def build_html(jobs_by_tier, new_count, health=None):
    today = date.today().strftime("%B %d, %Y")
    html = [f"<h2>Ottawa Job Digest - {today}</h2>"]

    banner = build_health_html(health)
    if banner:
        html.append(banner)

    total = sum(len(v) for v in jobs_by_tier.values())
    if total == 0:
        html.append("<p>No matching postings currently open.</p>")
        return "\n".join(html)

    html.append(
        f"<p style='color:#555'>{new_count} new since last digest &middot; "
        f"{total} total matching postings currently open</p>"
    )

    for tier_name, jobs in jobs_by_tier.items():
        if not jobs:
            continue
        html.append(f"<h3 style='margin-bottom:4px'>{tier_name}</h3>")

        # group postings by source (acts as the "category" within a tier)
        by_source = defaultdict(list)
        for job in jobs:
            by_source[job["source"]].append(job)

        for source in sorted(by_source.keys()):
            source_jobs = by_source[source]
            new_in_source = sum(1 for j in source_jobs if j.get("is_new"))
            label = f"{source} ({len(source_jobs)})"
            if new_in_source:
                label += f" &mdash; {new_in_source} new"
            html.append(f"<h4 style='margin:10px 0 4px 0;color:#333'>{label}</h4>")
            html.append("<ul style='margin-top:0'>")

            # new postings first within each source
            source_jobs.sort(key=lambda j: not j.get("is_new"))
            for job in source_jobs:
                badge = ""
                if job.get("is_new"):
                    badge = (" <span style='background:#c0392b;color:#fff;"
                             "font-size:11px;padding:1px 6px;border-radius:3px;"
                             "margin-left:6px'>NEW</span>")
                html.append(
                    f"<li><a href='{job['url']}'>{job['title']}</a>{badge}</li>"
                )
            html.append("</ul>")

    return "\n".join(html)


def send_digest(jobs_by_tier, new_count=0, health=None):
    api_key = os.environ["SENDGRID_API_KEY"]
    to_email = os.environ["EMAIL_TO"]
    from_email = os.environ.get("EMAIL_FROM", to_email)  # must be SendGrid-verified

    total = sum(len(v) for v in jobs_by_tier.values())

    broken = [s for s, status, _ in (health or []) if status in ("down", "crashed")]

    if broken:
        # lead with the failure - a silent 0 is worse than no email at all
        subject = f"[SCRAPER ISSUE] Ottawa Job Digest - {len(broken)} source(s) down"
    elif total == 0:
        subject = "Ottawa Job Digest - no matching postings open"
    elif new_count == 0:
        subject = "Ottawa Job Digest - no new postings today"
    else:
        subject = f"Ottawa Job Digest - {new_count} new posting(s)"

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/html",
                     "value": build_html(jobs_by_tier, new_count, health)}],
    }

    resp = requests.post(
        SENDGRID_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if resp.status_code >= 300:
        print(f"SendGrid error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    else:
        print(f"Email sent successfully ({new_count} new, {total} total shown).")
