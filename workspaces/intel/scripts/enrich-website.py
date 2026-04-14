#!/usr/bin/env python3
"""
enrich-website.py — Scrape company website for enrichment data
Uses requests + BeautifulSoup (fallback), Playwright JS for JS-rendered pages.
Usage: python3 enrich-website.py "domain.fr"
"""

import json
import os
import re
import subprocess
import sys
import urllib.request

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Paths to try for pages with useful info
PATHS_TO_TRY = [
    "/",
    "/contact",
    "/a-propos",
    "/about",
    "/about-us",
    "/equipe",
    "/team",
    "/notre-equipe",
    "/mentions-legales",
    "/legal",
]

# Regex patterns
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE)
PHONE_FR_RE = re.compile(r"(?:(?:\+33|0033|0)\s*[1-9])(?:[\s.-]*\d{2}){4}")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9_-]+/?")
FACEBOOK_RE = re.compile(r"https?://(?:www\.)?facebook\.com/[a-zA-Z0-9._-]+/?")
TWITTER_RE = re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+/?")
INSTAGRAM_RE = re.compile(r"https?://(?:www\.)?instagram\.com/[a-zA-Z0-9._]+/?")

# Common tech signatures in HTML
TECH_SIGNATURES = {
    "WordPress": ["/wp-content/", "/wp-includes/", "wp-json"],
    "Shopify": ["cdn.shopify.com", "shopify.com"],
    "Wix": ["wix.com", "wixstatic.com"],
    "Squarespace": ["squarespace.com", "sqsp.net"],
    "HubSpot": ["hubspot.com", "hs-scripts.com", "hbspt"],
    "Salesforce": ["salesforce.com", "pardot.com"],
    "Google Analytics": ["google-analytics.com", "googletagmanager.com", "gtag"],
    "Crisp": ["crisp.chat"],
    "Intercom": ["intercom.io"],
    "Zendesk": ["zendesk.com", "zdassets.com"],
    "Calendly": ["calendly.com"],
    "Ypareo": ["ypareo"],
    "React": ["react", "_next/"],
    "Vue.js": ["vue.js", "vue.min.js"],
    "Next.js": ["_next/"],
    "Webflow": ["webflow.com"],
}

# Noise emails to filter out
NOISE_EMAILS = {"email@example.com", "name@domain.com", "user@example.com", "test@test.com"}

PLAYWRIGHT_MODULE = os.environ.get("PLAYWRIGHT_MODULE_PATH", "")


def fetch_with_requests(url, timeout=10):
    """Simple HTTP fetch — no JS rendering."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def fetch_with_playwright(url, timeout=10000):
    """Fetch page with Playwright JS (headless chromium) for JS-rendered content."""
    js_code = f"""
const pw = require("{PLAYWRIGHT_MODULE}");
(async () => {{
    const browser = await pw.chromium.launch({{ headless: true }});
    const page = await browser.newPage();
    try {{
        await page.goto("{url}", {{ timeout: {timeout}, waitUntil: "domcontentloaded" }});
        await page.waitForTimeout(2000);
        const html = await page.content();
        process.stdout.write(html);
    }} catch (e) {{
        process.stderr.write(e.message);
    }} finally {{
        await browser.close();
    }}
}})();
"""
    try:
        result = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout if result.stdout else None
    except Exception:
        return None


def extract_text(html):
    """Extract readable text from HTML."""
    if HAS_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "path"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)
    # Fallback: basic regex
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_emails(html, text, domain):
    """Extract email addresses, prioritize domain matches."""
    all_emails = set(EMAIL_RE.findall(html)) | set(EMAIL_RE.findall(text))
    # Filter noise and image files
    filtered = set()
    for e in all_emails:
        e_lower = e.lower()
        if e_lower in NOISE_EMAILS:
            continue
        if e_lower.endswith((".png", ".jpg", ".gif", ".svg", ".webp")):
            continue
        filtered.add(e_lower)
    # Sort: domain emails first
    domain_emails = sorted(e for e in filtered if domain.lower() in e)
    other_emails = sorted(e for e in filtered if domain.lower() not in e)
    return domain_emails + other_emails


def extract_phones(text):
    """Extract French phone numbers."""
    phones = PHONE_FR_RE.findall(text)
    return list(dict.fromkeys(re.sub(r"[\s.-]", " ", p).strip() for p in phones))


def extract_social_links(html):
    """Extract social media profile URLs."""
    links = {}
    for name, regex in [("linkedin", LINKEDIN_RE), ("facebook", FACEBOOK_RE),
                         ("twitter", TWITTER_RE), ("instagram", INSTAGRAM_RE)]:
        matches = regex.findall(html)
        if matches:
            links[name] = matches[0]
    return links


def detect_tech_stack(html):
    """Detect technologies from HTML source."""
    html_lower = html.lower()
    detected = []
    for tech, signatures in TECH_SIGNATURES.items():
        for sig in signatures:
            if sig.lower() in html_lower:
                detected.append(tech)
                break
    return detected


def extract_team_mentions(text, director_hint=""):
    """Try to find person names in French business context."""
    # Look for patterns like "Dirigé par X", "Fondateur : X", "CEO : X", "Gérant : X"
    patterns = [
        r"(?:dirigeant|directeur|directrice|fondateur|fondatrice|gérant|gérante|CEO|PDG|président|présidente|DG)\s*(?::|;|,|-|–)?\s*([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][a-zàâäéèêëïîôùûüÿç]+(?:\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][a-zàâäéèêëïîôùûüÿç]+)+)",
        r"([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][a-zàâäéèêëïîôùûüÿç]+(?:\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ][a-zàâäéèêëïîôùûüÿç]+)+)\s*(?:,\s*)?(?:dirigeant|directeur|directrice|fondateur|fondatrice|gérant|gérante|CEO|PDG|président|présidente|DG)",
    ]
    names = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            name = m.strip()
            if 2 <= len(name.split()) <= 4 and len(name) < 50:
                names.append(name)
    return list(dict.fromkeys(names))[:5]


def enrich_website(domain):
    """Scrape company website and extract enrichment data."""
    base_url = f"https://{domain}"
    result = {
        "domain": domain,
        "reachable": False,
        "pages_found": [],
        "emails": [],
        "phones": [],
        "team_mentions": [],
        "tech_stack": [],
        "social_links": {},
        "title": "",
        "description": "",
    }

    all_html = ""
    all_text = ""

    for path in PATHS_TO_TRY:
        url = base_url + path
        html = fetch_with_requests(url)

        # If homepage fails with requests, try Playwright
        if html is None and path == "/":
            html = fetch_with_playwright(url)

        if html is None:
            continue

        result["reachable"] = True
        result["pages_found"].append(path)

        text = extract_text(html)
        all_html += html + "\n"
        all_text += text + "\n"

        # Get title and description from homepage
        if path == "/" and HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                result["title"] = title_tag.get_text(strip=True)[:200]
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                result["description"] = meta_desc.get("content", "")[:300]

    if not result["reachable"]:
        result["error"] = f"Could not reach {base_url}"
        return result

    # Extract all data from combined HTML/text
    result["emails"] = extract_emails(all_html, all_text, domain)[:10]
    result["phones"] = extract_phones(all_text)[:5]
    result["social_links"] = extract_social_links(all_html)
    result["tech_stack"] = detect_tech_stack(all_html)
    result["team_mentions"] = extract_team_mentions(all_text)

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 enrich-website.py 'domain.fr'", file=sys.stderr)
        sys.exit(1)

    result = enrich_website(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
