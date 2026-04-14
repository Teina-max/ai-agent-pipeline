# Email Infrastructure & SMTP Setup

## Overview

The prospection email system uses a dedicated domain with Cloudflare Email Routing for inbound mail and Resend (Amazon SES) for outbound SMTP. All emails are sent through Gmail's "Send as" feature for centralized management.

---

## Architecture

### Components

| Component | Service | Purpose |
|-----------|---------|---------|
| Prospection Domain | Your custom domain | Isolated reputation from main business domain |
| Inbound Routing | Cloudflare Email Routing | Forward replies to your Gmail inbox |
| Outbound SMTP | Resend (Amazon SES) | Send prospection emails at scale |
| Email Client | Gmail "Send as" | Unified inbox for writing & approving drafts |
| Domain DNS | Cloudflare | Host SPF, DKIM, DMARC records |

### Why a Separate Domain?

- **Reputation Isolation:** If prospection outreach triggers spam flags or bounces escalate, the main business domain remains untouched
- **Flexibility:** Can retire the prospection domain if reputation burns without losing business communications
- **Focus:** Dedicated SPF/DKIM/DMARC setup optimized purely for cold outreach
- **Legal Clarity:** Clearly separates transactional emails from business communications

---

## DNS Records Required

Configure these records in your Cloudflare DNS dashboard for `your-prospection-domain.com`:

### MX Records (Email Routing)

**Record 1: Main inbound routing**
| Type | Name | Priority | Content | TTL |
|------|------|----------|---------|-----|
| MX | `your-prospection-domain.com` | 10 | `route1.mx.cloudflare.net` | Auto |

**Record 2: Backup**
| Type | Name | Priority | Content | TTL |
|------|------|----------|---------|-----|
| MX | `your-prospection-domain.com` | 20 | `route2.mx.cloudflare.net` | Auto |

**Record 3: Tertiary**
| Type | Name | Priority | Content | TTL |
|------|------|----------|---------|-----|
| MX | `your-prospection-domain.com` | 30 | `route3.mx.cloudflare.net` | Auto |

**Record 4: Bounce handling (Resend)**
| Type | Name | Priority | Content | TTL |
|------|------|----------|---------|-----|
| MX | `send.your-prospection-domain.com` | 10 | `feedback-smtp.eu-west-1.amazonses.com` | Auto |

---

### SPF Record (Sender Policy Framework)

**Purpose:** Authorizes which mail servers can send email from your domain.

| Type | Name | Value |
|------|------|-------|
| TXT | `your-prospection-domain.com` | `v=spf1 include:_spf.mx.cloudflare.net include:amazonses.com ~all` |

**Breakdown:**
- `v=spf1` — SPF version 1
- `include:_spf.mx.cloudflare.net` — Allow Cloudflare's mail servers
- `include:amazonses.com` — Allow Amazon SES (Resend backend)
- `~all` — Soft fail on unauthorized senders (not strict fail)

---

### DKIM Records (DomainKeys Identified Mail)

**Purpose:** Cryptographically sign emails to prove they're from your domain.

#### DKIM Key 1: Resend (Primary)

| Type | Name | Value |
|------|------|-------|
| TXT | `resend._domainkey.your-prospection-domain.com` | `v=DKIM1; k=rsa; p={RESEND_PUBLIC_KEY}` |

**How to get the key:**
1. Log into Resend dashboard
2. Go to Domains → add `your-prospection-domain.com`
3. Copy the DKIM record provided
4. Paste into Cloudflare DNS

#### DKIM Key 2: Cloudflare (Optional, for Email Routing)

| Type | Name | Value |
|------|------|-------|
| TXT | `cf2024._domainkey.your-prospection-domain.com` | `v=DKIM1; k=rsa; p={CLOUDFLARE_PUBLIC_KEY}` |

**How to get the key:**
1. Log into Cloudflare → Email Routing
2. Go to Domain Configuration
3. Copy the DKIM record
4. Paste into DNS

