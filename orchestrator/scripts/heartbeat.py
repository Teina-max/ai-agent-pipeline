#!/usr/bin/env python3
"""
Heartbeat orchestrator main script.

Runs once per hour (via cron). Coordinates the Sanele Prospection pipeline:
- Fetches assignments
- Processes high-priority tasks
- Delegates work to agents
- Updates memory and facts
- Monitors budget

Environment variables (required):
  PAPERCLIP_API_URL
  PAPERCLIP_API_KEY
  PAPERCLIP_COMPANY_ID
  PAPERCLIP_AGENT_ID
  PAPERCLIP_RUN_ID
  PAPERCLIP_TASK_ID (optional)
  PAPERCLIP_WAKE_REASON (optional)
  PAPERCLIP_WAKE_COMMENT_ID (optional)
  PAPERCLIP_APPROVAL_ID (optional)
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Configuration
api_url = os.environ.get("PAPERCLIP_API_URL", "")
api_key = os.environ.get("PAPERCLIP_API_KEY", "")
company_id = os.environ.get("PAPERCLIP_COMPANY_ID", "")
agent_id = os.environ.get("PAPERCLIP_AGENT_ID", "")
run_id = os.environ.get("PAPERCLIP_RUN_ID", "")
task_id = os.environ.get("PAPERCLIP_TASK_ID", "")
wake_reason = os.environ.get("PAPERCLIP_WAKE_REASON", "")
approval_id = os.environ.get("PAPERCLIP_APPROVAL_ID", "")

# Memory
agent_home = os.environ.get("AGENT_HOME", Path.home() / ".paperclip" / "agents" / "heartbeat-orchestrator")
memory_dir = Path(agent_home) / "memory"
memory_dir.mkdir(parents=True, exist_ok=True)


def api_call(method: str, path: str, data: dict = None) -> dict:
    """Make an API call to Paperclip."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if method in ("PATCH", "POST") and run_id:
        headers["X-Paperclip-Run-Id"] = run_id

    url = api_url + path
    req_data = json.dumps(data).encode() if data else None

    req = urllib.request.Request(
        url,
        data=req_data,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode()}", file=sys.stderr)
        raise


def log_memory(event: str):
    """Append event to today's memory log."""
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = memory_dir / f"{today}.md"

    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {event}\n"

    with open(memory_file, "a") as f:
        f.write(entry)


def main():
    """Run the heartbeat orchestrator."""
    print(f"=== Heartbeat Orchestrator ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")

    # 1. Confirm identity
    print("\n[1] Confirming identity...")
    me = api_call("GET", "/api/agents/me")
    print(f"  Agent: {me['name']} (ID: {me['id']})")
    print(f"  Role: {me['role']}")
    print(f"  Budget remaining: {me.get('budget_remaining', 'N/A')}")
    log_memory(f"Heartbeat started. Role: {me['role']}")

    # 2. Check wake context
    print("\n[2] Wake context:")
    if task_id:
        print(f"  Task ID: {task_id} (priority)")
    if wake_reason:
        print(f"  Wake reason: {wake_reason}")
    if approval_id:
        print(f"  Approval pending: {approval_id}")

    # 3. Read daily plan
    print("\n[3] Checking daily plan...")
    today = datetime.now().strftime("%Y-%m-%d")
    plan_file = memory_dir / f"{today}.md"
    if plan_file.exists():
        with open(plan_file) as f:
            content = f.read()
        if "## Today's Plan" in content:
            print(f"  ✓ Plan exists ({plan_file.name})")
    else:
        print(f"  ⚠ No plan found for today")
        log_memory("No plan found for today")

    # 4. Get assignments
    print("\n[4] Fetching assignments...")
    issues = api_call("GET", f"/api/companies/{company_id}/issues?assigneeAgentId={agent_id}&status=todo,in_progress,blocked")

    print(f"  Found {len(issues)} assignments:")
    in_progress = [i for i in issues if i['status'] == 'in_progress']
    todo = [i for i in issues if i['status'] == 'todo']
    blocked = [i for i in issues if i['status'] == 'blocked']

    if in_progress:
        print(f"    - {len(in_progress)} in_progress")
        for issue in in_progress[:3]:
            print(f"      • {issue['title'][:60]}")

    if todo:
        print(f"    - {len(todo)} todo")
        for issue in todo[:3]:
            print(f"      • {issue['title'][:60]}")

    if blocked:
        print(f"    - {len(blocked)} blocked (escalate?)")

    # 5. Prioritize and checkout highest priority task
    print("\n[5] Processing tasks...")
    priority_issue = None

    if task_id:
        # Specific task assigned
        priority_issue = next((i for i in issues if i['id'] == task_id), None)
        if priority_issue:
            print(f"  [PRIORITY] Task {task_id[:8]}...")
    elif in_progress:
        # Resume in-progress
        priority_issue = in_progress[0]
        print(f"  [RESUME] {priority_issue['title'][:60]}")
    elif todo:
        # Start new task
        priority_issue = todo[0]
        print(f"  [START] {priority_issue['title'][:60]}")

    if priority_issue:
        try:
            # Attempt checkout
            api_call("POST", f"/api/issues/{priority_issue['id']}/checkout", {})
            print(f"  ✓ Checked out: {priority_issue['id'][:8]}...")
            log_memory(f"Checked out: {priority_issue['title'][:50]}")
        except urllib.error.HTTPError as e:
            if e.code == 409:
                print(f"  ⚠ Already checked out by another agent (409)")
                log_memory("Task conflict: already checked out by another agent")
            else:
                raise

    # 6. Summary
    print("\n[6] Heartbeat Summary:")
    print(f"  Total assignments: {len(issues)}")
    print(f"  Run ID: {run_id[:8]}..." if run_id else "  Run ID: (none)")
    print(f"  Timestamp: {datetime.now().isoformat()}")

    log_memory("Heartbeat completed")
    print("\n✓ Heartbeat cycle complete\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Heartbeat failed: {e}", file=sys.stderr)
        log_memory(f"ERROR: {str(e)}")
        sys.exit(1)
