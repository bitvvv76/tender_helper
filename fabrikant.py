"""
Tender Helper v1.5
Fabrikant source module.

Current goal:
- create a safe source interface
- do not break collector
- later add real parser after HTML/API inspection
"""


SOURCE_NAME = "Фабрикант"
BASE_URL = "https://www.fabrikant.ru"
URL = "https://www.fabrikant.ru/procedure/search"


def search_fabrikant_tenders(category=None, region=None, budget=None, limit=5):
    """
    Temporary safe stub for Fabrikant.

    Returns empty list until parser is implemented.
    Keeps collector stable.
    """
    print(f"{SOURCE_NAME}: parser not implemented yet")
    return []