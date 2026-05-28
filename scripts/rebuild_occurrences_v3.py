#!/usr/bin/env python3
"""Rebuild occurrences.json v3: CBR residence-based months + IOC names, remove GBIF records."""

import json

species = json.load(open('data/species.json'))
occurrences = json.load(open('data/occurrences.json'))
locations = json.load(open('data/locations.json'))
cbr_data = json.load(open('/tmp/cbr_residence_data.json'))

print(f"Species count: {len(species)}")
print(f"Occurrences count: {len(occurrences)}")
print(f"CBR residence entries: {len(cbr_data)}")

# Step 1: Remove non-native species (e.g., Black Swan)
non_native_ids = {'blkswa'}
before = len(species)
species = [s for s in species if s['birdId'] not in non_native_ids]
print(f"Removed non-native species: {before - len(species)}")

# Step 2: Keep only manual records from current occurrences and fix birdId mapping
# Map old underscore-based birdIds to correct eBird species codes
birdid_mapping = {
    'himantopus_himantopus': 'bkwsti',
    'recurvirostra_avosetta': 'pieavo1',
    'charadrius_dubius': 'lirplo',
    'charadrius_alexandrinus': 'kenplo1',
    'pluvialis_squatarola': 'bkbplo',
    'actitis_hypoleucos': 'comsan',
    'tringa_totanus': 'comred1',
    'tringa_nebularia': 'comgre',
    'pluvialis_fulva': 'pagplo',
    'charadrius_mongolus': 'lessap2',
    'limosa_lapponica': 'batgod',
    'limosa_limosa': 'bktgod',
    'numenius_madagascariensis': 'faecur',
    'numenius_arquata': 'eurcur',
    'calidris_tenuirostris': 'grekno',
    'calidris_canutus': 'redkno',
    'calidris_acuminata': 'shtsan',
    'calidris_ruficollis': 'rensti',
    'tringa_stagnatilis': 'marsan',
    'tringa_glareola': 'woosan',
    'tringa_erythropus': 'spored',
    'xenus_cinereus': 'tersan',
    'tringa_brevipes': 'gyttat1',
}

manual_records_raw = [o for o in occurrences if 'manual' in str(o.get('sourceRefs', ''))]
manual_records = []
for rec in manual_records_raw:
    rec = dict(rec)
    old_id = rec['birdId']
    if old_id in birdid_mapping:
        rec['birdId'] = birdid_mapping[old_id]
        rec['recordId'] = rec['recordId'].replace(old_id, birdid_mapping[old_id])
    manual_records.append(rec)

print(f"Kept manual records: {len(manual_records)}")

# Step 3: Build province location map
# Location JSON uses: code, name, level
# Occurrences use: locationCode, locationName, locationLevel
province_map = {}
for loc in locations:
    if loc.get('level') == 'province':
        # Map both full name and short variants
        name = loc['name']
        province_map[name] = loc['code']
        # Also add without 省/市/自治区 suffix
        short = name.replace('省', '').replace('市', '').replace('自治区', '').replace('特别行政区', '')
        if short != name:
            province_map[short] = loc['code']

print(f"Province locations: {len(set(v for v in province_map.values()))}")

# CBR province short names to location full names
cbr_province_map = {
    '黑龙江': '黑龙江省',
    '吉林': '吉林省',
    '辽宁': '辽宁省',
    '河北': '河北省',
    '北京': '北京市',
    '天津': '天津市',
    '山东': '山东省',
    '河南': '河南省',
    '山西': '山西省',
    '陕西': '陕西省',
    '宁夏': '宁夏回族自治区',
    '甘肃': '甘肃省',
    '内蒙古': '内蒙古自治区',
    '新疆': '新疆维吾尔自治区',
    '西藏': '西藏自治区',
    '云南': '云南省',
    '贵州': '贵州省',
    '四川': '四川省',
    '重庆': '重庆市',
    '湖北': '湖北省',
    '湖南': '湖南省',
    '安徽': '安徽省',
    '江西': '江西省',
    '江苏': '江苏省',
    '上海': '上海市',
    '浙江': '浙江省',
    '福建': '福建省',
    '广东': '广东省',
    '广西': '广西壮族自治区',
    '海南': '海南省',
    '青海': '青海省',
}

