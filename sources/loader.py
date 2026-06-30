"""
Tender Helper v1.5
Dynamic source loader.

This module loads enabled tender sources from sources.registry
and can call their search functions in a unified way.
"""

from importlib import import_module

from sources.registry import get_enabled_sources
from sources.postprocess import postprocess_tenders


def load_source_function(source_config):
    """
    Load source search function by module and function name.
    """
    module_name = source_config["module"]
    function_name = source_config["function"]

    module = import_module(module_name)
    return getattr(module, function_name)


def search_source(source_config, category=None, region=None, budget=None, limit=5):
    """
    Search one source safely.
    If source fails, return empty list and do not break the collector.
    """
    source_name = source_config.get("name", source_config.get("key", "unknown"))

    try:
        search_function = load_source_function(source_config)

        return search_function(
            category=category,
            region=region,
            budget=budget,
            limit=limit,
        )

    except Exception as e:
        print(f"{source_name} ERROR: {e}")
        return []


def search_all_sources(category=None, region=None, budget=None, limit=5):
    """
    Search all enabled sources and return combined results.
    """
    all_results = []

    for source_config in get_enabled_sources():
        source_name = source_config.get("name", source_config.get("key", "unknown"))

        results = search_source(
            source_config,
            category=category,
            region=region,
            budget=budget,
            limit=limit,
        )

        print(f"{source_name} found: {len(results)}")
        all_results.extend(results)

    return postprocess_tenders(all_results)