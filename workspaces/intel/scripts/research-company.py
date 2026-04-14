#!/usr/bin/env python3
"""
research-company.py — Company research script for Intel agent
Scrapes company info from free public sources.
Usage: python3 research-company.py "Nom Entreprise" "Ville"
"""

import json
import sys
import urllib.request
import urllib.parse
import re
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    """Simple HTML to text extractor."""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.text.append(text)

    def get_text(self):
        return ' '.join(self.text)


def fetch_url(url, timeout=10):
    """Fetch URL content as text."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; research-bot/1.0)'
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            extractor = TextExtractor()
            extractor.feed(html)
            return extractor.get_text()
    except Exception as e:
        return f"ERROR: {e}"


def search_pappers(company_name, city=""):
    """Search company on Pappers.fr (free public data)."""
    query = urllib.parse.quote(f"{company_name} {city}".strip())
    url = f"https://www.pappers.fr/recherche?q={query}"
    text = fetch_url(url)
    return {
        "source": "pappers.fr",
        "url": url,
        "raw": text[:3000]
    }


def search_societe(company_name):
    """Search company on societe.com (free public data)."""
    query = urllib.parse.quote(company_name)
    url = f"https://www.societe.com/cgi-bin/search?champs={query}"
    text = fetch_url(url)
    return {
        "source": "societe.com",
        "url": url,
        "raw": text[:3000]
    }


def search_infogreffe(company_name):
    """Search company on infogreffe.fr (free public data)."""
    query = urllib.parse.quote(company_name)
    url = f"https://www.infogreffe.fr/recherche-entreprise-commerce/{query}"
    text = fetch_url(url)
    return {
        "source": "infogreffe.fr",
        "url": url,
        "raw": text[:3000]
    }


def research(company_name, city=""):
    """Run all research sources and return combined results."""
    results = {
        "company": company_name,
        "city": city,
        "sources": []
    }

    for searcher in [search_pappers, search_societe, search_infogreffe]:
        try:
            if searcher == search_pappers:
                data = searcher(company_name, city)
            else:
                data = searcher(company_name)
            results["sources"].append(data)
        except Exception as e:
            results["sources"].append({
                "source": searcher.__name__,
                "error": str(e)
            })

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 research-company.py 'Company Name' ['City']", file=sys.stderr)
        sys.exit(1)

    company = sys.argv[1]
    city = sys.argv[2] if len(sys.argv) > 2 else ""

    results = research(company, city)
    print(json.dumps(results, ensure_ascii=False, indent=2))
