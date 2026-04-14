# Scout — Mémoire persistante

> Ce fichier est lu au début de chaque run et mis à jour après chaque détection.
> Il permet d améliorer la détection des agences immobilières au fil du temps.

## Stats par run

| Date | Scrapées | Nouvelles | Doublons | Remarques |
|------|--------:|----------:|--------:|-----------|
| 2026-04-14 | 0 | 0 | 0 | BLOCKED — GOOGLE_PLACES_API_KEY not set |

## Stats Google Maps

| Métrique | Valeur |
|----------|--------|
| Total agences détectées (cumul) | 0 |
| Total tickets créés (cumul) | 0 |
| Requête principale | "agence immobilière" |
| Zone | Toulouse, 30km |

## Patterns de doublons fréquents

_Aucun pattern identifié pour l instant._

## Leçons apprises

- 2026-04-03 à 2026-04-11 (ancien mode offres d emploi) : 2 runs le même jour = saturation totale. Espacer les runs. Applicable aussi aux agences — le stock d agences ne change pas d un jour à l autre, un run hebdomadaire suffit.
