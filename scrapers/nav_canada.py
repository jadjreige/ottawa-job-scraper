"""
NAV CANADA careers - hosted on Workday
(navcanada.wd10.myworkdayjobs.com/NAV_Careers). The HTML is JS-rendered,
but Workday's public CxS JSON API (the same endpoint the page calls)
returns clean listings.

Ottawa-HQ'd air navigation services company with a large in-house
technology group (they design and build their own air-traffic systems).
Good salaries; hires software developers and technical roles regularly.
"""
from .ats_common import scrape_workday, OTTAWA_LOCATION_FILTER

SOURCE_NAME = "NAV CANADA"


def scrape():
    return scrape_workday(
        tenant="navcanada",
        wd_instance="wd10",
        site="NAV_Careers",
        source_name=SOURCE_NAME,
        location_filter=OTTAWA_LOCATION_FILTER,
    )
