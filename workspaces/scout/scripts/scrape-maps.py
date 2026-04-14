#!/usr/bin/env python3
"""
scrape-maps.py — Google Places API (New) wrapper for Scout agent
Scrapes real estate agencies around Toulouse via Google Maps.
Uses the REST API directly (no SDK needed, just requests).
Outputs JSON to stdout for Claude Code to process.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# --- Configuration ---
SEARCH_QUERY = "agence immobilière"
LOCATION = {"latitude": 43.6047, "longitude": 1.4442}  # Toulouse center
RADIUS = 30000.0  # 30km in meters
PAGE_SIZE = 20  # Max per request
MAX_PAGES = 5  # Up to 100 results with pagination
PAGE_DELAY = 0.5  # Seconds between pagination requests

# Places API (New) endpoints
TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Fields to request (controls billing tier)
# Basic: id, displayName, formattedAddress, location, types, businessStatus
# Pro: internationalPhoneNumber, websiteUri, rating, userRatingCount
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.types",
    "places.businessStatus",
    "places.internationalPhoneNumber",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.rating",
    "places.userRatingCount",
])


def get_api_key():
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print(
            json.dumps({"error": "GOOGLE_PLACES_API_KEY environment variable not set"}),
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def text_search(api_key):
    """Search for real estate agencies around Toulouse using Places API (New)."""
    all_places = []
    page_token = None

    for page in range(MAX_PAGES):
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        }

        body = {
            "textQuery": SEARCH_QUERY,
            "locationBias": {
                "circle": {
                    "center": LOCATION,
                    "radius": RADIUS,
                }
            },
            "includedType": "real_estate_agency",
            "languageCode": "fr",
            "pageSize": PAGE_SIZE,
        }

        if page_token:
            body["pageToken"] = page_token

        try:
            resp = requests.post(TEXT_SEARCH_URL, headers=headers, json=body, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = resp.json().get("error", {}).get("message", "")
            except Exception:
                error_detail = resp.text[:500]
            print(
                json.dumps({
                    "error": f"API error page {page + 1}: {resp.status_code} — {error_detail}",
                }),
                file=sys.stderr,
            )
            break
        except Exception as e:
            print(
                json.dumps({"error": f"Request error page {page + 1}: {str(e)}"}),
                file=sys.stderr,
            )
            break

        places = data.get("places", [])
        all_places.extend(places)
        print(f"# Page {page + 1}: {len(places)} results", file=sys.stderr)

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(PAGE_DELAY)

    return all_places


def format_agency(place):
    """Format a Places API (New) result into our standard agency JSON."""
    location = place.get("location", {})
    display_name = place.get("displayName", {})

    return {
        "source": "google_maps",
        "placeId": place.get("id", ""),
        "name": display_name.get("text", ""),
        "address": place.get("formattedAddress", ""),
        "phone": place.get("internationalPhoneNumber")
        or place.get("nationalPhoneNumber"),
        "website": place.get("websiteUri"),
        "googleMapsUrl": place.get("googleMapsUri"),
        "rating": place.get("rating"),
        "totalRatings": place.get("userRatingCount"),
        "types": place.get("types", []),
        "businessStatus": place.get("businessStatus"),
        "location": {
            "lat": location.get("latitude"),
            "lng": location.get("longitude"),
        },
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
    }


def scrape_all():
    api_key = get_api_key()

    # Step 1: Text Search
    print(f"# Searching: {SEARCH_QUERY} around Toulouse...", file=sys.stderr)
    places = text_search(api_key)
    print(f"# Found {len(places)} total places", file=sys.stderr)

    # Step 2: Filter operational only
    agencies = []
    skipped = 0
    for place in places:
        status = place.get("businessStatus", "OPERATIONAL")
        if status != "OPERATIONAL":
            skipped += 1
            continue
        agencies.append(format_agency(place))

    if skipped:
        print(f"# Filtered {skipped} non-operational", file=sys.stderr)

    # Step 3: Deduplicate by placeId (within this run)
    seen = set()
    unique = []
    for agency in agencies:
        pid = agency["placeId"]
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(agency)

    if len(agencies) != len(unique):
        print(
            f"# Deduped {len(agencies) - len(unique)} within-run duplicates",
            file=sys.stderr,
        )

    return unique


if __name__ == "__main__":
    results = scrape_all()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n# Total: {len(results)} agencies scraped", file=sys.stderr)
