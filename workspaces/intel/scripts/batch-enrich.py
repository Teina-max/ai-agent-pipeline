#!/usr/bin/env python3
"""Batch enrichment: Sirene + franchise classification + email + scoring.

Usage:
    SUPABASE_SERVICE_KEY=... python3 batch-enrich.py [--limit 100] [--step sirene|email|score|all]

Reads agencies from intel_enrichments, enriches via Sirene API + find-email, scores.
"""

import json, os, sys, time, subprocess, re, requests

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

FRANCHISE_NETWORKS = [
    "century 21", "orpi", "foncia", "laforêt", "laforet", "era ",
    "citya", "guy hoquet", "nestenn", "l'adresse", "sotheby",
    "safti", "bsk", "stéphane plaza", "barnes", "engel", "coldwell",
    "re/max", "keller williams", "capifrance", "optimhome", "arthurimmo",
    "square habitat", "nexity", "iad france",
]


def supabase_get(path, params):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=headers, params=params)
    return resp.json() if resp.ok else []


def supabase_patch(enrichment_id, data):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments?id=eq.{enrichment_id}",
        headers=headers, json=data,
    )
    return resp.ok


def get_enrichments(limit, needs_field):
    """Get enrichments that need a specific field filled."""
    params = {
        "select": "id,agency_id",
        "limit": limit,
        needs_field: "is.null",
    }
    return supabase_get("intel_enrichments", params)


def get_agency(agency_id):
    """Get agency details from agencies table."""
    data = supabase_get("agencies", {
        "select": "id,name,city,website_url,gmaps_place_id",
        "id": f"eq.{agency_id}",
        "limit": 1,
    })
    return data[0] if data else None


def get_contacts(agency_id):
    """Get existing contacts from scraper's contacts table."""
    return supabase_get("contacts", {
        "select": "full_name,role,email,decision_maker_score",
        "agency_id": f"eq.{agency_id}",
        "order": "decision_maker_score.desc",
        "limit": 5,
    })


def classify_franchise(name):
    """Detect if agency is a franchise."""
    name_lower = name.lower()
    for net in FRANCHISE_NETWORKS:
        if net in name_lower:
            return True, net.strip().title()
    return False, None


def run_script(script_name, *args):
    """Run a script and return parsed JSON output."""
    cmd = ["python3", os.path.join(SCRIPTS_DIR, script_name)] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def extract_domain(website_url):
    """Extract domain from URL."""
    if not website_url:
        return None
    from urllib.parse import urlparse
    parsed = urlparse(website_url)
    domain = parsed.netloc.replace("www.", "")
    # Skip generic franchise domains
    skip = ["century21.fr", "orpi.com", "foncia.com", "laforet.com", "citya.com",
            "guyhoquet.com", "nestenn.com", "era-immobilier.com", "safti.fr"]
    if domain in skip:
        return None
    return domain if domain else None


def step_sirene(limit):
    """Enrich with Sirene data + franchise classification."""
    enrichments = get_enrichments(limit, "siren")
    print(f"# Sirene: {len(enrichments)} agencies to enrich", file=sys.stderr)

    for i, e in enumerate(enrichments):
        agency = get_agency(e["agency_id"])
        if not agency:
            continue

        name = agency["name"]
        city = agency.get("city") or ""

        # Franchise classification
        is_franchise, network = classify_franchise(name)

        # Sirene lookup
        sirene = run_script("search-sirene.py", name, city)

        update = {
            "is_franchise": is_franchise,
            "network_name": network,
        }

        if sirene and "error" not in sirene:
            update["siren"] = sirene.get("siren", "")
            update["legal_form"] = sirene.get("legal_form", "")
            update["employee_range"] = sirene.get("employee_range", "")
            update["naf_code"] = sirene.get("naf", "")

            if sirene.get("creation_date"):
                update["creation_date"] = sirene["creation_date"]

            # Find first physical person director
            directors = sirene.get("directors", [])
            for d in directors:
                if d.get("type") == "personne physique" and d.get("name"):
                    update["director_name"] = d["name"]
                    update["director_role"] = d.get("role", "")
                    break

        supabase_patch(e["id"], update)

        status = "✓" if sirene and "error" not in sirene else "✗"
        director = update.get("director_name", "?")
        emp = update.get("employee_range", "?")
        fran = f" [{network}]" if is_franchise else ""
        print(
            f"# [{i+1}/{len(enrichments)}] {status} {name[:40]}{fran} — {emp} sal. — {director}",
            file=sys.stderr,
        )
        time.sleep(0.3)  # Be nice to Sirene API


