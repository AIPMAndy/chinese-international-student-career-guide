#!/usr/bin/env python3
"""Validate the released PDF and render every page for human visual review."""
import argparse
import hashlib
import json
from pathlib import Path
import fitz
from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'downloads/chinese-international-student-career-guide.pdf'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    doc = fitz.open(PDF)
    reader = PdfReader(PDF)
    page_object_ids = {p.indirect_reference.idnum for p in reader.pages}
    page_records, errors, fonts_used = [], [], set()
    internal, external = 0, 0
    render_dir = ROOT / 'tmp/pdfs/final'
    if args.render:
        render_dir.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(doc):
        text = page.get_text()
        spans = [s for b in page.get_text('dict')['blocks'] if 'lines' in b
                 for l in b['lines'] for s in l['spans']]
        fonts_used.update(s['font'] for s in spans)
        outside = [s['text'] for s in spans if s['text'].strip() and
                   (s['bbox'][0] < -1 or s['bbox'][1] < -1 or
                    s['bbox'][2] > page.rect.width + 1 or s['bbox'][3] > page.rect.height + 1)]
        if outside:
            errors.append({'page': i+1, 'outside_page_text': outside})
        if '\ufffd' in text or '\x00' in text:
            errors.append({'page': i+1, 'error': 'replacement or null character in extracted text'})
        if not text.strip():
            errors.append({'page': i+1, 'error': 'empty text page'})
        for annot_ref in reader.pages[i].get('/Annots', []):
            annot = annot_ref.get_object()
            if '/Dest' in annot:
                internal += 1
                dest = annot['/Dest']
                if not isinstance(dest, list) or not dest or getattr(dest[0], 'idnum', None) not in page_object_ids:
                    errors.append({'page': i+1, 'error': 'invalid internal link'})
            elif annot.get('/A', {}).get('/S') == '/URI':
                external += 1
        page_records.append({'page': i+1, 'characters': len(text), 'outside_page_spans': len(outside)})
        if args.render:
            page.get_pixmap(matrix=fitz.Matrix(1.3,1.3), alpha=False).save(render_dir / f'page-{i+1:03d}.png')
    for level, title, page in doc.get_toc():
        if not 1 <= page <= len(doc):
            errors.append({'bookmark': title, 'error': 'invalid target'})
    font_files = {}
    for xref in {f[0] for page in doc for f in page.get_fonts()}:
        name, ext, kind, data = doc.extract_font(xref)
        if data:
            font_files[name] = {'format': ext, 'bytes': len(data)}
    coverage = json.loads((ROOT/'docs/font-coverage.json').read_text())
    if coverage['unsupported']:
        errors.append({'error': 'unsupported characters', 'characters': coverage['unsupported']})
    if args.render:
        for start in range(1, len(doc)+1, 2):
            files = [render_dir/f'page-{n:03d}.png' for n in range(start,min(start+2,len(doc)+1))]
            imgs = [Image.open(f).convert('RGB') for f in files]
            canvas = Image.new('RGB',(sum(x.width for x in imgs)+24*(len(imgs)+1),max(x.height for x in imgs)+56),'#dadada')
            x=24
            draw=ImageDraw.Draw(canvas)
            for n,img in enumerate(imgs,start):
                canvas.paste(img,(x,32));draw.text((x,12),f'PDF PAGE {n}',fill='black');x+=img.width+24
            canvas.save(render_dir/f'pair-{start:03d}-{start+len(imgs)-1:03d}.jpg',quality=89)
    result = {'checked_at':'2026-11-13','filename':PDF.name,'sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),
              'pages':len(doc),'bookmarks':len(doc.get_toc()),'internal_links':internal,'external_links':external,
              'fonts_used':sorted(fonts_used),'embedded_fonts':font_files,'font_coverage':coverage,
              'all_pages_rendered':bool(args.render),'errors':errors,'pages_detail':page_records,
              'scope':'Automated structure, links, extracted text bounds and font checks. Human per-page layout review is recorded separately.'}
    (ROOT/'docs/pdf-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'pages_detail'},ensure_ascii=False))
    raise SystemExit(bool(errors))

if __name__ == '__main__':
    main()
