#!/usr/bin/env python3
"""
verify-email.py — Validate email via DNS checks (no SMTP needed)
Uses dnspython for MX record validation + freemail/disposable detection.
Usage: python3 verify-email.py "email@domain.fr"
"""

import json
import re
import socket
import sys

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

FREEMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.fr", "hotmail.com", "hotmail.fr",
    "outlook.com", "outlook.fr", "live.com", "live.fr", "aol.com",
    "icloud.com", "me.com", "mac.com", "protonmail.com", "proton.me",
    "mail.com", "gmx.com", "gmx.fr", "free.fr", "orange.fr", "sfr.fr",
    "laposte.net", "wanadoo.fr", "bbox.fr", "numericable.fr",
}

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "yopmail.fr", "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "dispostable.com", "maildrop.cc", "trashmail.com",
    "10minutemail.com", "temp-mail.org", "fakeinbox.com", "mailnesia.com",
    "tempail.com", "emailondeck.com", "mintemail.com",
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def check_syntax(email):
    """Check email format validity."""
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email))


def check_domain_resolves(domain):
    """Check if domain has A or AAAA record."""
    if HAS_DNS:
        for rtype in ["A", "AAAA"]:
            try:
                dns.resolver.resolve(domain, rtype)
                return True
            except Exception:
                continue
    try:
        socket.setdefaulttimeout(3)
        socket.getaddrinfo(domain, 80, socket.AF_INET)
        return True
    except Exception:
        return False


def check_mx(domain):
    """Check MX records and return primary MX host."""
    if not HAS_DNS:
        return None, False
    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_records = sorted(answers, key=lambda r: r.preference)
        primary = str(mx_records[0].exchange).rstrip(".")
        return primary, True
    except Exception:
        return None, False


def check_mx_host_resolves(mx_host):
    """Verify MX host itself resolves."""
    if not mx_host:
        return False
    try:
        socket.setdefaulttimeout(3)
        socket.getaddrinfo(mx_host, 25, socket.AF_INET)
        return True
    except Exception:
        return False


def verify_email(email):
    """Run all verification checks and return scored result."""
    result = {
        "email": email,
        "valid_syntax": False,
        "domain_resolves": False,
        "has_mx": False,
        "mx_host": None,
        "mx_host_resolves": False,
        "is_freemail": False,
        "is_disposable": False,
        "confidence": "none",
        "score": 0,
        "checks": [],
    }

    # 1. Syntax check (+10)
    result["valid_syntax"] = check_syntax(email)
    if not result["valid_syntax"]:
        result["checks"].append("FAIL: invalid email syntax")
        return result
    result["score"] += 10
    result["checks"].append("OK: valid syntax")

    domain = email.split("@")[1].lower()

    # 2. Freemail check (+15 if not freemail)
    result["is_freemail"] = domain in FREEMAIL_DOMAINS
    if result["is_freemail"]:
        result["checks"].append("WARN: freemail domain")
    else:
        result["score"] += 15
        result["checks"].append("OK: not a freemail")

    # 3. Disposable check (+10 if not disposable)
    result["is_disposable"] = domain in DISPOSABLE_DOMAINS
    if result["is_disposable"]:
        result["checks"].append("FAIL: disposable email domain")
        result["confidence"] = "none"
        return result
    result["score"] += 10
    result["checks"].append("OK: not disposable")

    # 4. Domain resolves (+20)
    result["domain_resolves"] = check_domain_resolves(domain)
    if not result["domain_resolves"]:
        result["checks"].append("FAIL: domain does not resolve")
        result["confidence"] = "low"
        return result
    result["score"] += 20
    result["checks"].append("OK: domain resolves")

    # 5. MX record check (+30)
    mx_host, has_mx = check_mx(domain)
    result["has_mx"] = has_mx
    result["mx_host"] = mx_host
    if has_mx:
        result["score"] += 30
        result["checks"].append(f"OK: MX record found ({mx_host})")

        # 5b. MX host resolves (bonus info)
        result["mx_host_resolves"] = check_mx_host_resolves(mx_host)
        if result["mx_host_resolves"]:
            result["checks"].append("OK: MX host resolves")
        else:
            result["checks"].append("WARN: MX host does not resolve")
    else:
        result["checks"].append("WARN: no MX record (may use A record fallback)")

    # Calculate confidence
    score = result["score"]
    if score >= 75:
        result["confidence"] = "high"
    elif score >= 50:
        result["confidence"] = "medium"
    elif score >= 30:
        result["confidence"] = "low"
    else:
        result["confidence"] = "none"

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify-email.py 'email@domain.fr'", file=sys.stderr)
        sys.exit(1)

    result = verify_email(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