---

### DMARC Record (Domain-based Message Authentication)

**Purpose:** Policy for how recipients handle authentication failures; gather reports on phishing/spoofing.

| Type | Name | Value |
|------|------|-------|
| TXT | `_dmarc.your-prospection-domain.com` | `v=DMARC1; p=none; rua=mailto:contact@your-prospection-domain.com` |

**Breakdown:**
- `v=DMARC1` — DMARC version 1
- `p=none` — Do not enforce policy (just monitor). Later, upgrade to `p=quarantine` or `p=reject` once confident.
- `rua=mailto:contact@your-prospection-domain.com` — Send aggregate reports here

**Reports Include:**
- Authentication pass/fail rates
- Domains attempting to spoof yours
- IP addresses sending email

Review weekly for the first month. If spam detected, can increase policy to quarantine.

---

## SMTP Configuration (Gmail Send As)

### Setup in Gmail

1. Open Gmail settings → Accounts and Import → Send mail as
2. Click "Add another email address"
3. Enter: `contact@your-prospection-domain.com`
4. Uncheck "Treat as an alias"
5. SMTP Server Settings:

| Setting | Value |
|---------|-------|
| Server | `smtp.resend.com` |
| Port | `587` |
| Username | `resend` |
| Password | Your Resend API key |
| Encryption | TLS |

6. Test the setup (Gmail will send a verification email)
7. Once verified, you can compose/send from this address in Gmail

### Resend API Key

1. Log into Resend dashboard: https://resend.com/api-keys
2. Create or copy your API key
3. Use as SMTP password in Gmail

---

## Email Send Flow

### Step-by-Step Process

```
1. Writer Agent (Supabase)
   └─ save-draft() writes to email_drafts table
      └─ status: 'draft'
      └─ all fields: subject, body, to_address, from_address

2. Gmail Draft Creation Webhook
   └─ gmail_create_draft.py triggers
      └─ Uses Gmail API with service account
      └─ Creates draft in YOUR_GMAIL_ADDRESS "Send as" account
      └─ Links draft_id to email_drafts record

3. You Review in Gmail
   └─ Open Gmail inbox
   └─ Find draft in Drafts folder (or "Send as" section)
   └─ Read, edit subject/body if needed
   └─ Decide: Send or Delete

4. Send Approval
   └─ Click "Send" button in Gmail
   └─ OR trigger send-email.py webhook with draft_id

5. Resend SMTP Delivery
   └─ send-email.py calls Resend API:
      POST /emails
      {
        "from": "contact@your-prospection-domain.com",
        "to": "prospect@company.com",
        "subject": "...",
        "html": "..."
      }
   └─ Resend routes through Amazon SES
   └─ Email delivered to prospect inbox

6. Prospect Replies
   └─ Reply to contact@your-prospection-domain.com
   └─ Cloudflare Email Routing intercepts
   └─ Forwards to YOUR_GMAIL_ADDRESS
   └─ You see reply in inbox (in "Reply to:" section)

7. Status Update
   └─ send-email.py updates email_drafts:
      └─ status: 'sent'
      └─ sent_at: timestamp
      └─ delivery_status: 'delivered' or 'bounced'
```

---

## Configuration Files

### Example: `send-email.py`

```python
import os
from resend import Resend
from supabase import create_client, Client

# Initialize clients
resend = Resend(api_key=os.environ.get("RESEND_API_KEY"))
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)

def send_email(draft_id: str):
    # 1. Fetch draft from Supabase
    response = supabase.table("email_drafts").select("*").eq("id", draft_id).single().execute()
    draft = response.data
    
    # 2. Send via Resend
    email_response = resend.emails.send({
        "from": draft["from_address"],
        "to": draft["to_address"],
        "subject": draft["subject"],
        "html": draft["body"]
    })
    
    # 3. Update status in Supabase
    supabase.table("email_drafts").update({
        "status": "sent",
        "sent_at": "now()",
        "resend_id": email_response.get("id")
    }).eq("id", draft_id).execute()
    
    return email_response

if __name__ == "__main__":
    import sys
    draft_id = sys.argv[1]
    result = send_email(draft_id)
    print(f"✅ Email sent: {result['id']}")
```

