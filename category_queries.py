"""Combine suggested and custom business search phrases."""
def category_queries(selected, custom):
    seen = set()
    queries = []
    for item in list(selected) + custom.split(","):
        item = item.strip()
        if item and item.casefold() not in seen:
            seen.add(item.casefold())
            queries.append(item)
    return queries
