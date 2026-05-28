#!/usr/bin/env python3
"""Parse CBR Checklist of Birds of China (2005) PDF for residence type data - v2."""

import pdfplumber
import json
import re

pdf = pdfplumber.open('/tmp/cbr_checklist.pdf')

all_text = ""
for page in pdf.pages:
    t = page.extract_text()
    if t:
        all_text += t + "\n"

# Only keep the species section (from "一、中国鸟类分类与分布名录" to "二、中国特有种鸟类名录")
species_start = all_text.find('一、中国鸟类分类与分布名录')
endemic_start = all_text.find('二、中国特有种鸟类名录')
if species_start >= 0:
    all_text = all_text[species_start:]
if endemic_start >= 0:
    all_text = all_text[:endemic_start]

# Remove page markers like ·1·, ·2· etc
all_text = re.sub(r'·\d+·', '', all_text)

# Remove order/family header lines
all_text = re.sub(r'\n[IVX]+\.\s+\S+目\s+\S+', '\n', all_text)
all_text = re.sub(r'\n\d+\.\s+\S+科\s+[^\n]+', '\n', all_text)

# Remove the header itself
all_text = re.sub(r'一、中国鸟类分类与分布名录\n', '', all_text)

print(f"Text length after initial cleaning: {len(all_text)}")

# Strategy: The species entries are separated by blank lines or page breaks.
# Each entry has: ChineseName EnglishName | ScientificName | subspecies/residence | provinces

# Normalize line breaks and collapse whitespace
all_text = all_text.strip()

# Split by species entry patterns
# A new species starts with a line that has Chinese characters followed by English text
# Pattern: ^[Chinese]+ [A-Z][a-z] 

lines = all_text.split('\n')
non_empty_lines = [l.strip() for l in lines if l.strip()]

# Identify species name lines (Chinese + English on same line)
species_name_pattern = re.compile(r'^([\u4e00-\u9fff]+)\s+([A-Z][A-Za-z\-\'\s]+)$')

species_raw = []
i = 0
while i < len(non_empty_lines):
    line = non_empty_lines[i]
    m = species_name_pattern.match(line)
    if m:
        chinese_name = m.group(1)
        english_name = m.group(2)
        
        # Gather all lines belonging to this species
        entry_lines = [line]
        i += 1
        while i < len(non_empty_lines):
            next_line = non_empty_lines[i]
            # Stop at next species or order/family header
            if species_name_pattern.match(next_line):
                break
            if re.match(r'^[IVX]+\.\s+', next_line) or re.match(r'^\d+\.\s+', next_line):
                break
            entry_lines.append(next_line)
            i += 1
        
        species_raw.append(entry_lines)
        continue
    i += 1

print(f"Raw species entries found: {len(species_raw)}")

# Parse each entry
def extract_sci_name(entry_lines):
    """Extract scientific name from entry - the first line without Chinese characters."""
    for line in entry_lines:
        if not any('\u4e00' <= c <= '\u9fff' for c in line):
            # Skip lines that are purely region codes (e.g., "B C A")
            if re.match(r'^[IVXABCD]+\s*[ABCD]*\s*[ABCD]*\s*[ABCD]*$', line.strip()):
                continue
            # Skip lines that start with —
            if line.startswith('—'):
                continue
            # This should be the scientific name line
            parts = line.split()
            if len(parts) >= 2:
                # Remove subspecies info after "—"
                name = line
                if '—' in name:
                    name = name.split('—')[0].strip()
                return name.strip()
    return ''

def extract_residence_types(entry_lines):
    """Extract all residence type codes from the entry."""
    all_text = ' '.join(entry_lines)
    codes = set()
    matches = re.findall(r'\(([RSWPV,\s]+)\)', all_text)
    for m in matches:
        for c in m.split(','):
            c = c.strip()
            if c in ('R', 'S', 'W', 'P', 'V'):
                codes.add(c)
    return sorted(codes)

def extract_provinces(entry_lines):
    """Extract province names from entry."""
    province_patterns = [
        '黑龙江', '吉林', '辽宁', '河北', '北京', '天津', '山东', '河南',
        '山西', '陕西', '宁夏', '甘肃', '内蒙古', '新疆', '西藏', '云南',
        '贵州', '四川', '重庆', '湖北', '湖南', '安徽', '江西', '江苏',
        '上海', '浙江', '福建', '广东', '香港', '广西', '海南', '台湾', '青海'
    ]
    all_text = ' '.join(entry_lines)
    provinces = set()
    
    for p in province_patterns:
        if p in all_text:
            provinces.add(p)
    
    return sorted(provinces)

