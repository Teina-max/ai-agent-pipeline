#!/usr/bin/env python3
"""
search-sirene.py — Search French company registry (API Sirene gouv.fr)
Free, no API key required. Returns structured JSON.
Usage: python3 search-sirene.py "Company Name" ["City"]
"""

import json
import sys
import urllib.request
import urllib.parse

# INSEE employee range codes → readable ranges
TRANCHE_EFFECTIF = {
    "NN": "0",
    "00": "0",
    "01": "1-2",
    "02": "3-5",
    "03": "6-9",
    "11": "10-19",
    "12": "20-49",
    "21": "50-99",
    "22": "100-199",
    "31": "200-249",
    "32": "250-499",
    "41": "500-999",
    "42": "1000-1999",
    "51": "2000-4999",
    "52": "5000-9999",
    "53": "10000+",
}

# Common NAF codes for target sectors
NAF_LABELS = {
    "62.01Z": "Software development",
    "62.02A": "IT systems consulting",
    "62.09Z": "Other IT activities",
    "70.22Z": "Management consulting",
    "46.90Z": "Wholesale trade",
    "47.91B": "Distance selling",
    "69.20Z": "Accounting",
    "71.12B": "Engineering",
    "73.11Z": "Advertising agencies",
    "78.20Z": "Temporary work",
    "82.11Z": "Combined admin services",
    "85.31Z": "Secondary education",
    "85.32Z": "Technical secondary education",
    "85.41Z": "Post-secondary education",
    "85.42Z": "Higher education",
    "85.59A": "Adult continuing education",
    "43.21A": "Electrical installation",
    "41.20A": "Residential building",
    "25.62B": "Industrial mechanics",
    "10.71C": "Bakery-pastry",
    "56.10A": "Traditional restaurant",
}

# Nature juridique codes
NATURE_JURIDIQUE = {
    "1000": "Individual entrepreneur",
    "5410": "SARL",
    "5499": "Single-member SARL",
    "5510": "SA with board of directors",
    "5599": "SA (form unspecified)",
    "5710": "SAS",
    "5720": "SASU",
    "6540": "SCOP",
    "9220": "Registered association",
    "7112": "Independent administrative authority",
    "7210": "Municipality",
    "7220": "Department",
    "7225": "Public intercommunal body",
    "7344": "Local public establishment",
}

# Département mapping for common cities
CITY_TO_DEPT = {
    "toulouse": "31", "blagnac": "31", "tournefeuille": "31", "colomiers": "31",
    "muret": "31", "balma": "31", "ramonville": "31", "castanet": "31",
    "labege": "31", "saint-orens": "31", "cugnaux": "31", "plaisance": "31",
    "portet": "31", "fenouillet": "31", "launaguet": "31", "aucamville": "31",
    "bruguieres": "31", "castelginest": "31", "saint-jean": "31",
    "paris": "75", "lyon": "69", "marseille": "13", "bordeaux": "33",
    "nantes": "44", "montpellier": "34", "lille": "59", "nice": "06",
    "strasbourg": "67", "rennes": "35",
}


def get_departement(city):
    """Guess département from city name."""
    if not city:
        return None
    normalized = city.lower().strip().replace("è", "e").replace("é", "e").replace("ê", "e")
    for key, dept in CITY_TO_DEPT.items():
        if key in normalized or normalized in key:
            return dept
    return None


def search_sirene(company_name, city=""):
    """Search company on recherche-entreprises.api.gouv.fr."""
    params = {"q": company_name, "page": "1", "per_page": "5"}

    dept = get_departement(city)
    if dept:
        params["departement"] = dept

    url = "https://recherche-entreprises.api.gouv.fr/search?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; intel-agent/1.0)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "company": company_name, "city": city}

    results = data.get("results", [])
    if not results:
        return {"error": "No results found", "company": company_name, "city": city}

    # Return best match (first result) + alternatives
    best = results[0]
    siege = best.get("siege", {})

    directors = []
    for d in best.get("dirigeants", []):
        name = d.get("nom", d.get("denomination", ""))
        prenom = d.get("prenom", "")
        full_name = f"{prenom} {name}".strip() if prenom else name
        directors.append({
            "name": full_name,
            "role": d.get("qualite", ""),
            "type": d.get("type_dirigeant", ""),
        })

    naf = best.get("activite_principale", "")
    tranche = best.get("tranche_effectif_salarie", "")
    nature = str(best.get("nature_juridique", ""))

    result = {
        "siren": best.get("siren", ""),
        "siret": siege.get("siret", ""),
        "name": best.get("nom_complet", ""),
        "trade_name": best.get("nom_raison_sociale", ""),
        "address": siege.get("adresse", siege.get("geo_adresse", "")),
        "postal_code": siege.get("code_postal", ""),
        "city": siege.get("libelle_commune", ""),
        "naf": naf,
        "sector": NAF_LABELS.get(naf, naf),
        "legal_form": NATURE_JURIDIQUE.get(nature, nature),
        "employee_range": TRANCHE_EFFECTIF.get(tranche, tranche),
        "creation_date": best.get("date_creation", ""),
        "category": best.get("categorie_entreprise", ""),
        "is_employer": siege.get("caractere_employeur", "") == "O",
        "is_active": best.get("etat_administratif", "") == "A",
        "directors": directors,
        "total_results": data.get("total_results", 0),
    }

    # Include alternatives if multiple results
    if len(results) > 1:
        result["alternatives"] = [
            {
                "siren": r.get("siren", ""),
                "name": r.get("nom_complet", ""),
                "city": r.get("siege", {}).get("libelle_commune", ""),
                "naf": r.get("activite_principale", ""),
            }
            for r in results[1:4]
        ]

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 search-sirene.py 'Company Name' ['City']", file=sys.stderr)
        sys.exit(1)

    company = sys.argv[1]
    city = sys.argv[2] if len(sys.argv) > 2 else ""

    result = search_sirene(company, city)
    print(json.dumps(result, ensure_ascii=False, indent=2))
