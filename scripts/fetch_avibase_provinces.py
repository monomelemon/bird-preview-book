#!/usr/bin/env python3
"""Fetch Avibase provincial checklists to build species→province distribution map.

Usage:
  python3 scripts/fetch_avibase_provinces.py [--limit N]
"""

import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Avibase province region codes
PROVINCE_CODES = {
    "CNxi": "新疆",
    "CNti": "西藏",
    "CNga": "甘肃",
    "CNqi": "青海",
    "CNsi": "四川",
    "CNyu": "云南",
    "CNin": "内蒙古",
    "CNni": "宁夏",
    "CNsh": "陕西",
    "CNcg": "重庆",
    "CNgu": "贵州",
    "CNgz": "广西",
    "CNsx": "山西",
    "CNha": "河南",
    "CNhb": "湖北",
    "CNhu": "湖南",
    "CNgd": "广东",
    "CNhi": "海南",
    "CNhe": "河北",
    "CNbj": "北京",
    "CNtj": "天津",
    "CNsg": "山东",
    "CNan": "安徽",
    "CNjs": "江苏",
    "CNjx": "江西",
    "CNfu": "福建",
    "CNzh": "浙江",
    "CNsn": "上海",
    "CNli": "辽宁",
    "CNji": "吉林",
    "CNhg": "黑龙江",
}

# Species row regex (same as fetch_avibase_china.py)
ROW_RE = re.compile(
    r"<tr[^>]*>\s*"
    r"<td>\s*(.+?)\s*</td>\s*"
    r"<td><a\s+href=\"species\.jsp\?avibaseid=([A-F0-9]+)\">\s*"
    r"<i>(.+?)</i></a></td>\s*"
    r"<td>(.*?)</td>\s*"
    r"<td>((?:(?!</td>).)*?)</td>\s*"
    r"</tr>",
    re.DOTALL,
)


def fetch_checklist(region_code):
    """Fetch and parse a province checklist, return set of scientific names."""
    url = (
        f"https://avibase.bsc-eoc.org/checklist.jsp"
        f"?region={region_code}&list=clements&lang=ZH&format=text"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "BirdPreviewBook/3.0 (educational; opensource)",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            html = resp.read().decode("utf-8")
    except Exception as e:
        print(f"    ERROR: {e}", flush=True)
        return set()

    species = set()
    for m in ROW_RE.finditer(html):
        scientific_name = m.group(3).strip()
        species.add(scientific_name)

    return species


def main():
    import sys
    limit_arg = None
    for arg in sys.argv:
        if arg.startswith("--limit="):
            limit_arg = int(arg.split("=")[1])

    codes = list(PROVINCE_CODES.items())
    if limit_arg:
        codes = codes[:limit_arg]

    print(f"Fetching {len(codes)} provincial checklists...", flush=True)

    results = {}
    total_species = set()

    for i, (code, name) in enumerate(codes):
        print(f"[{i+1}/{len(codes)}] {name} ({code})...", end=" ", flush=True)
        species = fetch_checklist(code)
        results[code] = list(species)
        total_species.update(species)
        print(f"{len(species)} species", flush=True)

        # Rate limiting: 2s between requests
        if i < len(codes) - 1:
            time.sleep(2)

    # Also include the national checklist for cross-reference
    print(f"\nTotal unique species across all provinces: {len(total_species)}")

    # Build species→province reverse map
    sci_to_provinces = {}
    for code, name in PROVINCE_CODES.items():
        species_set = set(results.get(code, []))
        for sci_name in species_set:
            if sci_name not in sci_to_provinces:
                sci_to_provinces[sci_name] = []
            sci_to_provinces[sci_name].append(name)

    output = {
        "provinceList": list(PROVINCE_CODES.values()),
        "provinceCodes": {v: k for k, v in PROVINCE_CODES.items()},
        "speciesDistribution": sci_to_provinces,
        "stats": {
            "totalProvinces": len(PROVINCE_CODES),
            "totalSpeciesAcrossProvinces": len(total_species),
            "speciesWithDistribution": len(sci_to_provinces),
        },
    }

    out_path = DATA / "avibase_provinces.json"
    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nResults written to {out_path}")
    print(f"  Provinces: {output['stats']['totalProvinces']}")
    print(f"  Species with province data: {output['stats']['speciesWithDistribution']}")

    # Per-province breakdown
    print("\nPer province:")
    for code, name in sorted(PROVINCE_CODES.items(), key=lambda x: x[1]):
        count = len(results.get(code, []))
        print(f"  {name}: {count} species")


if __name__ == "__main__":
    main()
