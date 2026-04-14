#!/usr/bin/env python3
"""Classify review pain points using keyword matching. No LLM needed.

Usage:
    SUPABASE_SERVICE_KEY=... python3 analyze-reviews.py [--limit 50] [--report]

--report: aggregate pain points across all analyzed agencies and print market summary.
"""

import json, os, sys, re, requests

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Pain point taxonomy — keywords in FR + EN
TAXONOMY = {
    "response_time": {
        "label": "Délai de réponse / Injoignable",
        "solution": "Chatbot, auto-reply, SLA tracking",
        "keywords": [
            "impossible de les joindre", "impossible de joindre",
            "ne rappelle", "pas de réponse", "aucune réponse",
            "jamais joignable", "injoignable", "ne répond",
            "délai de réponse", "attente téléphone", "ne décroche",
            "no response", "never answer", "can.t reach", "ignored",
            "don.t answer", "unreachable", "no reply", "never respond",
            "never called back", "impossible to reach", "never pick up",
        ],
    },
    "follow_up": {
        "label": "Pas de suivi / Aucune nouvelle",
        "solution": "Workflow notifications, status pipeline",
        "keywords": [
            "pas de suivi", "aucun suivi", "aucune nouvelle",
            "jamais de nouvelle", "doit relancer", "sans nouvelle",
            "relancer plusieurs fois", "pas de retour",
            "no follow.up", "no update", "never hear", "had to chase",
            "no news", "ghosted", "left in the dark", "no communication",
        ],
    },
    "rent_receipts": {
        "label": "Quittances en retard",
        "solution": "Génération + envoi auto mensuel",
        "keywords": [
            "quittance", "quittances de loyer",
            "rent receipt", "rental receipt",
        ],
    },
    "charges": {
        "label": "Erreurs de charges / Régularisation",
        "solution": "Calcul automatique charges",
        "keywords": [
            "charges locatives", "régularisation de charges",
            "erreur de charges", "provision sur charges",
            "service charge", "additional charge", "extra charge",
        ],
    },
    "deposit_return": {
        "label": "Caution non rendue",
        "solution": "Workflow deadline + relance auto",
        "keywords": [
            "caution", "dépôt de garantie", "restitution",
            "rendre la caution", "retenir la caution",
            "deposit", "security deposit", "deposit back",
            "deposit return", "kept my deposit",
        ],
    },
    "repair_tracking": {
        "label": "Travaux / Maintenance non suivis",
        "solution": "Ticketing maintenance, SLA artisan",
        "keywords": [
            "travaux", "réparation", "artisan", "intervention",
            "plombier", "fuite", "dégât des eaux", "moisissure",
            "humidité", "chauffage en panne", "chaudière",
            "repair", "maintenance", "plumber", "leak", "broken",
            "mold", "mould", "heating", "fix", "not working",
        ],
    },
    "visit_scheduling": {
        "label": "Visites / RDV mal gérés",
        "solution": "Calendrier partagé, booking auto",
        "keywords": [
            "visite annulée", "rendez-vous annulé", "rdv annulé",
            "pas de créneau", "visite bâclée", "annulé sans prévenir",
            "visit cancel", "appointment cancel", "no show",
            "cancelled visit", "wasted time",
        ],
    },
    "document_management": {
        "label": "Dossiers perdus / Documents",
        "solution": "Workflow docs, templates, e-signature",
        "keywords": [
            "dossier perdu", "document perdu", "documents demandés",
            "papiers perdus", "erreur dans le contrat", "bail",
            "lost file", "lost document", "paperwork",
            "missing document", "asked again", "wrong contract",
        ],
    },
    "closing_delays": {
        "label": "Dossier qui traîne / Délais",
        "solution": "Pipeline suivi + alertes deadline",
        "keywords": [
            "dossier traîne", "délai", "trop long", "lent",
            "compromis", "signature", "notaire",
            "taking too long", "slow process", "delayed",
            "months to complete", "weeks to",
        ],
    },
    "billing_errors": {
        "label": "Erreurs facturation / Frais cachés",
        "solution": "Facturation auto, transparence",
        "keywords": [
            "erreur de facturation", "facture erronée",
            "frais cachés", "frais supplémentaires", "surfacturation",
            "billing error", "overcharged", "hidden fee",
            "unexpected charge", "wrong amount",
        ],
    },
}


