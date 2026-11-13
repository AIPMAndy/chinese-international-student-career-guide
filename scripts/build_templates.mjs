import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

// Run this source with the artifact-tool runtime. The optional first argument is the repository root.
const repo = path.resolve(process.argv[2] || path.join(path.dirname(fileURLToPath(import.meta.url)), '..'));
const dir = path.join(repo, 'templates');
const outputDir = path.join(path.dirname(repo), 'outputs', 'student-career-44af');
const reviewDir = path.join(outputDir, 'review');
await fs.mkdir(dir, { recursive: true });
await fs.mkdir(reviewDir, { recursive: true });
const version = '2026-11-13';
const brand = '作者：AI 酋长 Andy｜微信：AIPMAndy｜公众号：AI酋长Andy';
const links = '个人官网：https://metaver.vip/\n公司官网：https://www.a6no1.cn/';

const schemas = [
  {id:'route-decision', name:'路线决策', filename:'01-route-decision.csv', rows:12,
   purpose:'比较留当地、去第三地、回国三条路线。先确认身份、岗位和时间，再比较预算。',
   prepare:'毕业日期、当前身份与到期日、可动用预算、目标岗位原文、官方政策链接。',
   action:'每个具体国家或地区写一行。不要把“欧洲”当成同一工作许可地区。预算与成本使用同一种币种。',
   result:'一条主路线、一条备用路线，以及切换的最晚日期。',
   accept:'每条保留路线都有可追溯的资格证据、有效招聘窗口和下一步动作。待确认不能当作符合。',
   blocked:'先把资格问题发给学校国际学生办公室或对应雇主。没有书面答复前保留备用路线。',
   headers:['路线','国家或地区','目标岗位','工作资格结论','担保安排结论','资格证据链接','招聘截止日','最早到岗日','币种','月生活费','一次性成本','可动用预算','预算可支撑月数（公式）','路线门槛（公式）','切换最晚日','下一步'],
   widths:[14,18,24,18,18,34,16,16,12,16,16,18,21,22,16,34],
   dates:['G','H','O'], numeric:['J','K','L','M'],
   lists:{A:['留当地','去第三地','回国'],D:['符合','不符合','待确认'],E:['无需担保','雇主已书面确认','不支持','待确认']},
   formulas:{M:r=>`=IF(A${r}="","",IF(OR(J${r}="",K${r}="",L${r}=""),"缺成本或预算",IF(J${r}<=0,"检查月生活费",(L${r}-K${r})/J${r})))`,N:r=>`=IF(A${r}="","",IF(OR(D${r}="不符合",E${r}="不支持"),"暂停此路径",IF(AND(D${r}="符合",OR(E${r}="无需担保",E${r}="雇主已书面确认"),F${r}<>""),"可继续核对岗位", "先核验资格")))`}
  },
  {id:'time-plan',name:'时间计划',filename:'02-time-plan.csv',rows:40,
   purpose:'把毕业、身份、申请、返国和入职日期放在同一张表。',
   prepare:'学校毕业文件、个人身份文件、岗位原文、活动公告、本人旅行计划。',
   action:'日期必须抄自原始来源。当地截止时间与时区另列，自己换算后的时间不可覆盖原文。',
   result:'按截止日排序的行动日历，每项有负责人和完成证据。',
   accept:'没有只有月份的模糊截止；未公告项目标待公告，并安排复查日。',
   blocked:'没有官方日期时不猜。先填复查日，向发布机构确认，按最早可能窗口预备材料。',
   headers:['任务ID','地区','事件或任务','日期类别','开始日','截止日','原文时间和时区','来源链接','前置条件','负责人','状态','完成证据','复查日','备注'],
   widths:[14,16,30,18,16,16,28,34,28,16,16,34,16,34],dates:['E','F','M'],
   lists:{D:['官方截止','雇主截止','本人计划','待公告'],K:['未开始','进行中','待答复','已完成','已取消']}
  },
  {id:'eligibility-check',name:'岗位资格',filename:'03-eligibility-check.csv',rows:40,
   purpose:'逐条核验岗位毕业时间、所在地、工作资格和担保要求。',
   prepare:'雇主招聘原文、个人真实毕业日期与身份信息、当地官方政策链接。',
   action:'原文与自己的情况分列。现在可工作和未来需要担保分开回答。没有写担保不等于支持担保。',
   result:'每个岗位的符合、不符合或待确认结论，以及尚未解决的问题。',
   accept:'所有结论均能定位到原文或书面答复；没有用AI推测的资格结论。',
   blocked:'把不明确条件写成一个具体问题发给雇主或学校。期限前仍无结论时，按真实信息提交或暂缓。',
   headers:['岗位ID','地区','公司','岗位链接','JD保存日期','工作地点','毕业时间要求原文','本人毕业日期','工作资格要求原文','本人当前资格','未来是否需要担保','雇主担保原文','核验结论','政策官方链接','雇主书面答复','核验日期','待问问题','下一步'],
   widths:[14,16,22,34,17,22,40,17,40,28,24,40,18,34,40,17,40,34],dates:['E','H','P'],
   lists:{K:['是','否','待确认'],M:['符合','不符合','待确认']}
  },
  {id:'material-checklist',name:'材料清单',filename:'04-material-checklist.csv',rows:40,
   purpose:'为每个岗位提交它真正要求的材料，保持经历、日期与身份一致。',
   prepare:'岗位原文、真实经历证据、学校成绩与毕业文件、本人可公开的作品。',
   action:'按岗位逐项列材料、语言、格式与上限。只向真实招聘或认证渠道提交必要的个人资料。',
   result:'一份有版本号、能打开、可追溯的提交包。',
   accept:'抽查文件可读、链接无需额外权限、时间一致、附件无批注；不要把身份证件上传到公共仓库。',
   blocked:'缺正式证明时向签发机构申请，向雇主确认可否后补；不能自己制作证明。',
   headers:['岗位ID','材料名称','要求来源','语言','文件格式或上限','本地文件名或受限链接','版本日期','真实证据位置','状态','复核人','提交截止','是否含敏感信息','下一步'],
   widths:[14,26,36,14,24,38,17,38,18,16,17,22,38],dates:['G','K'],
   lists:{I:['待准备','待复核','可提交','已提交','待补件'],L:['是','否']}
  },
  {id:'contact-log',name:'联系记录',filename:'05-contact-log.csv',rows:40,
   purpose:'记录与学校、校友和招聘方的联系，明确每次沟通只解决一个问题。',
   prepare:'公开联系渠道、对方相关背景、岗位链接、自己的真实简短介绍。',
   action:'先问具体问题。需要内推时附岗位编号与真实匹配证据，给对方拒绝空间。',
   result:'有下一步的关系记录，不是群发名单。',
   accept:'每条有联系目的、回复内容和下次动作；不未经许可公开别人的姓名与邮件。',
   blocked:'若未回复，按对方流程在合适时间简短跟进一次。继续寻找其他渠道，不连续催促。',
   headers:['记录ID','对方称呼（可用代号）','地区或机构','渠道','联系目的','岗位ID','首次联系日','对方回复要点','下次跟进日','状态','下一步','私有证据位置'],
   widths:[14,28,26,22,40,14,17,40,17,18,40,36],dates:['G','I'],
   lists:{J:['待发送','待回复','已回复','已约谈','已结束']}
  },
  {id:'application-tracker',name:'申请台账',filename:'06-application-tracker.csv',rows:100,
   purpose:'用岗位ID贯穿资格核验、材料、面试和Offer。每周只改一个可解释的瓶颈。',
   prepare:'岗位链接、投递凭证、提交材料版本、最新回复。',
   action:'同一岗位一行，改阶段不新增重复记录。更新复盘日期，按“待跟进”筛选。关闭的岗位保留原因。',
   result:'本周需跟进清单和分阶段的问题记录。',
   accept:'阶段与邮件证据相符；每个活跃岗位有下一步和跟进日期；没有把未回复当作拒绝。',
   blocked:'无回复先查资格和投递成功证据；面试不推进先查具体答题证据；Offer不合适先查硬条件与预算。',
   headers:['岗位ID','地区','公司','岗位名称','招聘原文链接','截止日期','原文时间和时区','提交日期','来源渠道','当前阶段','最后更新日','下次跟进日','下一步动作','跟进状态（公式）','拒绝或卡点原话','提交材料版本','资格核验记录','备注'],
   widths:[14,16,22,30,36,17,28,17,20,18,17,17,38,22,40,28,28,34],dates:['F','H','K','L'],
   lists:{J:['待申请','已投递','笔试测评','HR沟通','业务面试','终面','Offer','拒绝','撤回','已接受']},
   formulas:{N:r=>`=IF(A${r}="","",IF(OR(J${r}="拒绝",J${r}="撤回",J${r}="已接受"),"已结束",IF(L${r}="","缺跟进日期",IF($C$4="","缺复盘日期",IF(L${r}<=$C$4,"待跟进","未到期")))))`}
  },
  {id:'interview-review',name:'面试复盘',filename:'07-interview-review.csv',rows:40,
   purpose:'把模糊的“表现不好”拆成可练习的问题。',
   prepare:'岗位要求、面试邀请、自己的复述记录。录音或转写须先取得必要同意。',
   action:'面试后尽快写题目、自己的回答和追问。把雇主实际反馈与自己的推测分开。',
   result:'每轮一到三个具体练习动作和下一次验证方法。',
   accept:'改进动作能用一次模拟面试验证；不虚构未完成的工作成果。',
   blocked:'想不起原话时标“本人回忆”。请同学按岗位要求追问，不让AI代替你参加真实评估。',
   headers:['岗位ID','轮次','日期','面试语言','题目或任务','我的回答要点','追问或卡住处','雇主实际反馈','我的推测','证据缺口','改进动作','复练日期','复练验收','下一轮时间'],
   widths:[14,16,17,16,40,44,40,40,36,36,40,17,40,24],dates:['C','L']
  },
  {id:'offer-comparison',name:'Offer比较',filename:'08-offer-comparison.csv',rows:12,
   purpose:'先核验能否真实入职，再比较同一币种与周期下的现金、岗位和生活条件。',
   prepare:'书面Offer、工作许可与担保条件、税费估算依据、生活成本、本人优先级。',
   action:'一份Offer一行。税后收入由你依据可靠来源填写，汇率单列，不把股权和不保证奖金当现金。',
   result:'可接受条件、必须追问的问题和书面回复截止日。',
   accept:'工作资格与担保明确，入职日可实现；币种周期一致，假设有来源；未决条件不被高薪抵消。',
   blocked:'要求HR书面确认条件或申请延长回复时间。不要在条件未清时按理想情况计算收益。',
   headers:['Offer ID','公司与岗位','工作地区','工作资格结论','担保安排结论','最早可入职日','雇主要求入职日','回复截止日','币种','月税后固定收入','月必要支出','月可支配金额（公式）','一次性搬迁成本','换算到比较币种汇率','比较币种','换算后月可支配（公式）','入职门槛（公式）','奖金股权说明（不计现金）','试用期与终止条款','岗位成长与职责','家庭与生活条件','待书面确认事项','证据链接与估算日期','本人决定'],
   widths:[15,30,22,18,22,18,18,18,12,21,20,24,23,26,16,26,26,42,40,40,40,42,42,28],dates:['F','G','H'],numeric:['J','K','L','M','N','P'],
   lists:{D:['符合','不符合','待确认'],E:['无需担保','雇主已书面确认','不支持','待确认'],X:['待决定','继续谈条件','接受','拒绝']},
   formulas:{L:r=>`=IF(A${r}="","",IF(OR(J${r}="",K${r}=""),"缺收入或支出",J${r}-K${r}))`,P:r=>`=IF(A${r}="","",IF(OR(N${r}="",O${r}="",J${r}="",K${r}=""),"缺换算输入",IF(N${r}<=0,"检查汇率",L${r}*N${r})))`,Q:r=>`=IF(A${r}="","",IF(OR(D${r}="不符合",E${r}="不支持"),"暂停接受",IF(OR(D${r}<>"符合",AND(E${r}<>"无需担保",E${r}<>"雇主已书面确认")),"先核验资格",IF(OR(F${r}="",G${r}=""),"缺入职日期",IF(F${r}>G${r},"需协调入职日","仍需核对合同")))))`}
  }
];

