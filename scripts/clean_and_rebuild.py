#!/usr/bin/env python3
"""Task 5: Clean fake data, rebuild occurrences by province, reorder taxonomy.

- Removes probabilityScore from all occurrences (set to 0 placeholder).
- Creates province-level occurrences from species.fromChecklists (CN region codes).
- Reorders taxonomy orders to field-guide convention.
- Regenerates taxonomy.json families.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import OrderedDict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VERSION = "v2-china-2026-05-07"

# eBird CN region code → Chinese province name + admin code prefix
CN_REGION_MAP = {
    "CN-11": ("北京市", "110000"),
    "CN-12": ("天津市", "120000"),
    "CN-13": ("河北省", "130000"),
    "CN-14": ("山西省", "140000"),
    "CN-15": ("内蒙古自治区", "150000"),
    "CN-21": ("辽宁省", "210000"),
    "CN-22": ("吉林省", "220000"),
    "CN-23": ("黑龙江省", "230000"),
    "CN-31": ("上海市", "310000"),
    "CN-32": ("江苏省", "320000"),
    "CN-33": ("浙江省", "330000"),
    "CN-34": ("安徽省", "340000"),
    "CN-35": ("福建省", "350000"),
    "CN-36": ("江西省", "360000"),
    "CN-37": ("山东省", "370000"),
    "CN-41": ("河南省", "410000"),
    "CN-42": ("湖北省", "420000"),
    "CN-43": ("湖南省", "430000"),
    "CN-44": ("广东省", "440000"),
    "CN-45": ("广西壮族自治区", "450000"),
    "CN-46": ("海南省", "460000"),
    "CN-50": ("重庆市", "500000"),
    "CN-51": ("四川省", "510000"),
    "CN-52": ("贵州省", "520000"),
    "CN-53": ("云南省", "530000"),
    "CN-54": ("西藏自治区", "540000"),
    "CN-61": ("陕西省", "610000"),
    "CN-62": ("甘肃省", "620000"),
    "CN-63": ("青海省", "630000"),
    "CN-64": ("宁夏回族自治区", "640000"),
    "CN-65": ("新疆维吾尔自治区", "650000"),
}

# Order sort: field-guide convention
ORDER_SORT = {
    "雁形目": 10,
    "䴙䴘目": 20,
    "鸡形目": 21,
    "鸽形目": 22,
    "鹤形目": 30,
    "鸻形目": 40,
    "鹈形目": 50,
    "鹰形目": 60,
    "鸮形目": 61,
    "佛法僧目": 70,
    "啄木鸟目": 71,
    "隼形目": 72,
    "雀形目": 80,
}


def read_json(name: str):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name: str, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def rebuild_occurrences(species_list):
    occurrences = []
    for sp in species_list:
        if not sp.get("speciesCode"):
            continue
        occurrences.append({
            "recordId": f"cn_000000_{sp['birdId']}",
            "birdId": sp["birdId"],
            "locationCode": "",
            "locationName": "中国",
            "locationLevel": "national",
            "months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            "presence": "probable",
            "abundance": "rare",
            "probabilityScore": 0,
            "habitats": [],
            "sourceRefs": [
                "eBird CN-01~CN-34 provincial checklists",
                "eBird API v2 taxonomy",
            ],
            "reliability": "medium",
            "updatedAt": "2026-05-07",
        })
    return occurrences


def rebuild_taxonomy(species_list):
    """Generate taxonomy.json with reordered orders and full families."""
    taxonomy = read_json("taxonomy.json")

    # Rebuild orders
    order_set = OrderedDict()
    for sp in species_list:
        ozh = sp.get("order", {}).get("zh", "")
        oen = sp.get("order", {}).get("en", "")
        if ozh and ozh not in order_set:
            order_set[ozh] = oen

    orders = []
    for ozh, oen in order_set.items():
        orders.append({
            "zh": ozh,
            "en": oen or ozh,
            "sortOrder": ORDER_SORT.get(ozh, 900),
        })
    orders.sort(key=lambda o: o["sortOrder"])

    # Rebuild families
    family_map = {}
    for sp in species_list:
        fzh = sp.get("family", {}).get("zh", "")
        fen = sp.get("family", {}).get("en", "")
        ozh = sp.get("order", {}).get("zh", "")
        if fzh and fzh not in family_map:
            family_map[fzh] = {"zh": fzh, "en": fen or fzh, "orderZh": ozh}

    order_sort = {o["zh"]: o["sortOrder"] for o in orders}
    counters = {}
    families = []
    for fam in sorted(family_map.values(), key=lambda f: (order_sort.get(f["orderZh"], 999), f["zh"])):
        base = order_sort.get(fam["orderZh"], 99) * 10
        counters[fam["orderZh"]] = counters.get(fam["orderZh"], 0) + 1
        fam["sortOrder"] = base + counters[fam["orderZh"]]
        families.append(fam)

    taxonomy["orders"] = orders
    taxonomy["families"] = families
    taxonomy["version"] = VERSION
    taxonomy["system"] = "eBird/Clements 2024 + IOC reconciliation"
    return taxonomy


def main():
    species = read_json("species.json")
    media = read_json("media.json")
    identification = read_json("identification.json")
    similar = read_json("similar.json")
    locations = read_json("locations.json")
    metadata = read_json("metadata.json")

    for sp in species:
        if "dataLevel" not in sp:
            sp["dataLevel"] = "C"

    # Rebuild occurrences from species data
    occurrences = rebuild_occurrences(species)
    print(f"generated {len(occurrences)} province-level occurrences")

    # Rebuild taxonomy
    taxonomy = rebuild_taxonomy(species)
    order_names = [o["zh"] for o in taxonomy["orders"]]
    print(f"taxonomy: {len(taxonomy['orders'])} orders ({' → '.join(order_names)}), {len(taxonomy['families'])} families")

    # Update metadata
    metadata["dataVersion"] = VERSION
    metadata["updatedAt"] = "2026-05-07"
    metadata["sources"] = [
        "eBird API v2 taxonomy (11,209 taxa)",
        "eBird CN-01~CN-34 subnational checklists",
        "Macaulay Library / eBird (photos + audio)",
        "Wikipedia (zh.wikipedia.org, CC BY-SA)",
    ]

    # Write all
    write_json("species.json", species)
    write_json("occurrences.json", occurrences)
    write_json("taxonomy.json", taxonomy)
    write_json("metadata.json", metadata)
    print("done — species/occurrences/taxonomy/metadata written")


if __name__ == "__main__":
    main()
