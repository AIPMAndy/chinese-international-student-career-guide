#!/usr/bin/env python3
"""Read the public deployment and compare each released file with local dist/."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('--base-url',required=True)
ap.add_argument('--output',default=str(ROOT/'docs/live-http-validation.json'))
args=ap.parse_args()
base=args.base_url.rstrip('/')+'/'
def check(path):
    rel=path.relative_to(ROOT/'dist').as_posix()
    url=base+rel
    try:
        with tempfile.TemporaryDirectory(prefix='student-career-check-') as folder:
            output=Path(folder)/'response'
            request=subprocess.run(['curl','--silent','--show-error','--location','--max-time','15','--fail-with-body',
                                    '--output',str(output),'--write-out','%{response_code}\n%{url_effective}\n%{content_type}',url],
                                   capture_output=True,text=True,timeout=20)
            if request.returncode:
                return {'path':rel,'error':request.stderr.strip() or 'HTTP request failed','response':request.stdout}
            status,final_url,content_type=request.stdout.split('\n',2)
            data=output.read_bytes()
            expected=hashlib.sha256(path.read_bytes()).hexdigest()
            actual=hashlib.sha256(data).hexdigest()
            return {'path':rel,'status':int(status),'final_url':final_url,
                    'content_type':content_type,'bytes':len(data),
                    'sha256':actual,'matches_local':actual==expected}
    except Exception as e:return {'path':rel,'error':str(e)}
paths=sorted(p for p in (ROOT/'dist').rglob('*') if p.is_file())
results=[]
with ThreadPoolExecutor(max_workers=4) as pool:
    futures=[pool.submit(check,p) for p in paths]
    for future in as_completed(futures):
        results.append(future.result())
        if len(results)%10==0:print(json.dumps({'checked':len(results),'total':len(paths)}),flush=True)
results.sort(key=lambda x:x['path'])
errors=[x for x in results if x.get('status')!=200 or not x.get('matches_local')]
record={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'base_url':base,
        'authentication':'None; public GET requests with no cookies or credentials',
        'files_checked':len(results),'errors':errors,'results':results}
Path(args.output).parent.mkdir(parents=True,exist_ok=True)
Path(args.output).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='results'},ensure_ascii=False))
raise SystemExit(bool(errors))
