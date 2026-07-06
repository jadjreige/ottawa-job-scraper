"""
JSI / Jatom Systems (JSI Telecom) careers - hosted on UltiPro/UKG
(recruiting.ultipro.ca). The HTML board is JS-rendered, but the underlying
LoadSearchResults JSON endpoint (which the page itself calls) is public.

Ottawa/Kanata HQ, law-enforcement & intelligence data systems, C#/Angular
stack, posts junior and co-op dev roles. Requires eligibility for Top Secret
clearance - a strong fit for a federal-government background.

Company code and board ID taken from their live job board URL.
"""
from .ats_common import scrape_ultipro, OTTAWA_LOCATION_FILTER

SOURCE_NAME = "JSI (Jatom Systems)"

COMPANY_CODE = "JAT5000JAT"
BOARD_ID = "df50e66e-c710-4410-afdb-88066904e063"


def scrape():
    return scrape_ultipro(COMPANY_CODE, BOARD_ID, SOURCE_NAME,
                          location_filter=OTTAWA_LOCATION_FILTER)
