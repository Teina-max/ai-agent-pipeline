# Skill: Analyze Job Offer

Analyze a job offer for automation feasibility. Return a structured assessment.

## Instructions

1. **Extract tasks** — List every task mentioned in the job description
2. **Evaluate each task**:
   - Is it automatable? (yes / partial / no)
   - How? Choose from: n8n workflow, Supabase (DB + Edge Functions), API integration, LLM (Claude/GPT), custom TypeScript app, dashboard/reporting, or "human required"
   - Build complexity: simple (< 1 day), medium (1-3 days), complex (> 3 days)
3. **Calculate automation rate** — % of tasks that are fully or partially automatable
4. **Company research** — Find:
   - Company name, sector, size (employees), approximate revenue, director/CEO name
   - Use web search if needed (Pappers, societe.com, LinkedIn)
5. **Verdict**:
   - ✅ Go if automation rate > 70%
   - ⚠️ Maybe if 50-70%
   - ❌ Skip if < 50%
6. **Approach angle** — One sentence that identifies the highest-impact automatable task and ties it to a business outcome (e.g., cash flow, time savings, error reduction)

## Output Format

Return a JSON object:

```json
{
  "company": {
    "name": "string",
    "sector": "string",
    "size": "number (employees)",
    "revenue": "string (e.g., 3.2M€)",
    "director": "string"
  },
  "tasks": [
    {
      "name": "string",
      "automatable": "yes | partial | no",
      "method": "string",
      "complexity": "simple | medium | complex"
    }
  ],
  "automationRate": "number (0-100)",
  "verdict": "go | maybe | skip",
  "angle": "string (one sentence)"
}
```

## Context

- Client: Freelance AI automation specialist (region)
- Stack: Supabase, n8n, Claude Code, TypeScript
- Offer: alternative to hiring — build an app that handles automatable tasks
- ROI: 38k€/year (salary) → ~25k€ (app + part-time assistant)
