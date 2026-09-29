"""Local filtering of an export-authorized CSV; no external requests."""
from __future__ import annotations

import math
import re
from lead_search import normalized


def _cell(row, *keys):
    return next((str(row[key]).strip() for key in keys if key in row and row[key] is not None and str(row[key]).strip()), "")


def _present(value):
    return bool(value and value.casefold() not in {"none", "n/a", "na", "null", "nan", "not found", "false"})


def _number(value):
    try:
        number = float(str(value).replace(",", ""))
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _mobile(row):
    explicit = _cell(row, "Mobile")
    if _present(explicit):
        return True
    possible = _cell(row, "WhatsApp Possible")
    if possible:
        return possible.casefold() in {"yes", "true", "1"}
    phone = re.sub(r"\D", "", _cell(row, "Intl Phone", "Phone"))
    return bool(re.fullmatch(r"(?:971|0)?5\d{8}", phone))


def filter_rows(rows, *, website="Any", phone="Any", mobile="Any", email="Any",
                categories=(), emirates=(), areas=(), min_rating=None, max_rating=None,
                min_reviews=None, max_reviews=None, name_keyword=""):
    """Filter without treating absent fields as evidence of a match.

    Category, emirate and area selections within a field are OR; filter groups
    combine with AND. Missing numeric values do not pass an active bound.
    """
    matched = []
    for row in rows:
        website_value = _cell(row, "Website Found", "Website", "Website URL")
        phone_value = _cell(row, "Mobile", "Intl Phone", "Phone")
        flags = {"website": _present(website_value), "phone": _present(phone_value),
                 "mobile": _mobile(row), "email": _present(_cell(row, "Email"))}
        if any(choice != "Any" and flags[key] != (choice == "Has") for key, choice in
               (("website", website), ("phone", phone), ("mobile", mobile), ("email", email))):
            continue
        if name_keyword and normalized(name_keyword) not in normalized(_cell(row, "Company Name", "Name")):
            continue
        facets = ((categories, _cell(row, "Business Category", "Category", "Categories", "Business Type")),
                  (emirates, _cell(row, "Emirate", "City")),
                  (areas, _cell(row, "Area", "Location")))
        if any(values and normalized(cell) not in {normalized(v) for v in values} for values, cell in facets):
            continue
        for label, low, high in (("Rating", min_rating, max_rating), ("Reviews", min_reviews, max_reviews)):
            if low is None and high is None:
                continue
            value = _number(_cell(row, label, "Review Count" if label == "Reviews" else label))
            if value is None or (low is not None and value < low) or (high is not None and value > high):
                break
        else:
            matched.append(row)
    return matched


def facet_values(rows, *fields):
    return sorted({_cell(row, *fields) for row in rows if _cell(row, *fields)}, key=str.casefold)
