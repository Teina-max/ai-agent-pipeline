# System Architecture

## Overview

Sanele Prospection is an automated sales pipeline that converts job postings and business opportunities into qualified automation proposals. The system operates as a three-stage agent workflow with human approval gates.

**Pipeline stages:**
1. **Scout** — detect prospects (agencies, companies)
2. **Intel** — research, enrich, and score
3. **Writer** — compose personalized outreach emails

---

## Agent Lifecycle & Workflow

### Stage 1: Scout (Detection)

**Role:** Detect real estate agencies and other target businesses using data sources.

**Current Implementation:**
- **Source:** Google Places API (Text Search REST)
- **Target:** Real estate agencies within 30km of Toulouse
- **Execution:** Weekly (Mondays 8:00 AM Paris time)
- **Deduplication:** By Google `placeId` (stable, unique identifier)

**Output per detection:**
- 1 Paperclip ticket created
- Type: `agency`
- Assigned to: Intel agent for enrichment

**Key Fields Captured:**
```
- name, address, phone, website
- googleMapsUrl, rating, totalRatings
- businessStatus (OPERATIONAL)
- coordinates (lat/lng)
- scrapedAt (ISO timestamp)
```

**Cost:** ~$0.035 per API request; 1 run/week ≈ $0.14/month (covered by Google free credits).

---

### Stage 2: Intel (Enrichment & Scoring)

**Role:** Research the prospect, enrich with contextual data, calculate automation potential, and make go/skip decisions.

**Execution Flow:**

1. **Company Research** — Extract legal info (SIREN, employee count, revenue, founding year)
2. **Website Analysis** — Visit company website, extract tech stack, tools mentioned in job listings
3. **Email Discovery** — Find business contact email addresses
4. **Email Verification** — Validate deliverability
5. **Pain Point Detection** — Identify from website, reviews, or public signals
6. **Task Analysis** — If job offer present, list all tasks mentioned
7. **Automation Assessment** — Evaluate each task for automatable vs. manual
8. **Scoring** — Calculate automation rate and final verdict

**Scoring Algorithm:**

| Component | Weight | Details |
|-----------|--------|---------|
| Automation Rate | 50% | % of job tasks that are fully or partially automatable |
| Company Size Fit | 15% | PME 10-50 employees (ideal range) |
| Tech Receptivity | 15% | Evidence of existing automation/modern tools |
| Contact Quality | 10% | Direct decision-maker email found |
| Urgency | 10% | Job posting recent, hiring actively |

**Verdict Thresholds:**
- **✅ GO** ≥ 70 points — propose automation
- **⚠️ MAYBE** 50–69 points — require manual review
- **❌ SKIP** < 50 points — not a fit

**Output per prospect:**
- Enriched JSON document (legal, profile, people, fit assessment)
- Automation rate (specific number: e.g., 75%)
- 2–3 key tasks identified (by name)
- Estimated deal value: 25k€
- Best contact: name + role + email

**Human Gate 1: Discord Validation**
- Intel posts summary with go/skip/maybe recommendation
- Teina reviews and approves/rejects
- Only "go" verdicts proceed to Writer

---

### Stage 3: Writer (Email Composition)

**Role:** Draft personalized outreach email (J0 — first contact insight).

**Inputs Required:**
- Intel enriched analysis
- Original job offer (if applicable)
- Writer memory (subject formulas used, style registers tried)

**Email Philosophy:** "This person actually researched us" — not a cold pitch.

**Structure:** Insight → Understanding → Lead → Opening (not Pitch → ROI → CTA)

**Subject Line Formulas (rotate, never repeat):**
1. `{Position} at {Company}: An automation opportunity`
2. `{Company} + {Tool}: {N} tasks we can automate`
3. `Quick question about your {position} posting`
4. `{Sector} and {key task}: lessons from the field`
5. `{FirstName}, {N}% of this role is automatable`
6. `Your {position} on {source}: What if we automated {N}%?`

**Style Registers (rotate across prospects, adapt to target):**

