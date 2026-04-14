#!/usr/bin/env python3
"""Save an email draft to Supabase email_drafts table.

Usage:
    SUPABASE_SERVICE_KEY=... python3 save-draft.py '<json>'

Input JSON:
    {
        "contact_id": "uuid",
        "subject": "...",
        "body": "...",
        "sequence_number": 1,
        "notes": "Formula #2, Register B"
    }

Output: JSON with the created draft (including id).
"""

import json, os, sys, requests

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def main():
    if not SUPABASE_KEY:
        print(json.dumps({"error": "SUPABASE_SERVICE_KEY not set"}))
        sys.exit(1)

    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: save-draft.py '<json>'"}))
        sys.exit(1)

    data = json.loads(sys.argv[1])

    required = ["contact_id", "subject", "body"]
    for field in required:
        if not data.get(field):
            print(json.dumps({"error": f"Missing required field: {field}"}))
            sys.exit(1)

    row = {
        "contact_id": data["contact_id"],
        "subject": data["subject"],
        "body": data["body"],
        "sequence_number": data.get("sequence_number", 1),
        "status": "draft",
        "notes": data.get("notes"),
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/email_drafts",
        headers=headers,
        json=row,
    )

    if resp.ok:
        result = resp.json()
        print(json.dumps(result[0] if isinstance(result, list) else result))
    else:
        print(json.dumps({"error": resp.text}))
        sys.exit(1)


if __name__ == "__main__":
    main()
