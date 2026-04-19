# Case Study — AI Agent Pipeline

> Self-built autonomous B2B prospection system.  Running since January
> 2026 to prospect real estate agencies in the Toulouse region for my
> own freelance automation practice. Every metric below is real; no
> synthetic data.

## The context

I needed a repeatable pipeline to turn "agencies in my target region"
into "qualified cold emails with personalised hooks" without spending
my own hours on it. The alternatives — Lemlist, Apollo, HubSpot
sequences — all fail on one axis: the emails read like a template. My
pitch is "I automate things"; sending generic AI-assembled sentences is
the worst possible signal to send to a prospect.

So the constraint was: **each email must reference something
specific and true** about the agency, extracted from open sources,
with a human approval gate before send.

## What I built

A 3-stage pipeline orchestrated by a heartbeat trigger (Monday 08:00 CET):

1. **Scout** — Google Places API query for real-estate agencies within
   30km of Toulouse. 15–25 candidates per week.
2. **Intel** — 9 Python sub-agents enrich each candidate: SIRENE
   (company size / sector / revenue), website scrape for pain-point
   hints, email permutation + DNS verification, Google reviews
   sentiment (Claude Haiku classifier), competitor profiling.
3. **Writer** — Claude Haiku composes the first-touch email using the
   intel as hooks. Generated emails land as Gmail drafts for final
   review before send.

Between each stage: a **Discord approval gate** so a bad lead can be
killed before the next stage burns tokens.

## Cost & ROI

- **Infra**: ~€75/month (Supabase + Resend + Google Places + Anthropic API).
- **ROI break-even**: one closed 25k€ contract pays for ~28 years of
  infra. Even a single qualified call back pays for 6+ months.
- **Token cost per email**: ~$0.008 (Haiku 3), dominated by context
  from website scrape + reviews.

## Architecture decisions I'd make again

### 1. Paperclip tickets as the orchestration primitive

Each prospect is a ticket that moves through states
(`detected → enriched → approved → drafted → sent`). Scripts read the
current state and write the next. No workflow engine, no DAG library.
The state machine *is* the database schema.

### 2. Python scripts over a framework

Each sub-agent is a single `.py` file under 200 lines, takes JSON
stdin, writes JSON stdout. No LangChain, no AutoGen. When enrichment
changes (e.g. a new SIRENE field), I edit one file. Composability
comes from the orchestrator calling the scripts in sequence, not from
framework abstractions.

### 3. Requests over SDKs

Anthropic and Resend both ship Python SDKs. I use `requests` directly.
Reasons: one less dependency to pin, identical request bodies between
n8n (HTTP) and Python, and the SDKs are thin wrappers over HTTP
anyway. Cost: I lose SDK-level type hints. Net: worth it for a
long-running agent pipeline with few deps.

### 4. Human gates are non-negotiable

Two manual approvals per prospect (Discord after Intel, Gmail after
Writer). Adds friction, but (a) catches bad Places data that slipped
through the size filter, (b) lets me tweak the email if the hook
feels weak. The system is "autonomous" in that it never blocks on
me; but I always ship the last mile.

## What I'd do differently

- **Prompt caching** on the Writer agent. Same system prompt × 20 emails/week,
  should have been caching from day 1.
- **Deterministic eval** on the Writer output. Currently I check emails by
  reading them; I should grade each draft against a rubric (specificity,
  length, CTA clarity) and auto-reject below a threshold.
- **Sector expansion**. The same pipeline works 1-for-1 on any sector
  available in Google Places + SIRENE. Pulling this out as a
  multi-tenant SaaS is the obvious next step.

## Stack

Python 3.10+ · Claude Haiku 3 · Google Places API · SIRENE API · Resend ·
Gmail (drafts via IMAP) · Paperclip (ticket state) · Discord webhooks ·
Supabase (persistence).