- **Register A: Direct & Concise** — < 100 words, for SMEs < 10 employees
- **Register B: Insight & Context** — 120–150 words, for PMEs 10–50 employees, established structures
- **Register C: Question & Curiosity** — 80–120 words, tech-savvy founders, inquisitive leaders

**Personalization Requirements (must include ≥ 3):**
- Company creation year or age
- Exact employee range
- Specific ERP/tool from job posting
- 2–3 tasks named verbatim from offer
- Sector-specific vocabulary
- Automation rate as specific percentage

**Anti-Patterns (never do):**
- Start with "I saw your job posting…"
- Include ROI calculations (38k€ → 25k€) in J0
- Mention OPCO funding in J0
- Use tech jargon
- Repeat the same subject formula twice consecutively

**Output:**
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

**Human Gate 2: Gmail Draft Review**
- Writer saves draft to Supabase
- Gmail "Send as" creates draft in inbox
- Teina reviews, edits, approves/rejects
- Only approved drafts sent via Resend API

---

## Heartbeat Orchestration

**Scheduler:** n8n workflows with webhook triggers (Paperclip integration)

**Weekly Routine:**

| Agent | Frequency | Trigger | Input | Output | Next Step |
|-------|-----------|---------|-------|--------|-----------|
| Scout | Weekly (Mon 8 AM) | Cron | Google API key | N agencies as tickets | Intel assignment |
| Intel | Continuous | Ticket assignment | Agency data + job posting | Enriched analysis + verdict | Discord gate |
| Writer | On approval | Teina action (Discord) | "go" verdict + enriched data | Email draft | Gmail gate |

**Handoff Points:**
- Scout → Intel: ticket creation with `type: agency`
- Intel → Discord: summary post with recommendation
- Discord → Writer: Teina approval comment triggers Writer agent
- Writer → Gmail: draft saved via Supabase, Gmail creates draft
- Gmail → Resend: Teina clicks "send" in Gmail, backend calls Resend SMTP API

---

## Inter-Agent Communication

**Mechanism:** Paperclip ticket system (task/issue tracking).

1. **Scout creates ticket(s)** with type: `agency`
   - Title: `Prospect — {Company Name}`
   - Description: JSON from Google Places API
   - Assigned to: Intel agent

2. **Intel checks out ticket**, enriches, comments with verdict
   - Status: updates to `in_progress` → `completed` (or `blocked`)
   - Comment: structured JSON (company info, automation rate, recommendation)

3. **Paperclip webhook** posts to Discord
   - Channel: `#prospection-verdicts`
   - Message: summary + link to approval form

4. **Teina approves** (Discord reaction or comment)
   - Creates new ticket for Writer with `parentId` pointing to Intel ticket
   - Passes enriched data via `inheritExecutionWorkspaceFromIssueId`

5. **Writer creates draft**, saves to Supabase
   - Status: `draft` (awaiting Gmail approval)
   - Teina moves to Gmail, reviews, sends via Resend

---

## Scoring Algorithm (Detailed)

### Automation Rate Calculation

1. **Extract Tasks** from job description
   - Parse requirements, responsibilities, tools
   - Example: "Manage customer database in Salesforce, send weekly reports, process invoices"

2. **Evaluate Each Task**
   ```
   Task: "Process invoices"
   ├─ Automatable? YES
   ├─ Method: n8n workflow + Supabase + email API
   └─ Complexity: simple (< 1 day)
   
   Task: "Send weekly reports"
   ├─ Automatable? PARTIAL (data generation automated, review manual)
   ├─ Method: custom TypeScript app + scheduled job
   └─ Complexity: medium (1–3 days)
   
   Task: "Customer relationship building"
   ├─ Automatable? NO
   ├─ Method: human required
   └─ Complexity: N/A
   ```

3. **Calculate Rate**
   - Full automatable tasks: 2 (100%)
   - Partial automatable: 1 (50% credit)
   - Manual only: 1 (0%)
   - **Automation Rate = (2 + 0.5) / 3 = 83%**

### Multi-Factor Scoring (0–100)

