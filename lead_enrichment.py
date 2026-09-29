"""Enrich an export-authorized business CSV, independent of Google Places.

No Google Maps API data is fetched or exported by this module. Search is optional
and uses an official API, never a scraped search-results page.
"""
from __future__ import annotations

import argparse
import csv
import ipaddress
import os
import re
import socket
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

USER_AGENT = "GoogleScraperLeadEnrichment/1.0 (+respect robots.txt)"
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
MOBILE_RE = re.compile(r"(?<!\d)(?:\+?971[\s().-]*|0)5[0-9](?:[\s().-]*\d){7}(?!\d)")
SOCIAL_HOSTS = {"instagram.com", "facebook.com", "linkedin.com", "tiktok.com", "x.com"}


def public_url(url: str) -> str | None:
    """Reject local/non-web URLs before navigation, including DNS-resolved private IPs."""
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            return None
        host = parsed.hostname.lower().rstrip(".")
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return None
        for answer in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM):
            if not ipaddress.ip_address(answer[4][0]).is_global:
                return None
        return url
    except (ValueError, OSError):
        return None


def mobile_number(text: str) -> str:
    match = MOBILE_RE.search(text or "")
    if not match:
        return ""
    digits = re.sub(r"\D", "", match.group())
    return "+971" + digits[1:] if digits.startswith("0") else "+" + digits


def same_site(url: str, base: str) -> bool:
    a, b = urlparse(url), urlparse(base)
    return a.hostname == b.hostname and a.scheme in ("http", "https")


def allowed_by_robots(url: str, session: requests.Session) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = session.get(robots_url, timeout=8, allow_redirects=False)
        if response.status_code in (401, 403) or response.status_code >= 500:
            return False
        if response.status_code == 404:
            return True
        if response.status_code != 200 or len(response.content) > 500_000:
            return False
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(USER_AGENT, url)
    except requests.RequestException:
        return False


def fetch_page(url: str, session: requests.Session, use_playwright: bool = False) -> tuple[str, str]:
    if not public_url(url) or not allowed_by_robots(url, session):
        return "", ""
    if use_playwright:
        # One short-lived browser; no CAPTCHA bypass, credentials, or bulk crawling.
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                # Only the intended document is fetched. Block subresources and
                # redirects to other hosts or private addresses.
                def route_request(route):
                    request_url = route.request.url
                    if route.request.resource_type != "document" or not same_site(request_url, url) or not public_url(request_url):
                        route.abort()
                    else:
                        route.continue_()
                page.route("**/*", route_request)
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                final_url = page.url
                if not same_site(final_url, url) or not public_url(final_url) or not allowed_by_robots(final_url, session):
                    return "", ""
                return page.content()[:1_000_000], final_url
            finally:
                browser.close()
    response = session.get(url, timeout=12, allow_redirects=False, headers={"User-Agent": USER_AGENT})
    if response.status_code != 200 or "text/html" not in response.headers.get("Content-Type", "").lower():
        return "", ""
    if len(response.content) > 1_000_000:
        return "", ""
    return response.text, url


