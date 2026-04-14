# Skill: Research Company

Deep research on a company when the basic analysis needs more context.

## Instructions

1. Search for the company on:
   - Pappers.fr or societe.com (legal info, revenue, size)
   - LinkedIn (company page, employee count, recent posts)
   - Company website (services, clients, culture)
2. Build a profile:
   - Legal name, SIREN/SIRET
   - Sector and main activity
   - Employee count (exact or estimate)
   - Revenue (CA) and trend (growing/stable/declining)
   - Director/CEO name and LinkedIn profile
   - Key decision makers (DRH, DAF, DG)
   - Recent news or events (funding, hiring spree, restructuring)
3. Assess fit for automation offer:
   - Is this company likely to be receptive to automation?
   - Are they already tech-savvy or traditional?
   - What's the best entry point (who to contact, what angle)?

## Output Format

```json
{
  "legal": {
    "name": "string",
    "siren": "string",
    "address": "string"
  },
  "profile": {
    "sector": "string",
    "activity": "string",
    "size": "number",
    "revenue": "string",
    "trend": "growing | stable | declining"
  },
  "people": [
    {
      "name": "string",
      "role": "string",
      "linkedin": "string (URL or null)"
    }
  ],
  "fit": {
    "receptivity": "high | medium | low",
    "techLevel": "high | medium | low",
    "bestContact": "string (name + role)",
    "bestAngle": "string (one sentence)"
  }
}
```