**Factor 1: Automation Rate (50 points max)**
- 0–50% → 0 points
- 50–70% → 25 points
- 70–85% → 40 points
- 85%+ → 50 points

**Factor 2: Company Size Fit (15 points max)**
- < 10 employees → 5 points (likely no budget)
- 10–50 employees → 15 points (ideal mid-market)
- 50–200 employees → 10 points (structure may block us)
- 200+ employees → 3 points (procurement delays)

**Factor 3: Tech Receptivity (15 points max)**
- Low (still using paper/email) → 3 points
- Medium (Excel, Salesforce) → 10 points
- High (API integrations, custom apps) → 15 points

**Factor 4: Contact Quality (10 points max)**
- No contact found → 0 points
- Indirect (HR email, general inbox) → 5 points
- Direct (founder, CTO, operations manager) → 10 points

**Factor 5: Urgency (10 points max)**
- Posting > 3 months old → 0 points
- Posting 1–3 months old → 5 points
- Posting < 1 month old → 10 points

**Total Score = Sum of all factors**

**Decision:**
- Score ≥ 70 → **GO** (high probability of meeting objections)
- Score 50–69 → **MAYBE** (review manually)
- Score < 50 → **SKIP** (better opportunities exist)

---

## Intel Enrichment Pipeline

**9 Python Scripts & Data Flow:**

```
Raw Agency Data (Google Places)
    ↓
[1. scrape-maps.py]
    ↓ placeId, name, address, phone, website
    ↓
[2. research-company.py] — SIREN lookup, legal info
    ↓ siren, legal_name, founded, employees, revenue, sector
    ↓
[3. extract-tech-stack.py] — Website analysis
    ↓ tools, erp, crm_system, integrations
    ↓
[4. find-email.py] — Email discovery (domain patterns)
    ↓ business_email, decision_maker_name
    ↓
[5. verify-email.py] — SMTP validation
    ↓ email_valid (true/false), deliverability_score
    ↓
[6. analyze-reviews.py] — Google/web reviews mining
    ↓ pain_points (list), sentiment, common_complaints
    ↓
[7. check-job-posting.py] — If offer exists, extract tasks
    ↓ job_title, job_description, tasks[], required_tools
    ↓
[8. calculate-automation-rate.py] — Task analysis
    ↓ automatable_tasks, automation_rate, complexity_breakdown
    ↓
[9. score-prospect.py] — Multi-factor scoring
    ↓ final_score, verdict (go/maybe/skip), confidence_level
    ↓
intel_enrichments table (Supabase)
```

**Data Model:**

```sql
-- agencies
CREATE TABLE agencies (
  id UUID PRIMARY KEY,
  google_place_id TEXT UNIQUE,
  name TEXT,
  address TEXT,
  phone TEXT,
  website TEXT,
  rating NUMERIC,
  total_ratings INTEGER,
  location POINT,
  created_at TIMESTAMP,
  company_id UUID REFERENCES companies(id)
);

-- intel_enrichments
CREATE TABLE intel_enrichments (
  id UUID PRIMARY KEY,
  agency_id UUID REFERENCES agencies(id),
  siren TEXT,
  legal_name TEXT,
  founded_year INTEGER,
  employee_count TEXT,
  revenue TEXT,
  sector TEXT,
  tech_stack TEXT[],
  business_email TEXT,
  email_valid BOOLEAN,
  pain_points TEXT[],
  job_title TEXT,
  job_description TEXT,
  tasks TEXT[],
  automation_rate NUMERIC,
  automation_breakdown JSON,
  final_score INTEGER,
  verdict TEXT, -- 'go', 'maybe', 'skip'
  confidence NUMERIC,
  enriched_at TIMESTAMP,
  created_by UUID REFERENCES auth.users(id)
);

-- email_drafts
CREATE TABLE email_drafts (
  id UUID PRIMARY KEY,
  intel_id UUID REFERENCES intel_enrichments(id),
  subject TEXT,
  body TEXT,
  from_address TEXT,
  to_address TEXT,
  subject_formula INTEGER,
  style_register TEXT,
  status TEXT, -- 'draft', 'approved', 'sent'
  gmail_draft_id TEXT,
  sent_at TIMESTAMP,
  created_at TIMESTAMP
);
```