def get_agencies(limit, status_filter):
    """Get agencies to analyze or report on."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={
            "select": "id,agency_id,review_pain_points,intel_status",
            "intel_status": f"eq.{status_filter}",
            "reviews_analyzed_count": "gt.0",
            "limit": limit,
        },
    )
    return resp.json() if resp.ok else []


def classify_review(text, rating):
    """Match review text against taxonomy keywords. Return list of pain points."""
    text_lower = text.lower()
    pain_points = []
    for category, config in TAXONOMY.items():
        for keyword in config["keywords"]:
            pattern = keyword.replace(".", r"\b.?\b") if "." in keyword else keyword
            if re.search(pattern, text_lower):
                # Extract surrounding quote (max 120 chars around match)
                match = re.search(pattern, text_lower)
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 80)
                quote = text[start:end].strip()
                if start > 0:
                    quote = "..." + quote
                if end < len(text):
                    quote = quote + "..."

                severity = {1: 3, 2: 2, 3: 1}.get(rating, 1)
                pain_points.append({
                    "category": category,
                    "label": config["label"],
                    "quote": quote,
                    "severity": severity,
                    "solution": config["solution"],
                    "review_rating": rating,
                })
                break  # one match per category per review
    return pain_points


def analyze_agency(raw_reviews):
    """Analyze all reviews for one agency. Return structured pain points."""
    all_pain_points = []
    for review in raw_reviews:
        rating = review.get("rating", 5)
        text = review.get("text", "")
        if not text:
            continue
        # Analyze ALL reviews, not just negative — a 4★ can mention a problem
        points = classify_review(text, rating)
        all_pain_points.extend(points)
    return all_pain_points


def update_enrichment(enrichment_id, pain_points):
    """Update intel_enrichments with classified pain points."""
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
    """Aggregate pain points across all analyzed agencies."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={
            "select": "agency_id,review_pain_points,intel_status",
            "intel_status": "eq.analyzed",
            "limit": 1000,
        },
    )
    if not resp.ok:
        print("Failed to fetch data", file=sys.stderr)
        return

    agencies = resp.json()
    total = len(agencies)

    # Aggregate
    from collections import Counter
    category_counts = Counter()
    category_severities = {}
    agencies_with_pain = 0

    for a in agencies:
        points = a.get("review_pain_points", [])
        if points:
            agencies_with_pain += 1
        seen_cats = set()
        for p in points:
            cat = p["category"]
            if cat not in seen_cats:
                category_counts[cat] += 1
                seen_cats.add(cat)
            category_severities.setdefault(cat, []).append(p["severity"])

    print(f"\n{'='*60}")
    print(f"  RAPPORT MARCHÉ — Douleurs agences immobilières")
    print(f"  {total} agences analysées | {agencies_with_pain} avec douleurs détectées")
    print(f"{'='*60}\n")

    if not category_counts:
        print("  Aucune douleur détectée.")
        return

    print(f"  {'#':<4} {'Catégorie':<35} {'Agences':>8} {'%':>6} {'Sév.moy':>8}")
    print(f"  {'-'*4} {'-'*35} {'-'*8} {'-'*6} {'-'*8}")

    for rank, (cat, count) in enumerate(category_counts.most_common(), 1):
        pct = count * 100 / total if total else 0
        avg_sev = sum(category_severities[cat]) / len(category_severities[cat])
        label = TAXONOMY[cat]["label"]
        print(f"  {rank:<4} {label:<35} {count:>8} {pct:>5.1f}% {avg_sev:>7.1f}")

    print(f"\n  Solutions prioritaires :")
    for cat, _ in category_counts.most_common(5):
        print(f"    → {TAXONOMY[cat]['label']}: {TAXONOMY[cat]['solution']}")
    print()


def main():
    limit = 50
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

    # Analyze mode: process reviews_fetched → analyzed
    agencies = get_agencies(limit, "reviews_fetched")
    print(f"# {len(agencies)} agencies to analyze", file=sys.stderr)

    results = []
    for i, a in enumerate(agencies):
        raw_reviews = a.get("review_pain_points", [])
        pain_points = analyze_agency(raw_reviews)
        ok = update_enrichment(a["id"], pain_points)

        results.append({
            "agency_id": a["agency_id"],
            "pain_points_found": len(pain_points),
            "categories": list({p["category"] for p in pain_points}),
            "stored": ok,
        })

        cats = ", ".join({p["category"] for p in pain_points}) or "none"
        status = "✓" if ok else "✗"
        print(
            f"# [{i+1}/{len(agencies)}] {status} {len(pain_points)} pain points ({cats})",
            file=sys.stderr,
        )

    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
