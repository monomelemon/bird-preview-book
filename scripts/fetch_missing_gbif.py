#!/usr/bin/env python3
"""Fetch GBIF data for 21 species that were missed due to IOC/GBlF name mismatch.

Uses the same logic as fetch_gbif.py but only processes the 21 fixable species
and merges results into the existing gbif_raw.json.
"""

import json
import sys
import time
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

GBIF_NAME_MAP: dict[str, str] = {
    "Botaurus cinnamomeus": "Ixobrychus cinnamomeus",
    "Botaurus eurhythmus": "Ixobrychus eurhythmus",
    "Botaurus sinensis": "Ixobrychus sinensis",
    "Botaurus flavicollis": "Ixobrychus flavicollis",
    "Butorides atricapilla": "Butorides striata",
    "Ardea coromanda": "Bubulcus coromandus",
    "Tachyspiza gularis": "Accipiter gularis",
    "Tachyspiza virgata": "Accipiter virgatus",
    "Tachyspiza soloensis": "Accipiter soloensis",
    "Ictinaetus malaiensis": "Ictinaetus malayensis",
    "Astur gentilis": "Accipiter gentilis",
    "Lophospiza trivirgata": "Accipiter trivirgatus",
    "Thinornis dubius": "Charadrius dubius",
    "Thinornis placidus": "Charadrius placidus",
    "Anarhynchus mongolus": "Charadrius mongolus",
    "Anarhynchus atrifrons": "Charadrius atrifrons",
    "Larus mongolicus": "Larus vegae",
    "Anthus japonicus": "Anthus rubescens",
    "Cinnyris ornatus": "Cinnyris jugularis",
    "Tarsiger albocoeruleus": "Tarsiger cyanurus",
}

GBIF_TAXON_KEY_MAP: dict[str, int] = {
    "Chloris sinica": 6101015,
}

PROVINCE_MAP = {
    "Beijing": "北京",
    "Tianjin": "天津",
    "Hebei": "河北",
    "Shanxi": "山西",
    "Nei Mongol": "内蒙古",
    "Inner Mongolia": "内蒙古",
    "Liaoning": "辽宁",
    "Jilin": "吉林",
    "Heilongjiang": "黑龙江",
    "Shanghai": "上海",
    "Jiangsu": "江苏",
    "Zhejiang": "浙江",
    "Anhui": "安徽",
    "Fujian": "福建",
    "Jiangxi": "江西",
    "Shandong": "山东",
    "Henan": "河南",
    "Hubei": "湖北",
    "Hunan": "湖南",
    "Guangdong": "广东",
    "Guangxi": "广西",
    "Hainan": "海南",
    "Chongqing": "重庆",
    "Sichuan": "四川",
    "Guizhou": "贵州",
    "Yunnan": "云南",
    "YunNan": "云南",
    "Xizang": "西藏",
    "Tibet": "西藏",
    "Shaanxi": "陕西",
    "Gansu": "甘肃",
    "Qinghai": "青海",
    "Ningxia": "宁夏",
    "Xinjiang": "新疆",
    "Xinjiang Uygur": "新疆",
    "Sinkiang": "新疆",
}


def normalise_province(raw: str) -> str | None:
    if not raw:
        return None
    name = raw.strip()
    if name.lower() == "china":
        return None
    mapped = PROVINCE_MAP.get(name)
    if mapped:
        return mapped
    for key, val in PROVINCE_MAP.items():
        if key.lower() == name.lower():
            return val
    if any('\u4e00' <= c <= '\u9fff' for c in name):
        return name
    return None


SESSION = requests.Session()
SESSION.headers["User-Agent"] = (
    "BirdPreviewBook/3.0 (educational; monomelemon/bird-preview-book)"
)


def fetch_species_gbif(scientific_name, taxon_key=None):
    if taxon_key:
        url = (
            f"https://api.gbif.org/v1/occurrence/search"
            f"?country=CN&taxonKey={taxon_key}"
            f"&facet=stateProvince&facet=month&limit=0"
        )
    else:
        encoded = urllib.parse.quote(scientific_name, safe="")
        url = (
            f"https://api.gbif.org/v1/occurrence/search"
            f"?country=CN&scientificName={encoded}"
            f"&facet=stateProvince&facet=month&limit=0"
        )
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  [ERROR] {scientific_name}: {exc}", file=sys.stderr)
        return None

    province_counts: dict[str, int] = {}
    month_counts: dict[int, int] = {}

    for facet in data.get("facets", []):
        field = facet.get("field", "")
        for entry in facet.get("counts", []):
            entry_name = entry.get("name", "")
            count = entry.get("count", 0)
            if field == "STATE_PROVINCE":
                zh = normalise_province(entry_name)
                if zh and count >= 3:
                    province_counts[zh] = province_counts.get(zh, 0) + count
            elif field == "MONTH":
                try:
                    month_int = int(entry_name)
                    if 1 <= month_int <= 12 and count >= 3:
                        month_counts[month_int] = month_counts.get(month_int, 0) + count
                except (ValueError, TypeError):
                    pass

    if not province_counts:
        return None

    months_list = sorted(month_counts.keys())
    return {p: months_list for p in province_counts}


def main():
    species_list = json.loads((DATA / "species.json").read_text(encoding="utf-8"))
    gbif_data = json.loads((DATA / "gbif_raw.json").read_text(encoding="utf-8"))

    fixable_ids = set()
    for sci in GBIF_NAME_MAP:
        for sp in species_list:
            if sp["scientificName"] == sci:
                fixable_ids.add(sp["birdId"])
                break
    for sci in GBIF_TAXON_KEY_MAP:
        for sp in species_list:
            if sp["scientificName"] == sci:
                fixable_ids.add(sp["birdId"])
                break

    print(f"Missing species with fixable names: {len(fixable_ids)}")
    count_new = 0

    for sp in species_list:
        bird_id = sp["birdId"]
        if bird_id not in fixable_ids:
            continue
        if bird_id in gbif_data:
            print(f"  SKIP {bird_id} — already in gbif_raw.json")
            continue

        sci_name = sp["scientificName"]
        query_name = GBIF_NAME_MAP.get(sci_name, sci_name)
        taxon_key = GBIF_TAXON_KEY_MAP.get(sci_name)

        print(f"  [{bird_id}] {sci_name} -> {query_name}" +
              (f" (taxonKey={taxon_key})" if taxon_key else ""))

        result = fetch_species_gbif(query_name, taxon_key=taxon_key)
        if result:
            gbif_data[bird_id] = result
            count_new += 1
            provinces = list(result.keys())
            print(f"    OK: {len(provinces)} provinces — {', '.join(provinces[:5])}{'...' if len(provinces) > 5 else ''}")
        else:
            print(f"    NO DATA (even with mapped name)")

        time.sleep(1)

    (DATA / "gbif_raw.json").write_text(
        json.dumps(gbif_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nDone: {count_new} species added, total now {len(gbif_data)} in gbif_raw.json")


if __name__ == "__main__":
    main()