**RLS Policies:**
- All tables: `SELECT` + `INSERT` only for agents with `role = 'agent'` and assigned `company_id`
- `intel_enrichments`: agents can only update own enrichments
- `email_drafts`: users (Teina) can approve; agents create only
- Sensitive columns (email addresses): masked for non-decision-maker roles

---

## Email Infrastructure

### Architecture Overview

**Components:**
- **Prospection Domain:** `your-prospection-domain.com` (isolated from main domain)
- **Inbound:** Cloudflare Email Routing → Gmail inbox
- **Outbound:** Resend SMTP (Amazon SES backend) → `contact@your-prospection-domain.com`
- **Interface:** Gmail "Send as" feature (centralized inbox)

**Why separate domain?**
- Reputation isolation: If prospection domain bounces/gets flagged, main domain unaffected
- Deliverability focus: Dedicated SPF/DKIM/DMARC for outreach
- Recovery: Can retire prospection domain without losing main business email

### DNS Records Required

| Type | Name | Content | Purpose |
|------|------|---------|---------|
| MX | your-prospection-domain.com | route{1,2,3}.mx.cloudflare.net | Email Routing (inbound) |
| MX | send.your-prospection-domain.com | feedback-smtp.eu-west-1.amazonses.com | Resend bounce handling |
| TXT | your-prospection-domain.com | `v=spf1 include:_spf.mx.cloudflare.net include:amazonses.com ~all` | SPF (send authorization) |
| TXT | resend._domainkey.your-prospection-domain.com | {DKIM_KEY_FROM_RESEND} | DKIM (Resend signing) |
| TXT | cf2024._domainkey.your-prospection-domain.com | {DKIM_KEY_FROM_CLOUDFLARE} | DKIM (Cloudflare signing) |
| TXT | _dmarc.your-prospection-domain.com | `v=DMARC1; p=none; rua=mailto:contact@your-prospection-domain.com` | DMARC (monitor reports) |

### Email Flow

```
Writer Agent (save-draft.py)
    ↓ Save to Supabase
    ↓ Trigger webhook
    ↓
[gmail_create_draft.py]
    ↓ Gmail API: create draft in "Send as" account
    ↓
YOUR_GMAIL_ADDRESS (Gmail inbox)
    ↓ Manual review: read, edit if needed
    ↓
[send-email.py] (Teina clicks Send)
    ↓ Call Resend API
    ↓ SMTP: contact@your-prospection-domain.com → prospect
    ↓
Prospect inbox (delivered)
    ↓ Reply
    ↓
Cloudflare Email Routing
    ↓ contact@your-prospection-domain.com
    ↓
YOUR_GMAIL_ADDRESS (reply received)
```

### SMTP Configuration (Gmail Send As)

- **Server:** `smtp.resend.com`
- **Port:** 587
- **Username:** `resend`
- **Password:** Resend API key (stored in Gmail secrets)
- **Encryption:** TLS

### Warmup Plan

| Phase | Duration | Daily Volume | Notes |
|-------|----------|--------------|-------|
| Week 1 | 7 days | 2–3 emails | Establish reputation, monitor bounces |
| Week 2 | 7 days | 5 emails | Increase gradually, check spam folder |
| Week 3+ | ongoing | 10 emails/day max | Monitor delivery rates, adjust if needed |

**Free Tier:** Resend allows 3,000 emails/month at no cost. At 10 emails/day, we use ~300/month.

### Monitoring & Maintenance

- **DMARC Reports:** Monitor `_dmarc.your-prospection-domain.com` for authentication failures
- **Bounce Handling:** Resend webhook → update `email_valid` flag in Supabase
- **Spam Monitoring:** Check Gmail spam folder weekly, adjust content if needed
- **Rotation:** If domain reputation drops, retire and spin up new prospection domain

---

## Human Review Gates

### Gate 1: Intel Verdict (Discord)

**Trigger:** Intel agent completes analysis.

