#!/usr/bin/env python3
"""Classify review pain points using Claude Haiku instead of keywords.

Usage:
    SUPABASE_SERVICE_KEY=... ANTHROPIC_API_KEY=... python3 classify-reviews-haiku.py [--limit 50] [--report]
"""

import json, os, sys, time, requests

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Tu es un analyste spécialisé dans l'immobilier français.
Tu reçois les avis Google d'une agence immobilière. Identifie UNIQUEMENT les douleurs opérationnelles automatisables.

Catégories possibles :
- response_time : impossible de joindre, ne répond pas, ignoré
- follow_up : pas de suivi, aucune nouvelle, doit relancer
- rent_receipts : quittance en retard, jamais envoyée
- charges : erreur de charges, régularisation tardive
- deposit_return : caution non rendue, retenue abusive
- repair_tracking : travaux jamais faits, artisan jamais envoyé, logement insalubre
- visit_scheduling : rdv annulé, visite bâclée
- document_management : dossier perdu, documents demandés plusieurs fois
- closing_delays : process anormalement lent, dossier qui traîne des mois (PAS juste une mention de délai)
- billing_errors : erreur de facturation, frais cachés

IGNORE : attitude, impolitesse, incompétence, prix élevés, problèmes de voisinage.
IGNORE les avis positifs sans mention de problème.
closing_delays = UNIQUEMENT si le client se plaint explicitement que le process a pris des MOIS de trop. Pas juste "ça a pris du temps".

Retourne un JSON array. Si aucune douleur opérationnelle → retourne [].
Chaque entrée : {"category": "...", "quote": "extrait exact max 100 car", "severity": 1-3, "review_rating": N}
severity : 1=mention légère, 2=plainte claire, 3=très négatif/impactant"""


def get_agencies_to_classify(limit):
    """Get agencies with raw reviews to re-classify."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={
            "select": "id,agency_id,review_pain_points,reviews_analyzed_count",
            "reviews_analyzed_count": "gt.0",
            "intel_status": "in.(%22analyzed%22,%22scored%22,%22reviews_fetched%22)",
            "limit": limit,
        },
    )
    return resp.json() if resp.ok else []


