#!/usr/bin/env python3
"""Fail the build if SEO/GEO declarations drift from the generated Pages content.

Source: scripts/build_site.py. No network requests or ranking guarantees.
"""
from html.parser import HTMLParser
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "dist"
BASE = "https://aipmandy.github.io/chinese-international-student-career-guide/"
AUTHOR = "AI 酋长 Andy"
BRAND_URL = "https://www.a6no1.cn/"
PERSON_URL = "https://metaver.vip/"


class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.titling = False
        self.h1 = 0
        self.description = ""
        self.canonical = []
        self.og = {}
        self.jsonld = []
        self.reading_jsonld = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.titling = True
        if tag == "link" and "canonical" in attrs.get("rel", "").split():
            self.canonical.append(attrs.get("href", ""))
        if tag == "meta":
            if attrs.get("name") == "description":
                self.description = attrs.get("content", "")
            if attrs.get("property", "").startswith("og:"):
                self.og[attrs["property"]] = attrs.get("content", "")
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.reading_jsonld = True
            self.jsonld.append("")

    def handle_data(self, data):
        if self.titling:
            self.title += data
        if self.reading_jsonld:
            self.jsonld[-1] += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.titling = False
        if tag == "script":
            self.reading_jsonld = False


def main():
    errors = []
    files = sorted(SITE.glob("*.html"))
    expected_urls = set()
    for file in files:
        path = file.name
        url = BASE if path == "index.html" else BASE + path
        expected_urls.add(url)
        meta = Meta()
        meta.feed(file.read_text("utf-8"))
        if meta.h1 != 1:
            errors.append(f"{path}: expected one H1; got {meta.h1}")
        if not meta.title or not meta.description:
            errors.append(f"{path}: missing title or meta description")
        if meta.canonical != [url]:
            errors.append(f"{path}: canonical {meta.canonical!r} != {url!r}")
        for key in ("og:title", "og:description", "og:url", "og:site_name"):
            if not meta.og.get(key):
                errors.append(f"{path}: missing {key}")
        if meta.og.get("og:url") != url:
            errors.append(f"{path}: OG URL does not match canonical")
        if meta.og.get("og:title") != meta.title:
            errors.append(f"{path}: OG title differs from HTML title")
        if len(meta.jsonld) != 1:
            errors.append(f"{path}: expected one JSON-LD object")
            continue
        try:
            data = json.loads(meta.jsonld[0])
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON-LD: {exc}")
            continue
        if data.get("@context") != "https://schema.org" or data.get("@type") != "WebPage":
            errors.append(f"{path}: unexpected JSON-LD type/context")
        if data.get("url") != url or data.get("inLanguage") != "zh-CN":
            errors.append(f"{path}: JSON-LD URL/language mismatch")
        if data.get("author", {}).get("name") != AUTHOR or data.get("author", {}).get("url") != PERSON_URL:
            errors.append(f"{path}: incorrect author entity")
        if data.get("publisher", {}).get("url") != BRAND_URL:
            errors.append(f"{path}: incorrect company URL")

    try:
        robots = (SITE / "robots.txt").read_text("utf-8")
        if "Sitemap: " + BASE + "sitemap.xml" not in robots:
            errors.append("robots.txt: missing absolute Sitemap link")
        tree = ET.parse(SITE / "sitemap.xml")
        locs = [node.text for node in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        if len(locs) != len(set(locs)):
            errors.append("sitemap.xml: duplicate URLs")
        if set(locs) != expected_urls:
            errors.append(f"sitemap.xml: expected {len(expected_urls)} published HTML URLs; got {len(set(locs))}")
    except (OSError, ET.ParseError) as exc:
        errors.append(f"robots/sitemap invalid: {exc}")

    homepage = (SITE / "index.html").read_text("utf-8")
    for value in ("AIPMAndy", PERSON_URL, BRAND_URL, "https://metaver.vip/services", "data-copy-wechat"):
        if value not in homepage:
            errors.append(f"Homepage: missing brand/service/copy target {value}")
    summary = {"html_pages": len(files), "sitemap_urls": len(expected_urls),
               "errors": errors[:30], "omitted_errors": max(0, len(errors)-30)}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
