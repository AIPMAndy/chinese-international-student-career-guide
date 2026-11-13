#!/usr/bin/env python3
"""Build the complete monochrome handbook from the authoritative Markdown files.

No network is used. Reuses included subset fonts. To regenerate the font subset
after introducing new characters, pass --font-source /path/NotoSansSC-VF.ttf.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak, CondPageBreak, Table, TableStyle, KeepTogether, Flowable
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
DATE = '2026-11-13'
SITE = 'https://aipmandy.github.io/chinese-international-student-career-guide'
TITLE = '中国留学生求职全局保姆级攻略'
W, H = A4
M = 48
WIDTH = W - 2*M
INK = colors.HexColor('#141414')
GRAY = colors.HexColor('#696969')
LIGHT = colors.HexColor('#efefec')
RULE = colors.HexColor('#d0d0cc')
R, B = 'AndyCareer', 'AndyCareerBold'

def normalize(text):
    return text.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')

def lists(pattern):
    all_items=[]
    for file in sorted((ROOT/'data').glob(pattern)):
        obj=json.loads(file.read_text('utf-8'))
        if isinstance(obj,list):all_items.extend(obj)
    return all_items

def fonts(source):
    from fontTools.ttLib import TTFont as FTFont
    dest=ROOT/'assets/fonts';dest.mkdir(parents=True,exist_ok=True)
    paths=[dest/'AndyCareerSans-Regular.ttf',dest/'AndyCareerSans-Bold.ttf']
    corpus=normalize(Path(__file__).read_text('utf-8'))
    for folder in ['content','data','templates']:
        for p in (ROOT/folder).rglob('*'):
            if p.suffix in ['.md','.json','.csv']:corpus+=normalize(p.read_text('utf-8-sig'))
    chars={ord(c) for c in corpus}|set(range(32,127))
    chars.discard(0);chars.discard(10);chars.discard(13);chars.discard(9)
    if source:
        from fontTools import subset
        from fontTools.varLib.instancer import instantiateVariableFont
        f=FTFont(source)
        available=set(f.getBestCmap())
        options=subset.Options();options.layout_features=['*'];options.name_IDs=['*'];options.name_legacy=True
        sub=subset.Subsetter(options=options);sub.populate(unicodes=chars & available);sub.subset(f)
        for weight,p,label in [(400,paths[0],'Regular'),(700,paths[1],'Bold')]:
            font=instantiateVariableFont(copy.deepcopy(f),{'wght':weight},inplace=True)
            for record in font['name'].names:
                if record.nameID in [1,2,3,4,6,16,17]:
                    val={1:'Andy Career Sans',2:label,3:'AndyCareerSans-'+label,4:'Andy Career Sans '+label,6:'AndyCareerSans-'+label,16:'Andy Career Sans',17:label}[record.nameID]
                    record.string=val.encode(record.getEncoding(),errors='replace')
            font.save(p)
    if not all(p.exists() for p in paths):raise SystemExit('Missing fonts. Supply --font-source NotoSansSC-VF.ttf; see assets/fonts/README.md.')
    cmap=set(FTFont(paths[0]).getBestCmap());missing=chars-cmap
    # Ignore only invisible format controls that are not printed in the PDF.
    missing={c for c in missing if chr(c) not in '\ufeff\u200b\u200d\ufe0f'}
    (ROOT/'docs/font-coverage.json').write_text(json.dumps({'checked_at':DATE,'characters':len(chars),'unsupported':''.join(chr(c) for c in sorted(missing))},ensure_ascii=False,indent=2),'utf-8')
    pdfmetrics.registerFont(TTFont(R,str(paths[0])))
    pdfmetrics.registerFont(TTFont(B,str(paths[1])))
    pdfmetrics.registerFontFamily(R,normal=R,bold=B,italic=R,boldItalic=B)

ST={}
def styles():
    base=dict(fontName=R,fontSize=10.1,leading=16.2,textColor=INK,wordWrap='CJK',spaceAfter=7,allowWidows=0,allowOrphans=0)
    ST['body']=ParagraphStyle('Body',**base)
    ST['small']=ParagraphStyle('Small',parent=ST['body'],fontSize=8.6,leading=13.5,textColor=GRAY,spaceAfter=5)
    ST['h1']=ParagraphStyle('H1',parent=ST['body'],fontName=B,fontSize=24,leading=32,spaceAfter=18,keepWithNext=True)
    ST['h2']=ParagraphStyle('H2',parent=ST['body'],fontName=B,fontSize=12.2,leading=18.5,spaceBefore=11,spaceAfter=6,keepWithNext=True)
    ST['h3']=ParagraphStyle('H3',parent=ST['body'],fontName=B,fontSize=10.7,leading=17,spaceBefore=8,spaceAfter=5,keepWithNext=True)
    ST['table']=ParagraphStyle('TableCell',parent=ST['body'],fontSize=9.1,leading=14.4,spaceAfter=0)
    ST['th']=ParagraphStyle('TableHead',parent=ST['table'],fontName=B,textColor=colors.white)
    ST['quote']=ParagraphStyle('Quote',parent=ST['body'],fontSize=9.1,leading=14.4,leftIndent=9,rightIndent=8,borderColor=RULE,borderWidth=.6,borderPadding=9,backColor=LIGHT,spaceAfter=12)
    ST['bullet']=ParagraphStyle('Bullet',parent=ST['body'],leftIndent=12,firstLineIndent=-12,spaceAfter=6)
    ST['toc']=ParagraphStyle('TOC0',parent=ST['body'],fontSize=9.3,leading=14.5,spaceBefore=0,spaceAfter=3,rightIndent=20)

def inline(text):
    text=normalize(text).strip();tokens=[]
    def hold(s):tokens.append(s);return f'ZZTOKEN{len(tokens)-1}ZZ'
    def link(m):
        label,url=m.group(1),m.group(2)
        if url.startswith('https://') or url.startswith('http://'):
            return hold('<a href="'+html.escape(url,quote=True)+'" color="#313131"><u>'+html.escape(label)+'</u></a>')
        return html.escape(label)
    text=re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',link,text)
    text=re.sub(r'`([^`]+)`',lambda m:hold('<b>'+html.escape(m.group(1))+'</b>'),text)
    text=html.escape(text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',text)
    for i,s in enumerate(tokens):text=text.replace(f'ZZTOKEN{i}ZZ',s)
    return text

def P(text,style='body'):return Paragraph(inline(text),ST[style])

class Kicker(Flowable):
    def __init__(self,text):super().__init__();self.text=text;self.height=30;self.width=WIDTH
    def draw(self):
        c=self.canv;c.setStrokeColor(INK);c.setLineWidth(.7);c.line(0,25,WIDTH,25)
        c.setFont(R,8);c.setFillColor(GRAY);c.drawString(0,11,self.text)

class Cover(Flowable):
    def __init__(self):super().__init__();self.width=WIDTH;self.height=H-110
    def draw(self):
        c=self.canv;c.saveState()
        # Draw in absolute page coordinates for a full-bleed monochrome cover.
        c.resetTransforms();c.setFillColor(INK);c.rect(0,0,W,H,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor('#4c4c4c'));c.setLineWidth(.6)
        for radius in [130,179,228]:c.circle(W-85,H-146,radius,fill=0,stroke=1)
        c.setFillColor(colors.white);c.setFont(B,12);c.drawString(M,H-68,'AI 酋长 Andy')
        c.setFont(R,8.8);c.drawString(M,H-91,'GLOBAL CAREER FIELD GUIDE / 2026.11')
        c.setFont(B,39);c.drawString(M,H-235,'中国留学生')
        c.setFont(B,39);c.drawString(M,H-291,'求职全局')
        c.setFont(R,26);c.drawString(M,H-338,'保姆级攻略')
        c.setStrokeColor(colors.white);c.line(M,H-375,W-M,H-375)
        c.setFont(R,12);c.drawString(M,H-409,'决定去哪就业，走哪条路线，什么时候行动。')
        c.setFillColor(colors.HexColor('#cccccc'));c.setFont(R,10)
        c.drawString(M,H-443,'在读 / 毕业前 / 毕业后 / 回国')
        c.drawString(M,H-467,'北美 · 欧洲 · 亚洲 · 大洋洲 · 回国求职')
        c.setFont(R,9);c.drawString(M,132,'完整中文攻略 · 可编辑模板 · 官方来源 · 可打印行动表')
        c.setFont(R,9);c.drawString(M,108,'微信  AIPMAndy     公众号  AI酋长Andy')
        c.setFont(R,8.5);c.drawString(M,83,'metaver.vip   /   www.a6no1.cn')
        c.drawRightString(W-M,54,'v1.0.0  |  核验日期 '+DATE)
        c.linkURL('https://metaver.vip/',(M,78,M+83,93),relative=0)
        c.linkURL('https://www.a6no1.cn/',(M+97,78,M+214,93),relative=0)
        c.restoreState()

class Book(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=A4,leftMargin=M,rightMargin=M,topMargin=52,bottomMargin=49,title=TITLE,author='AI 酋长 Andy',subject='中国留学生跨地区求职路线与实操手册',pageCompression=1,allowSplitting=1)
        self.current='';self.chapter_pages={}
        f=Frame(M,49,WIDTH,H-101,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates([PageTemplate(id='Book',frames=f,onPageEnd=self.chrome)])
    def beforeDocument(self):self.current='';self.chapter_pages={}
    def chrome(self,c,doc):
        if doc.page==1:return
        c.saveState();c.setFont(R,7.5);c.setFillColor(GRAY)
        c.drawString(M,H-30,'中国留学生求职全局攻略')
        c.drawRightString(W-M,H-30,self.current[:35])
        c.setStrokeColor(RULE);c.setLineWidth(.4);c.line(M,36,W-M,36)
        c.setFont(R,7.5);c.drawString(M,23,'AI 酋长 Andy  /  微信 AIPMAndy  /  '+DATE)
        c.setFont(B,9);c.drawRightString(W-M,22,f'{doc.page:02d}')
        c.restoreState()
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and getattr(f,'_book_key',None):
            text=f.getPlainText();key=f._book_key;self.current=text
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,level=0,closed=False)
            self.notify('TOCEntry',(0,text,self.page,key));self.chapter_pages[key]=self.page

def heading(title,key,label):
    h=P(title,'h1');h._book_key=key
    return [Kicker(label),h]

def table(rows,ratios=None,blank_height=None):
    n=len(rows[0]);ratios=ratios or ({2:[.27,.73],3:[.21,.39,.4],4:[.16,.28,.28,.28]}.get(n,[1/n]*n))
    data=[]
    for i,row in enumerate(rows):
        data.append([P(str(cell),'th' if i==0 else 'table') for cell in row])
    heights=None if not blank_height else [None]+[blank_height]*(len(rows)-1)
    t=Table(data,colWidths=[WIDTH*r for r in ratios],rowHeights=heights,repeatRows=1,hAlign='LEFT')
    cmds=[('BACKGROUND',(0,0),(-1,0),INK),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.4,INK),('LINEBELOW',(0,1),(-1,-1),.4,RULE)]
    for i in range(1,len(rows)):
        if i%2:cmds.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#f5f5f2')))
    t.setStyle(TableStyle(cmds));return t

def markdown(text, region=False):
    original = {}
    if region:
        for key in ['body','bullet','h2','h3']:
            original[key] = ST[key]
            ST[key] = copy.copy(ST[key])
        ST['body'].leading=15.5; ST['body'].spaceAfter=6
        ST['bullet'].leading=15.5; ST['bullet'].spaceAfter=4
        ST['h2'].spaceBefore=8; ST['h2'].spaceAfter=5
        ST['h3'].spaceBefore=7; ST['h3'].spaceAfter=4
    out=[];lines=normalize(text).splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line or line.startswith('# '):i+=1;continue
        if line.startswith('```'):
            b=[];i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'):b.append(lines[i]);i+=1
            out.append(Paragraph(inline('\n'.join(b)).replace('\n','<br/>'),ST['quote']));i+=1;continue
        if line.startswith('## '):out.append(P(line[3:],'h2'));i+=1;continue
        if line.startswith('### '):out.append(P(line[4:],'h3'));i+=1;continue
        if i+1<len(lines) and '|' in line and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):
            cells=lambda s:[c.strip() for c in s.strip().strip('|').split('|')]
            rows=[cells(line)];i+=2
            while i<len(lines) and lines[i].strip() and '|' in lines[i]:
                r=cells(lines[i]);rows.append((r+['']*len(rows[0]))[:len(rows[0])]);i+=1
            out.extend([table(rows),Spacer(1,10)]);continue
        if line.startswith('>'):
            q=[]
            while i<len(lines) and lines[i].strip().startswith('>'):q.append(lines[i].strip()[1:].strip());i+=1
            out.append(P(' '.join(q),'quote'));continue
        m=re.match(r'^(?:[-*+] |(\d+)\. )(.*)',line)
        if m:
            prefix=(m.group(1)+'. ') if m.group(1) else '· '
            out.append(P(prefix+m.group(2),'bullet'));i+=1;continue
        if re.match(r'^[-*_]{3,}$',line):i+=1;continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|>|```|\s*[-*+] |\d+\. )',lines[i]):
            if '|' in lines[i] and i+1<len(lines) and re.match(r'^\s*\|?\s*:?-{3,}',lines[i+1]):break
            para.append(lines[i].strip());i+=1
        out.append(P(' '.join(para)))
    for key, value in original.items():ST[key]=value
    return out

def worksheet(title,key,label,fields,note):
    out=[PageBreak()]+heading(title,key,label)
    out.append(P(note,'small'))
    rows=[['核对字段','填写 / 证据 / 下一步']]+[[x,''] for x in fields]
    out.extend([table(rows,[.3,.7],blank_height=38),Spacer(1,14),P('验收：关键条件有依据；未知项保留待确认；下一步有负责人和日期。完整电子版见可编辑工作簿。','small')])
    return out

def build(output):
    story=[Cover(),PageBreak(),Kicker('READING MAP / 目录'),P('把路线想清，\n把动作做实。','h1'),P('点击目录标题可跳转。各地区独立核验，来源和覆盖缺口请与正文一起使用。','small')]
    toc=TableOfContents();toc.levelStyles=[ST['toc']];toc.dotsMinLevel=0
    story.extend([toc,PageBreak()])
    story+=heading('地区导航与使用边界','region-map','REGION INDEX / 地区导航')
    coverage=lists('coverage-*.json');source=lists('sources-*.json')
    regionids=['us','ca','uk','ie','de','fr','nl','se','fi','ch','hk','mo','tw','jp','kr','sg','my','ae','au','nz']
    cov={c['id']:c for c in coverage}
    rows=[['大区','地区（可点击）','本版核验深度']]
    for group in ['北美','欧洲','亚洲','大洋洲']:
        for rid in regionids:
            c=cov.get(rid,{})
            if c.get('group')!=group:continue
            rows.append([group, c.get('name',rid), c.get('status','见正文')])
    # Actual clickable internal links are set after converting cells.
    rows.append(['回国','回国求职',cov['return-china']['status']])
    nav=table(rows,[.15,.25,.6])
    nav.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    for row,rid in enumerate([r for g in ['北美','欧洲','亚洲','大洋洲'] for r in regionids if cov.get(r,{}).get('group')==g],1):
        nav._cellvalues[row][1]=Paragraph('<a href="#region-'+rid+'"><u>'+html.escape(cov[rid]['name'])+'</u></a>',ST['table'])
    nav._cellvalues[-1][1]=Paragraph('<a href="#core-11-return-china"><u>回国求职</u></a>',ST['table'])
    story.extend([nav,Spacer(1,12),Paragraph('其他国家的待补充清单见<a href="#core-15-coverage-gaps"><u>“覆盖范围与缺口”</u></a>。本册不覆盖非洲、南美洲；不声称覆盖所有国家或个人情形。',ST['small'])])
    for n,p in enumerate(sorted((ROOT/'content/core').glob('*.md')),1):
        text=p.read_text('utf-8');title=re.search(r'^#\s+(.+)$',text,re.M).group(1)
        section_start=[PageBreak()] if n==1 else [CondPageBreak(440),Spacer(1,16)]
        story+=section_start+heading(title,'core-'+p.stem,f'{n:02d} / 通用实操')+markdown(text)
    for rid in regionids:
        p=ROOT/'content/regions'/f'{rid}.md'
        if not p.exists():continue
        text=p.read_text('utf-8');title=re.search(r'^#\s+(.+)$',text,re.M).group(1)
        story+=[PageBreak()]+heading(title,'region-'+rid,'REGION / '+cov.get(rid,{}).get('group','地区'))+markdown(text,region=True)
    story+=worksheet('路线决策表','worksheet-route','ACTION SHEET / 01',['当前学习地与学位','课程完成 / 学位授予日期','现有停留与工作权利','留当地：硬条件 / 来源','第三地：硬条件 / 来源','回国：招聘类别 / 日期','可用预算 / 每月必要支出','主路线 / 备选路线','最迟切换日 / 切换条件','本周三个动作'],'先填事实，再比较偏好。工作资格与申请条件不通过时，不用总分替代。')
    story+=worksheet('时间表','worksheet-calendar','ACTION SHEET / 02',['学业节点 / 来源','身份截止 / 申请地点','工作可开始日期 / 条件','招聘截止 / 时区','评估 / 面试时间','证书 / 认证预计完成日','回国 / 搬迁 / 租约','最早可入职日 / 前提','提醒日 / 负责人','完成凭证 / 下一次复核'],'学业、身份、招聘、生活四类日期分开写。不要把提交申请等同于批准。')
    story+=worksheet('岗位资格检查表','worksheet-eligibility','ACTION SHEET / 03',['公司主体 / 职位编号','岗位链接 / 核验日期','招聘类别 / 工作地点','毕业范围 / 计算依据','当前工作权利 / 证明','未来担保说明 / 来源','必须条件 / 个人证据','偏好条件 / 能力缺口','待问雇主 / 待问学校','决定：投递 / 先问 / 暂缓'],'逐条对照雇主原文。未写担保信息时记未知，不能推断支持。')
    story+=worksheet('申请材料清单','worksheet-materials','ACTION SHEET / 04',['真实经历底稿','中文简历 / 版本','英文简历 / 版本','Cover letter / 动机信','作品链接 / 访问验证','学位 / 成绩材料','推荐人同意 / 联系方式','岗位所需资格材料','中英日期与经历一致','最终文件 / 提交回执'],'只保留申请需要的材料；公开作品脱敏，正式证件不上传公开仓库。')
    story+=worksheet('联系与跟进记录','worksheet-contact','ACTION SHEET / 05',['联系对象 / 合理渠道','共同点 / 联系理由','本次具体问题','对方适合回答的范围','首次联系日期','得到的事实 / 来源','承诺的下一步','跟进日期 / 前提','对方拒绝或停止要求','正式投递编号 / 回执'],'先请求具体信息，再在合适时请求正式推荐；允许对方拒绝。中英邮件在后附文字模板中。')
    story+=worksheet('申请台账与周复盘','worksheet-application','ACTION SHEET / 06',['地区 / 公司 / 职位编号','JD / 资格结论','申请日 / 简历版本','人工回复日','约面日 / 实际面试日','后续推进日','书面Offer日 / 条件','当前状态 / 结束原因','下一动作 / 到期日期','本周假设 / 下周改动'],'每个阶段记录实际发生日期。自动回执不算人工回复，重复岗位不重复计算。')
    story+=worksheet('面试复盘表','worksheet-interview','ACTION SHEET / 07',['岗位 / 面试轮次 / 日期','原问题','我的核心回答','追问与回答','我提供的真实证据','未解释清楚的贡献','能力缺口 / 表达缺口','获得的反馈 / 仍未知','需要澄清的入职条件','下一次只练的一项'],'先记事实，再写判断。没有反馈时保留不确定，不把拒信当成唯一原因证明。')
    story+=worksheet('Offer比较表','worksheet-offer','ACTION SHEET / 08',['主体 / 地点 / 职责','工作资格 / 担保安排','入职日 / 录用前提','回复期限 / 书面文件','固定现金 / 币种 / 期间','奖金股权 / 兑现条件','生活成本 / 搬迁支出','个人税后估算 / 来源日期','成长 / 支持 / 生活安排','待确认条件 / 最终取舍'],'先确认可以履约，再比较价值。保留原币金额和汇率日期，未知金额不要填零。')
    for p in sorted((ROOT/'templates').glob('*.md')):
        if p.name not in ['09-contact-emails.md','10-application-materials.md','11-ai-assistance.md']:continue
        text=p.read_text('utf-8');title=re.search(r'^#\s+(.+)$',text,re.M).group(1)
        story+=[PageBreak()]+heading(title,'template-'+p.stem,'TEMPLATES / 可复制文字')+markdown(text)
    story+=[PageBreak()]+heading('官方来源与核验记录','sources','SOURCES / 一手资料')
    partial=sum(s.get('status')!='verified' for s in source)
    story.append(P(f'本版登记 {len(source)} 条来源，其中 {partial} 条保留部分核验或冲突状态。编号与正文一致。点击标题打开官方页面；来源可读与个人符合资格是两件事。'))
    story.append(P('逐条完整网址、适用范围和读取限制见网站“来源与核验”及源文件 data/sources-*.json。部分链接可能依赖动态页面或对访问环境有要求。','small'))
    grouped=defaultdict(list)
    for s in source:grouped[s.get('region','通用')].append(s)
    for group,items in grouped.items():
        story.append(P(group,'h2'))
        for s in items:
            status='已核验' if s.get('status')=='verified' else '部分核验 / 见限制'
            lead=f"**{s['id']}**  [{s['title']}]({s['url']})"
            detail=f"{s.get('publisher','官方来源')} | {s.get('checked_at',DATE)} | {status}"
            claim=s.get('supports','');claim='；'.join(claim) if isinstance(claim,list) else str(claim)
            notes=s.get('notes','');notes='；'.join(notes) if isinstance(notes,list) else str(notes)
            story.append(KeepTogether([P(lead,'small'),P(detail,'small'),P('支持范围：'+claim,'small')]+([P('限制：'+notes,'small')] if notes else [])))
            story.append(Spacer(1,5))
    story+=[PageBreak()]+heading('带着问题，继续往前走','closing','NEXT STEP / 下一步')
    story.append(P('今天不需要解决所有国家、所有岗位。先确认一条可行路线，完成一次真实申请，把下一步记下来。','h2'))
    story.append(P('完整网站与下载：['+SITE+']('+SITE+')'))
    story.append(P('作者：**AI 酋长 Andy**\n微信：**AIPMAndy**\n公众号：**AI酋长Andy**'))
    story.append(P('个人官网：[metaver.vip](https://metaver.vip/)\n公司官网：[www.a6no1.cn](https://www.a6no1.cn/)'))
    story.append(P('免费内容完整开放。需要个人路线、材料、面试或Offer诊断时，可以备注“留学生求职”联系。先说明地区、毕业日期、目标岗位、卡点与已尝试动作。咨询不承诺录用、薪资或身份资格。'))
    story.append(P('原创文字和模板：CC BY 4.0。网站及构建代码：MIT。第三方来源与字体保留其原有权利。版本 v1.0.0 / '+DATE,'small'))
    output.parent.mkdir(parents=True,exist_ok=True)
    doc=Book(output);doc.multiBuild(story)
    (ROOT/'docs/pdf-chapter-pages.json').write_text(json.dumps(doc.chapter_pages,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'output':str(output),'pages':doc.page,'chapters':len(doc.chapter_pages),'sources':len(source),'partial_sources':partial},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--font-source');ap.add_argument('--output',default=str(ROOT/'downloads/chinese-international-student-career-guide.pdf'));args=ap.parse_args()
    fonts(args.font_source);styles();build(Path(args.output))
