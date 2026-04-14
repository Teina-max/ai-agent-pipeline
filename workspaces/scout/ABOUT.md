# Scout — Agent de détection d'agences immobilières

## Mission

Détecter les agences immobilières autour de Toulouse via Google Places API et créer des tickets assignés à Intel pour enrichissement.

## Architecture

```
Scout (scrape-maps.py) → Tickets → Intel (enrichissement)
```

- **Source** : Google Places API (New) — Text Search REST
- **Cible** : Agences immobilières, rayon 30km autour de Toulouse
- **Fréquence** : Hebdomadaire (lundi 8h Paris)
- **Dédup** : Par `placeId` Google Maps (identifiant unique et stable)
- **Output** : 1 ticket/agence assigné à Intel

## Fichiers clés

| Fichier | Rôle |
|---------|------|
| `workspaces/scout/scripts/scrape-maps.py` | Script Python — appelle Google Places API, output JSON |
| `workspaces/scout/MEMORY.md` | Mémoire persistante du scout (stats, leçons) |
| `agents/YOUR_AGENT_ID/.../AGENTS.md` | Instructions principales du scout |
| `agents/YOUR_AGENT_ID/.../HEARTBEAT.md` | Procédure heartbeat (checklist d'exécution) |

## Script scrape-maps.py

- Utilise l'API REST Google Places (New) directement via `requests`
- Pas de SDK spécifique — juste `requests` (déjà installé)
- Le package `googlemaps` est installé mais non utilisé (legacy API non activée sur le projet GCP)
- Clé API dans `GOOGLE_PLACES_API_KEY` (configurée dans `.env` de l'instance)

### Paramètres configurables (constantes dans le script)

```python
SEARCH_QUERY = "agence immobilière"
LOCATION = {"latitude": 43.6047, "longitude": 1.4442}  # Toulouse
RADIUS = 30000.0  # 30km
PAGE_SIZE = 20
MAX_PAGES = 5
```

### Format de sortie (JSON par agence)

```json
{
  "source": "google_maps",
  "placeId": "ChIJ...",
  "name": "Le Clos Immobilier",
  "address": "9 Pl. du Capitole, 31000 Toulouse",
  "phone": "+33 5 34 25 87 15",
  "website": "https://www.leclos-immobilier.fr/",
  "googleMapsUrl": "https://maps.google.com/?cid=...",
  "rating": 4.9,
  "totalRatings": 177,
  "types": ["real_estate_agency"],
  "businessStatus": "OPERATIONAL",
  "location": {"lat": 43.6039, "lng": 1.4427},
  "scrapedAt": "2026-04-11T21:15:29Z"
}
```

## Coût API

| Métrique | Valeur |
|----------|--------|
| SKU | Text Search Advanced ($0.035/req) |
| Requêtes/run | 1-5 (pagination) |
| Crédit gratuit Google | $200/mois |
| Coût pour 1 run/semaine | ~$0.14/mois → **gratuit** |
| Coût pour 1 run/jour | ~$1.05/mois → **gratuit** |
| Coût pour 20 runs/jour | ~$21/mois → **gratuit** (couvert par crédit) |

## Pipeline complet

1. **Scout** → scrape Google Maps → déduplique → crée tickets (type: `agency`)
2. **Intel** → enrichit (Sirene + website + find-email + verify-email) → verdict go/skip → post Discord
3. **User** → valide go/skip sur Discord
4. **Writer** → rédige l'outreach si go

## IDs (example placeholders)

| Entité | ID |
|--------|-----|
| Company | `YOUR_COMPANY_ID` |
| Project (Sales Pipeline) | `YOUR_PROJECT_ID` |
| Scout agent | `YOUR_AGENT_ID` |
| Intel agent | `YOUR_AGENT_ID` |

## Historique

- **2026-04-02 → 2026-04-11** : Scout v1 — scraping job postings via web scraper. 11 runs, 0 "go", rapid saturation, many off-target results.
- **2026-04-11** : Scout v2 — pivot to Google Places API. Direct targeting of agencies instead of detecting via job postings. First test: 20 qualified agencies in 1 run.

## TODO

- [ ] Adapter Intel pour les tickets de type "agency" (enrichissement sans analyse d'offre)
- [ ] Augmenter la couverture (requêtes complémentaires, zones élargies)
- [ ] Créer la routine cron hebdo dans votre système
- [ ] Tester le flow complet Scout → Intel → Discord → Writer
