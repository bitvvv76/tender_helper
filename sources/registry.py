"""
Tender Helper v1.5
Единый реестр источников тендеров.

На этом этапе файл не ломает старый collector.py.
Он нужен как основа для аккуратного перехода на архитектуру источников.
"""


SOURCES_REGISTRY = [
    {
        "name": "ЕИС",
        "key": "eis",
        "enabled": True,
        "module": "real_tenders",
        "function": "search_real_tenders",
    },
    {
        "name": "Сбер А",
        "key": "sber_ast",
        "enabled": True,
        "module": "sber_ast",
        "function": "search_sber_tenders",
    },
    {
        "name": "Росэлторг",
        "key": "roseltorg",
        "enabled": True,
        "module": "roseltorg",
        "function": "search_roseltorg_tenders",
    },
    {
        "name": "Газпромбанк АСТ",
        "key": "gpb_ast",
        "enabled": True,
        "module": "gpb_ast",
        "function": "search_gpb_tenders",
    },
        {
        "name": "TEK-Torg",
        "key": "tek_torg",
        "enabled": False,
        "module": "tek_torg",
        "function": "search_tek_torg_tenders",
    },
]


def get_enabled_sources():
    """
    Возвращает только включённые источники.
    """
    return [source for source in SOURCES_REGISTRY if source.get("enabled")]