# Orchestrator — Agent Coordination System

Multi-agent orchestration for Sanele Prospection (automated lead generation pipeline).

## What is This?

An AI agent system that:
1. Detects agencies via Google Places (Scout)
2. Analyzes them (Intel)
3. Writes personalized outreach (Writer)
4. Orchestrates the flow (Heartbeat/CEO)

All agents communicate via Paperclip API with centralized task management.

## Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent registry: Scout, Intel, Writer, Heartbeat — roles, triggers, APIs |
| `HEARTBEAT.md` | Orchestrator checklist (runs every 1h) |
| `SOUL.md` | CEO persona: posture, voice, decisions |
| `TOOLS.md` | Available APIs: Paperclip, Supabase, Gmail, Google Places |
| `scripts/heartbeat.py` | Main orchestrator entry point (Python) |
| `scripts/heartbeat.sh` | Shell wrapper for cron |

## Quick Start

### Prerequisites
- Python 3.8+
- `.env` file with `PAPERCLIP_API_URL`, `PAPERCLIP_API_KEY`, etc.

### Run Heartbeat
```bash
python3 scripts/heartbeat.py
```

Or via shell:
```bash
./scripts/heartbeat.sh
```

### Cron (every hour)
```cron
0 * * * * cd /path/to/orchestrator && ./scripts/heartbeat.sh >> /var/log/heartbeat.log 2>&1
```

## Agent Roster

| Agent | Role | Trigger |
|-------|------|---------|
| Scout | Detect agencies | Cron 8h daily |
| Intel | Analyze feasibility | New agency from Scout |
| Writer | Draft emails | CEO validates "go" |
| Heartbeat | Orchestrate | Cron every 1h |

## Pipeline Flow

```
Scout → detects agencies → creates ticket → Intel analyzes
                                                 ↓
                                Heartbeat validates verdict
                                                 ↓
                         If "go": Writer drafts → CEO sends
```

## Key Points

- **Verdicts**: Go (≥70% automatable) → Maybe (50-69%) → Skip (<50%)
- **Budget cap**: Agents stop at 80% spend
- **Memory**: Daily notes + durable facts (PARA system)
- **API**: All coordination via Paperclip REST API
- **Anonymization**: UUIDs → readable names, secrets → placeholders

## References

- `AGENTS.md` — Full team definition
- `HEARTBEAT.md` — Hourly execution checklist
- `SOUL.md` — CEO persona & framework
- `TOOLS.md` — API reference

---

**From:** Teina's automation practice  
**Framework:** Paperclip Agent Coordination
