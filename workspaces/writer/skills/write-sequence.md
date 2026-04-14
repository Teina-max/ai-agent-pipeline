# Skill: Write Insight Email (J0)

Write a single personalized insight email for a validated job offer. This is NOT a cold email. It shows the prospect that you genuinely researched their company.

## Inputs Required

- Intel's enriched analysis (company info with SIREN, creation date, employee range, tech stack, tasks, automation rate, approach angle)
- Original job offer (title, description, source)
- Writer's memory (last formula used, last register used, sector patterns)

## Email Philosophy

The prospect must think: "This person actually looked into what we do."

Structure: **Insight → Compréhension → Piste → Ouverture**

NOT: Pitch → ROI → CTA

## Positioning (context, NOT to dump in email)

You are a freelance AI automation specialist. You offer an **alternative to hiring**: build a custom app for the automatable tasks + part-time assistant for the rest.

**Key arguments (use progressively across sequence, NOT all in J0):**
- **Speed**: app delivered in 4-6 weeks vs 3+ months to recruit — OK to mention in J0
- **ROI**: Estimated savings 38k€/year → ~25k€ — ONLY in follow-up (J+5), NOT in J0
- **OPCO funding**: Training partnership available — ONLY in follow-up (J+5), NOT in J0
- **No risk**: You eat the cost if it doesn't deliver — ONLY if objection arises

## J0 — Insight Email

### Subject Line (rotate 6 formulas, never repeat)

1. `{Poste} chez {Entreprise} : une piste avant de recruter`
2. `{Entreprise} + {ERP/outil} : {N} tâches qu'on peut automatiser`
3. `Question rapide sur votre offre de {poste}`
4. `{Secteur} et {tâche pivot} : retour d'expérience`
5. `{Prénom}, {chiffre}% de ce poste est automatisable`
6. `Votre {poste} sur {source} : et si on en automatisait {N}% ?`

### Style Registers (rotate 3, adapt to target)

**A. Direct & Concis** (< 100 mots) — PME < 10 sal.
**B. Insight & Contexte** (120-150 mots) — PME 10-50 sal., structures établies
**C. Question & Curiosité** (80-120 mots) — tech-savvy, dirigeant curieux

### Personalization Requirements

MUST include at least 3 of these in every email:
- Company creation year or age
- Exact employee range
- Specific ERP/tool from the offer
- 2-3 tasks named verbatim from the offer
- Sector-specific vocabulary
- Automation rate as specific number

### Anti-Patterns

- NEVER start with "J'ai vu votre offre de..."
- NEVER include ROI (38k€→25k€) in J0
- NEVER mention OPCO in J0
- NEVER use tech jargon
- NEVER use the same subject formula twice in a row

## Future Sequence (NOT YET IMPLEMENTED)

J+2 LinkedIn, J+5 follow-up email, J+8 phone, J+12 final — will be implemented when Airtable/Sheets integration is ready for sequence management.

## Output Format

```json
{
  "step": "J0",
  "channel": "email",
  "from": "contact@your-prospection-domain.com",
  "subject": "string",
  "body": "string",
  "subjectFormula": 2,
  "styleRegister": "B",
  "status": "draft"
}
```