def step_email(limit):
    """Find director emails."""
    # Get enrichments with director_name but no director_email
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={
            "select": "id,agency_id,director_name",
            "director_name": "not.is.null",
            "director_email": "is.null",
            "limit": limit,
        },
    )
    enrichments = resp.json() if resp.ok else []
    print(f"# Email: {len(enrichments)} directors to find", file=sys.stderr)

    for i, e in enumerate(enrichments):
        agency = get_agency(e["agency_id"])
        if not agency:
            continue

        director = e["director_name"]
        domain = extract_domain(agency.get("website_url"))

        # Check scraper's contacts first
        contacts = get_contacts(e["agency_id"])
        best_contact = None
        for c in contacts:
            if c.get("decision_maker_score", 0) >= 8 and c.get("email"):
                best_contact = c
                break

        update = {}

        if best_contact:
            update["director_email"] = best_contact["email"]
            update["director_email_confidence"] = best_contact["decision_maker_score"] * 10
            update["director_email_source"] = "contacts_table"
        elif domain and director:
            email_data = run_script("find-email.py", director, agency["name"], domain)
            if email_data and email_data.get("best_guess"):
                update["director_email"] = email_data["best_guess"]
                update["director_email_confidence"] = email_data.get("score", 50)
                update["director_email_source"] = "find-email"

        if update:
            supabase_patch(e["id"], update)

        email = update.get("director_email", "?")
        src = update.get("director_email_source", "none")
        print(f"# [{i+1}/{len(enrichments)}] {email} ({src})", file=sys.stderr)
        time.sleep(0.1)


def step_score(limit):
    """Compute intel_score and verdict."""
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/intel_enrichments",
        headers=headers,
        params={
            "select": "id,agency_id,siren,employee_range,director_name,director_email,"
                      "director_email_confidence,is_franchise,review_pain_points,services",
            "intel_score": "is.null",
            "siren": "not.is.null",
            "limit": limit,
        },
    )
    enrichments = resp.json() if resp.ok else []
    print(f"# Score: {len(enrichments)} agencies to score", file=sys.stderr)

    # Also need Google categories for service scoring
    for i, e in enumerate(enrichments):
        agency = get_agency(e["agency_id"])
        if not agency:
            continue

        # Get categories from raw_gmaps_json
        agency_full = supabase_get("agencies", {
            "select": "raw_gmaps_json",
            "id": f"eq.{e['agency_id']}",
            "limit": 1,
        })
        categories = []
        if agency_full:
            categories = agency_full[0].get("raw_gmaps_json", {}).get("categories", [])

        # Size score (25%)
        emp = e.get("employee_range", "0")
        # Solo/micro = direct decision maker, time-starved, receptive
        size_map = {"0": 70, "1-2": 80, "3-5": 90, "6-9": 100, "10-19": 80, "20-49": 60, "50-99": 20}
        size_score = size_map.get(emp, 10)

        # Service score (25%) — from Google categories
        cats_lower = " ".join(c.lower() for c in categories)
        service_score = 30  # base
        detected_services = []
        if "gestion" in cats_lower:
            service_score = 100
            detected_services.append("gestion_locative")
        if "syndic" in cats_lower or "copropri" in cats_lower:
            service_score = max(service_score, 90)
            detected_services.append("syndic")
        if "location" in cats_lower and "vacances" in cats_lower:
            service_score = max(service_score, 70)
            detected_services.append("location_saisonniere")
        if "entreprise" in cats_lower or "bureau" in cats_lower:
            service_score = max(service_score, 60)
            detected_services.append("immobilier_pro")

        # Pain points score (20%)
        pain_points = e.get("review_pain_points", [])
        pain_count = len(pain_points) if isinstance(pain_points, list) else 0
        pain_score = min(pain_count * 25, 100)

        # Contact score (20%)
        contact_score = 0
        if e.get("director_name"):
            contact_score = 40
        if e.get("director_email"):
            conf = e.get("director_email_confidence", 0) or 0
            contact_score = 40 + min(conf, 60)

        # Independence score (10%)
        indep_score = 50 if e.get("is_franchise") else 100

        # Composite
        total = int(
            size_score * 0.25
            + service_score * 0.25
            + pain_score * 0.20
            + contact_score * 0.20
            + indep_score * 0.10
        )

        verdict = "go" if total >= 70 else ("maybe" if total >= 50 else "skip")

        breakdown = {
            "size": size_score,
            "services": service_score,
            "pain_points": pain_score,
            "contact": contact_score,
            "independence": indep_score,
        }

        update = {
            "intel_score": total,
            "score_breakdown": breakdown,
            "intel_verdict": verdict,
            "services": detected_services,
            "intel_status": "scored",
        }

        supabase_patch(e["id"], update)

        emoji = {"go": "✅", "maybe": "⚠️", "skip": "❌"}.get(verdict, "?")
        print(
            f"# [{i+1}/{len(enrichments)}] {emoji} {total}/100 {agency['name'][:35]} "
            f"— size:{size_score} svc:{service_score} pain:{pain_score} "
            f"contact:{contact_score} indep:{indep_score}",
            file=sys.stderr,
        )


def main():
    limit = 1000
    step = "all"
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
        if arg == "--step" and i + 1 < len(args):
            step = args[i + 1]

    if not SUPABASE_KEY:
        print("Set SUPABASE_SERVICE_KEY", file=sys.stderr)
        sys.exit(1)

    if step in ("all", "sirene"):
        step_sirene(limit)
    if step in ("all", "email"):
        step_email(limit)
    if step in ("all", "score"):
        step_score(limit)


if __name__ == "__main__":
    main()
