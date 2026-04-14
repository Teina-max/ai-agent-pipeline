# Agent Registry — Sanele Prospection Pipeline

Orchestrator system for automated real estate agency detection, analysis, and outreach.

## Agent Roster

| Agent | ID | Role | Triggers | Primary Actions |
|-------|----|----|----------|-----------------|
| **Scout** | `scout-agent` | Detection | Cron 8h daily | Detect agencies via Google Places API, deduplicate, create tickets for Intel |
| **Intel** | `intel-agent` | Analysis | New ticket from Scout | Feasibility analysis, company research, go/skip recommendation |
| **Writer** | `writer-agent` | Outreach | "Go" validation from CEO | Draft 5-message sequences (J0→J12): email, LinkedIn DM, follow-ups |
| **Heartbeat** | `heartbeat-orchestrator` | Orchestration | Cron every 1h | Coordinate pipeline flow, monitor assignments, resolve blockers |

## Pipeline Flow

```
[Cron 8h] → Scout detects agencies → ticket created in Paperclip
    ↓
    → Intel analyzes feasibility → posts recommendation + verdict
    ↓
    → Heartbeat (CEO) validates "go" or "skip" → routes to Writer
    ↓
    → Writer drafts outreach sequence → posts draft in Discord
    ↓
    → CEO sends manually (copy-paste) or approves for automation
```

## Agent Details

### Scout Agent

**What it does:**
- Runs Google Places Text Search daily at 08:00
- Filters by: location (Toulouse 30km), query ("real estate agency", "agence immobilière"), rating filters
- Deduplicates against existing tickets
- Creates one Paperclip issue per new agency, assigned to Intel

**Inputs:**
- Cron trigger (daily 8h)
- Google Places API
- Existing ticket database (deduplication)

**Outputs:**
- Paperclip issues (todo status)
- Memory log (stats per run, patterns)

**Interface:**
```bash
POST /api/companies/{companyId}/issues
{
  "title": "<Agency Name> - <City>",
  "description": "## Prospect Agency\n- **Source**: Google Places\n- **URL**: <maps-link>\n- **Rating**: <rating>/5\n- **Reviews**: <count>\n- **Phone**: <phone>\n\n## Business Info\n- Location: <address>\n- Website: <url>\n...",
  "assigneeAgentId": "intel-agent",
  "status": "todo",
  "priority": "medium"
}
```

---

### Intel Agent

**What it does:**
- Receives ticket from Scout
- Analyzes agency profile for partnership potential (% likelihood of needing services)
- Researches agency: Sirene (legal data), social profiles, market presence
- Finds decision-maker email via domain research + verification
- Computes qualification score (0-100) based on agency size, market activity, contact quality
- Produces verdict: `go` (>70%), `maybe` (50-70%), `skip` (<50%)
- Drafts outreach brief for "go" cases

**Inputs:**
- Scout ticket (prospect agency)
- Sirene API (company legal data)
- Google Places API (agency reviews, ratings)
- Email finder tools (domain + name patterns)

**Outputs:**
- Ticket comment with verdict + analysis
- Intel enrichment record in database
- Outreach brief (JSON) for Writer

**Verdict Thresholds:**
- ✅ **Go** (≥70% automatable) → assign to Writer after CEO confirms
- ⚠️ **Maybe** (50-69%) → flag for CEO judgment
- ❌ **Skip** (<50%) → archive, no further action

---

### Writer Agent

**What it does:**
- Receives validated "go" ticket from CEO
- Reads its own memory (past formulas, registers, sector patterns)
- Chooses unique subject line formula (never repeat last one)
- Selects style register (A: Direct, B: Insight, C: Question) based on company profile
- Writes personalized insight email (4-block structure):
  1. Accroche — specific observation about their company
  2. Compréhension — what we understand about their need
  3. Piste — automation alternative, with concrete numbers
  4. Ouverture — soft question (not a call-to-action)
- Self-reviews against checklist
- Saves draft to Supabase + Gmail
- Posts to Discord
- Updates ticket status to `in_review`

**Inputs:**
- Validated ticket + Intel enrichment
- Memory log (formulas, registers, sector patterns)
- Email configuration (sender: contact@your-prospection-domain.com)

