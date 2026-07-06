"""
Registry of active scrapers. Add new entries here as we expand to the
full 20-source list. Each module must expose a scrape() function that
returns a list of job dicts (see utils.make_job).

NOTE: GC Jobs (emploisfp-psjobs.cfp-psc.gc.ca) is intentionally NOT
included here - the site's robots.txt explicitly disallows automated
access. Use their native "Job Alerts" feature instead (free, official,
and won't break when their site changes): create an account at
https://emploisfp-psjobs.cfp-psc.gc.ca, search IT-02/IT-03 + your
location, and click "Create job alert" to get official email notifications.
"""
from . import city_ottawa
from . import hydro_ottawa
from . import cgi
from . import telesat
from . import versaterm
from . import coveo
from . import foci
from . import jsi
from . import bank_of_canada
from . import nav_canada

ACTIVE_SCRAPERS = [
    city_ottawa,
    hydro_ottawa,
    cgi,
    telesat,
    versaterm,
    coveo,
    foci,
    jsi,
    bank_of_canada,
    nav_canada,
]
