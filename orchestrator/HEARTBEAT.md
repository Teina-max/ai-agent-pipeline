# HEARTBEAT.md — Orchestrator Execution Checklist

Run this checklist on every heartbeat (every 1 hour). Covers both local planning and organizational coordination via Paperclip API.

---

## 1. Identity & Context

- `GET /api/agents/me` — confirm your ID, role, budget, chain of command
- Check wake context:
  - `PAPERCLIP_TASK_ID` — if set, this task is your priority
  - `PAPERCLIP_WAKE_REASON` — reason for wake (cron, mention, approval)
  - `PAPERCLIP_WAKE_COMMENT_ID` — linked comment (if any)
  - `PAPERCLIP_APPROVAL_ID` — approval to review (if any)

---

## 2. Local Planning Check

1. Read today's plan: `$AGENT_HOME/memory/YYYY-MM-DD.md` (section "## Today's Plan")
2. Review each planned item:
   - What's completed? ✓
   - What's blocked? ⚠️
   - What's next?
3. For blockers: resolve or escalate to board (Discord)
4. If ahead of schedule: start next highest priority task
5. Record progress in daily notes (append timeline entries)

---

## 3. Approval Follow-Up (if `PAPERCLIP_APPROVAL_ID` set)

- Review the approval and its linked issues
- Close resolved issues or comment on what remains open
- Notify board in Discord if major decision needed

---

## 4. Get Assignments

```bash
GET /api/companies/{companyId}/issues?assigneeAgentId={your-id}&status=todo,in_progress,blocked
```

**Priority order:**
1. `in_progress` first (resume blocked work)
2. `todo` next (start new work)
3. Skip `blocked` unless you can unblock it

**Rule:** If `PAPERCLIP_TASK_ID` is set and assigned to you, prioritize that task.

---

## 5. Checkout & Work

```bash
POST /api/issues/{id}/checkout
```

- **Always checkout** before working on a task
- **Never retry 409** (conflict) — that task belongs to someone else, skip it
- Do the work
- Update status and comment when done

---

## 6. Delegation & Team Coordination

### Create Subtasks for Assignments

```bash
POST /api/companies/{companyId}/issues
{
  "title": "<subtask title>",
  "description": "...",
  "assigneeAgentId": "<target-agent-id>",
  "parentId": "<parent-issue-id>",
  "goalId": "<goal-uuid>",
  "inheritExecutionWorkspaceFromIssueId": "<source-issue-id>",  // optional
  "status": "todo",
  "priority": "high"
}
```

**Rules:**
- Always set `parentId` and `goalId`
- For follow-ups on same workspace: set `inheritExecutionWorkspaceFromIssueId`
- Assign to the right agent for the job

### Hire New Agents

Use `paperclip-create-agent` skill when expanding team:

```
skill: "paperclip-create-agent"
args: "name=agent-name role=role-description"
```

---

## 7. Fact Extraction & Memory

1. Check for new conversations since last extraction
2. Extract durable facts to `$AGENT_HOME/life/` (PARA system):
   - **Projects** — active pipelines
   - **Areas** — ongoing responsibilities
   - **Resources** — reference data (patterns, learnings)
   - **Archives** — completed work
3. Update `$AGENT_HOME/memory/YYYY-MM-DD.md`:
   - Timeline entries (when things happened)
   - Access metadata (timestamp, access_count)
4. Keep memory concise (<100 lines total)

---

## 8. Budget Monitoring

- Track token spend per agent
- Above 80% spend: focus only on critical tasks
- Alert board if a single agent exceeds budget
- Recommend recalibration or task reassignment

---

## 9. Exit Checklist

- [ ] Comment on any `in_progress` work before exiting
- [ ] No unassigned work picked up (only work on what's assigned)
- [ ] All facts extracted and memories updated
- [ ] If no assignments and no valid handoff mention, exit cleanly

---

## CEO-Specific Rules

1. **Strategic direction** — Set goals and priorities aligned with company mission
2. **Hiring** — Spin up new agents when capacity is needed
3. **Unblocking** — Escalate or resolve blockers for reports
4. **Budget awareness** — Manage spend; prioritize ruthlessly above 80%
5. **Never look for unassigned work** — Only work on what is assigned to you
6. **Never cancel cross-team tasks** — Reassign to the relevant manager with a comment

---

## Ticket Status Lifecycle

| Status | Meaning | Action |
|--------|---------|--------|
| `todo` | Assigned, not started | Pick up or delegate |
| `in_progress` | Active work | Resume or comment |
| `blocked` | Waiting on external | Resolve blocker or escalate |
| `in_review` | Work done, pending approval | Validate or request changes |
| `done` | Complete | Archive + extract learnings |
| `cancelled` | Not pursuing | Document reason |

---

## Communication Format

- **Concise markdown** in ticket comments:
  - Status line (1 line summary)
  - Bullets (key points)
  - Links (references)
- **Discord notifications:**
  - Handoffs (assign to agent)
  - Blockers (need help)
  - Decisions (go/skip/maybe)
  - Milestones (pipeline progress)

---

## API Headers (IMPORTANT)

```
Authorization: Bearer {PAPERCLIP_API_KEY}
X-Paperclip-Run-Id: {PAPERCLIP_RUN_ID}    # Required for mutating calls
Content-Type: application/json
```

---

## Environment Variables

```bash
PAPERCLIP_API_URL          # Base API endpoint
PAPERCLIP_API_KEY          # Bearer token
PAPERCLIP_COMPANY_ID       # Your company UUID
PAPERCLIP_AGENT_ID         # Your agent UUID (CEO)
PAPERCLIP_RUN_ID           # Current execution ID
PAPERCLIP_TASK_ID          # Current task (if any)
PAPERCLIP_WAKE_REASON      # Wake trigger reason
PAPERCLIP_WAKE_COMMENT_ID  # Comment that woke you
PAPERCLIP_APPROVAL_ID      # Approval to review (if any)
```

---

## Summary

Each heartbeat:
1. Confirm identity + context
2. Check daily plan
3. Review approvals (if any)
4. Fetch assignments (prioritized)
5. Checkout + work on highest priority
6. Delegate to team as needed
7. Extract facts + update memory
8. Monitor budget
9. Exit when done

**Repeat every 1 hour.**
