#!/usr/bin/env python3
"""
find-email.py - Find director email for Intel agent
Strategy: guess domain via DNS + generate French email permutations
Usage: python3 find-email.py "Prenom Nom" "Company Name" ["domain.fr"]
Fast (<5s): no SMTP (port 25 blocked from Docker), no external API calls.
"""

import json
import sys
import re
import socket
import unicodedata

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False


def normalize_french(text):
    result = unicodedata.normalize("NFD", text.lower().strip())
    result = "".join(c for c in result if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9\s-]", "", result).strip()


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"\s+", "-", normalize_french(text))).strip("-")


def domain_has_mx(domain):
    if HAS_DNS:
        try:
            mx = dns.resolver.resolve(domain, "MX")
            return str(sorted(mx, key=lambda r: r.preference)[0].exchange).rstrip(".")
        except Exception:
            pass
    return None


def domain_resolves(domain):
    if HAS_DNS:
        for rtype in ["MX", "A"]:
            try:
                dns.resolver.resolve(domain, rtype)
                return True
            except Exception:
                continue
    try:
        socket.setdefaulttimeout(2)
        socket.getaddrinfo(domain, 80, socket.AF_INET)
        return True
    except Exception:
        return False


def guess_domains(company_name):
    slug = slugify(company_name)
    words = slug.split("-")
    short = "".join(w[0] for w in words if w) if len(words) > 2 else None
    c = []
    if words:
        c += [words[0] + ".fr", words[0] + ".com"]
    c += [slug + ".fr", slug + ".com"]
    if len(words) >= 2:
        c += ["-".join(words[:2]) + ".fr", "-".join(words[:2]) + ".com"]
    c += [slug.replace("-", "") + ".fr", slug.replace("-", "") + ".com"]
    if short and len(short) >= 2:
        c += [short + ".fr", short + ".com"]
    c.append(slug + ".eu")
    return list(dict.fromkeys(c))


def find_domain(company_name, hint=""):
    if hint and "." in hint and " " not in hint:
        if domain_resolves(hint):
            return hint
    for d in guess_domains(company_name):
        if domain_resolves(d):
            return d
    return None


def generate_permutations(first_name, last_name, domain):
    f = normalize_french(first_name)
    l = normalize_french(last_name)
    fp = f.replace(" ", "-").split("-")
    fi = "".join(p[0] for p in fp) if len(fp) > 1 else f[0]
    fj = "".join(fp)
    lj = l.replace("-", "").replace(" ", "")
    return list(dict.fromkeys([
        "{}.{}@{}".format(fj, lj, domain),       # prenom.nom (most common FR)
        "{}.{}@{}".format(fi, lj, domain),        # p.nom
        "{}{}@{}".format(fi, lj, domain),          # pnom
        "{}@{}".format(fj, domain),                # prenom
        "{}.{}@{}".format(lj, fj, domain),        # nom.prenom
        "{}@{}".format(lj, domain),                # nom
        "contact@{}".format(domain),
        "direction@{}".format(domain),
        "info@{}".format(domain),
    ]))


def find_email(director_name, company_name, hint=""):
    result = {
        "director_name": director_name,
        "company": company_name,
        "domain": None,
        "candidates": [],
        "best_guess": None,
        "method": "none",
    }

    parts = director_name.strip().split()
    if len(parts) < 2:
        result["error"] = "Need first and last name"
        return result

    first_name, last_name = parts[0], " ".join(parts[1:])

    domain = find_domain(company_name, hint)
    if not domain:
        result["error"] = "No domain found for {}".format(company_name)
        return result
    result["domain"] = domain

    mx = domain_has_mx(domain)
    result["has_mx"] = mx is not None
    if mx:
        result["mx_host"] = mx

    perms = generate_permutations(first_name, last_name, domain)

    for email in perms:
        result["candidates"].append(email)

    # prenom.nom@domain is statistically most common in French companies
    result["best_guess"] = perms[0]
    result["method"] = "dns_permutation"

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 find-email.py 'Prenom Nom' 'Company' ['domain.fr']", file=sys.stderr)
        sys.exit(1)
    res = find_email(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    print(json.dumps(res, ensure_ascii=False, indent=2))
