"""Local free-text search over an authorized business CSV. No network calls."""
from __future__ import annotations

import argparse
import csv
import re
import unicodedata

SEARCH_COLUMNS = ("Company Name", "Address", "Location", "Area", "Emirate", "City", "Business Type", "Business Category", "Category", "Categories", "Keywords", "Description")


def normalized(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").casefold()
    return re.sub(r"\s+", " ", text).strip()


def search_rows(rows: list[dict[str, str]], query: str, columns: list[str] | None = None) -> list[dict[str, str]]:
    """Match each space-separated term in any selected field, order-independent.

    Terms need not be in the same field: `Dubai cafe` can match City=Dubai and
    Business Category=Cafe. A quoted phrase is treated as adjacent words.
    Empty query returns all rows without changing their order.
    """
    terms = [normalized(quoted or plain) for quoted, plain in re.findall(r'"([^"]+)"|(\S+)', query or "")]
    terms = [term for term in terms if term]
    if not terms:
        return list(rows)
    matched = []
    for row in rows:
        selected = columns or [field for field in SEARCH_COLUMNS if field in row]
        cells = [normalized(str(row.get(field) or "")) for field in selected]
        if all(any(term in cell for cell in cells) for term in terms):
            matched.append(row)
    return matched


def main() -> None:
    parser = argparse.ArgumentParser(description="Search a local CSV you are allowed to use; no remote search or API calls.")
    parser.add_argument("input_csv")
    parser.add_argument("query", help='Search name, location or business category (e.g. "Dubai cafe")')
    parser.add_argument("--output-csv", help="Write matching rows to a separate CSV")
    args = parser.parse_args()
    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if not fields:
            parser.error("Input needs CSV headers")
        rows = list(reader)
    matches = search_rows(rows, args.query)
    if args.output_csv:
        if args.input_csv == args.output_csv:
            parser.error("Output must differ from input")
        with open(args.output_csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(matches)
    print(f"{len(matches)} matches out of {len(rows)} rows")


if __name__ == "__main__":
    main()