def extract(html: str, url: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    emails = set(EMAIL_RE.findall(soup.get_text(" ", strip=True)))
    phones = []
    socials = []
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        if a["href"].startswith("mailto:"):
            emails.update(EMAIL_RE.findall(a["href"]))
        elif a["href"].startswith("tel:"):
            phones.append(a["href"][4:])
        else:
            hostname = (urlparse(href).hostname or "").lower()
            if any(hostname == domain or hostname.endswith("." + domain) for domain in SOCIAL_HOSTS):
                socials.append(href)
    phones.insert(0, soup.get_text(" ", strip=True))
    return {
        "Email": "; ".join(sorted(emails))[:500],
        "Mobile": next((number for text in phones if (number := mobile_number(text))), ""),
        "Social URLs": "; ".join(sorted(set(socials)))[:1000],
        "Contact Source URL": url,
    }


def search_candidates(name: str, area: str, key: str, session: requests.Session) -> list[dict]:
    if not key:
        return []
    response = session.get("https://api.search.brave.com/res/v1/web/search", params={"q": f'"{name}" {area} official site', "count": 5}, headers={"X-Subscription-Token": key}, timeout=12)
    response.raise_for_status()
    return [{"title": item.get("title", "")[:180], "url": item.get("url", ""), "description": item.get("description", "")[:400]} for item in response.json().get("web", {}).get("results", [])[:5]]


def typesafe_match(name: str, area: str, candidates: list[dict], key: str, session: requests.Session) -> str:
    if not key or not candidates:
        return ""
    # TypeSafe judges supplied evidence; it neither searches nor invents URLs.
    questions = {f"candidate_{i}": {"type": "noul", "instructions": f"Is candidates[{i}] clearly the official website of the named business in the named area, rather than an unrelated business, directory, or social profile?"} for i in range(len(candidates))}
    response = session.post("https://api.typesafe.ai/v1/systemone", headers={"Authorization": f"Bearer {key}"}, json={"model": "jev-latest", "state": {"business": name, "area": area, "candidates": candidates}, "questions": questions}, timeout=12)
    response.raise_for_status()
    answers = response.json().get("answers", {})
    accepted = []
    for i, candidate in enumerate(candidates):
        answer = answers.get(f"candidate_{i}", {})
        if answer.get("type") == "noul" and isinstance(answer.get("noul"), (int, float)) and answer["noul"] >= .95:
            accepted.append(candidate["url"])
    # Ambiguity is not a license to pick a domain.
    return accepted[0] if len(accepted) == 1 else ""


def enrich_row(row: dict[str, str], session: requests.Session, brave_key: str = "", typesafe_key: str = "", use_playwright: bool = False) -> dict[str, str]:
    result = dict(row)
    website = (row.get("Website") or row.get("Website URL") or "").strip()
    if website.lower() in ("none", "n/a", "null"):
        website = ""
    status = "supplied website" if website else "website not found"
    if not website and brave_key and typesafe_key and row.get("Company Name"):
        try:
            candidates = search_candidates(row["Company Name"], row.get("Address", ""), brave_key, session)
            website = typesafe_match(row["Company Name"], row.get("Address", ""), candidates, typesafe_key, session)
            status = "search candidate judged likely" if website else "no unambiguous match"
        except (requests.RequestException, ValueError, KeyError):
            status = "search unavailable"
    result["Website Found"] = website if website and public_url(website) else ""
    result["Enrichment Status"] = status
    result.update({"Email": row.get("Email", ""), "Mobile": mobile_number(row.get("Mobile") or row.get("Intl Phone") or row.get("Phone") or ""), "Social URLs": row.get("Social URLs", ""), "Contact Source URL": row.get("Contact Source URL", "")})
    if not result["Website Found"]:
        return result
    try:
        html, final_url = fetch_page(result["Website Found"], session, use_playwright)
        if html:
            found = extract(html, final_url)
            for field in ("Email", "Mobile", "Social URLs"):
                result[field] = result[field] or found[field]
            if found["Email"] or found["Mobile"]:
                result["Contact Source URL"] = final_url
            result["Enrichment Status"] = status + "; site fetched"
            soup = BeautifulSoup(html, "html.parser")
            contacts = [urljoin(final_url, a["href"]) for a in soup.find_all("a", href=True) if re.search(r"contact", a.get_text(" ", strip=True), re.I)]
            for contact in contacts[:1]:
                if same_site(contact, final_url) and public_url(contact):
                    time.sleep(1)
                    contact_html, contact_url = fetch_page(contact, session, use_playwright)
                    if contact_html:
                        extra = extract(contact_html, contact_url)
                        for field in ("Email", "Mobile", "Social URLs"):
                            result[field] = result[field] or extra[field]
                        if extra["Email"] or extra["Mobile"]:
                            result["Contact Source URL"] = contact_url
        else:
            result["Enrichment Status"] = status + "; blocked or unavailable"
    except (requests.RequestException, ValueError, OSError, ImportError, RuntimeError):
        result["Enrichment Status"] = status + "; fetch unavailable"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich an export-authorized business CSV. No Google Maps export is performed.")
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--has-email", action="store_true")
    parser.add_argument("--has-mobile", action="store_true")
    parser.add_argument("--whatsapp-possible", action="store_true", help="UAE mobile format only; does not verify WhatsApp")
    parser.add_argument("--playwright", action="store_true", help="Load JS sites with locally installed Chromium")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 100:
        parser.error("--limit must be 1-100")
    if os.path.abspath(args.input_csv) == os.path.abspath(args.output_csv):
        parser.error("input and output must differ")
    with open(args.input_csv, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "Company Name" not in reader.fieldnames:
            parser.error("CSV needs a Company Name column")
        rows = [row for _, row in zip(range(args.limit), reader)]
        fields = list(dict.fromkeys(reader.fieldnames + ["Website Found", "Enrichment Status", "Email", "Mobile", "Social URLs", "Contact Source URL", "WhatsApp Possible"]))
    session = requests.Session()
    brave_key = os.getenv("BRAVE_SEARCH_API_KEY", "")
    typesafe_key = os.getenv("TYPESAFE_API_KEY", "")
    with open(args.output_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            result = enrich_row(row, session, brave_key, typesafe_key, args.playwright)
            result["WhatsApp Possible"] = "yes" if result["Mobile"] else "no"
            if (args.has_email and not result["Email"]) or (args.has_mobile and not result["Mobile"]) or (args.whatsapp_possible and result["WhatsApp Possible"] != "yes"):
                continue
            writer.writerow(result)
            time.sleep(1)


if __name__ == "__main__":
    main()
