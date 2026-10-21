"""
Generate ranked XLSX - pure Python, no external dependencies
Uses zipfile + XML to write a valid .xlsx file
"""
import json, zipfile, io, os, struct, re
from datetime import datetime

# ── AI skill set ──────────────────────────────────────────────────────────
AI_SKILLS = {
    'python','pytorch','tensorflow','scikit-learn','sklearn','keras',
    'xgboost','lightgbm','catboost','nlp','llm','fine-tuning llms',
    'transformers','hugging face transformers','bert','gpt','langchain',
    'prompt engineering','embeddings','sentence transformers','peft','lora',
    'faiss','pinecone','weaviate','qdrant','milvus','vector search',
    'information retrieval','bm25','elasticsearch','opensearch',
    'mlops','mlflow','kubeflow','weights & biases','bentoml',
    'recommendation systems','feature engineering','machine learning',
    'aws','gcp','azure','spark','airflow','data pipelines','sql',
    'computer vision','opencv','image classification','object detection',
    'cnn','yolo','gans','speech recognition','tts','statistical modeling',
    'data science','forecasting','object detection'
}
REQUIRED_YEARS = 3

def matched_skills(c):
    return [s['name'] for s in c.get('skills',[]) if s['name'].lower() in AI_SKILLS]

def skill_sc(c):   return min(1.0, len(matched_skills(c)) / 8)
def exp_sc(c):     return min(1.0, c['profile']['years_of_experience'] / REQUIRED_YEARS)

def beh_sc(c):
    s = c.get('redrob_signals',{})
    rr = s.get('recruiter_response_rate', 0.5)
    cr = s.get('interview_completion_rate', 0.5)
    gh = s.get('github_activity_score', -1)
    gs = (gh/100) if gh >= 0 else 0.3
    sv = min(1.0, s.get('saved_by_recruiters_30d', 0) / 20)
    return 0.35*rr + 0.35*cr + 0.15*gs + 0.15*sv

def avail_sc(c):
    s = c.get('redrob_signals',{})
    ow = 1.0 if s.get('open_to_work_flag') else 0.0
    la = s.get('last_active_date','')
    ra = 1.0 if '2026' in la else (0.7 if '2025' in la else 0.4)
    np = s.get('notice_period_days', 90)
    ns = max(0.0, (150 - np) / 120)
    return 0.5*ow + 0.3*ra + 0.2*ns

def career_sc(c):
    titles = [h.get('title','').lower() for h in c.get('career_history',[])]
    levels = {'junior':1,'associate':1,'engineer':2,'analyst':2,'senior':3,
              'lead':4,'principal':5,'staff':5,'manager':4,'director':6}
    lvs = []
    for t in titles:
        for k,v in levels.items():
            if k in t: lvs.append(v); break
    if not lvs: return 0.4
    return min(1.0, max(lvs)/5 + (0.1 if len(set(lvs))>1 else 0))

def profile_sc(c):
    s = c.get('redrob_signals',{})
    comp = s.get('profile_completeness_score', 50) / 100
    ver = (0.5 if s.get('verified_email') else 0) + (0.5 if s.get('verified_phone') else 0)
    return 0.7*comp + 0.3*ver

def score(c):
    sk = skill_sc(c); ex = exp_sc(c); bh = beh_sc(c)
    av = avail_sc(c); ca = career_sc(c); pq = profile_sc(c)
    fs = 0.35*sk + 0.20*ex + 0.15*bh + 0.10*av + 0.10*ca + 0.10*pq
    return round(fs,4), sk, ex, bh, av, ca

def reasoning(c, ms, sk, ex, bh, av):
    parts = []
    s = c.get('redrob_signals',{})
    if ms: parts.append(f"AI skills: {', '.join(ms[:4])}")
    yrs = c['profile']['years_of_experience']
    parts.append(f"{yrs:.1f} yrs exp ({'meets' if yrs>=REQUIRED_YEARS else 'below'} {REQUIRED_YEARS}+ req)")
    rr = s.get('recruiter_response_rate',0)
    if rr >= 0.7: parts.append(f"High response rate ({rr:.0%})")
    if s.get('open_to_work_flag'): parts.append("Open to work")
    np = s.get('notice_period_days',90)
    if np <= 30: parts.append(f"{np}-day notice")
    gh = s.get('github_activity_score',-1)
    if gh >= 50: parts.append(f"GitHub score {gh:.0f}/100")
    return ' | '.join(parts)

# ── Load candidates ────────────────────────────────────────────────────────
jsonl = r"c:\Users\Admin\OneDrive\Desktop\redrob-ai\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
candidates = [json.loads(l) for l in open(jsonl, encoding='utf-8') if l.strip()]
print(f"Loaded {len(candidates)} candidates")

