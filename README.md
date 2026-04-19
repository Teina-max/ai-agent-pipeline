# AI Agent Pipeline — Autonomous B2B Prospection

![Status](https://img.shields.io/badge/status-In%20Production-red?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)

An autonomous three-agent sales pipeline that detects, analyzes, and outreaches to qualified B2B prospects. Built for freelance automation services targeting SMEs across France.

**Status**: Actively prospecting agencies in Toulouse region (30km radius). Real-time heartbeat orchestration with human-in-the-loop approval gates.

---

## Overview

This is a fully automated sales pipeline that runs 24/7, converting lead detection into qualified prospect emails with minimal human oversight:

1. **Scout** — Weekly scan via Google Places API; detects 20+ agency targets
2. **Intel** — Enriches with company data, contact discovery, and compatibility scoring
3. **Discord Gate** — Human approves/rejects before copy writing
4. **Writer** — Generates personalized cold emails with research-backed insights
5. **Gmail Gate** — Final approval before send
6. **Send** — Resend API delivery to prospect

**Cost**: ~€75/month (Resend + Supabase + APIs). **ROI**: One closed deal (25k€ contract) breaks even in 3 hours of Teina's time.

---

## Architecture & Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  HEARTBEAT TRIGGER (Monday 8am CET, orchestrated by Paperclip)
└──────────────────────┬──────────────────────────────────────┘
                       │
      ┌────────────────▼────────────────┐
      │  SCOUT (Detection Phase)        │
      │  scrape-maps.py                 │
      │  Google Places API              │
      │  Query: "agences immobilière"  │
      │  Radius: 30km from Toulouse     │
      │  Output: 15-25 candidates/week  │
      └────────────────┬────────────────┘
                       │
        Creates Paperclip Tickets (type: agency)
        with raw JSON: {placeId, name, address, phone, website, rating}
                       │
      ┌────────────────▼─────────────────┐
      │  INTEL (Enrichment & Scoring)   │
      │  9 Python scripts (auto-exec)    │
      │                                   │
      │  1. search-sirene.py             │
      │     → Company size, sector, CA   │
      │     → Exclude: >200 employees    │
      │                                   │
      │  2. enrich-website.py            │
      │     → Get homepage + parse       │
      │     → Extract pain points clues  │
      │                                   │
      │  3. find-email.py                │
      │     → DNS email permutation      │
      │     → Pattern: firstname.lastname@domain    │
      │                                   │
      │  4. verify-email.py              │
      │     → DNS MX record validation   │
      │     → Deliverability scoring    │
      │                                   │
      │  5. fetch-reviews.py             │
      │     → Google Reviews sentiment   │
      │     → Extract customer feedback  │
      │                                   │
      │  6. batch-enrich.py              │
      │     → Orchestrate all steps above│
      │     → Score = 0-100              │
      │     - Size (25%)                 │
      │     - Services (25%)             │
      │     - Pain Points (20%)          │
      │     - Contact (20%)              │
      │     - Independence (10%)         │
      │     → Send verdict to Discord    │
      │     → Store enrichment in DB     │
      │     → Post Discord alert         │
      └────────────────┬─────────────────┘
                       │
           Score ≥ 70? → "go" / "skip"
                       │
      ┌────────────────▼──────────────┐
      │  DISCORD GATE                  │
      │  (Human: Teina approves)       │
      │  Reads: score, pain points,    │
      │  angle, contact quality        │
      │  Responds: ✅ go / ❌ skip     │
      └────────────────┬──────────────┘
                       │ (if "go")
      ┌────────────────▼─────────────────┐
      │  WRITER (Copy Generation)        │
      │  Claude agent with write-sequence skill │
      │  Model: Claude Haiku 4.5         │
      │                                   │
      │  Email structure (4 blocks):     │
      │  1. Accroche (emotion-driven)   │
      │     "Most agencies lose 20% of  │
      │      leads to slow follow-up"   │
      │                                   │
      │  2. Compréhension (research)    │
      │     "You specialize in [sector] │
      │      and process [N] contracts" │
      │                                   │
      │  3. Piste (automation angle)    │
      │     "75% of your follow-ups     │
      │      could run on autopilot"    │
      │                                   │
      │  4. Ouverture (soft CTA)        │
      │     "15 min call to explore?"   │
      │                                   │
      │  Output: HTML + plain text      │
      └────────────────┬─────────────────┘
                       │
    save-draft.py creates Gmail draft + stores in Supabase (status: draft)
                       │
      ┌────────────────▼──────────────┐
      │  GMAIL GATE                    │
      │  (Human: Teina reviews draft)  │
      │  Reads: full email, tone,      │
      │  personalization, CTA clarity  │
      │  Action: approve / edit / skip │
      └────────────────┬──────────────┘
                       │ (if approve)
      ┌────────────────▼──────────────┐
      │  SEND (Delivery Phase)         │
      │  send-email.py                 │
      │  Resend API (Amazon SES)       │
      │  From: contact@your-domain.com │
      │  To: prospect@agency.fr        │
      │  Warm-up schedule (first week) │
      │  - Mon-Wed: 2/day              │
      │  - Thu-Fri: 3/day              │
      │  - Week 2+: 10/day max         │
      └────────────────┬──────────────┘
                       │
    Supabase: update status → sent, timestamp, unsubscribe_url
                       │
      ┌────────────────▼──────────────┐
      │  TRACKING (Post-Send)          │
      │  Cloudflare Email Routing      │
      │  All replies → YOUR_GMAIL_ADDRESS  │
      │  Gmail "From: contact@..."     │
      │  Real-time notification        │
      │  (Paperclip agent monitors)    │
      └────────────────────────────────┘
```

---

## Agents Breakdown

### Scout
**Role**: Lead detection via Google Places API  
**Frequency**: Weekly (Monday 8am CET)  
**Input**: Query ("agence immobilière") + location (Toulouse) + radius (30km)  
**Output**: 15-25 qualified candidates per week  
**API**: Google Places (Text Search) — $0.035/request  
**Deduplication**: By `placeId` (stable, unique identifier)

**Key Fields Extracted**:
- Place ID (Google Maps)
- Name, address, phone
- Website URL
- Rating + review count
- Business status (operational filter)
- GPS coordinates

**Cost**: ~€0.14/week = **free** (covered by Google $200 monthly credit)

### Intel
**Role**: Enrichment, qualification, scoring  
**Trigger**: On each Scout ticket (auto-exec)  
**Input**: Raw prospect data from Scout  
**Output**: Score 0-100 + enriched profile + verdict (go/skip/maybe)

**9 Python Sub-Agents**:

| Script | Source | Purpose | Cost |
|--------|--------|---------|------|
| `search-sirene.py` | Sirene API (INSEE) | Company size, sector, revenue | Free |
| `enrich-website.py` | HTTP GET | Homepage parsing for pain points | Free |
| `find-email.py` | DNS permutation + MX | Email discovery & validation | Free |
| `verify-email.py` | DNS MX records | Deliverability scoring | Free |
| `fetch-reviews.py` | Google Reviews scraper | Sentiment, customer feedback | Free |
| `analyze-reviews.py` | Custom logic | Review sentiment analysis | Free |
| `batch-enrich.py` | Orchestration | Score (0-100), Discord alert, DB storage | Free |

**Scoring Formula** (0-100):
```
score = (
  size(emp_count) * 0.25 +              // 1-50 emp = 100%, >200 = 0%
  service_match(sector) * 0.25 +        // Agency + real estate + PME focus
  pain_points(website_analysis) * 0.20 +// Keywords: follow-up, automation, CRM
  contact_quality(email_valid) * 0.20 + // Valid email >= risky >= invalid
  independence(parent_company) * 0.10   // No parent/subsidiary
)

Go Decision:   score >= 70
Maybe:         50-69 (manual review)
Skip:          < 50
```

**Example Scoring**:
- **Le Clos Immobilier** (Toulouse, 12 emp, verified email, good reviews)
  - Size: 100% | Service: 100% | Pain: 75% | Contact: 100% | Independence: 100%
  - **Score: 95/100 → GO**

- **MegaRealEstate Group** (800 emp, corporate subsidiary, no direct email)
  - Size: 10% | Service: 75% | Pain: 60% | Contact: 30% | Independence: 0%
  - **Score: 28/100 → SKIP**

### Writer
**Role**: Personalized cold email generation  
**Trigger**: After human Discord approval  
**Model**: Claude Haiku 3 (fast, cost-effective: ~$0.008/email)  
**Input**: Enriched prospect + score breakdown + pain points + website copy

**Email Philosophy**:
> **"The prospect must think: this person actually researched my company."**

The email proves research in every sentence:
- Accroche: Address a real problem (from review sentiment or pain point detection)
- Compréhension: Mention specific company details (sector, service type, employee count)
- Piste: Quantified automation claim ("75% of X tasks") not vague promises
- Ouverture: Soft CTA, mutual benefit framing

**Email Structure** (4 blocks):

```
╔════════════════════════════════════════════╗
║ ACCROCHE (Hook — Emotion)                 ║
║                                            ║
║ Most agencies lose 15-20% of leads to     ║
║ slow follow-up. Your own Google reviews  ║
║ mention "response time" as friction.      ║
╚════════════════════════════════════════════╝

╔════════════════════════════════════════════╗
║ COMPRÉHENSION (Understanding — Proof)      ║
║                                            ║
║ You manage 40+ ongoing projects, each      ║
║ requiring weekly status emails, contract  ║
║ scans, and negotiation tracking. That's   ║
║ 80 hours/month of manual admin.            ║
╚════════════════════════════════════════════╝

╔════════════════════════════════════════════╗
║ PISTE (Angle — Specific Automation)        ║
║                                            ║
║ 75% of that is automatable: contract      ║
║ status → email summaries, lead scoring    ║
║ → ranking, follow-up reminders → Slack.   ║
║ Probably frees up 60 hours/month.          ║
╚════════════════════════════════════════════╝

╔════════════════════════════════════════════╗
║ OUVERTURE (Open — Soft CTA)               ║
║                                            ║
║ I automate workflows like yours for       ║
║ freelance projects. If you're curious,    ║
║ 15 min call to explore?                   ║
║                                            ║
║ — Teina                                    ║
╚════════════════════════════════════════════╝
```

**Output**: HTML email + plain text + tracking parameters

---

## Tech Stack

### Backend & Orchestration
- **Paperclip** — Heartbeat orchestration, ticket workflow, webhook triggers
- **Claude API** — Haiku 3 (fast, cheap reasoning for Writer)
- **Supabase** — PostgreSQL DB + RLS security + API

### Data Enrichment
- **Google Places API** — Lead detection (Text Search)
- **Sirene API (INSEE)** — French company registry (free)
- **DNS Lookup** — Email permutation + MX record validation
- **HTTP Scraping** — Website & reviews analysis

### Communication & Delivery
- **Discord Webhook** — Real-time alerts to Teina
- **Gmail API** — Draft creation, "Send As" from prospect domain
- **Resend** — Email delivery (Amazon SES backend)
- **Cloudflare Email Routing** — Inbound routing (free)

### Development & Automation
- **Python 3.10+** — All data scripts
- **Requests library** — HTTP calls
- **DNSPython** — MX record checks
- **Anthropic SDK** — Claude API calls

---

## Project Structure

```
ai-agent-pipeline/
├── README.md                          # This file
├── .env.example                       # Environment template
│
├── docs/
│   ├── architecture.md                # System architecture overview
│   └── email-infrastructure.md        # Email discovery & validation approach
│
├── workspaces/
│   ├── scout/
│   │   ├── ABOUT.md
│   │   ├── MEMORY.md
│   │   └── scripts/
│   │       └── scrape-maps.py        # Google Places detection
│   │
│   ├── intel/
│   │   ├── MEMORY.md
│   │   ├── skills/
│   │   │   ├── analyze-offer.md
│   │   │   └── research-company.md
│   │   └── scripts/
│   │       ├── analyze-reviews.py    # Review sentiment analysis
│   │       ├── batch-enrich.py       # Orchestration & scoring engine
│   │       ├── classify-reviews-haiku.py  # AI review classification
│   │       ├── enrich-website.py     # Homepage analysis
│   │       ├── fetch-reviews.py      # Google Reviews fetcher
│   │       ├── find-email.py         # DNS email permutation
│   │       ├── research-company.py   # Company research
│   │       ├── search-sirene.py      # Sirene API lookup
│   │       └── verify-email.py       # Email validation via DNS/MX
│   │
│   └── writer/
│       ├── MEMORY.md
│       ├── skills/
│       │   └── write-sequence.md
│       └── scripts/
│           ├── save-draft.py         # Create Gmail draft + DB entry
│           └── send-email.py         # Resend API delivery
│
└── orchestrator/
    ├── AGENTS.md
    ├── HEARTBEAT.md
    ├── SOUL.md
    ├── TOOLS.md
    ├── README.md
    └── scripts/
        ├── heartbeat.py
        └── heartbeat.sh
```

---

## Setup & Deployment

### Prerequisites
- Python 3.10+
- Supabase account (free tier OK)
- Paperclip instance (orchestration)
- API keys: Google Places, Resend, Anthropic

### Installation

```bash
# 1. Clone & install
git clone <repo-url>
cd ai-agent-pipeline

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Deploy scripts to Paperclip
# Upload each script to corresponding workspace in Paperclip

# 4. Set heartbeat trigger
# Paperclip: Create cron job for Scout (Monday 8am CET)
# Configure Discord webhook URL for Intel alerts
```

### Running Locally (Testing)

```bash
# Test Scout detection
python workspaces/scout/scripts/scrape-maps.py

# Test Intel pipeline on a single prospect
python workspaces/intel/scripts/batch-enrich.py --place-id "ChIJ..."

# Test Writer email generation
python workspaces/writer/scripts/save-draft.py --company-id "agency-123"
```

---

## Security & Privacy

### Environment Variables (Never Hardcode)
```
GOOGLE_PLACES_API_KEY=
RESEND_API_KEY=
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
DISCORD_WEBHOOK_URL=
GMAIL_API_CREDENTIALS_JSON=
```

### Supabase RLS (Row Level Security)
All tables enforce RLS:
- `prospects` — visible only to authenticated user
- `emails_sent` — write-only on send; read-only for tracking
- `discord_approvals` — append-only audit log

### Human-in-the-Loop Gates
1. **Discord Gate** — Teina reviews score + angle before Writer executes
2. **Gmail Gate** — Teina reviews draft before Resend sends

### Domain Segregation
- **Sending**: `contact@your-prospection-domain.com` (dedicated reputation)
- **Main domain**: `your-domain.com` (never used for cold outreach)
- **Receiving**: Cloudflare Email Routing to personal Gmail

---

## Monitoring & Observability

### Metrics Dashboard (Supabase)
- Prospects detected (weekly)
- Qualified (score ≥ 70)
- Emails sent
- Response rate (tracked via Gmail → Paperclip webhook)
- Conversion rate (qualified responses → meetings)

### Discord Alerts
- Scout: "21 candidates detected this week"
- Intel: "Agency X scored 78/100 (pain: low contact quality)"
- Writer: "Email draft created — awaiting approval"
- Send: "Email sent to prospect@agency.fr"

### Logs
All Python scripts log to:
- `stdout` (local testing)
- Paperclip execution logs (production)
- Supabase `audit_log` table (compliance)

---

## Cost Analysis

### Monthly Budget Estimate

| Component | Cost | Notes |
|-----------|------|-------|
| **Scout** (Google Places) | €0 | Free tier (covered by $200 credit) |
| **Intel** (APIs) | €0 | DNS-based email discovery (free) |
| **Writer** (Claude Haiku) | €5 | ~600 emails × $0.008 = €4.80 |
| **Send** (Resend) | €40 | ~1200 emails × $0.03 = €36 |
| **Supabase** (DB + Auth) | €25 | Pro plan ($25/month) |
| **Infrastructure** | €5 | Paperclip hosting (shared) |
| **Total** | **~€75/month** | Scales linearly with volume |

### ROI Example
- **Cost**: €75/month
- **Time Invested**: 5 hours/month (Discord approvals + Gmail reviews)
- **Deal Value**: €25k (typical automation contract, 4-6 weeks build)
- **Breakeven**: **1 deal closed / 3 hours of work**

---

## Customization

### Adjust Scoring Weights
Edit `workspaces/intel/scripts/batch-enrich.py`:
```python
SCORE_WEIGHTS = {
    "size": 0.25,           # Favor SMEs
    "service": 0.25,        # Industry fit
    "pain_points": 0.20,    # Website analysis
    "contact_quality": 0.20,# Email validity
    "independence": 0.10    # No parent companies
}
```

### Change Prospect Search Criteria
Edit `workspaces/scout/scripts/scrape-maps.py`:
```python
SEARCH_QUERY = "agence immobilière"  # ← Change to: "cabinet comptable", "agence SEO", etc.
LOCATION = {"latitude": 43.6047, "longitude": 1.4442}  # Toulouse
RADIUS = 30000.0  # 30km
```

### Modify Email Template
Edit the Writer agent's `write-sequence` skill in Paperclip

### Adjust Warmup Schedule
Edit `workspaces/writer/scripts/send-email.py`:
```python
WARMUP_SCHEDULE = {
    "week_1": 2,   # Monday-Wednesday: 2 emails/day
    "week_2": 5,   # Thursday-Friday: 3 emails/day
    "week_3_plus": 10  # Week 3+: 10/day max
}
```

---

## Troubleshooting

### Scout finds 0 results
- **Check**: Google Places API quota (verify in GCP Console)
- **Check**: Location coordinates (use maps.google.com to confirm)
- **Check**: Search query too restrictive (broaden: "immobilier" vs "agence immobilière")

### Intel score seems too low
- **Check**: Company size > 200 employees (auto-skip in code)
- **Check**: Email validation failed (DNS/MX lookup issue)
- **Check**: Website unreachable (network issue or robots.txt blocking)

### Writer email not created
- **Check**: Claude API quota (Anthropic dashboard)
- **Check**: Prospect missing required fields (run Intel fully)
- **Check**: Discord approval missing (check #prospection channel)

### Emails not sending
- **Check**: Resend API key valid (test: `curl -X POST https://api.resend.com/emails`)
- **Check**: SPF/DKIM/DMARC DNS records (check Cloudflare DNS)
- **Check**: Domain reputation (check Resend bounce report)

---

## Performance Metrics (Production)

*As of April 2026*

| Metric | Value | Target |
|--------|-------|--------|
| Leads detected/week | 18-22 | 15+ |
| Score ≥ 70 (qualified) | 65-75% | 60%+ |
| Teina approval rate | 80-85% | 80%+ |
| Email delivery rate | 95%+ | 95%+ |
| Response rate | TBD | 5-8% (cold email benchmark) |
| Cost per qualified lead | €2.50 | <€5 |

---

## License & Author

**Built by**: Teina, freelance automation engineer  
**Based in**: Toulouse, France  
**Status**: Portfolio project (open for reference)

This pipeline demonstrates:
- Multi-agent orchestration (Scout → Intel → Writer)
- Human-in-the-loop approval patterns
- Cost-effective B2B outreach at scale
- Production-grade security (RLS, env vars, audit logs)

---

## Further Reading

1. **Architecture overview**: See `docs/architecture.md`
2. **Email infrastructure**: See `docs/email-infrastructure.md`

Questions? Open an issue or contact teina@your-domain.com

---

**Last Updated**: April 2026  
**Status**: Actively prospecting real estate agencies in Toulouse region
