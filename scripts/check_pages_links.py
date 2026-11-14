#!/usr/bin/env python3
"""Check committed static pages at their GitHub Pages project subpath.

Pure standard library, read only. External links and browser interactions
are not checked, and success does not establish a remote deployment.
"""
from __future__ import annotations
import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.canonicals, self.ids = [], [], set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for key in ("id", "name"):
            if a.get(key): self.ids.add(a[key])
        for key in ("href", "src", "poster", "action"):
            if a.get(key): self.refs.append((a[key], self.getpos()[0]))
        if a.get("srcset") and not a["srcset"].lstrip().startswith("data:"):
            for item in a["srcset"].split(","):
                if item.strip(): self.refs.append((item.strip().split()[0], self.getpos()[0]))
        if tag == "link" and "canonical" in a.get("rel", "").split():
            self.canonicals.append((a.get("href", ""), self.getpos()[0]))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", default="dist")
    parser.add_argument("--repo-name", default=Path(__file__).resolve().parents[1].name)
    parser.add_argument("--owner", default="AIPMAndy")
    parser.add_argument("--require", action="append", default=[])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    site = (root / args.site).resolve()
    base = f"https://{args.owner.lower()}.github.io/{args.repo_name}/"
    origin = urlsplit(base)
    errors, refs, pages = [], [], {}
    checked = external = 0
    def fail(source, target, message):
        errors.append({"source": source, "target": target, "error": message})
    for rel in ["index.html", *args.require]:
        target = (site / rel).resolve()
        if not target.is_relative_to(site):
            fail("required", rel, "Required path escapes dist")
        elif not target.is_file() or target.stat().st_size == 0:
            fail("required", rel, "Required release file is missing or empty")
    for path in sorted(site.rglob("*")):
        rel = path.relative_to(site).as_posix()
        if path.is_symlink():
            fail(rel, rel, "Pages artifact must not contain symbolic links")
            continue
        if not path.is_file(): continue
        if path.suffix.lower() in {".html", ".htm"}:
            page = Page()
            page.feed(path.read_text(encoding="utf-8"))
            pages[rel] = page
            refs.extend((rel, url, line) for url, line in page.refs)
            for url, line in page.canonicals:
                if not url.startswith(base):
                    fail(f"{rel}:{line}", url, "Canonical does not use this GitHub Pages project")
        elif path.suffix.lower() == ".css":
            text = path.read_text(encoding="utf-8")
            pattern = r"url\(\s*[\"']?([^\"')]+)[\"']?\s*\)"
            refs.extend((rel, m.group(1).strip(), text[:m.start()].count("\n") + 1)
                        for m in re.finditer(pattern, text))
    for source, raw, line in refs:
        raw = raw.strip()
        if not raw or raw == "#": continue
        value = urlsplit(urljoin(base + source, raw))
        if value.scheme not in {"http", "https"}: continue
        if value.netloc.lower() == origin.netloc.lower() and not value.path.startswith(origin.path):
            sibling_prefixes = ("/chinese-international-student-product-jobs/", "/chinese-international-student-ai-jobs/", "/chinese-international-student-business-jobs/")
            if any(value.path.startswith(prefix) for prefix in sibling_prefixes):
                external += 1
                continue
            fail(f"{source}:{line}", raw, "Link escapes the GitHub Pages project subpath")
            continue
        if value.netloc.lower() != origin.netloc.lower():
            external += 1
            continue
        target = (site / unquote(value.path[len(origin.path):])).resolve()
        if not target.is_relative_to(site):
            fail(f"{source}:{line}", raw, "Decoded link escapes dist")
            continue
        if target.is_dir(): target /= "index.html"
        checked += 1
        if not target.is_file():
            fail(f"{source}:{line}", raw, "Local target does not exist")
            continue
        fragment = unquote(value.fragment).split(":~:text=", 1)[0]
        page_key = target.relative_to(site).as_posix()
        if fragment and page_key in pages and fragment not in pages[page_key].ids:
            fail(f"{source}:{line}", raw, "HTML anchor does not exist")
    print(json.dumps({"site": str(site), "simulated_base_url": base, "html_pages": len(pages),
        "local_references_checked": checked, "external_references_not_checked": external,
        "error_count": len(errors), "errors": errors[:100],
        "omitted_errors": max(0, len(errors)-100)}, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
