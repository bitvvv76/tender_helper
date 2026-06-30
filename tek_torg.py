"""
Tender Helper v1.5
TEK-Torg source module.

Current goal:
- create a safe source interface
- do not break collector
- later add real parser after HTML/API inspection
"""


SOURCE_NAME = "ТЭК-Торг"
BASE_URL = "https://www.tektorg.ru"
URL = "https://www.tektorg.ru/procedures"


def search_tek_torg_tenders(category=None, region=None, budget=None, limit=5):
    """
    Temporary safe stub for TEK-Torg.

    Returns empty list until parser is implemented.
    Keeps collector stable.
    """
    print(f"{SOURCE_NAME}: parser not implemented yet")
    return []