#!/usr/bin/env python3
"""Check source IDs, inline citations, region paths and local Markdown links."""
import collections
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parents[1]
errors=[]
sources=[s for p in sorted((ROOT/'data').glob('sources-*.json')) for s in json.loads(p.read_text())]
coverage=[s for p in sorted((ROOT/'data').glob('coverage-*.json')) for s in json.loads(p.read_text())]
for label,items in [('source',sources),('region',coverage)]:
    counts=collections.Counter(x['id'] for x in items)
    errors.extend({'error':'duplicate '+label+' id','id':k} for k,v in counts.items() if v>1)
source_map={s['id']:s for s in sources}
refs=0
for p in (ROOT/'content').rglob('*.md'):
    for sid,url in re.findall(r'\[(S-[A-Z0-9-]+)\]\((https?://[^\s)]+)\)',p.read_text()):
        refs+=1
        if sid not in source_map or source_map[sid]['url']!=url:
            errors.append({'file':str(p.relative_to(ROOT)),'source':sid,'error':'missing or mismatched source'})
for s in sources:
    if not s.get('checked_at') or not s.get('supports') or not s['url'].startswith('https://'):
        errors.append({'source':s['id'],'error':'missing verification metadata'})
for c in coverage:
    if c.get('file'):
        if not (ROOT/'content/regions'/c['file']).exists():errors.append({'region':c['id'],'error':'missing region source'})
    elif c.get('verified') or c.get('status')!='待补充':
        errors.append({'region':c['id'],'error':'unresearched entry incorrectly marked'})
local_links=0
for p in ROOT.rglob('*.md'):
    if set(p.relative_to(ROOT).parts)&{'tmp','dist','.git','node_modules'}:continue
    for href in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)',p.read_text('utf-8')):
        parts=urlsplit(href)
        if parts.scheme or parts.netloc or not parts.path:continue
        local_links+=1
        if not (p.parent/unquote(parts.path)).exists():
            errors.append({'file':str(p.relative_to(ROOT)),'target':href,'error':'missing local Markdown destination'})
result={'checked_at':'2026-11-13','official_source_records':len(sources),
        'source_statuses':dict(collections.Counter(s['status'] for s in sources)),
        'inline_source_occurrences':refs,'route_pages':sum(bool(c.get('file')) for c in coverage),
        'gap_only_entries':sum(not c.get('file') for c in coverage),
        'coverage_statuses':dict(collections.Counter(c['status'] for c in coverage)),
        'local_markdown_links':local_links,'errors':errors,
        'scope':'Consistency and file checks. Official page reads and access limitations are recorded in data/sources-*.json and docs/research-*.md; this is not a new network crawl.'}
(ROOT/'docs/content-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(bool(errors))