const excelCol = n => { let t=''; for (let x=n; x>0; x=Math.floor((x-1)/26)) t=String.fromCharCode(65+(x-1)%26)+t; return t; };
const csv = rows => '\uFEFF'+rows.map(row=>row.map(x=>'"'+String(x??'').replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
for (const t of schemas) await fs.writeFile(path.join(dir,t.filename),csv([t.headers,...Array.from({length:5},()=>t.headers.map(()=>''))]));
await fs.writeFile(path.join(repo,'data','template-schema.json'),JSON.stringify({version,author:'AI 酋长 Andy',templates:schemas.map(({formulas,...rest})=>({...rest,calculated_columns:Object.keys(formulas||{})}))},null,2)+'\n');

const wb = Workbook.create();
const order = ['application-tracker','route-decision','time-plan','eligibility-check','material-checklist','contact-log','interview-review','offer-comparison'];
for (const id of order) wb.worksheets.add(schemas.find(x=>x.id===id).name);
const guide=wb.worksheets.add('使用说明');
const font='Noto Sans CJK SC';
const start=9;
for (const id of order) {
 const t=schemas.find(x=>x.id===id),s=wb.worksheets.getItem(t.name),last=excelCol(t.headers.length),end=start+t.rows-1;
 s.showGridLines=false;s.tabColor=id==='application-tracker'?'#111111':'#999999';
 s.getRange(`A1:${last}${end}`).format={font:{name:font,size:10,color:'#171717'},verticalAlignment:'center',rowHeight:25};
 t.widths.forEach((v,i)=>s.getRange(`${excelCol(i+1)}1:${excelCol(i+1)}${end}`).format.columnWidth=v);
 s.getRange('A2').values=[[t.name]];s.getRange('A2').format.font={name:font,size:16,bold:true,color:'#111111'};
 s.getRange(`A3:${last}3`).format.borders={bottom:{style:'thin',color:'#999999'}};
 s.getRange('A4').values=[[id==='application-tracker'?'复盘日期':'使用规则']];
 if(id==='application-tracker') {
  s.getRange('C4').values=[[null]];s.getRange('C4').format.fill='#EFEFEF';s.getRange('C4').format.numberFormat='yyyy-mm-dd';
  s.getRange('E4').values=[['有记录岗位数']];s.getRange('F4').formulas=[['=COUNTA(A9:A108)']];
  s.getRange('I4').values=[['待跟进']];s.getRange('J4').formulas=[['=COUNTIFS(N9:N108,"待跟进")']];
  s.getRange('L4').values=[['缺跟进日期']];s.getRange('M4').formulas=[['=COUNTIFS(N9:N108,"缺跟进日期")']];
  s.getRange('A5').values=[['先填 C4 的复盘日期。灰底列自动计算。状态不代表雇主承诺。']];
 } else {
  s.getRange('C4').values=[['白底可填写；灰底为公式；所有日期请输入真正的日期值。']];
  s.getRange('A5').values=[[t.purpose]];
 }
 s.getRange('A6').values=[['详细填写方法见“使用说明”及 templates/README.md。空白表不包含个人数据。']];
 s.getRange(`A8:${last}8`).values=[t.headers];
 s.getRange(`A8:${last}8`).format={fill:'#1C1C1C',font:{name:font,size:10,bold:true,color:'#FFFFFF'},rowHeight:45,wrapText:true,horizontalAlignment:'center',verticalAlignment:'center',borders:{insideVertical:{style:'thin',color:'#FFFFFF'}}};
 s.getRange(`A${start}:${last}${end}`).format={rowHeight:33,wrapText:true,verticalAlignment:'top'};
 for(let r=start;r<=end;r+=2) s.getRange(`A${r}:${last}${r}`).format.fill='#FAFAFA';
 for(const c of t.dates||[])s.getRange(`${c}${start}:${c}${end}`).format.numberFormat='yyyy-mm-dd';
 for(const c of t.numeric||[])s.getRange(`${c}${start}:${c}${end}`).format.numberFormat='#,##0.00';
 for(const [c,values] of Object.entries(t.lists||{}))s.getRange(`${c}${start}:${c}${end}`).dataValidation={rule:{type:'list',values}};
 for(const [c,fn] of Object.entries(t.formulas||{})) {
  s.getRange(`${c}${start}`).formulas=[[fn(start)]];s.getRange(`${c}${start}:${c}${end}`).fillDown();
  s.getRange(`${c}${start}:${c}${end}`).format.fill='#EDEDED';
 }
 s.freezePanes.freezeRows(8);s.freezePanes.freezeColumns(1);
 const table=s.tables.add(`A8:${last}${end}`,true,`Career_${id.replaceAll('-','_')}`);table.style='TableStyleLight1';
 // Applying the native table last can apply its theme. Reassert the intended monochrome header.
 s.getRange(`A8:${last}8`).format.fill='#1C1C1C';s.getRange(`A8:${last}8`).format.font={name:font,size:10,bold:true,color:'#FFFFFF'};
}

guide.showGridLines=false;guide.tabColor='#666666';
guide.getRange('A1:H65').format={font:{name:font,size:10,color:'#171717'},rowHeight:25,verticalAlignment:'top'};
guide.getRange('A1:A65').format.columnWidth=20;guide.getRange('B1:B65').format.columnWidth=100;
guide.getRange('A2').values=[['中国留学生求职工作簿']];guide.getRange('A2').format.font={name:font,size:16,bold:true};
const intro=[['版本',version],['作者','AI 酋长 Andy'],['微信','AIPMAndy'],['公众号','AI酋长Andy'],['个人官网','https://metaver.vip/'],['公司官网','https://www.a6no1.cn/'],['开始填写','先复制一份私有副本。先填路线和资格，再管理申请。工作簿不含真实个人数据。'],['输入与公式','白底输入，灰底公式。没有工作表保护，公式可编辑；修改前先留副本。'],['日期与时区','日期列输入日期值。雇主截止时刻和时区保留在原文字段；跟进公式只比较日期，不判断跨时区时刻。'],['资格硬门槛','“待确认”不能算符合。路线门槛只提醒核验，不证明你具有工作权利。Offer 门槛不代替合同审查。'],['现金与币种','Offer 收入为你填写的月税后固定现金；股权和不保证奖金不计入。汇率为 1 单位原币折算比较币种。'],['容量与扩展','申请台账预留100行，其余40行，路线和Offer各12行。超过容量时扩展表格、公式、验证和顶端统计范围。'],['数据保护','只在个人副本填申请与身份资料；公开仓库保留空白模板。不要上传护照、身份证、合同、他人联系方式。'],['CSV说明','CSV 不保留公式、下拉和格式。标有“公式”的列须手算或用工作簿。Excel导入选择UTF-8。'],['真实表达','邮件与简历中的方括号必须替换为可核实事实；不适用的句子直接删除。'],['辅助服务','免费模板完整可用。需要个人路线诊断时，可通过微信 AIPMAndy 联系；不承诺录用、薪资或身份资格。']];
guide.getRange('A4:B19').values=intro;guide.getRange('B4:B19').format.wrapText=true;guide.getRange('A4:B19').format.rowHeight=37;
let gr=22;
for(const t of schemas){guide.getRange(`A${gr}:B${gr}`).values=[[t.name,t.purpose]];guide.getRange(`A${gr}:B${gr}`).format={fill:'#1C1C1C',font:{name:font,size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:37};gr++;
 for(const [label,key] of [['准备','prepare'],['做法','action'],['验收','accept'],['卡住','blocked']]){guide.getRange(`A${gr}:B${gr}`).values=[[label,t[key]]];guide.getRange(`B${gr}`).format.wrapText=true;guide.getRange(`A${gr}:B${gr}`).format.rowHeight=37;gr++;}}

// Meaningful input-change checks, then restore the blank public template.
const checks=[];const assert=(name,actual,expected)=>{const ok=actual===expected;checks.push({name,actual,expected,ok});if(!ok)throw new Error(`${name}: ${JSON.stringify(actual)} != ${JSON.stringify(expected)}`);};
const a=wb.worksheets.getItem('申请台账');
assert('blank tracker remains blank',a.getRange('N9').values[0][0],'');
a.getRange('A9').values=[['TEST-ONLY']];assert('missing due date visible',a.getRange('N9').values[0][0],'缺跟进日期');
a.getRange('L9').values=[[new Date('2026-11-13T00:00:00Z')]];assert('missing review date visible',a.getRange('N9').values[0][0],'缺复盘日期');
a.getRange('C4').values=[[new Date('2026-11-13T00:00:00Z')]];assert('due today requires follow up',a.getRange('N9').values[0][0],'待跟进');
a.getRange('J9').values=[['拒绝']];assert('closed application does not request follow up',a.getRange('N9').values[0][0],'已结束');
a.getRange('A9:M9').clear({applyTo:'contents'});a.getRange('C4').clear({applyTo:'contents'});
const r=wb.worksheets.getItem('路线决策');r.getRange('A9').values=[['去第三地']];r.getRange('D9').values=[['不符合']];assert('eligibility rejection is a hard gate',r.getRange('N9').values[0][0],'暂停此路径');
r.getRange('D9:F9').values=[['符合','待确认','https://example.invalid/test-only']];assert('uncertain sponsorship remains unresolved',r.getRange('N9').values[0][0],'先核验资格');
r.getRange('E9').values=[['雇主已书面确认']];assert('confirmed conditions only permit next review',r.getRange('N9').values[0][0],'可继续核对岗位');
r.getRange('J9:L9').values=[[100,0,300]];assert('zero one-time cost preserved',r.getRange('M9').values[0][0],3);r.getRange('A9:L9').clear({applyTo:'contents'});
const o=wb.worksheets.getItem('Offer比较');o.getRange('A9').values=[['TEST-ONLY']];o.getRange('J9:K9').values=[[0,100]];assert('zero income preserved',o.getRange('L9').values[0][0],-100);
o.getRange('N9:O9').values=[[2,'比较币种']];assert('currency conversion uses entered rate',o.getRange('P9').values[0][0],-200);
o.getRange('D9:G9').values=[['符合','无需担保',new Date('2026-12-01T00:00:00Z'),new Date('2026-11-30T00:00:00Z')]];assert('start date conflict is visible',o.getRange('Q9').values[0][0],'需协调入职日');
o.getRange('A9:K9').clear({applyTo:'contents'});o.getRange('M9:O9').clear({applyTo:'contents'});
wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:40},maxChars:3000});
await fs.writeFile(path.join(outputDir,'formula-checks.json'),JSON.stringify({checks,error_scan:errors.ndjson},null,2));
for(const id of order){const t=schemas.find(x=>x.id===id);const max=excelCol(Math.min(t.headers.length,8));const blob=await wb.render({sheetName:t.name,range:`A1:${max}12`,scale:1.4,format:'png'});await fs.writeFile(path.join(reviewDir,`${id}.png`),new Uint8Array(await blob.arrayBuffer()));
 for(let col=9;col<=t.headers.length;col+=8){const endCol=excelCol(Math.min(t.headers.length,col+7));const blob=await wb.render({sheetName:t.name,range:`${excelCol(col)}8:${endCol}12`,scale:1.3,format:'png'});await fs.writeFile(path.join(reviewDir,`${id}-columns-${col}.png`),new Uint8Array(await blob.arrayBuffer()));}
}
const gb=await wb.render({sheetName:'使用说明',range:'A1:B19',scale:1.3,format:'png'});await fs.writeFile(path.join(reviewDir,'instructions.png'),new Uint8Array(await gb.arrayBuffer()));
for(const [i,range] of ['A22:B41','A42:B61'].entries()){const blob=await wb.render({sheetName:'使用说明',range,scale:1.3,format:'png'});await fs.writeFile(path.join(reviewDir,`instructions-detail-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));}
const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path.join(outputDir,'career-workbook.xlsx'));
await fs.copyFile(path.join(outputDir,'career-workbook.xlsx'),path.join(dir,'career-workbook.xlsx'));
console.log(JSON.stringify({file:path.join(dir,'career-workbook.xlsx'),sheets:order.length+1,checks:checks.length,preview_dir:reviewDir,error_scan:errors.ndjson}));

const readme=`# 可编辑求职模板\n\n${brand}\n\n${links}\n\n版本：${version}\n\n先下载 [career-workbook.xlsx](career-workbook.xlsx) 并保存为私人副本。工作簿的 9 个工作表包含 8 类工具及使用说明。所有个人输入均为空白，公开模板没有任何客户资料。\n\n## 选择格式\n\n- **Excel**：保留公式、下拉、冻结表头、筛选与黑白版式。推荐日常管理。\n- **CSV**：可导入 Excel、Google Sheets、飞书多维表格等；不带公式与验证。采用 UTF-8 BOM。日期列请按日期导入，编号按文本导入。\n- **Markdown**：邮件、简历骨架和 AI 辅助提示词可以直接复制编辑。方括号仅是待填写位置，不是可直接发送的个人事实。\n\nCSV 中标为“公式”的列在 CSV 内为空白；请手算或使用工作簿，不要把空白理解为 0。新增超过预留行数时，需扩展表格、公式、验证与顶部统计范围。\n\n## 推荐使用顺序\n\n路线决策 → 时间计划 → 岗位资格 → 材料清单 → 联系与申请 → 面试复盘 → Offer 比较。\n\n每周固定一次复盘。在申请台账 C4 填当次复盘日期，过滤“待跟进”，逐个核对资格、投递凭证、答题表现和下一步。跟进公式按日期比较，不替你解释招聘截止的时区。\n\n${schemas.map(t=>`## ${t.name}\n\n[下载 CSV](${t.filename})\n\n**解决什么：**${t.purpose}\n\n**准备什么：**${t.prepare}\n\n**具体怎么做：**${t.action}\n\n**得到什么：**${t.result}\n\n**如何验收：**${t.accept}\n\n**卡住怎么办：**${t.blocked}\n`).join('\n')}\n## 文字模板\n\n- [联系邮件与消息](09-contact-emails.md)：学校、校友、招聘方资格问询、跟进、改期、Offer 澄清。\n- [中英文申请材料骨架](10-application-materials.md)：简历、求职信、经历证据卡、提交检查。\n- [AI 辅助与复盘提示词](11-ai-assistance.md)：岗位原文抽取、简历校对、模拟面试和漏斗复盘。\n- [一页路线决策填写单](12-route-worksheet.md)：在纸面或文档中完成个人路线判断。\n\n## 计算口径\n\n- 路线预算可支撑月数 =（可动用预算 − 一次性成本）÷ 月生活费。输入同一币种；三项均需填写。一次性成本可以为 0；负数结果表示预算不足。\n- 资格与担保有任一明确不满足，路线显示“暂停此路径”；待确认显示“先核验资格”。显示“可继续核对岗位”仍不代表已取得工作许可。\n- Offer 月可支配金额 = 月税后固定收入 − 月必要支出。不把未保证奖金、股权估值或报销计为固定现金。\n- 换算后月可支配 = 月可支配金额 × 用户填写汇率。汇率定义：1 单位原币可换多少比较币种。核对日期与来源另填。\n- Offer 门槛依次检查资格、担保、两方入职日期。通过这些检查后仍显示“仍需核对合同”，不会自动推荐接受。\n- 申请总量按非空岗位ID计数。用一个稳定ID代表同一岗位，不按每次跟进重复建行。拒绝、撤回、已接受被视为已结束；其他活跃记录需有跟进日期。\n\n## 本周没有进展，先检查什么\n\n| 现象 | 先找证据 | 本周只改的一件事 | 下周验收 |\n| --- | --- | --- | --- |\n| 投了没有回复 | 资格记录、投递成功回执、岗位是否仍在招、材料版本 | 对同一目标岗位组逐份复查最常见硬条件和第一屏证据 | 记录修正前后各自投递与回复，不能凭小样本断言因果 |\n| 进入面试后不推进 | 原题、本人回答、追问、真实反馈 | 只练最常卡住的一类问题，录下自己的模拟回答 | 能用真实事实讲清动作、判断和结果，并应对追问 |\n| 只有不合适的Offer | 地区、入职时间、资格、职责、现金与生活条件 | 在投递前加一项明确筛选条件 | 新候选岗位在该条件上有原文或书面答复 |\n| 进展慢且预算接近底线 | 余额、月支出、身份和招聘截止 | 按路线决策表执行备用路线切换 | 切换动作与日期完成，不以尚未收到的Offer支撑预算 |\n\n## 使用边界\n\n只填真实经历和真实身份。政策资格由对应主管机构确认；模板帮助你整理证据，不代替审批。AI 可辅助提取和练习，不能编造成果、填虚假身份或冒充你完成测评。\n\n免费内容完整开放。需要针对个人经历、地区和时间安排做诊断，可联系微信 **AIPMAndy**。咨询不承诺录用、薪资或身份资格。\n`;
await fs.writeFile(path.join(dir,'README.md'),readme);