### Example: `save-draft.py` (Writer Agent)

```python
import os
from supabase import create_client, Client

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)

def save_draft(intel_id: str, subject: str, body: str, to_address: str):
    # 1. Create draft record
    response = supabase.table("email_drafts").insert({
        "intel_id": intel_id,
        "subject": subject,
        "body": body,
        "from_address": "contact@your-prospection-domain.com",
        "to_address": to_address,
        "status": "draft"
    }).execute()
    
    draft = response.data[0]
    
    # 2. Trigger Gmail webhook (optional, for auto-draft creation)
    # POST to your webhook with draft_id
    
    return draft["id"]
```

### Example: `gmail_create_draft.py`

```python
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import base64

def create_gmail_draft(to_address: str, subject: str, body: str):
    # Load service account credentials
    credentials = Credentials.from_service_account_info(
        json.loads(os.environ.get("GMAIL_SERVICE_ACCOUNT_JSON")),
        scopes=["https://www.googleapis.com/auth/gmail.compose"]
    )
    
    # Build Gmail API client
    service = build("gmail", "v1", credentials=credentials)
    
    # Create MIME message
    import email
    message = email.mime.text.MIMEText(body, "html")
    message["to"] = to_address
    message["from"] = "YOUR_GMAIL_ADDRESS"
    message["subject"] = subject
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    # Send as draft
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw_message}}
    ).execute()
    
    return draft["id"]
```

---

## Warmup Schedule

Email reputation takes time to build. Follow this gradual warmup:

| Phase | Duration | Daily Volume | Action Items |
|-------|----------|--------------|--------------|
| **Week 1** | 7 days | 2–3 emails | Send only to warm leads; monitor bounce rate |
| **Week 2** | 7 days | 5 emails | Increase volume; check Gmail spam folder daily |
| **Week 3+** | ongoing | 10 emails/day max | Monitor delivery metrics; adjust if needed |

**Monitoring Checklist:**
- [ ] Bounce rate < 3%
- [ ] Complaint rate < 0.1%
- [ ] No emails in recipient spam folders
- [ ] Resend dashboard: green health score

---

## Monitoring & Maintenance

### DMARC Reports

**Frequency:** Weekly (especially first month)

1. Check email inbox for DMARC aggregate reports
2. Look for:
   - Authentication pass rates (should be 100% SPF + DKIM)
   - Any suspicious IPs sending from your domain
   - Phishing/spoofing attempts
3. Action: If failures detected, verify DNS records are correct

### Bounce Handling

Resend automatically handles bounces:

1. Hard bounce (invalid email) → `email_valid = false` in Supabase
2. Soft bounce (mailbox full) → Resend retries up to 72 hours
3. Complaint (marked as spam) → Alert Teina, pause sending to that domain

**Webhook Integration:**
```python
# Resend webhooks POST to your endpoint
# /webhooks/resend/bounce
POST {
  "type": "bounced",
  "email": "prospect@company.com",
  "reason": "invalid_email"
}
```

Update Supabase: `email_valid = false` for this address.

### Spam Monitoring

**Weekly Check:**
1. Send a test email to yourself
2. Check if it lands in spam or inbox
3. If spam: review recent emails for trigger words
4. Adjust content if needed

**Trigger Words to Avoid:**
- "Free," "guaranteed," "act now," "limited time"
- "Click here," "buy now," "don't miss out"
- Multiple exclamation marks or all caps
- Heavy discount language

---

## Reputation Management

### Good Practices

