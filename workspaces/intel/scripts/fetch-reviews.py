#!/usr/bin/env python3
"""Fetch Google Places reviews for agencies in Supabase.

Usage:
    GOOGLE_PLACES_API_KEY=... SUPABASE_SERVICE_KEY=... python3 fetch-reviews.py [--limit 50]

Outputs JSON array to stdout. Upserts raw reviews into intel_enrichments.
"""

import json, os, sys, time, requests

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GOOGLE_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
DELAY = 0.2


def get_agencies(limit, refetch=False):
    """Get agencies to fetch reviews for."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

    if refetch:
        # Refetch mode: get agencies that already have intel_enrichments
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/intel_enrichments",
            headers=headers,
            params={"select": "agency_id", "limit": limit},
        )
        enriched_ids = {r["agency_id"] for r in resp.json()} if resp.ok else set()

        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/agencies",
            headers=headers,
            params={
                "select": "id,gmaps_place_id,name,google_rating,review_count",
                "review_count": "gt.0",
                "order": "review_count.desc",
                "limit": limit * 2,
            },
        )
        return [a for a in resp.json() if a["id"] in enriched_ids][:limit]

    # Normal mode: skip already done
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={"select": "agency_id", "reviews_analyzed_count": "gt.0"},
    )
    done_ids = {r["agency_id"] for r in resp.json()} if resp.ok else set()

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/agencies",
        headers=headers,
        params={
            "select": "id,gmaps_place_id,name,google_rating,review_count",
            "review_count": "gt.0",
            "order": "review_count.desc",
            "limit": limit * 2,
        },
    )
    agencies = [a for a in resp.json() if a["id"] not in done_ids]
    return agencies[:limit]


def fetch_reviews(place_id):
    """Fetch up to 5 reviews from Google Places API."""
    resp = requests.get(
        f"https://places.googleapis.com/v1/places/{place_id}",
        headers={
            "X-Goog-Api-Key": GOOGLE_KEY,
            "X-Goog-FieldMask": "reviews",
            "X-Goog-Api-Language": "fr",
        },
    )
    if not resp.ok:
        return []
    return [
        {
            "rating": r.get("rating"),
            "text": r.get("text", {}).get("text", ""),
            "author": r.get("authorAttribution", {}).get("displayName", ""),
            "time": r.get("relativePublishTimeDescription", ""),
        }
        for r in resp.json().get("reviews", [])
    ]


def upsert(agency_id, reviews, refetch=False):
    """Upsert raw reviews into intel_enrichments."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "review_pain_points": reviews,
        "reviews_analyzed_count": len(reviews),
    }
    if refetch:
        # Patch existing record, set status back to reviews_fetched
        payload["intel_status"] = "reviews_fetched"
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/intel_enrichments?agency_id=eq.{agency_id}",
            headers=headers, json=payload,
        )
    else:
        headers["Prefer"] = "resolution=merge-duplicates"
        payload["agency_id"] = agency_id
        payload["intel_status"] = "reviews_fetched"
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/intel_enrichments",
            headers=headers, json=payload,
        )
    return resp.ok


def main():
    limit = 50
    refetch = "--refetch" in sys.argv
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--limit" and i + 2 <= len(sys.argv):
            limit = int(sys.argv[i + 2])

    if not GOOGLE_KEY or not SUPABASE_KEY:
        print("Set GOOGLE_PLACES_API_KEY and SUPABASE_SERVICE_KEY", file=sys.stderr)
        sys.exit(1)

    agencies = get_agencies(limit, refetch=refetch)
    print(f"# {len(agencies)} agencies to process", file=sys.stderr)

    results = []
    for i, a in enumerate(agencies):
        reviews = fetch_reviews(a["gmaps_place_id"])
        ok = upsert(a["id"], reviews, refetch=refetch)
        neg = sum(1 for r in reviews if r.get("rating", 5) <= 3)

        results.append({
            "agency_id": a["id"],
            "name": a["name"],
            "rating": a["google_rating"],
            "reviews_fetched": len(reviews),
            "negative_reviews": neg,
            "stored": ok,
        })

        status = "✓" if ok else "✗"
        print(
            f"# [{i+1}/{len(agencies)}] {status} {a['name'][:45]} — "
            f"{len(reviews)} reviews ({neg} neg)",
            file=sys.stderr,
        )
        time.sleep(DELAY)

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
