#!/usr/bin/env python3
"""Build the complete, dependency-free static Chinese career guide website.

Usage: python3 scripts/build_site.py [--base-url URL] [--repo-url VERIFIED_URL]
Markdown sources remain authoritative. No external assets or network calls.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
VERSION = '2026-11-13'
TITLE = '中国留学生求职全局保姆级攻略'
E = html.escape


def slug(text):
    return re.sub(r'[^\w\u3400-\u9fff-]+', '-', text.lower()).strip('-') or 'section'


def title_of(text, fallback):
    m = re.search(r'^#\s+(.+)$', text, re.M)
    return m.group(1).strip() if m else fallback


def plain(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    return re.sub(r'[#*`_>\[\]]', '', text).strip()


def safe_url(url):
    url = html.unescape(url).strip()
    return url if not re.match(r'(?i)\s*(javascript|data|vbscript):', url) else '#'


def inline(text, resolve=lambda u: u):
    tokens = []
    def hold(s):
        tokens.append(s)
        return '\x00%d\x00' % (len(tokens)-1)
    text = re.sub(r'`([^`]+)`', lambda m: hold('<code>'+E(m.group(1))+'</code>'), text)
    text = re.sub(r'\[([^\]]+)\]\(([^\s)]+)(?:\s+"[^"]*")?\)', lambda m: hold('<a href="'+E(safe_url(resolve(m.group(2))),quote=True)+'">'+E(m.group(1))+'</a>'), text)
    text = re.sub(r'https?://[^\s<>\x00]+', lambda m: hold('<a href="'+E(m.group(0).rstrip('。，；、）)'),quote=True)+'">'+E(m.group(0).rstrip('。，；、）)'))+'</a>'+E(m.group(0)[len(m.group(0).rstrip('。，；、）)')):])), text)
    text = E(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    for i,t in enumerate(tokens): text = text.replace('\x00%d\x00'%i,t)
    return text


def markdown(text, resolve=lambda u:u, skip_title=True):
    lines=text.replace('\r\n','\n').split('\n');out=[];headings=[];used={};i=0
    def cells(line): return [x.strip() for x in line.strip().strip('|').split('|')]
    def heading_id(t):
        s=slug(plain(t));used[s]=used.get(s,0)+1
        return s if used[s]==1 else f'{s}-{used[s]}'
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1;continue
        if line.startswith('```'):
            lang=line[3:].strip();body=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):body.append(lines[i]);i+=1
            out.append('<pre><code'+(' class="language-'+E(lang,quote=True)+'"' if lang else '')+'>'+E('\n'.join(body))+'</code></pre>');i+=1;continue
        h=re.match(r'^(#{1,6})\s+(.+)$',line)
        if h:
            level=len(h.group(1));t=h.group(2).strip();hid=heading_id(t)
            if not (skip_title and level==1):
                out.append(f'<h{level} id="{E(hid,quote=True)}">{inline(t,resolve)}</h{level}>')
                if level in (2,3):headings.append((level,t,hid))
            i+=1;continue
        if i+1<len(lines) and '|' in line and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):
            header=cells(line);rows=[];i+=2
            while i<len(lines) and '|' in lines[i] and lines[i].strip():rows.append(cells(lines[i]));i+=1
            body='<table><thead><tr>'+''.join('<th scope="col">'+inline(x,resolve)+'</th>' for x in header)+'</tr></thead><tbody>'
            for row in rows:
                row=(row+['']*len(header))[:len(header)];body+='<tr>'+''.join('<td>'+inline(x,resolve)+'</td>' for x in row)+'</tr>'
            out.append('<div class="table-scroll" role="region" aria-label="可横向滚动的表格" tabindex="0">'+body+'</tbody></table></div>');continue
        if re.match(r'^\s*([-*_])(?:\s*\1){2,}\s*$',line):out.append('<hr>');i+=1;continue
        if re.match(r'^\s*>',line):
            quote=[]
            while i<len(lines) and re.match(r'^\s*>',lines[i]):quote.append(re.sub(r'^\s*>\s?','',lines[i]));i+=1
            rendered,_=markdown('\n'.join(quote),resolve,False);out.append('<blockquote>'+rendered+'</blockquote>');continue
        lm=re.match(r'^\s*(?:([-+*])|(\d+)[.)])\s+(.+)$',line)
        if lm:
            ordered=bool(lm.group(2));tag='ol' if ordered else 'ul';items=[]
            while i<len(lines):
                m=re.match(r'^\s*(?:([-+*])|(\d+)[.)])\s+(.+)$',lines[i])
                if not m or bool(m.group(2))!=ordered:break
                item=m.group(3);i+=1
                while i<len(lines) and lines[i].startswith('  ') and lines[i].strip() and not re.match(r'^\s*(?:[-+*]|\d+[.)])\s+',lines[i]):item+=' '+lines[i].strip();i+=1
                check=re.match(r'^\[([ xX])\]\s*(.*)',item)
                if check:items.append('<li class="check-item">'+('☑ ' if check.group(1).strip() else '☐ ')+inline(check.group(2),resolve)+'</li>')
                else:items.append('<li>'+inline(item,resolve)+'</li>')
            out.append('<'+tag+'>'+''.join(items)+'</'+tag+'>');continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip():
            if re.match(r'^(#{1,6}\s|```|\s*>|\s*(?:[-+*]|\d+[.)])\s+)',lines[i]):break
            if i+1<len(lines) and '|' in lines[i] and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):break
            para.append(lines[i]);i+=1
        out.append('<p>'+'<br>'.join(inline(x.strip(),resolve) for x in para)+'</p>')
    return '\n'.join(out),headings


def read_json_lists(pattern):
    result=[]
    for file in sorted((ROOT/'data').glob(pattern)):
        try:
            data=json.loads(file.read_text('utf-8'))
            if isinstance(data,list):result.extend(data)
            elif isinstance(data,dict):result.extend(data.get('sources',data.get('regions',[])))
        except (ValueError,OSError):pass
    return result


def build(base_url='',repo_url=''):
    OUT.mkdir(exist_ok=True);(OUT/'assets').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'website/style.css',OUT/'assets/style.css');shutil.copyfile(ROOT/'website/app.js',OUT/'assets/app.js')
    shutil.copytree(ROOT/'templates',OUT/'templates',dirs_exist_ok=True)
    if (ROOT/'downloads').exists():shutil.copytree(ROOT/'downloads',OUT/'downloads',dirs_exist_ok=True)
    pages=[]
    for kind,folder,prefix in [('core',ROOT/'content/core','guide'),('region',ROOT/'content/regions','region'),('template',ROOT/'templates','template')]:
        for file in sorted(folder.glob('*.md')):
            text=file.read_text('utf-8');pages.append({'kind':kind,'file':file,'text':text,'title':title_of(text,file.stem),'url':prefix+'-'+file.stem.lower()+'.html'})
    pathmap={p['file'].resolve():p['url'] for p in pages};core=[p for p in pages if p['kind']=='core'];regions=[p for p in pages if p['kind']=='region'];templatepages=[p for p in pages if p['kind']=='template']
    allcov=read_json_lists('coverage-*.json');cov_by_id={c.get('id'):c for c in allcov}
    for c in allcov:
        if not c.get('file'):continue
        candidate=(ROOT/'content/regions'/c['file']).resolve()
        if candidate in pathmap and not any(p['file'].resolve()==candidate for p in regions):
            source_page=next(p for p in pages if p['file'].resolve()==candidate)
            regions.append({**source_page,'id':c.get('id',candidate.stem),'title':c.get('name',source_page['title'])})
    fallback_groups={'us':'北美','ca':'北美','uk':'欧洲','ie':'欧洲','de':'欧洲','fr':'欧洲','nl':'欧洲','se':'欧洲','fi':'欧洲','ch':'欧洲','au':'大洋洲','nz':'大洋洲','cn':'回国','china':'回国','return-china':'回国'}
    for p in regions:
        id=p.get('id',p['file'].stem);c=cov_by_id.get(id,{})
        # Honour the actual file field if the coverage id and file basename differ.
        if not c:c=next((x for x in allcov if Path(x.get('file') or '').stem==id),{})
        m=re.search(r'状态[：:]\s*([^。\n]+)',p['text']);status=c.get('status',m.group(1).strip() if m else '正文标注为准')
        p.update(id=id,group=c.get('group',fallback_groups.get(id,'亚洲')),status=status,verified=c.get('verified',[]),gaps=c.get('gaps',[]),has_article=True)
    region_article_count=len(regions)
    known_ids={p['id'] for p in regions}
    for c in allcov:
        if not c.get('id') or c['id'] in known_ids:continue
        # A gap entry has no invented country page or transferred policy rules.
        regions.append({'id':c['id'],'title':c.get('name',c['id']),'group':c.get('group','待分类'),'status':c.get('status','待补充'),'verified':c.get('verified',[]),'gaps':c.get('gaps',[]),'has_article':False,'url':'coverage.html#'+slug(c['id'])})
        known_ids.add(c['id'])
    pending_navigation_count=len(regions)-region_article_count
    sources=read_json_lists('sources-*.json');seen=set();sources=[s for s in sources if s.get('id') and not (s['id'] in seen or seen.add(s['id']))]
    verified=sum('已核验' in p['status'] for p in regions)
    def resolve_for(page):
        def resolve(url):
            if re.match(r'^(?:https?:|mailto:|tel:|#)',url):return url
            u,sep,fragment=url.partition('#');target=(page['file'].parent/u).resolve()
            if target in pathmap:return pathmap[target]+('#'+fragment if sep else '')
            try:return str(target.relative_to(ROOT)).replace('\\','/')+('#'+fragment if sep else '')
            except ValueError:return url
        return resolve
    def dl(filename,label,cls='button'):
        return f'<a class="{cls}" href="downloads/{E(filename,quote=True)}" download>{E(label)} <span aria-hidden="true">↓</span></a>' if (OUT/'downloads'/filename).exists() else '<span class="pending-download">文件正在制作，完成后开放下载</span>'
    def header():
        return '<a class="skip" href="#main">跳转到正文</a><header class="topbar"><div class="topbar-inner"><a class="brand" href="index.html"><span class="brandmark" aria-hidden="true">A</span><span><strong>AI 酋长 Andy</strong><small>GLOBAL CAREER FIELD GUIDE</small></span></a><button class="menu" data-menu aria-expanded="false" aria-controls="main-nav">导航</button><nav class="nav" id="main-nav" aria-label="主导航"><a href="index.html#start">从这里开始</a><a href="contents.html">完整攻略</a><a href="index.html#regions">地区导航</a><a href="downloads.html">免费资源</a><a href="sources.html">来源与核验</a></nav></div></header>'
    def footer():
        repo=f'<a href="{E(repo_url,quote=True)}">GitHub 开源仓库</a>' if repo_url else '<span>GitHub 发布状态见交付说明</span>'
        return '<footer class="footer"><div>© 2026 AI 酋长 Andy · '+VERSION+'</div><div class="footer-links"><a href="coverage.html">覆盖范围与缺口</a><a href="downloads.html">源文件与模板</a>'+repo+'<a href="https://metaver.vip/services">咨询与陪跑</a><a href="https://metaver.vip/">个人官网</a><a href="https://www.a6no1.cn/">公司官网</a><a href="index.html#about">关于作者</a></div></footer>'
    def save(url,title,body,description='',article=False):
        # SEO and JSON-LD are derived from the same source as the rendered page.
        description = description or '面向中国留学生的跨地区求职路线、招聘窗口、资格核验、申请材料与可编辑模板。'
        site_root = base_url.rstrip('/') + '/' if base_url else ''
        public_url = site_root + ('' if url == 'index.html' else url) if site_root else ''
        page_title = title + ' | AI 酋长 Andy'
        canonical = '<link rel="canonical" href="' + E(public_url, quote=True) + '">' if public_url else ''
        social = ''
        structured = ''
        if public_url:
            social = (
                '<meta property="og:type" content="' + ('article' if article else 'website') + '">'
                '<meta property="og:site_name" content="' + E(TITLE, quote=True) + '">'
                '<meta property="og:locale" content="zh_CN">'
                '<meta property="og:title" content="' + E(page_title, quote=True) + '">'
                '<meta property="og:description" content="' + E(description, quote=True) + '">'
                '<meta property="og:url" content="' + E(public_url, quote=True) + '">'
                '<meta name="twitter:card" content="summary">'
            )
            schema = {
                '@context': 'https://schema.org',
                '@type': 'WebPage',
                'name': title,
                'description': description,
                'url': public_url,
                'inLanguage': 'zh-CN',
                'dateModified': VERSION,
                'isPartOf': {'@type': 'WebSite', 'name': TITLE, 'url': site_root},
                'author': {'@type': 'Person', 'name': 'AI 酋长 Andy', 'url': 'https://metaver.vip/'},
                'publisher': {'@type': 'Organization', 'name': '星觉科技', 'url': 'https://www.a6no1.cn/'}
            }
            structured = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>'
        doc = (
            '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="theme-color" content="#fbfbf8">'
            '<title>' + E(page_title) + '</title>'
            '<meta name="description" content="' + E(description, quote=True) + '">'
            + canonical + social + structured +
            '<link rel="stylesheet" href="assets/style.css">'
            '<script src="assets/app.js" defer></script></head><body>'
            + header() + '<main id="main">' + body + '</main>' + footer() + '</body></html>'
        )
        (OUT/url).write_text(doc, 'utf-8')
    def heading(title,sub,kicker='FIELD GUIDE'):
        return '<div class="page-heading"><div class="breadcrumb"><a href="index.html">首页</a> / '+E(title)+'</div><div class="kicker">'+E(kicker)+'</div><h1>'+E(title)+'</h1><p>'+sub+'</p></div>'
    def list_chapters(items):
        return '<div class="chapter-list">'+''.join('<a class="chapter-item" href="'+p['url']+'"><span>'+f'{i+1:02}'+'</span><strong>'+E(p['title'])+'</strong><i aria-hidden="true">↗</i></a>' for i,p in enumerate(items))+'</div>'
    def consult():
        return '<div class="consult-inline"><strong>需要结合个人情况判断？</strong><p>先完成路线决策表，带上目标地区、毕业日期和两个真实岗位，再联系微信 <b>AIPMAndy</b>。免费内容完整开放。咨询不承诺录用、薪资或身份资格。</p></div>'
    def region_markup():
        groups=defaultdict(list)
        for p in regions:groups[p['group']].append(p)
        body=''
        for group in ['北美','欧洲','亚洲','大洋洲','回国']+sorted(set(groups)-{'北美','欧洲','亚洲','大洋洲','回国'}):
            if not groups[group]:continue
            body+='<section class="region-group"><h3>'+E(group)+'</h3><div class="region-grid">'
            for p in groups[group]:
                status='verified' if '已核验' in p['status'] else 'pending';desc='；'.join(p['verified'][:2]) if isinstance(p['verified'],list) and p['verified'] else ('尚未核验。查看待核验项目与补充方法；不能套用邻国规则。' if not p['has_article'] else '工作资格、招聘入口、申请材料与本周行动。具体适用条件及缺口见正文。')
                body+='<a class="region-card" data-region data-group="'+E(group,quote=True)+'" data-status="'+status+'" data-search="'+E(p['title']+' '+p['id']+' '+group+' '+desc,quote=True)+'" href="'+p['url']+'"><div class="region-title"><h4>'+E(p['title'])+'</h4><span class="code">'+E(p['id'])+'</span></div><p>'+E(desc)+'</p><span class="badge '+('pending' if status=='pending' else '')+'">'+E(p['status'])+'</span></a>'
            body+='</div></section>'
        return body
    stage_defs=[
      ('studying','01','在读','尽早认识岗位，安排实习与证据积累。',[
       ('先建立事实卡','分别记下课程结束、学位授予、当前身份条件和可用时间。未知项写明由谁确认。','00-start'),
       ('选一条主路线和备用路线','把留当地、第三地与回国放到同一张表，比较资格、岗位窗口、时间和预算。','01-routes'),
       ('用好学校与校友资源','查本校 Career Service、招聘活动、校友入口与实习要求；用一个具体问题开始联系。','05-resources')]),
      ('graduating','02','毕业前','把招聘窗口、毕业材料和到岗时间对齐。',[
       ('把硬截止放进日历','学校、身份和雇主的日期分开记录。按最早截止日倒排，不用统一月份替代真实公告。','02-calendar'),
       ('逐条读岗位资格','核对毕业日期、当前工作资格、未来担保、地点和到岗条件。未说明的项目仍是未知。','03-eligibility'),
       ('提交可追溯的材料','围绕真实岗位准备中英文材料、保存版本与回执，并安排下一次跟进。','06-materials')]),
      ('graduated','03','毕业后','核对剩余时间，处理空档与路径切换。',[
       ('重新检查当前条件','先确认当前停留与工作条件、预算、离境安排和可接受的求职期限。','01-routes'),
       ('找出申请真正卡在哪里','把资格、没有回复、面试表现和Offer条件分开记录。只凭已有证据判断下一步。','07-application'),
       ('把真实经历整理成可用证据','没有当地实习时，明确课程、研究、个人项目的真实性质和本人贡献。','06-materials')]),
      ('returned','04','回国 / 准备回国','衔接校招社招、学历材料和跨境面试。',[
       ('先查目标雇主的毕业范围','分别核对校招与社招入口、海外毕业日期定义、到岗条件和所需材料。','03-eligibility'),
       ('把回国节点放进同一张表','返程、学校文件、认证要求、面试时区与最早入职日一起安排。','02-calendar'),
       ('按回国路径继续执行','核对官方材料入口和雇主本轮要求，保留来源与核验日期。','return')])]
    def pick(key):
        if key=='return':return next((p for p in pages if '回国' in p['title']),core[0] if core else None)
        return next((p for p in core if p['file'].stem==key),core[0] if core else None)
    stages=''.join('<a class="stage-card" href="stage-'+id+'.html"><span class="number">'+num+'</span><span class="arrow" aria-hidden="true">↗</span><h3>'+name+'</h3><p>'+desc+'</p></a>' for id,num,name,desc,steps in stage_defs)
    for id,num,name,desc,steps in stage_defs:
        body='<div class="wrap">'+heading(name,desc,'START / '+num)+'<div class="stage-body">'
        for i,(t,desc,key) in enumerate(steps):
            target=pick(key);body+='<section class="step"><span class="step-number">'+f'{i+1:02}'+'</span><div><h2>'+t+'</h2><p>'+desc+'</p>'+('<a href="'+target['url']+'">阅读对应步骤 →</a>' if target else '<a href="contents.html">查看已完成章节 →</a>')+'</div></section>'
        body+='<div class="actions"><a class="button dark" href="downloads.html">打开可编辑模板</a><a class="button soft" href="index.html#regions">选择目标地区</a></div>'+consult()+'</div></div>';save('stage-'+id+'.html',name+'起步入口',body)
    downloads_cards='<div class="downloads-grid"><div class="download-card"><span class="format">PDF / 完整读本</span><h3>带着走的求职攻略</h3><p>适合阅读和打印。包含地区导航、行动表、来源与版本日期。</p>'+dl('chinese-international-student-career-guide.pdf','免费下载 PDF')+'</div><div class="download-card"><span class="format">XLSX + CSV + MD</span><h3>可以直接填写的工具</h3><p>路线、日历、资格、材料、联系、申请、面试和Offer，配中英文文字模板。</p><a class="button" href="templates/career-workbook.xlsx" download>下载工作簿 <span aria-hidden="true">↓</span></a></div><div class="download-card"><span class="format">OPEN SOURCE</span><h3>模板包与全部源文件</h3><p>正文与生成源可编辑。免费资源完整开放，无需先加微信。</p><a class="button" href="downloads.html">查看全部文件 <span aria-hidden="true">↗</span></a></div></div>'
    home='<div class="wrap"><section class="hero"><div><div class="eyebrow"><span>中国留学生求职</span><span>2026.11 / V1.0</span></div><h1><span>去哪就业，</span><span>怎么走这一步。</span></h1><p class="intro">'+TITLE+'。从在读到回国，把跨地区路线、招聘窗口、工作资格和每周行动，整理成一套能照着做的步骤。</p><div class="actions"><a class="button dark" href="#start">从我的阶段开始 <span aria-hidden="true">↗</span></a><a class="button soft" href="downloads.html">下载完整资料</a></div><p class="smallnote">作者 AI 酋长 Andy · 免费开放 · 核验日期 '+VERSION+'</p></div><aside class="hero-aside"><div class="kicker">先把三个问题说清</div><h2>我能在哪里工作？<br>哪一轮招聘接受我？<br>最晚什么时候行动？</h2><div class="factrow"><span>地区路线页（含回国）</span><strong>'+str(region_article_count)+'</strong></div><div class="factrow"><span>待补充地区导航</span><strong>'+str(pending_navigation_count)+'</strong></div><div class="factrow"><span>通用实操章节</span><strong>'+str(len(core))+'</strong></div><div class="factrow"><span>可填写工具类别</span><strong>8</strong></div><p>每个地区独立核验。导航数量不代表完整覆盖所有国家，也不代表个人资格已经确认。</p></aside></section><section class="section" id="start"><div class="section-heading"><div><div class="kicker">01 / FIND YOUR START</div><h2>从你现在的位置开始</h2></div><p>先处理当前阶段最紧迫的条件，再进入地区和岗位。四个入口都能直接通向完整步骤。</p></div><div class="stage-grid">'+stages+'</div></section><section class="section" id="guide"><div class="section-heading"><div><div class="kicker">02 / THE WORKING GUIDE</div><h2>从选择路线，到拿到结果</h2></div><a href="contents.html">打开完整目录 →</a></div><div class="two-column">'+list_chapters(core)+'<aside class="quote-panel"><div class="kicker">HOW TO USE</div><h3>每一步，都要留下<br>可以核对的产出。</h3><p>准备什么、具体怎么做、得到什么、如何验收、卡住怎么办，按同一套结构往前走。</p><ol class="plain-list"><li>选一个阶段入口，完成事实卡。</li><li>选择具体地区，核验身份与窗口。</li><li>下载模板，开始真实投递与复盘。</li></ol><p>本册负责通用路线。专业能力训练另设专题，地址确认存在后再接入。</p></aside></div></section><section class="section" id="regions"><div class="section-heading"><div><div class="kicker">03 / CHOOSE A REGION</div><h2>每个地区，分别判断</h2></div><p>覆盖北美、欧洲、亚洲、大洋洲的部分国家与地区及回国。非洲、南美洲不在本册范围。</p></div><div class="filters"><label class="search-field"><span class="hidden">搜索国家或地区</span><input type="search" data-region-query placeholder="搜索国家、地区或关键词" aria-label="搜索国家或地区"></label><select data-region-group aria-label="按大区筛选"><option value="">所有大区</option>'+''.join('<option>'+E(g)+'</option>' for g in ['北美','欧洲','亚洲','大洋洲','回国'])+'</select><select data-region-status aria-label="按核验状态筛选"><option value="">全部核验状态</option><option value="verified">已核验基础路径</option><option value="pending">待补充或部分核验</option></select></div><div class="region-count" data-region-count>当前显示 '+str(len(regions))+' 个国家或地区。</div>'+region_markup()+'<p class="empty-filter" data-region-empty hidden>没有符合筛选条件的地区。可以清空关键词，或查看覆盖缺口。</p><div class="coverage-note">“已核验基础路径”仅说明本版核对了所列官方资料。学校流程、雇主要求和个人资格仍需分别确认。<a href="coverage.html">查看具体覆盖缺口 →</a></div></section><section class="section" id="downloads"><div class="section-heading"><div><div class="kicker">04 / TAKE IT WITH YOU</div><h2>完整资料，免费带走</h2></div><a href="downloads.html">全部下载与源文件 →</a></div>'+downloads_cards+'</section><section class="section" id="about"><div class="about"><div><div class="kicker">ABOUT THE AUTHOR</div><h2>AI 酋长 Andy</h2><p>前腾讯、百度 AI 产品专家，前大模型公司 VP。提供求职咨询、求职陪跑和 AI 相关服务。上述背景由作者提供。</p><p>需要个人路线诊断时，先整理毕业日期、当前条件、目标地区和两条真实岗位。咨询从具体问题开始，不承诺录用、薪资或身份资格。</p></div><div class="contact"><div class="contact-line"><span>微信</span><strong>AIPMAndy</strong><button data-copy-wechat type="button">复制</button></div><div class="contact-line"><span>公众号</span><strong>AI酋长Andy</strong></div><div class="contact-links"><a href="https://metaver.vip/">个人官网 ↗</a><a href="https://www.a6no1.cn/">公司官网 ↗</a></div><p>免费内容完整开放，无需购买服务。公开版本不使用未经核实和授权的学校、客户、Offer、薪资或成功率案例。</p><div class="copy-status" data-copy-status aria-live="polite"></div></div></div></section></div>'
    save('index.html',TITLE,home)
    for page in pages:
        rendered,headings=markdown(page['text'],resolve_for(page));kindlabel={'core':'通用实操','region':'地区攻略','template':'可编辑模板'}[page['kind']]
        sidebar='<aside class="reader-nav" aria-label="章节导航"><h2>阅读导航</h2><details data-reader-menu><summary>打开章节导航</summary>'+''.join('<a class="'+('current' if p['url']==page['url'] else '')+'" href="'+p['url']+'">'+E(p['title'])+'</a>' for p in core)+'<div class="divider"></div><a href="index.html#regions">选择国家或地区</a><a href="downloads.html">下载 PDF 与模板</a><a href="sources.html">官方来源与核验</a><a href="coverage.html">覆盖缺口</a></details></aside>'
        toc='<details class="toc" open><summary>本页目录</summary><ol>'+''.join('<li><a href="#'+E(hid,quote=True)+'">'+E(plain(t))+'</a></li>' for level,t,hid in headings if level==2)+'</ol></details>' if headings else ''
        subtitle='适用条件、核验深度和待补充内容以本页正文为准。' if page['kind']=='region' else '按准备、行动、产出、验收和受阻处理，把判断转成具体动作。'
        meta='<div class="article-meta"><span>'+kindlabel+'</span><span>版本 '+VERSION+'</span><span>作者 AI 酋长 Andy</span><button class="print-link" data-print>打印本页</button></div>'
        i=core.index(page) if page in core else -1
        prev='<a href="'+core[i-1]['url']+'">← '+E(core[i-1]['title'])+'</a>' if i>0 else '<a href="contents.html">← 返回完整目录</a>'
        nex='<a href="'+core[i+1]['url']+'">'+E(core[i+1]['title'])+' →</a>' if 0<=i<len(core)-1 else '<a href="downloads.html">下载工具 →</a>'
        body='<div class="wrap">'+heading(page['title'],subtitle,kindlabel)+'<div class="reader-layout">'+sidebar+'<article class="article">'+meta+toc+rendered+'<div class="article-bottom">'+prev+nex+'</div>'+consult()+'</article></div></div>'
        save(page['url'],page['title'],body,article=True)
    body='<div class="wrap">'+heading('完整攻略目录','通用章节按顺序阅读。地区页按你的目标地点进入；模板可以直接下载填写。','CONTENTS')+'<section class="section">'+list_chapters(core)+'</section><section class="section"><div class="section-heading"><h2>国家与地区</h2></div>'+region_markup()+'</section><section class="section"><div class="section-heading"><h2>工具与文字模板</h2></div>'+list_chapters(templatepages)+'</section></div>';save('contents.html','完整攻略目录',body)
    resources=[]
    for f in sorted((ROOT/'templates').iterdir()):
        if not f.is_file():continue
        page=pathmap.get(f.resolve());label=next((t['title'] for t in templatepages if t['file']==f),f.name)
        resources.append('<div class="resource-item"><div><strong>'+E(label)+'</strong><small>'+E(f.name)+'</small></div><div>'+('<a href="'+page+'">在线阅读</a> · ' if page else '')+'<a href="templates/'+E(f.name,quote=True)+'" download>下载</a></div></div>')
    body='<div class="wrap">'+heading('免费资源与下载','下载后保留私人副本，再填写自己的求职信息。工作簿带公式与下拉，CSV 和 Markdown 便于迁移和编辑。','DOWNLOADS')+'<section class="section">'+downloads_cards+'<div class="actions" style="margin-top:28px">'+dl('editable-templates.zip','下载完整模板包','button dark')+dl('source-code.zip','下载项目源文件','button soft')+'</div></section><section class="section"><div class="section-heading"><h2>单独下载每个工具</h2></div><div class="resource-list">'+''.join(resources)+'</div><p class="source-note">CSV 不保留公式、下拉和格式；请用工作簿计算，或自行建立公式。公开模板为空白，个人证件、合同与他人联系方式不应上传到公共仓库。</p></section></div>';save('downloads.html','免费资源与下载',body)
    body='<div class="wrap">'+heading('来源与核验记录','优先政府、学校与雇主官方页面。来源条目说明它支持什么；页面可访问不等于个人符合资格。申请前应再次核对现行条件。','SOURCES')+'<div class="sources-list">'
    for s in sources:
        supports=s.get('supports','');supports='；'.join(supports) if isinstance(supports,list) else str(supports);url=s.get('url','');notes=s.get('notes','');notes='；'.join(notes) if isinstance(notes,list) else str(notes)
        body+='<article class="source-card" id="'+E(str(s['id']),quote=True)+'"><span class="source-id">'+E(str(s['id']))+' · '+E(str(s.get('region','')))+'</span><h2>'+E(s.get('title','官方来源'))+'</h2><p>发布机构：'+E(str(s.get('publisher','详见官方页面')))+'<br>核验日期：'+E(str(s.get('checked_at',VERSION)))+' · 状态：'+E(str(s.get('status','以核验备注为准')))+'</p><p>'+E(supports)+'</p>'+('<p>'+E(notes)+'</p>' if notes else '')+'<a href="'+E(safe_url(url),quote=True)+'">打开官方原文 ↗</a><span class="source-domain">'+E(urlsplit(url).netloc)+'</span></article>'
    body+='</div></div>';save('sources.html','来源与核验记录',body)
    body='<div class="wrap">'+heading('覆盖范围与缺口','本版提供部分国家与地区的基础路线，未声称覆盖所有国家、学校或雇主。非洲、南美洲不在本项目范围。','COVERAGE')+'<section class="section"><div class="article"><p>已建立 '+str(region_article_count)+' 个地区路线页（含回国），其中 '+str(verified)+' 页标注为已核验基础路径；另有 '+str(pending_navigation_count)+' 个地区仅建立缺口导航，尚未核验当地规则。这个标签不等于完整政策审查或个人资格确认。来源、适用条件和核验日期应一起阅读。</p><div class="table-scroll" role="region" aria-label="地区覆盖与缺口" tabindex="0"><table><thead><tr><th>地区</th><th>本版状态</th><th>已核验范围</th><th>待补充或另查</th></tr></thead><tbody>'
    for p in regions:
        verified_text='；'.join(p['verified']) if isinstance(p['verified'],list) else str(p['verified']);gaps='；'.join(p['gaps']) if isinstance(p['gaps'],list) else str(p['gaps'])
        body+='<tr id="'+E(slug(p['id']),quote=True)+'"><td><a href="'+p['url']+'">'+E(p['title'])+'</a></td><td>'+E(p['status'])+'</td><td>'+E(verified_text or ('见地区正文与对应来源' if p['has_article'] else '尚未核验'))+'</td><td>'+E(gaps or '具体学校流程、雇主岗位、个人身份条件需再次核验')+'</td></tr>'
    body+='</tbody></table></div><h2>其他国家与地区怎么处理</h2><p>未列地区保持待补充。先确定主管机关、学校国际学生办公室和雇主招聘原文，再套用本册的核验流程。不能把同一洲、同一种语言或相邻地区视为同一套规则。</p><h2>来源失效或规则变化时</h2><p>保留原来源和旧核验日期，记录新页面、新适用条件与生效日期。无法确认的内容改为待核验，不继续沿用旧结论。招聘窗口必须对应具体雇主和当轮岗位。</p></div></section></div>';save('coverage.html','覆盖范围与缺口',body)
    # A static machine-readable manifest for offline validation and future maintenance.
    manifest={'version':VERSION,'title':TITLE,'core_pages':len(core),'region_pages':region_article_count,'region_navigation_count':len(regions),'pending_navigation_count':pending_navigation_count,'template_pages':len(templatepages),'source_count':len(sources),'pages':[{'title':p['title'],'url':p['url'],'kind':p['kind']} for p in pages]}
    (OUT/'site-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n' + ('Sitemap: ' + base_url.rstrip('/') + '/sitemap.xml\n' if base_url else ''),'utf-8')
    if base_url:
        urls=['index.html','contents.html','downloads.html','sources.html','coverage.html']+[p['url'] for p in pages]+['stage-'+s[0]+'.html' for s in stage_defs]
        sitemap='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+E(base_url.rstrip('/')+'/' + ('' if u == 'index.html' else u))+'</loc><lastmod>'+VERSION+'</lastmod></url>' for u in urls)+'</urlset>'
        (OUT/'sitemap.xml').write_text(sitemap,'utf-8')
    print(json.dumps(manifest,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='');parser.add_argument('--repo-url',default='');args=parser.parse_args();build(args.base_url,args.repo_url)
