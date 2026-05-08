#!/usr/bin/env python3
"""Fetch GBIF province+month occurrence data for all species.

Calls GBIF occurrence search API per species. Extracts stateProvince and month
facets, normalises province names to Chinese, filters counts >= 3, and writes
data/gbif_raw.json as {birdId: {province_zh: [month_int, ...]}}.
"""

import json
import sys
import time
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

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


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


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


def fetch_species_gbif(scientific_name):
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
    species_list = read_json("species.json")
    total = len(species_list)

    result: dict[str, dict[str, list[int]]] = {}
    success_count = 0
    error_count = 0

    print(f"Fetching GBIF data for {total} species...")
    print(f"Rate limit: 1 s delay between calls (est. {total // 60 + 1} min)\n")

    for i, sp in enumerate(species_list, start=1):
        bird_id = sp["birdId"]
        sci_name = sp["scientificName"]

        time.sleep(1)

        if i % 50 == 0 or i == 1 or i == total:
            print(f"  [{i}/{total}] {sci_name} ...")

        gbif_data = fetch_species_gbif(sci_name)
        if gbif_data:
            result[bird_id] = gbif_data
            success_count += 1
        else:
            error_count += 1

    write_json("gbif_raw.json", result)

    provinces = set()
    for bird_data in result.values():
        provinces.update(bird_data.keys())

    print(f"\n{'─' * 40}")
    print(f"Done: {success_count} species had GBIF data ({error_count} had none)")
    print(f"{len(provinces)} provinces covered: {', '.join(sorted(provinces))}")
    print(f"Output written to data/gbif_raw.json")


if __name__ == "__main__":
    main()
