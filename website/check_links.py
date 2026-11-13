#!/usr/bin/env python3
"""Check every local website file link and fragment without network access."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = []
        self.h1_count = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1': self.h1_count += 1
        if 'id' in attrs: self.ids.append(attrs['id'])
        for attr in ('href', 'src'):
            if attr in attrs: self.links.append(attrs[attr])


scans = {}
for file in sorted(DIST.glob('*.html')):
    scan = Scan()
    scan.feed(file.read_text('utf-8'))
    scans[file] = scan
errors = []
count = 0
for file, scan in scans.items():
    if scan.h1_count != 1:
        errors.append({'page':file.name,'error':'expected exactly one h1','count':scan.h1_count})
    if len(scan.ids) != len(set(scan.ids)):
        errors.append({'page':file.name,'error':'duplicate element ids'})
    for url in scan.links:
        parts = urlsplit(url)
        if parts.scheme or parts.netloc: continue
        count += 1
        target = (file.parent / unquote(parts.path)).resolve() if parts.path else file
        if not target.exists(): errors.append({'page':file.name,'url':url,'error':'missing local file'})
        elif parts.fragment and target in scans and unquote(parts.fragment) not in scans[target].ids:
            errors.append({'page':file.name,'url':url,'error':'missing local anchor'})
result = {'checked_at':'2026-11-13','html_pages':len(scans),'local_link_occurrences':count,'errors':errors,
          'scope':'Static HTML, local asset/download links and fragment destinations. External source checks are recorded separately.'}
output = ROOT / 'website' / 'static-validation.json'
output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(bool(errors))
