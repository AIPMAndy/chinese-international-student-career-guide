#!/usr/bin/env python3
"""Build deterministic, editable release archives without credentials or caches.

Run before the final website build. The source ZIP excludes generated dist/ and
downloads/ to avoid self-inclusion; rebuild them using the documented commands.
"""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'downloads'
PREFIX = 'chinese-international-student-career-guide'
EXCLUDE = {'.git','.openai','.sites-runtime','.sites-checkout','tmp','outputs','node_modules','__pycache__','dist','downloads'}

def archive(destination, paths, prefix):
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(paths):
            rel = p.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(prefix+'/'+rel, date_time=(2026,11,13,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o755 if p.suffix=='.sh' else 0o644)<<16
            z.writestr(info,p.read_bytes())
    with zipfile.ZipFile(destination) as z:
        bad=z.testzip()
        if bad: raise RuntimeError('Invalid ZIP member: '+bad)
    return {'file':destination.name,'bytes':destination.stat().st_size,
            'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}

def main():
    OUT.mkdir(exist_ok=True)
    records=[]
    records.append(archive(OUT/'editable-templates.zip',[*(ROOT/'templates').glob('*'),ROOT/'CONTENT_LICENSE.md',ROOT/'LICENSE'],PREFIX))
    source=[]
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if not p.is_file() or any(part in EXCLUDE for part in rel.parts):continue
        if p.name.startswith('.env') or p.suffix in {'.pyc','.tar','.gz'}:continue
        if p.name == 'release-manifest.json':continue
        source.append(p)
    records.append(archive(OUT/'source-code.zip',source,PREFIX))
    for p in [OUT/'chinese-international-student-career-guide.pdf',ROOT/'templates/career-workbook.xlsx']:
        if p.exists():records.append({'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest={'version':'1.0.0','date':'2026-11-13','artifacts':records,
              'source_archive_excludes':['Git metadata','hosting identity','generated website','generated downloads','temporary files','environment files'],
              'archive_integrity':'CRC checks passed'}
    (OUT/'release-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))

if __name__=='__main__':main()