# ── Score & rank ───────────────────────────────────────────────────────────
rows = []
for c in candidates:
    fs, sk, ex, bh, av, ca = score(c)
    ms = matched_skills(c)
    p = c['profile']
    s = c.get('redrob_signals',{})
    rows.append({
        'rank': 0,
        'candidate_id': c['candidate_id'],
        'score': fs,
        'current_title': p.get('current_title',''),
        'years_experience': p.get('years_of_experience',0),
        'location': p.get('location',''),
        'country': p.get('country',''),
        'matched_skill_count': len(ms),
        'matched_skills': ', '.join(ms),
        'skill_score': round(sk,4),
        'experience_score': round(ex,4),
        'behavior_score': round(bh,4),
        'availability_score': round(av,4),
        'career_score': round(ca,4),
        'open_to_work': 'Yes' if s.get('open_to_work_flag') else 'No',
        'notice_period_days': s.get('notice_period_days',90),
        'recruiter_response_rate': round(s.get('recruiter_response_rate',0),2),
        'github_activity_score': s.get('github_activity_score',-1),
        'profile_completeness': s.get('profile_completeness_score',0),
        'reasoning': reasoning(c, ms, sk, ex, bh, av)
    })

rows.sort(key=lambda x: x['score'], reverse=True)
for i, r in enumerate(rows, 1): r['rank'] = i

# ── Write XLSX using zipfile + XML ─────────────────────────────────────────
COLS = ['rank','candidate_id','score','current_title','years_experience',
        'location','country','matched_skill_count','matched_skills',
        'skill_score','experience_score','behavior_score','availability_score',
        'career_score','open_to_work','notice_period_days',
        'recruiter_response_rate','github_activity_score',
        'profile_completeness','reasoning']

HEADERS = ['Rank','Candidate ID','Final Score','Current Title','Years Experience',
           'Location','Country','AI Skill Count','Matched AI Skills',
           'Skill Score','Experience Score','Behavior Score','Availability Score',
           'Career Score','Open to Work','Notice Period (Days)',
           'Recruiter Response Rate','GitHub Activity Score',
           'Profile Completeness (%)','Reasoning']

def esc(v):
    return str(v).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;').replace("'",'&apos;')

def cell_xml(col_idx, row_idx, value, is_header=False):
    col_letter = chr(ord('A') + col_idx) if col_idx < 26 else chr(ord('A')+(col_idx//26)-1)+chr(ord('A')+(col_idx%26))
    ref = f"{col_letter}{row_idx}"
    if isinstance(value, (int, float)):
        s = ' s="1"' if is_header else ''
        return f'<c r="{ref}" t="n"{s}><v>{value}</v></c>'
    else:
        s = ' s="1"' if is_header else ''
        return f'<c r="{ref}" t="inlineStr"{s}><is><t>{esc(str(value))}</t></is></c>'

# Build sheet XML
sheet_rows = []
# Header row
header_cells = ''.join(cell_xml(j, 1, HEADERS[j], True) for j in range(len(HEADERS)))
sheet_rows.append(f'<row r="1">{header_cells}</row>')
# Data rows
for i, row in enumerate(rows, 2):
    cells = ''.join(cell_xml(j, i, row[COLS[j]]) for j in range(len(COLS)))
    sheet_rows.append(f'<row r="{i}">{cells}</row>')

col_widths = [6,18,10,22,8,16,10,8,40,8,8,8,8,8,8,8,8,8,8,60]
col_defs = ''.join(f'<col min="{j+1}" max="{j+1}" width="{col_widths[j]}" customWidth="1"/>' for j in range(len(COLS)))

sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
<cols>{col_defs}</cols>
<sheetData>{''.join(sheet_rows)}</sheetData>
<autoFilter ref="A1:{chr(ord('A')+len(COLS)-1)}1"/>
</worksheet>'''

styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF4472C4"/></patternFill></fill></fills>
<borders><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs>
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0"><alignment horizontal="center" wrapText="1"/></xf>
</cellXfs>
</styleSheet>'''

workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Ranked Candidates" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''

rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''

root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

out_path = r"c:\Users\Admin\OneDrive\Desktop\redrob-ai\outputs\ranked_candidates.xlsx"
os.makedirs(os.path.dirname(out_path), exist_ok=True)

with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', content_types)
    zf.writestr('_rels/.rels', root_rels)
    zf.writestr('xl/workbook.xml', workbook_xml)
    zf.writestr('xl/_rels/workbook.xml.rels', rels_xml)
    zf.writestr('xl/styles.xml', styles_xml)
    zf.writestr('xl/worksheets/sheet1.xml', sheet_xml)

print(f"\nXLSX written: {out_path}")
print(f"Total candidates ranked: {len(rows)}")
print(f"\nTop 10:")
for r in rows[:10]:
    print(f"  {r['rank']:3d}. {r['candidate_id']}  {r['score']:.4f}  {r['current_title'][:28]:<28}  Skills:{r['matched_skill_count']}")