**Discord Post:**
```
📊 New Prospect: [Company Name]
├─ Automation Rate: 78%
├─ Key Tasks: Invoice processing, report generation, email follow-ups
├─ Employee Count: 18 (perfect fit)
├─ Verdict: ✅ GO
└─ Score: 76/100 — [Approve?] [Review more?] [Skip]
```

**Teina Action:**
- ✅ Approve → Writer agent notified
- ❌ Skip → Ticket closed
- ❓ Review → Opens enrichment details, can override verdict

### Gate 2: Gmail Draft (Human Approval)

**Trigger:** Writer agent saves draft to Supabase.

**Gmail Inbox:**
- Draft appears in "Send as" account
- Status: **Draft** (not sent)
- Teina can: edit subject/body, add custom notes, or send as-is

**Teina Action:**
- 📤 Send → Calls Resend API
- ✏️ Edit → Modify draft in place
- 🗑️ Delete → If prospect not suitable or message weak

---

## Security Model

### Environment Variables

All secrets stored as environment variables in `.env` (Paperclip instance):

```
GOOGLE_PLACES_API_KEY=<key>
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_SECRET=<service-role-key>
RESEND_API_KEY=<key>
GMAIL_CREDENTIALS=<oauth-json>
CLOUDFLARE_API_TOKEN=<token>
```

### Supabase RLS

Every table enforces Row-Level Security:

```sql
-- Agents can only view agencies in their assigned company
CREATE POLICY "agents_view_own_company_agencies"
  ON agencies FOR SELECT
  USING (company_id = auth.jwt() ->> 'company_id');

-- Only assigned agent can update intel enrichments
CREATE POLICY "agent_update_own_enrichment"
  ON intel_enrichments FOR UPDATE
  USING (created_by = auth.uid());

-- Users can view all email drafts (not agents)
CREATE POLICY "users_view_all_drafts"
  ON email_drafts FOR SELECT
  USING (auth.jwt() ->> 'role' = 'user');
```

### Input Validation

- **Email discovery:** Validate domain matches agency website domain before storing
- **Automation rate:** Reject if > 100% or < 0%
- **Scores:** Enforce 0–100 range
- **Phone/address:** Validate format before inserting

### Human-in-the-Loop

- **No automatic sends:** Every email requires Teina's explicit approval in Gmail
- **Discord gates:** Verdicts reviewed before next stage
- **Audit trail:** All agent actions logged with `created_by` + `created_at`

---

## Metrics & Monitoring

### Pipeline KPIs

| Metric | Target | Notes |
|--------|--------|-------|
| Agencies detected/week | 20–30 | Scout efficiency |
| Automation rate avg. | 65%+ | Intel quality (higher = fewer bad prospects) |
| Go verdict rate | 30–40% | % of analyzed prospects deemed "go" |
| Email open rate | 25%+ | Subject line & personalization effectiveness |
| Reply rate | 5–10% | Overall pipeline efficacy |
| Conversion rate (reply → call) | 20–30% | Closes booked / replies received |

### Cost Tracking

| Component | Cost/Month | Notes |
|-----------|-----------|-------|
| Google Places API | ~$0.14 | 1 run/week (covered by free credits) |
| Resend SMTP | $0 | 300 emails/month (within free tier) |
| Supabase | ~$25 | 2GB DB, moderate functions (pay-as-you-go) |
| n8n workflows | $0 | Self-hosted instance |
| **Total** | **~$25** | Very lean infrastructure |

---

## Future Enhancements

1. **Sequence Automation:** J+2 (LinkedIn), J+5 (follow-up email), J+8 (call reminder) — pending Airtable/Sheets integration
2. **Objection Handling:** Writer agent drafts responses to common objections (budget, timing, integration)
3. **A/B Testing:** Subject lines & email bodies tracked for click/open rates
4. **Lead Scoring Refinement:** Adjust weights based on actual conversion data
5. **Multi-Persona Outreach:** Reach founder + CFO + operations in parallel for larger prospects
6. **Sales Crm Integration:** Sync leads, responses, meetings to external CRM (Pipedrive, HubSpot)
