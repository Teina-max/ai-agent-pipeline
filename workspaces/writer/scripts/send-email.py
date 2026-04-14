#!/usr/bin/env python3
"""Send approved email drafts via Resend API.

Usage:
    SUPABASE_SERVICE_KEY=... RESEND_API_KEY=... python3 send-email.py [--limit 5] [--dry-run]

Reads drafts with status='approved' from Supabase, sends via Resend,
updates status to 'sent' with sent_at timestamp.
"""

import json, os, sys, time, requests
from datetime import datetime, timezone

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
RESEND_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER = "Your Name <contact@your-prospection-domain.com>"


def get_approved_drafts(limit):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/email_drafts",
        headers=headers,
        params={
            "select": "id,contact_id,subject,body,sequence_number,contacts(email,full_name,agency_id,agencies(name))",
            "status": "eq.approved",
            "order": "created_at.asc",
            "limit": limit,
        },
    )
    return resp.json() if resp.ok else []


def send_via_resend(to_email, subject, body):
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": SENDER,
            "to": [to_email],
            "subject": subject,
            "text": body,
        },
    )
    return resp.ok, resp.json()


def update_draft_status(draft_id, status, resend_id=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    data = {"status": status}
    if status == "sent":
        data["sent_at"] = datetime.now(timezone.utc).isoformat()
    if resend_id:
        data["notes"] = f"resend_id:{resend_id}"

    requests.patch(
        f"{SUPABASE_URL}/rest/v1/email_drafts?id=eq.{draft_id}",
        headers=headers,
        json=data,
    )


def main():
    if not SUPABASE_KEY:
        print("Set SUPABASE_SERVICE_KEY", file=sys.stderr)
        sys.exit(1)
    if not RESEND_KEY:
        print("Set RESEND_API_KEY", file=sys.stderr)
        sys.exit(1)

    limit = 5
    dry_run = False
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
        if arg == "--dry-run":
            dry_run = True

    drafts = get_approved_drafts(limit)
    print(f"# {len(drafts)} approved drafts to send", file=sys.stderr)

    sent = 0
    for i, d in enumerate(drafts):
        contact = d.get("contacts") or {}
        email = contact.get("email")
        name = contact.get("full_name") or "?"
        agency = (contact.get("agencies") or {}).get("name") or "?"

        if not email:
            print(f"# [{i+1}] SKIP {name} — no email", file=sys.stderr)
            continue

        if dry_run:
            print(f"# [{i+1}] DRY-RUN → {email} ({agency}): {d['subject'][:50]}", file=sys.stderr)
            continue

        ok, result = send_via_resend(email, d["subject"], d["body"])

        if ok:
            resend_id = result.get("id", "")
            update_draft_status(d["id"], "sent", resend_id)
            sent += 1
            print(f"# [{i+1}] SENT → {email} ({agency})", file=sys.stderr)
        else:
            print(f"# [{i+1}] FAIL → {email}: {result}", file=sys.stderr)

        time.sleep(1)  # Rate limit: 1 email/sec

    print(json.dumps({"sent": sent, "total": len(drafts)}))


if __name__ == "__main__":
    main()