✅ **DO:**
- Send only to engaged prospects (verified email)
- Personalize every email (use automation rate, company name, real person's name)
- Include unsubscribe link in footer (legally required)
- Monitor reply rates; pause if dropping below 2%
- Use consistent sending schedule (morning, business hours)

❌ **DON'T:**
- Send to batch lists without personalization
- Ignore bounces; remove invalid emails immediately
- Use purchased email lists
- Send the same email to multiple addresses in same company simultaneously
- Send more than 10 emails/day from this domain early on

### Reputation Recovery

If domain reputation drops (spam complaints, high bounce rate):

1. **Pause sending** for 1–2 weeks
2. **Review recent emails** for trigger words or poor targeting
3. **Clean list** — remove all bounced, complained, or unengaged addresses
4. **Restart slowly** — send 1–2 emails/day to warm prospects only
5. **Consider new domain** if reputation doesn't recover after 4 weeks

---

## Cost Breakdown

| Service | Tier | Cost/Month | Notes |
|---------|------|-----------|-------|
| Resend SMTP | Free | $0 | 3,000 emails/month included |
| Cloudflare Email Routing | Free | $0 | Unlimited custom domains |
| Gmail | Free | $0 | Using your existing account |
| Supabase (for draft storage) | Pay-as-you-go | ~$5–10 | Minimal usage for email logs |
| **Total** | — | **$5–10** | Very lean email ops |

---

## Compliance & Legal

### Required Elements

Every prospection email must include:

1. **Sender Identification:** Clear "From:" address and company name
2. **Unsubscribe Link:** Easy way to opt out (footer)
3. **Privacy Policy:** Link to your privacy policy
4. **Business Address:** Your actual business location (can be "Toulouse, France")

### Example Footer

```html
---
Sent by Teina | Automation Consulting | Toulouse, France
[Unsubscribe](https://your-domain.com/unsubscribe?email={{PROSPECT_EMAIL}})
Privacy Policy: [link]
Contact: contact@your-prospection-domain.com
```

### GDPR Compliance

- **Consent:** In France, B2B email to business addresses is permitted (no explicit opt-in needed for cold outreach)
- **Unsubscribe:** Must honor requests within 10 days
- **Data:** Do not collect personal data beyond what's publicly available
- **Retention:** Delete email logs after 12 months

---

## Troubleshooting

### Email Not Delivering

**Check:**
1. Is SPF configured? `dig TXT your-prospection-domain.com` should show SPF record
2. Is DKIM valid? Resend dashboard shows green checkmark
3. Is recipient email correct? Typos cause hard bounces
4. Is daily volume low enough? (2–5 during warmup)

**Action:**
- Check Resend dashboard for error message
- Review DNS propagation: https://mxtoolbox.com
- Test with personal email first

### Emails in Spam Folder

**Check:**
1. DMARC reports — authentication failing?
2. Content — contains spam trigger words?
3. Recipient domain — blacklist your IP?
4. Reply rate — low engagement signals spam

**Action:**
- Pause sending for 1 week
- Remove trigger words from email templates
- Ask one reply-er to move email to inbox (trains filters)
- Switch Resend IP if issue persists

### Low Reply Rates (< 2%)

**Likely causes:**
- Subject line too generic ("Question about your job posting")
- Missing personalization (no company name, no specific task)
- Automation rate not mentioned
- Wrong contact person (HR vs. founder)

**Action:**
- A/B test subject lines (change formula, track opens)
- Increase personalization depth (3+ data points minimum)
- Target founders/CTOs directly instead of HR
- Shorten email body (aim for 100–150 words)

---

## References

- Resend SMTP Docs: https://resend.com/docs/send/smtp
- Cloudflare Email Routing: https://developers.cloudflare.com/email-routing/
- Gmail API (Drafts): https://developers.google.com/gmail/api/reference/rest/v1/users.drafts
- DMARC Best Practices: https://dmarcian.com/dmarc-basics/
- SPF, DKIM, DMARC Guide: https://www.mailmodo.com/guides/spf-dkim-dmarc/
