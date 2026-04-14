# TOOLS.md — Available Tools & Integrations

This document describes the tools available to all agents in the Sanele Prospection pipeline.

---

## Paperclip API (Core Coordination)

**Base URL:** `{PAPERCLIP_API_URL}`  
**Auth:** Bearer token in `Authorization` header  
**Headers:** `X-Paperclip-Run-Id` required for mutations

### Endpoints

#### Get My Identity
```bash
GET /api/agents/me
```
Response: `{ id, name, role, budget, chainOfCommand }`

#### Get Inbox
```bash
GET /api/agents/me/inbox-lite
```
Response: List of assigned tasks with status, priority, title

#### Get Issues (Search/Filter)
```bash
GET /api/companies/{companyId}/issues?assigneeAgentId={id}&status=todo,in_progress,blocked&q={query}
```
Response: Array of issue objects

#### Create Issue (or Subtask)
```bash
POST /api/companies/{companyId}/issues
{
  "title": "...",
  "description": "...",
  "assigneeAgentId": "<uuid>",
  "parentId": "<parent-uuid>",           // optional (for subtasks)
  "goalId": "<goal-uuid>",               // optional
  "inheritExecutionWorkspaceFromIssueId": "<issue-uuid>",  // optional
  "status": "todo",
  "priority": "medium|high|low"
}
```

#### Checkout Issue (Claim Work)
```bash
POST /api/issues/{id}/checkout
```
Response: Locked for you; 409 if already checked out by someone else

#### Update Issue
```bash
PATCH /api/issues/{id}
{
  "status": "in_progress|in_review|done|cancelled|blocked",
  "priority": "high|medium|low",
  "comment": "... markdown comment ..."
}
```

#### Get Agents in Company
```bash
GET /api/companies/{companyId}/agents
```
Response: List of all agents (id, name, role, etc.)

---

## Scout Agent Tools

### Google Places API — Agency Detection
**Source:** Google Places Text Search API for real estate agencies

```bash
python3 /path/to/scrape-maps.py \
  --location "Toulouse" \
  --radius-km 30 \
  --query "real estate agency" \
  --min-rating 3.5
```

**Output:** JSON array with fields:
- `name`, `address`, `location`, `rating`
- `review_count`, `phone`, `website`
- `opening_hours`, `business_type`, `maps_url`

---

## Intel Agent Tools

### Supabase (Shared Database)
**Connection:**
```python
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
```

**Tables:**
- `agencies` (read-only) — populated by external scraper
- `contacts` (read-only) — contact directory
- `intel_enrichments` (read+write) — Intel's enriched data

### Sirene API (Legal Company Data)
**Endpoint:** `https://data.sirene.insee.fr/api/...`

**Query:** Search by company name + city  
**Response:**
- SIREN, SIRET
- Directors (physical persons)
- Employee range, NAF code, legal form
- Creation date, status

### Google Places API
**Key:** `GOOGLE_PLACES_API_KEY`

**Use cases:**
- Fetch reviews for agencies
- Rating, review count, categories
- Business hours, website, phone

### Email Finder Tools
**Generate candidates:** Find email patterns based on director name + company domain

**Verify:** Check deliverability of candidate emails

---

## Writer Agent Tools

### Supabase (Email Drafts)
**Table:** `email_drafts`

**Save draft:**
```python
POST /api/draft
{
  "contact_id": "<uuid>",
  "subject": "...",
  "body": "...",
  "sequence_number": 1,
  "formula_id": 2,
  "style_register": "B",
  "notes": "..."
}
```

### Gmail (Draft Creation)
**via MCP:** `mcp__claude_ai_Gmail__gmail_create_draft`

**Parameters:**
- `to`: recipient email
- `from`: `contact@your-prospection-domain.com` (dedicated outreach domain)
- `subject`: email subject
- `body`: email body (plain text)

**Rule:** Always use the dedicated prospect domain, never personal email.

---

## Heartbeat Orchestrator Tools

### Paperclip API (Full Coverage)
- All endpoints listed above
- Task checkout, subtask creation
- Issue status updates + comments
- Agent lookup

### Paperclip Skills
#### `paperclip-create-agent`
**Hire a new agent:**
```bash
skill: "paperclip-create-agent"
args: "name=agent-name role=role-description"
```

#### Memory & PARA System
**Stored in:** `$AGENT_HOME/memory/` and `$AGENT_HOME/life/`

**Update memory:**
```bash
echo "Timeline entry: [DATE] Event description" >> $AGENT_HOME/memory/$(date +%Y-%m-%d).md
```

---

## Discord Integration (Communication)

**Channel:** Agent-to-board updates (external to system, manual posts)

**Format:**
```
🎯 <Action> – <Details>
📊 <Metric> – <Value>
⚠️  <Blocker> – <Context>
```

---

## Environment Variables (Required)

```bash
# Paperclip
PAPERCLIP_API_URL
PAPERCLIP_API_KEY
PAPERCLIP_COMPANY_ID
PAPERCLIP_AGENT_ID
PAPERCLIP_RUN_ID
PAPERCLIP_TASK_ID
PAPERCLIP_WAKE_REASON
PAPERCLIP_WAKE_COMMENT_ID
PAPERCLIP_APPROVAL_ID

# Data Sources
SUPABASE_URL
SUPABASE_SERVICE_KEY
GOOGLE_PLACES_API_KEY
SIRENE_API_KEY  (optional; public API)

# Email
GMAIL_USER
GMAIL_APP_PASSWORD  (or OAuth token)
```

---

## Tool Constraints

| Tool | Rate Limit | Cost | Fallback |
|------|-----------|------|----------|
| Paperclip API | 1000/hour | Included | Queue & retry |
| Sirene API | 100/min | Free (public) | None — manual lookup |
| Google Places | 1000/day | $0.032/request | Use cached data |
| Gmail Draft | 100/day | Free | Use Supabase only |

---

## Adding New Tools

To integrate a new tool:

1. Document in this file
2. Add env vars to all agent configs
3. Update relevant agent's instructions
4. Test with mock data first
5. Announce to board + log in memory

---

## References

- `AGENTS.md` — Which agents use which tools
- `HEARTBEAT.md` — Orchestrator workflow
- `scripts/` — Working examples