**Outputs:**
- Email draft (Supabase + Gmail)
- Ticket comment (formula #, register, hook)
- Discord notification
- Memory update (formula, register, sector pattern)

**Subject Line Formulas (rotate):**
1. `{Poste} chez {Entreprise} : une piste avant de recruter`
2. `{Entreprise} + {ERP/outil} : {N} tâches qu'on peut automatiser`
3. `Question rapide sur votre offre de {poste}`
4. `{Secteur} et {tâche pivot} : retour d'expérience`
5. `{Prénom}, {chiffre}% de ce poste est automatisable`
6. `Votre {poste} sur {source} : et si on en automatisait {N}% ?`

**Style Registers:**
- **A. Direct & Concis** — PME <10 employees, <100 words
- **B. Insight & Contexte** — PME 10-50, 120-150 words (default)
- **C. Question & Curiosité** — Tech-savvy, 80-120 words

---

### Heartbeat Orchestrator (CEO)

**What it does:**
- Runs every 1 hour (cron)
- Confirms identity: `GET /api/agents/me`
- Checks wake context (task ID, approval ID, reason)
- Reads daily plan from memory
- Fetches assignments: `GET /api/companies/{companyId}/issues?assigneeAgentId=me`
- Prioritizes: `in_progress` → `todo` → resolve blockers
- Validates approval follow-ups
- Delegates work to right agents (create subtasks)
- Extracts durable facts to memory (PARA system)
- Monitors costs per agent
- Coordinates cross-team signals

**Inputs:**
- Cron trigger (every 1h)
- Paperclip API (inbox, tasks, approvals)
- Daily memory file
- Assignment queue

**Outputs:**
- Task checkout + status updates
- Subtask creation (delegation)
- Discord notifications (handoff, blockers, decisions)
- Memory updates (timeline, facts)
- New agent hiring (via `paperclip-create-agent` skill)

**Key Responsibilities:**
- Set pipeline priorities when multiple offers arrive
- Resolve blockers between agents
- Communicate with board (Teina) via Discord
- Track budget per agent (cap at 80% spend)
- Adjust filtering criteria (Scout config)
- Hire new agents if capacity needed

---

## Cross-Agent Signals

| Signal | Route | Action |
|--------|-------|--------|
| Client signed deal | ops-projets | Create new project |
| Build invoicing ready | rico-finance | Trigger invoicing workflow |
| Maintenance contract signed | rico-finance | Add recurring revenue |
| SaaS pattern detected (recurring pain point) | sage-learning | Track for future SaaS |
| Follow-up sequence complete | link-relation | Log prospect interaction |

---

## Data Flow & Paperclip API

All agents coordinate via Paperclip REST API:

```
POST   /api/agents/me/inbox-lite           — fetch assignments
GET    /api/companies/{id}/issues          — search/list issues
POST   /api/companies/{id}/issues          — create ticket
POST   /api/issues/{id}/checkout           — claim work
PATCH  /api/issues/{id}                    — update status/comment
POST   /api/companies/{id}/issues          — create subtask (parentId + goalId)
```

### Required Headers

```
Authorization: Bearer {PAPERCLIP_API_KEY}
X-Paperclip-Run-Id: {PAPERCLIP_RUN_ID}    (for mutating calls)
Content-Type: application/json
```

---

## Memory System (PARA)

Each agent maintains memory in `$AGENT_HOME/memory/`:

- **Projects** — current active pipelines
- **Areas** — ongoing responsibilities (sector expertise, email formula stats)
- **Resources** — reference data (agency profiles, email patterns, automation rates)
- **Archives** — completed/discarded work

Daily note: `YYYY-MM-DD.md` with:
- Timeline entries (events, decisions)
- Today's plan + progress
- Blockers and escalations

---

## Communication Channels

- **Internal** (agent-to-agent): Paperclip API + comments
- **External** (to board): Discord channel
- **Prospect tracking**: Email drafts + replies logged in Supabase

**Language:**
- French for human-facing messages (Discord, emails)
- English for code, commits, technical docs

---

## References

- `HEARTBEAT.md` — orchestrator execution checklist
- `SOUL.md` — CEO persona and voice
- `TOOLS.md` — available integrations and capabilities
- `scripts/heartbeat.py` — main heartbeat entry point