def get_location_code(cbr_name):
    """Get location code from CBR province name."""
    full = cbr_province_map.get(cbr_name, cbr_name)
    return province_map.get(full)

# Build CBR-based occurrences
cbr_occurrences = []
cbr_source_refs = [
    "IOC World Bird List v15.2: https://www.worldbirdnames.org/new/",
    "CBR Checklist of Birds of China (2005): 郑光美主编，中国鸟类分类与分布名录"
]

record_counter = 0
cbr_bird_ids = set()

for sci_name, data in cbr_data.items():
    sp = next((s for s in species if s['scientificName'] == sci_name), None)
    if not sp:
        continue

    bird_id = sp['birdId']
    months = data.get('months', [])
    provinces = data.get('provinces', [])
    residence_types = data.get('residence_types', [])
    cbr_bird_ids.add(bird_id)

    if not provinces:
        record_counter += 1
        cbr_occurrences.append({
            'recordId': f'occ_{bird_id}_cbr_CN_{record_counter}',
            'birdId': bird_id,
            'locationCode': 'CN',
            'locationName': '中国',
            'locationLevel': 'country',
            'months': months,
            'presence': 'confirmed' if months else 'possible',
            'abundance': 'common' if 'R' in residence_types else 'uncommon',
            'probabilityScore': 0.95 if months else 0.5,
            'habitats': [],
            'sourceRefs': cbr_source_refs[:],
            'reliability': 'high',
            'updatedAt': '2026-05-08'
        })
        continue

    for province in provinces:
        loc_code = get_location_code(province)
        if not loc_code:
            continue

        record_counter += 1
        full_name = cbr_province_map.get(province, province)
        cbr_occurrences.append({
            'recordId': f'occ_{bird_id}_cbr_{loc_code}_{record_counter}',
            'birdId': bird_id,
            'locationCode': loc_code,
            'locationName': full_name,
            'locationLevel': 'province',
            'months': months,
            'presence': 'confirmed' if months else 'possible',
            'abundance': 'common' if 'R' in residence_types else 'uncommon',
            'probabilityScore': 0.95 if months else 0.5,
            'habitats': [],
            'sourceRefs': cbr_source_refs[:],
            'reliability': 'high',
            'updatedAt': '2026-05-08'
        })

print(f"CBR-based occurrences created: {len(cbr_occurrences)}")
print(f"CBR bird IDs with records: {len(cbr_bird_ids)}")

# Step 4: Combine
all_occurrences = manual_records + cbr_occurrences
print(f"Total occurrences: {len(all_occurrences)}")

# Step 5: Save
json.dump(species, open('data/species.json', 'w'), ensure_ascii=False, indent=2)
json.dump(all_occurrences, open('data/occurrences.json', 'w'), ensure_ascii=False, indent=2)

# Update metadata
metadata = json.load(open('data/metadata.json'))
metadata['dataVersion'] = 'v3-cbr-2026-05-08'
metadata['sources'] = [
    "IOC World Bird List v15.2 (Multilingual Version)",
    "CBR Checklist of Birds of China (2005) - partial extraction",
    "eBird API v2 taxonomy",
    "Wild Beijing Nanpu Tangshan 2011 manual records"
]
json.dump(metadata, open('data/metadata.json', 'w'), ensure_ascii=False, indent=2)

# Summary
all_bird_ids = set(o['birdId'] for o in all_occurrences)
species_ids = set(s['birdId'] for s in species)
no_occ = species_ids - all_bird_ids

print(f"\n=== SUMMARY ===")
print(f"Species: {len(species)}")
print(f"Occurrences: {len(all_occurrences)}")
print(f"  Manual records: {len(manual_records)}")
print(f"  CBR-based records: {len(cbr_occurrences)}")
print(f"Species with CBR data: {len(cbr_data)}")
print(f"Species with occurrences: {len(all_bird_ids)}")
print(f"Species without occurrences: {len(no_occ)}")
blkswa = [s for s in species if s['birdId'] == 'blkswa']
print(f"blkswa in species: {len(blkswa)} (should be 0)")

# Check Chinese names
non_cn = [s for s in species if not any('\u4e00' <= c <= '\u9fff' for c in s.get('chineseName', ''))]
print(f"Non-Chinese names remaining: {len(non_cn)}")
for n in non_cn[:5]:
    print(f"  {n['birdId']}: {n['chineseName']}")
