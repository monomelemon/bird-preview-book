#!/usr/bin/env python3
"""Apply authoritative Chinese names from IOC World Bird List v15.2 to species.json."""

import openpyxl
import json
import sys

from text_utils import to_simplified

MANUAL_ALIASES = {
    "Alaudala cheleensis": ["短趾百灵"],
}

xlsx_path = '/tmp/IOC_Multilingual_v15.2.xlsx'
wb = openpyxl.load_workbook(xlsx_path, read_only=True)
ws = wb.active

ioc_names = {}
for row in ws.iter_rows(min_row=2, values_only=True):
    sci = row[3] if len(row) > 3 else None
    cn = row[6] if len(row) > 6 else None
    if sci and cn:
        sci = str(sci).strip()
        cn = to_simplified(str(cn).strip())
        if cn and sci:
            ioc_names[sci] = cn

print(f'IOC entries with Chinese names: {len(ioc_names)}')

species = json.load(open('data/species.json'))
matched = 0
unmatched = []

for sp in species:
    sci = sp['scientificName']
    old_name = to_simplified(sp['chineseName']).strip()
    sp['chineseName'] = old_name
    if sci in ioc_names:
        new_name = ioc_names[sci]
        if old_name != new_name:
            if old_name not in sp.get('aliases', []):
                sp.setdefault('aliases', []).append(old_name)
        sp['chineseName'] = new_name
        matched += 1
    else:
        unmatched.append(f"{sp['birdId']} | {sci} | {sp['chineseName']}")

    aliases = []
    seen = set()
    for alias in [*(sp.get('aliases') or []), *MANUAL_ALIASES.get(sci, [])]:
        alias = to_simplified(alias).strip()
        if alias and alias != sp['chineseName'] and alias not in seen:
            aliases.append(alias)
            seen.add(alias)
    sp['aliases'] = aliases

print(f'Matched: {matched}/{len(species)}')
print(f'Unmatched: {len(unmatched)}')
for u in unmatched:
    print(f'  {u}')

json.dump(species, open('data/species.json', 'w'), ensure_ascii=False, indent=2)
print('species.json written')