def get_raw_reviews(agency_id):
    """Fetch the original raw reviews from the first insert (before keyword analysis overwrote them).
    If reviews were already classified by keywords, the raw text is still in the 'text' field."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={
            "select": "review_pain_points",
            "agency_id": f"eq.{agency_id}",
            "limit": 1,
        },
    )
    data = resp.json()
    if not data:
        return []
    reviews = data[0].get("review_pain_points", [])
    # Check if these are raw reviews (have 'text' field) or classified pain points (have 'category')
    if reviews and isinstance(reviews[0], dict):
        if "text" in reviews[0]:
            return reviews  # Raw reviews
        if "quote" in reviews[0]:
            return []  # Already classified, no raw text available
    return []


def classify_with_haiku(reviews):
    """Send reviews to Claude Haiku for classification."""
    # Build review text for prompt
    review_texts = []
    for r in reviews:
        rating = r.get("rating", "?")
        text = r.get("text", "")
        if text:
            review_texts.append(f"[{rating}★] {text}")

    if not review_texts:
        return []

    user_msg = "Avis Google de cette agence :\n\n" + "\n\n".join(review_texts)

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_msg}],
        },
    )

    if not resp.ok:
        return None

    data = resp.json()
    text = data.get("content", [{}])[0].get("text", "[]")

    # Parse JSON from response
    try:
        # Handle markdown code blocks
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return []


def update_enrichment(enrichment_id, pain_points):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments?id=eq.{enrichment_id}",
        headers=headers,
        json={
            "review_pain_points": pain_points,
            "intel_status": "analyzed",
        },
    )
    return resp.ok


def run_report():
    """Same report as analyze-reviews.py."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={
            "select": "agency_id,review_pain_points,intel_status",
            "intel_status": "in.(%22analyzed%22,%22scored%22)",
            "limit": 1000,
        },
    )
    if not resp.ok:
        print("Failed to fetch data", file=sys.stderr)
        return

    from collections import Counter

    LABELS = {
        "response_time": "Délai de réponse / Injoignable",
        "follow_up": "Pas de suivi / Aucune nouvelle",
        "rent_receipts": "Quittances en retard",
        "charges": "Erreurs de charges / Régularisation",
        "deposit_return": "Caution non rendue",
        "repair_tracking": "Travaux / Maintenance non suivis",
        "visit_scheduling": "Visites / RDV mal gérés",
        "document_management": "Dossiers perdus / Documents",
        "closing_delays": "Dossier qui traîne / Délais",
        "billing_errors": "Erreurs facturation / Frais cachés",
    }

    agencies = resp.json()
    total = len(agencies)
    category_counts = Counter()
    category_severities = {}
    agencies_with_pain = 0

    for a in agencies:
        points = a.get("review_pain_points", [])
        if not isinstance(points, list):
            continue
        # Filter to only classified pain points (have 'category')
        classified = [p for p in points if isinstance(p, dict) and "category" in p]
        if classified:
            agencies_with_pain += 1
        seen = set()
        for p in classified:
            cat = p["category"]
            if cat not in seen:
                category_counts[cat] += 1
                seen.add(cat)
            category_severities.setdefault(cat, []).append(p.get("severity", 1))

    print(f"\n{'='*60}")
    print(f"  RAPPORT MARCHÉ (Haiku) — Douleurs agences immobilières")
    print(f"  {total} agences analysées | {agencies_with_pain} avec douleurs")
    print(f"{'='*60}\n")

    if not category_counts:
        print("  Aucune douleur détectée.")
        return

    print(f"  {'#':<4} {'Catégorie':<35} {'Agences':>8} {'%':>6} {'Sév.':>6}")
    print(f"  {'-'*4} {'-'*35} {'-'*8} {'-'*6} {'-'*6}")

    for rank, (cat, count) in enumerate(category_counts.most_common(), 1):
        pct = count * 100 / total if total else 0
        avg_sev = sum(category_severities[cat]) / len(category_severities[cat])
        label = LABELS.get(cat, cat)
        print(f"  {rank:<4} {label:<35} {count:>8} {pct:>5.1f}% {avg_sev:>5.1f}")
    print()


def main():
    limit = 1000
    report_mode = "--report" in sys.argv
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--limit" and i + 2 <= len(sys.argv):
            limit = int(sys.argv[i + 2])

    if not SUPABASE_KEY:
        print("Set SUPABASE_SERVICE_KEY", file=sys.stderr)
        sys.exit(1)

    if report_mode:
        run_report()
        return

    if not ANTHROPIC_KEY:
        print("Set ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    agencies = get_agencies_to_classify(limit)
    print(f"# {len(agencies)} agencies to classify with Haiku", file=sys.stderr)

    # Check which have raw reviews (text field) vs already-classified
    to_process = []
    for a in agencies:
        reviews = a.get("review_pain_points", [])
        if isinstance(reviews, list) and reviews and isinstance(reviews[0], dict) and "text" in reviews[0]:
            to_process.append(a)

    print(f"# {len(to_process)} have raw reviews to classify", file=sys.stderr)

    results = []
    for i, a in enumerate(to_process):
        reviews = a["review_pain_points"]
        pain_points = classify_with_haiku(reviews)

        if pain_points is None:
            print(f"# [{i+1}/{len(to_process)}] ✗ API error", file=sys.stderr)
            continue

        ok = update_enrichment(a["id"], pain_points)

        cats = ", ".join({p["category"] for p in pain_points}) if pain_points else "none"
        print(
            f"# [{i+1}/{len(to_process)}] {'✓' if ok else '✗'} {len(pain_points)} pain points ({cats})",
            file=sys.stderr,
        )

        results.append({
            "agency_id": a["agency_id"],
            "pain_points_found": len(pain_points),
            "categories": list({p["category"] for p in pain_points}),
        })

        time.sleep(0.1)

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
