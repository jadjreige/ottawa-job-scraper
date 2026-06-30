"""
Configuration for the Ottawa job scraper.
Keyword weighting is used to approximate a "good enough fit" filter
without needing an exact title match.
"""

# Each keyword has a weight. Hitting enough weight in a job title/snippet
# clears the relevance bar. This is intentionally broad per your request -
# doesn't need to be a perfect resume match, just relevant.
KEYWORDS = {
    # strong signals - title-level matches
    "developer": 3,
    "software": 3,
    "programmer": 3,
    "engineer": 2,
    "applications": 2,
    "systems": 1,
    "analyst": 2,
    "it officer": 2,
    "web": 2,
    "database": 2,
    "full stack": 3,
    "backend": 2,
    "front end": 2,
    "frontend": 2,
    # tech stack signals
    "c#": 3,
    ".net": 3,
    "asp.net": 3,
    "azure": 2,
    "devops": 2,
    "sql": 1,
    "github": 1,
    "git": 1,
    "javascript": 1,
    "html": 1,
    "python": 1,
    "java": 1,
    "powershell": 1,
    "scrum": 1,
    "agile": 1,
    "ci/cd": 1,
    "cloud": 1,
}

# A posting needs to reach this score to be included.
# Roughly tuned to act as a "60%+ fit" bar rather than requiring an exact title match.
RELEVANCE_THRESHOLD = 3

# Salary filter - if a posting includes a parsed salary, only keep ones
# overlapping this range. Postings with no salary info are kept by default
# (most career pages don't list salary in the listing view).
MIN_SALARY = 90000
MAX_SALARY = 100000

# Seniority filtering - titles containing these terms are excluded outright,
# regardless of keyword relevance score. Based on ~1.5-2 years of professional
# experience (DOJ Software Developer since Oct 2024, plus OPC/House of
# Commons/CIPO). Adjust this list as your experience grows.
EXCLUDED_SENIORITY_TERMS = [
    "senior", "sr.", "sr ", "lead developer", "lead engineer", "tech lead",
    "principal", "staff engineer", "staff developer", "director", "head of",
    "vp ", "vice president", "chief", "manager", "architect",
    "10+ years", "8+ years", "7+ years", "6+ years", "5+ years",
]

# Titles containing these terms are a positive signal that the role is
# appropriately junior/intermediate - not required, but if present, the
# posting is never excluded by EXCLUDED_SENIORITY_TERMS even if it overlaps
# (e.g. "Junior Developer mentored by Senior team" shouldn't be excluded
# just because "Senior" appears in the description).
JUNIOR_FRIENDLY_TERMS = [
    "junior", "jr.", "jr ", "entry level", "entry-level", "associate",
    "intermediate", "co-op", "coop", "internship", "intern", "new grad",
    "graduate", "level 1", "level i", "i -", "developer i",
]

EMAIL_TO = None  # set via GitHub secret EMAIL_TO at runtime, see main.py
EMAIL_FROM = None  # set via GitHub secret EMAIL_FROM at runtime (must be a SendGrid-verified sender)

SEEN_JOBS_FILE = "seen_jobs.json"
SEEN_JOBS_RETENTION_DAYS = 30  # don't let the file grow forever
