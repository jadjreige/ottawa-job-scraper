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
# experience. Loosened: removed ambiguous terms like "architect", "lead",
# "manager", "director" on their own since these were over-filtering roles that
# were actually fine (e.g. "Team Lead" excluded, but also dev roles mentioning
# leading a feature). Now only excludes unambiguous senior-level signals.
EXCLUDED_SENIORITY_TERMS = [
    "senior", "sr.", "sr ", "principal", "staff engineer", "staff developer",
    "vp ", "vice president", "chief", "head of",
    "10+ years", "8+ years", "7+ years",
    "director,", "director of", "director -",  # only clear director TITLES, not "directory" etc
]

# Titles containing these terms are a positive signal that the role is
# appropriately junior/intermediate - if present, the posting is never
# excluded by EXCLUDED_SENIORITY_TERMS even if a senior term also appears.
JUNIOR_FRIENDLY_TERMS = [
    "junior", "jr.", "jr ", "entry level", "entry-level", "associate",
    "intermediate", "co-op", "coop", "internship", "intern", "new grad",
    "graduate", "level 1", "level i", "developer i", "developer 1",
    "analyst i", "analyst 1",
]

EMAIL_TO = None  # set via GitHub secret EMAIL_TO at runtime, see main.py
EMAIL_FROM = None  # set via GitHub secret EMAIL_FROM at runtime (must be a SendGrid-verified sender)

SEEN_JOBS_FILE = "seen_jobs.json"
SEEN_JOBS_RETENTION_DAYS = 30  # don't let the file grow forever