def extract_region_codes(entry_lines):
    """Extract geographic region codes like I_B, II_A, etc."""
    all_text_lines = entry_lines
    # Region codes appear as lines like "I (W, S, P), I (W, P), II (W, P), VI (W, P)"
    # with sub-region codes on next lines: "B C A A"
    regions = set()
    for line in all_text_lines:
        matches = re.findall(r'([IVX]+)\s*\(', line)
        for m in matches:
            regions.add(m)
    return sorted(regions)

def residence_to_months(codes):
    """Convert R/S/W/P/V codes to month arrays."""
    months = set()
    for code in codes:
        if code == 'R':
            months.update(range(1, 13))
        elif code == 'S':
            months.update([4, 5, 6, 7, 8, 9])
        elif code == 'W':
            months.update([10, 11, 12, 1, 2, 3])
        elif code == 'P':
            months.update([3, 4, 5, 8, 9, 10])
    return sorted(months) if months else []

# Build CBR data
cbr_data = {}
for entry_lines in species_raw:
    # Get the first line (species name line)
    name_match = species_name_pattern.match(entry_lines[0])
    if not name_match:
        continue
    cn_name = name_match.group(1)
    
    sci_name = extract_sci_name(entry_lines)
    if not sci_name:
        continue
    
    residence = extract_residence_types(entry_lines)
    months = residence_to_months(residence)
    provinces = extract_provinces(entry_lines)
    
    # Handle "见于各省" and "All" patterns
    all_text = ' '.join(entry_lines)
    if '见于各省' in all_text or 'All' in all_text:
        all_provinces_list = [
            '黑龙江', '吉林', '辽宁', '河北', '北京', '天津', '山东', '河南',
            '山西', '陕西', '宁夏', '甘肃', '内蒙古', '新疆', '西藏', '云南',
            '贵州', '四川', '重庆', '湖北', '湖南', '安徽', '江西', '江苏',
            '上海', '浙江', '福建', '广东', '香港', '广西', '海南', '台湾', '青海'
        ]
        provinces = sorted(all_provinces_list)
    
    # Normalize key: first two words
    key = sci_name.strip()
    
    if key in cbr_data:
        # Merge residence types
        old = cbr_data[key]
        old['residence_types'] = sorted(set(old['residence_types'] + residence))
        old['months'] = residence_to_months(old['residence_types'])
        old['provinces'] = sorted(set(old['provinces'] + provinces))
    else:
        cbr_data[key] = {
            'scientific_name': sci_name,
            'chinese_name_cbr': cn_name,
            'residence_types': residence,
            'months': months,
            'provinces': provinces,
        }

print(f"CBR entries parsed: {len(cbr_data)}")

# Match to our species
species = json.load(open('data/species.json'))
matched = 0
unmatched = []
cbr_matched = {}

for sp in species:
    sci = sp['scientificName']
    if sci in cbr_data:
        cbr_matched[sci] = cbr_data[sci]
        matched += 1
    else:
        unmatched.append(f"{sp['birdId']} | {sci} | {sp['chineseName']}")

print(f"CBR matched to species: {matched}/{len(species)}")
print(f"CBR unmatched: {len(unmatched)}")

# Save
json.dump(cbr_matched, open('/tmp/cbr_residence_data.json', 'w'), ensure_ascii=False, indent=2)
print(f"Saved {len(cbr_matched)} entries to /tmp/cbr_residence_data.json")

# Stats
r_count = sum(1 for v in cbr_matched.values() if 'R' in v['residence_types'])
s_count = sum(1 for v in cbr_matched.values() if 'S' in v['residence_types'])
w_count = sum(1 for v in cbr_matched.values() if 'W' in v['residence_types'])
p_count = sum(1 for v in cbr_matched.values() if 'P' in v['residence_types'])
v_count = sum(1 for v in cbr_matched.values() if 'V' in v['residence_types'])
with_provinces = sum(1 for v in cbr_matched.values() if v['provinces'])
with_months = sum(1 for v in cbr_matched.values() if v['months'])
print(f"Resident(R): {r_count}, Summer(S): {s_count}, Winter(W): {w_count}, Passage(P): {p_count}, Vagrant(V): {v_count}")
print(f"With provinces: {with_provinces}, With months: {with_months}")

if unmatched:
    print(f"\nFirst 20 unmatched:")
    for u in unmatched[:20]:
        print(f"  {u}")
