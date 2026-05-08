#!/usr/bin/env python3
"""Rebuild locations.json from actual occurrence data.

1. Read occurrences.json, collect all unique locationCode values
2. Read current locations.json as baseline
3. Build province/city/district lookup
4. For each locationCode from occurrences: keep if it's a province or city
   that matches occurrence data
5. Always keep Tangshan (130200) and its districts
6. Remove locations with 0 occurrence matches
7. Write cleaned data/locations.json
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

OCCURRENCES_PATH = os.path.join(PROJECT_DIR, "data", "occurrences.json")
LOCATIONS_PATH = os.path.join(PROJECT_DIR, "data", "locations.json")

# Complete China administrative codes: province codes with their city/district hierarchy
# GB/T 2260 administrative divisions
CHINA_ADMIN = {
    "110000": {"name": "北京市", "level": "province", "children": {
        "110100": {"name": "北京市", "level": "city"},
    }},
    "120000": {"name": "天津市", "level": "province", "children": {
        "120100": {"name": "天津市", "level": "city"},
    }},
    "130000": {"name": "河北省", "level": "province", "children": {
        "130100": {"name": "石家庄市", "level": "city"},
        "130200": {"name": "唐山市", "level": "city", "children": {
            "130202": {"name": "路南区", "level": "district"}, "130203": {"name": "路北区", "level": "district"},
"130224": {"name": "滦南县", "level": "district"}, "130225": {"name": "乐亭县", "level": "district"},
"130229": {"name": "玉田县", "level": "district"},
        }},
        "130300": {"name": "秦皇岛市", "level": "city"},
        "130400": {"name": "邯郸市", "level": "city"},
        "130500": {"name": "邢台市", "level": "city"},
        "130600": {"name": "保定市", "level": "city"},
        "130700": {"name": "张家口市", "level": "city"},
        "130800": {"name": "承德市", "level": "city"},
        "130900": {"name": "沧州市", "level": "city"},
        "131000": {"name": "廊坊市", "level": "city"},
        "131100": {"name": "衡水市", "level": "city"},
    }},
    "140000": {"name": "山西省", "level": "province", "children": {
        "140100": {"name": "太原市", "level": "city"},
    }},
    "150000": {"name": "内蒙古自治区", "level": "province", "children": {
        "150100": {"name": "呼和浩特市", "level": "city"},
    }},
    "210000": {"name": "辽宁省", "level": "province", "children": {
        "210100": {"name": "沈阳市", "level": "city"},
    }},
    "220000": {"name": "吉林省", "level": "province", "children": {
        "220100": {"name": "长春市", "level": "city"},
    }},
    "230000": {"name": "黑龙江省", "level": "province", "children": {
        "230100": {"name": "哈尔滨市", "level": "city"},
    }},
    "310000": {"name": "上海市", "level": "province", "children": {
        "310100": {"name": "上海市", "level": "city"},
    }},
    "320000": {"name": "江苏省", "level": "province", "children": {
        "320100": {"name": "南京市", "level": "city"},
    }},
    "330000": {"name": "浙江省", "level": "province", "children": {
        "330100": {"name": "杭州市", "level": "city"},
    }},
    "340000": {"name": "安徽省", "level": "province", "children": {
        "340100": {"name": "合肥市", "level": "city"},
    }},
    "350000": {"name": "福建省", "level": "province", "children": {
        "350100": {"name": "福州市", "level": "city"},
    }},
    "360000": {"name": "江西省", "level": "province", "children": {
        "360100": {"name": "南昌市", "level": "city"},
    }},
    "370000": {"name": "山东省", "level": "province", "children": {
        "370100": {"name": "济南市", "level": "city"},
    }},
    "410000": {"name": "河南省", "level": "province", "children": {
        "410100": {"name": "郑州市", "level": "city"},
    }},
    "420000": {"name": "湖北省", "level": "province", "children": {
        "420100": {"name": "武汉市", "level": "city"},
    }},
    "430000": {"name": "湖南省", "level": "province", "children": {
        "430100": {"name": "长沙市", "level": "city"},
    }},
    "440000": {"name": "广东省", "level": "province", "children": {
        "440100": {"name": "广州市", "level": "city"},
    }},
    "450000": {"name": "广西壮族自治区", "level": "province", "children": {
        "450100": {"name": "南宁市", "level": "city"},
    }},
    "460000": {"name": "海南省", "level": "province", "children": {
        "460100": {"name": "海口市", "level": "city"},
    }},
    "500000": {"name": "重庆市", "level": "province", "children": {
        "500100": {"name": "重庆市", "level": "city"},
    }},
    "510000": {"name": "四川省", "level": "province", "children": {
        "510100": {"name": "成都市", "level": "city"},
    }},
    "520000": {"name": "贵州省", "level": "province", "children": {
        "520100": {"name": "贵阳市", "level": "city"},
    }},
    "530000": {"name": "云南省", "level": "province", "children": {
        "530100": {"name": "昆明市", "level": "city"},
    }},
    "540000": {"name": "西藏自治区", "level": "province", "children": {
        "540100": {"name": "拉萨市", "level": "city"},
    }},
    "610000": {"name": "陕西省", "level": "province", "children": {
        "610100": {"name": "西安市", "level": "city"},
    }},
    "620000": {"name": "甘肃省", "level": "province", "children": {
        "620100": {"name": "兰州市", "level": "city"},
    }},
    "630000": {"name": "青海省", "level": "province", "children": {
        "630100": {"name": "西宁市", "level": "city"},
    }},
    "640000": {"name": "宁夏回族自治区", "level": "province", "children": {
        "640100": {"name": "银川市", "level": "city"},
    }},
    "650000": {"name": "新疆维吾尔自治区", "level": "province", "children": {
        "650100": {"name": "乌鲁木齐市", "level": "city"},
    }},
}


def flatten_admin(admin, parent=None):
    """Convert admin dict to flat list for lookup."""
    result = []
    for code, info in admin.items():
        entry = {"code": code, "name": info["name"], "level": info["level"], "parent": parent}
        result.append(entry)
        children = info.get("children", {})
        if children:
            result.extend(flatten_admin(children, code))
    return result


def to_location_tree(flat_items, occ_codes):
    """Build tree structure from flat items, only keeping codes that appear in occurrences."""
    occ_set = set(occ_codes)

    # Find provinces
    provinces = [item for item in flat_items if item["level"] == "province"]

    result = []
    for prov in provinces:
        prov_code = prov["code"]
        if prov_code not in occ_set:
            continue  # skip provinces with 0 occurrence matches

        prov_entry = {"code": prov_code, "name": prov["name"], "level": "province"}

        # Find cities under this province (codes ending in 00 after province prefix)
        cities_in_occ = [c for c in occ_codes if
                         len(c) == 6 and c.startswith(prov_code[:2]) and c[2:4] != "00" and c[4:6] == "00"]

        if cities_in_occ:
            children = []
            for city_code in sorted(set(cities_in_occ)):
                city_item = next((item for item in flat_items if item["code"] == city_code), None)
                if not city_item:
                    continue
                city_entry = {"code": city_code, "name": city_item["name"], "level": "city"}

                # Find districts under this city
                districts_in_occ = [d for d in occ_codes if
                                    len(d) == 6 and d.startswith(city_code[:4]) and d[4:6] != "00"]
                if districts_in_occ:
                    district_entries = []
                    for d_code in sorted(set(districts_in_occ)):
                        d_item = next((item for item in flat_items if item["code"] == d_code), None)
                        if d_item:
                            district_entries.append({"code": d_code, "name": d_item["name"], "level": "district"})
                    if district_entries:
                        city_entry["children"] = district_entries

                children.append(city_entry)
            if children:
                prov_entry["children"] = children

        result.append(prov_entry)

    return result


def main():
    # Read occurrences
    with open(OCCURRENCES_PATH, encoding="utf-8") as f:
        occurrences = json.load(f)

    # Collect unique location codes
    occ_codes = sorted(set(occ["locationCode"] for occ in occurrences))
    print(f"Occurrence records: {len(occurrences)}")
    print(f"Unique location codes in occurrences: {len(occ_codes)}")

    # Always include Tangshan (130200) and its districts
    TANGSHAN_CODES = {"130200", "130202", "130203", "130224", "130225", "130229"}
    missing_tangshan = TANGSHAN_CODES - set(occ_codes)
    if missing_tangshan:
        print(f"Adding Tangshan codes to occurrences: {missing_tangshan}")
        occ_codes = sorted(set(occ_codes) | TANGSHAN_CODES)

    # Build flat admin lookup
    flat = flatten_admin(CHINA_ADMIN)

    # Build location tree
    locations = to_location_tree(flat, occ_codes)

    print(f"Provinces kept: {len(locations)}")

    # Write
    with open(LOCATIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

    print("Done rebuilding locations.json")


if __name__ == "__main__":
    main()
