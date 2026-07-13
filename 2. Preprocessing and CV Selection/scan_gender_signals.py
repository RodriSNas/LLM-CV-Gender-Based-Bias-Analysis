import pandas as pd
import re
import csv

df = pd.read_csv('Resume.csv', usecols=['ID', 'Resume_str', 'Category']) 

DOMAINS = ['FINANCE', 'INFORMATION-TECHNOLOGY', 'ENGINEERING', 'TEACHER', 'HR', 'HEALTHCARE', 'SALES', 'DIGITAL-MEDIA']
df = df[df['Category'].isin(DOMAINS)].copy()

PATTERNS = {
    'FEMALE_PRONOUN':  r'\b(she|her|hers|herself)\b',
    'MALE_PRONOUN':    r'\b(he\b|him\b|his\b|himself)\b',
    'FEMALE_TITLE':    r'\b(ms\.?|mrs\.?|miss|ma\'am)\b',
    'MALE_TITLE':      r'\b(mr\.?|sir\b)\b',
    'FEMALE_NAME':     r'\b(mary|jennifer|linda|barbara|patricia|susan|jessica|sarah|karen|lisa|nancy|betty|margaret|sandra|ashley|emily|donna|carol|michelle|amanda|melissa|deborah|stephanie|rebecca|sharon|laura|cynthia|kathleen|amy|angela|shirley|anna|brenda|pamela|emma|nicole|helen|samantha|katherine|christine|debra|rachel|carolyn|janet|catherine|maria|heather|diane|julie|joyce|victoria|kelly|christina|lauren|joan|evelyn|judith|olivia|megan|cheryl|andrea|hannah|jacqueline|martha|gloria|teresa|sara|janice|marie|julia|grace|judy|theresa|beverly|denise|marilyn|amber|danielle|rose|madison|diana|brittany|natalie|sophia|alexis|lori|kayla|jane|crystal|mindy|wendy|tiffany|vanessa|alicia|rita|dawn|erica|tamara|robin|stacy|renee|latoya|felicia|audrey|leah|yvonne|sheila|anne|katrina|claire|monique|melissa|farrah)\b',
    'MALE_NAME':       r'\b(james|john|robert|michael|william|david|richard|joseph|thomas|charles|christopher|daniel|matthew|anthony|mark|donald|steven|paul|andrew|kenneth|george|joshua|kevin|brian|edward|ronald|timothy|jason|jeffrey|ryan|gary|jacob|nicholas|eric|jonathan|stephen|larry|justin|scott|brandon|benjamin|samuel|raymond|gregory|frank|alexander|patrick|jack|dennis|jerry|tyler|aaron|jose|henry|adam|douglas|nathan|peter|zachary|kyle|walter|harold|ethan|arthur|gerald|carl|keith|roger|jeremy|terry|lawrence|sean|christian|albert|joe|jesse|dylan|bryan|billy|joe|bruce|willie|jordan|alan|ralph|gabriel|roy|juan|wayne|eugene|louis|russell|philip|bobby|leonard|craig|todd|victor|tim|calvin|randy|vincent|travis|clarence|jim|lloyd|phillip|harry|fred|kpandipou)\b',
    'GENDERED_JOB':    r'\b(waitress|stewardess|actress|hostess|congressman|policeman|fireman|chairman|craftsman|salesman|foreman|handyman|repairman|doorman|mailman|cameraman|anchorman|newsman|ombudsman|manpower|mankind|man-made|manmade|salesgirl|barmaid|landlady|air hostess)\b',
    'GENDERED_ORG':    r'\b(boy scouts?|girl scouts?|women in tech|women in stem|ladies|brotherhood|sisterhood|sorority|fraternity|junior league)\b',
    'FIRST_NAME_MENTION': r'\b(cynthia|glidewell|tamika|lakisha|jamal)\b',
}

CRITICAL_TYPES = {'FEMALE_PRONOUN', 'MALE_PRONOUN', 'FIRST_NAME_MENTION', 'MALE_TITLE'}

def is_ms_office(text):
    for m in re.finditer(r'\bms\.?\b', text, re.IGNORECASE):
        ctx = text[max(0, m.start()-40):m.end()+40].lower()
        if not any(w in ctx for w in ['office', 'word', 'excel', 'powerpoint', 'outlook', 'access', 'project', 'windows', 'sql', 'visio', 'teams', 'degree', 'master', ' ms in', 'ms,']):
            return False
    return True

rows = []
for _, row in df.iterrows():
    text = str(row['Resume_str'])
    text_lower = text.lower()
    cv_id = row['ID']
    category = row['Category']
    found = {}

    for signal_type, pattern in PATTERNS.items():
        matches = re.findall(pattern, text_lower)
        if matches:
            found[signal_type] = list(set(matches))

    if not found:
        continue

    # Check if FEMALE_TITLE is just MS Office
    if 'FEMALE_TITLE' in found:
        ms_only = all(m in ['ms', 'ms.'] for m in found['FEMALE_TITLE'])
        if ms_only and is_ms_office(text):
            del found['FEMALE_TITLE']
            if not found:
                continue

    has_critical = any(t in CRITICAL_TYPES for t in found) or 'FEMALE_TITLE' in found
    severity = 'CRITICAL — EXCLUDE' if has_critical else 'MILD — REVIEW'

    signal_summary = '; '.join([f"{k}: {', '.join(v)}" for k, v in found.items()])
    rows.append([cv_id, category, severity, signal_summary])

rows.sort(key=lambda x: (x[1], x[2], x[0]))

with open('gender_signals_report.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['CV_ID', 'Category', 'Severity', 'Signals Found'])
    writer.writerows(rows)

critical = [r for r in rows if 'CRITICAL' in r[2]]
mild = [r for r in rows if 'MILD' in r[2]]
total = len(df)

print(f"Total CVs in target domains: {total}")
print(f"Clean CVs (no signals):      {total - len(rows)}")
print(f"CRITICAL — EXCLUDE:          {len(critical)}")
print(f"MILD — REVIEW:               {len(mild)}")
print(f"\nBreakdown by domain:")

from collections import defaultdict
by_domain = defaultdict(lambda: {'total': 0, 'critical': 0, 'mild': 0, 'clean': 0})
for _, row_data in df.iterrows():
    by_domain[row_data['Category']]['total'] += 1

for r in critical:
    by_domain[r[1]]['critical'] += 1
for r in mild:
    by_domain[r[1]]['mild'] += 1
for cat in by_domain:
    by_domain[cat]['clean'] = by_domain[cat]['total'] - by_domain[cat]['critical'] - by_domain[cat]['mild']

print(f"\n{'Domain':<25} {'Total':>7} {'Clean':>7} {'Critical':>10} {'Mild':>7}")
print("-" * 60)
for domain in sorted(by_domain.keys()):
    d = by_domain[domain]
    print(f"{domain:<25} {d['total']:>7} {d['clean']:>7} {d['critical']:>10} {d['mild']:>7}")

print(f"\nReport saved")
