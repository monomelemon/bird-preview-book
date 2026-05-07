#!/usr/bin/env python3
"""Clean species names/families and add Macaulay/eBird photos.

This script is for local data preparation only. The eBird API key is read from
EBIRD_API_KEY and is never written to frontend files.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VERSION = "v1-macaulay-2026-05-07"

TRAD_TO_SIMP = str.maketrans({
    "凍": "冻", "鵝": "鹅", "鴨": "鸭", "鴛": "鸳", "鴦": "鸯", "鵠": "鹄",
    "鵰": "雕", "鷹": "鹰", "鷂": "鹞", "鷲": "鹫", "鶚": "鹗", "鶻": "鹘",
    "鷺": "鹭", "鶴": "鹤", "鷗": "鸥", "鷗": "鸥", "鴴": "鸻", "鷸": "鹬",
    "鵐": "鹀", "鶲": "鹟", "鵯": "鹎", "鶇": "鸫", "鴉": "鸦", "鵲": "鹊",
    "鴟": "鸱", "鵑": "鹃", "鶯": "莺", "鷦": "鹪", "鷯": "鹩", "鴞": "鸮",
    "雞": "鸡", "鷿": "䴙", "鸊": "䴘", "鵜": "鹈", "鸕": "鸬", "鷓": "鹧",
    "黃": "黄", "灣": "湾", "濱": "滨", "蹺": "跷", "紅": "红", "藍": "蓝",
    "綠": "绿", "烏": "乌", "鳳": "凤", "頭": "头", "頸": "颈", "嘴": "嘴",
    "長": "长", "腳": "脚", "翹": "翘", "斑": "斑", "臉": "脸", "雜": "杂",
    "極": "极", "賊": "贼", "蠣": "蛎", "潛": "潜", "鶘": "鹕", "額": "额", "鴻": "鸿",
    "劍": "剑", "寬": "宽", "棲": "栖", "漁": "渔", "禿": "秃", "細": "细", "緋": "绯",
    "脇": "胁", "蒼": "苍", "蘇": "苏", "諾": "诺", "遺": "遗", "頂": "顶", "簑": "蓑",
    "東": "东", "歐": "欧", "亞": "亚", "遷": "迁", "鶺": "鹡", "鴒": "鸰",
    "雛": "雏", "鳾": "鳾", "鶉": "鹑", "鵪": "鹌", "鴇": "鸨", "鴿": "鸽",
    "鸚": "鹦", "鵡": "鹉", "鵬": "鹏", "鷚": "鹨", "鱗": "鳞", "塒": "埘",
    "雲": "云", "為": "为", "華": "华", "臺": "台", "瀆": "渎", "鹽": "盐",
    "裏": "里", "裡": "里", "畫": "画", "點": "点", "廣": "广", "雙": "双",
    "學": "学", "體": "体", "類": "类", "種": "种", "鳥": "鸟", "鳴": "鸣",
    "觀": "观", "記": "记", "錄": "录", "據": "据", "貝": "贝", "門": "门",
})

MANUAL_CN = {
    "lobmur": "长嘴斑海雀",
    "ibisbi1": "鹮嘴鹬",
    "harduc": "丑鸭",
    "himgri1": "高山兀鹫",
    "rebgoo1": "红胸黑雁",
    "shteag1": "短趾雕",
    "steeag1": "草原雕",
    "swirai1": "花田鸡",
    "whwsco1": "斑脸海番鸭",
}

FAMILY_MAP = {
    "Auks, Murres, and Puffins": "海雀科",
    "Bulbuls": "鹎科",
    "Buttonquail": "三趾鹑科",
    "Cranes": "鹤科",
    "Crows, Jays, and Magpies": "鸦科",
    "Ducks, Geese, and Waterfowl": "鸭科",
    "Grebes": "䴙䴘科",
    "Gulls, Terns, and Skimmers": "鸥科",
    "Hawks, Eagles, and Kites": "鹰科",
    "Herons, Egrets, and Bitterns": "鹭科",
    "Ibisbill": "鹮嘴鹬科",
    "Ibises and Spoonbills": "鹮科",
    "Jacanas": "水雉科",
    "Kingfishers": "翠鸟科",
    "Osprey": "鹗科",
    "Oystercatchers": "蛎鹬科",
    "Painted-Snipes": "彩鹬科",
    "Pelicans": "鹈鹕科",
    "Plovers and Lapwings": "鸻科",
    "Pratincoles and Coursers": "燕鸻科",
    "Rails, Gallinules, and Coots": "秧鸡科",
    "Sandpipers and Allies": "鹬科",
    "Skuas and Jaegers": "贼鸥科",
    "Stilts and Avocets": "反嘴鹬科",
}

CJK_RE = re.compile(r"[\u3400-\u9fff\U00020000-\U0002ebe0]")


def read_json(name: str):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name: str, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def to_simplified(text: str) -> str:
    return str(text or "").translate(TRAD_TO_SIMP)


def is_cjk(text: str) -> bool:
    return bool(CJK_RE.search(str(text or "")))


def fetch_json(url: str, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ebird_taxonomy():
    key = os.environ.get("EBIRD_API_KEY", "").strip()
    if not key:
        print("EBIRD_API_KEY missing; names will be cleaned without eBird English backfill.")
        return {}
    url = "https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=json"
    data = fetch_json(url, {"X-eBirdApiToken": key})
    by_sci = {}
    for item in data:
        sci = item.get("sciName")
        if sci:
            by_sci[sci.lower()] = item
    print(f"loaded eBird taxonomy: {len(by_sci)} taxa")
    return by_sci


def macaulay_photos(taxon_code: str, limit=3):
    query = urllib.parse.urlencode({"taxonCode": taxon_code, "mediaType": "photo", "pageSize": limit})
    url = f"https://search.macaulaylibrary.org/api/v1/search?{query}"
    data = fetch_json(url)
    return data.get("results", {}).get("content", []) or []


def clean_species(species, taxonomy_by_sci):
    for sp in species:
        tax = taxonomy_by_sci.get(str(sp.get("scientificName", "")).lower(), {})
        if tax.get("speciesCode"):
            sp["speciesCode"] = tax["speciesCode"]
        sp["chineseName"] = MANUAL_CN.get(sp["birdId"], to_simplified(sp.get("chineseName", "")))
        if tax.get("comName") and (is_cjk(sp.get("englishName")) or not sp.get("englishName")):
            sp["englishName"] = tax["comName"]
        sp["englishName"] = str(sp.get("englishName", "")).strip()
        aliases = []
        seen = set()
        for alias in sp.get("aliases") or []:
            a = to_simplified(alias).strip()
            if a and a != sp["chineseName"] and a not in seen:
                aliases.append(a)
                seen.add(a)
        sp["aliases"] = aliases
        fam = sp.get("family") or {}
        raw_zh = fam.get("zh", "")
        raw_en = fam.get("en") or raw_zh
        zh = FAMILY_MAP.get(raw_zh) or FAMILY_MAP.get(raw_en) or to_simplified(raw_zh)
        sp["family"] = {"zh": zh, "en": raw_en}
        refs = sp.setdefault("sourceRefs", [])
        if tax.get("speciesCode") and "eBird API v2 taxonomy" not in refs:
            refs.append("eBird API v2 taxonomy")


def rebuild_taxonomy(taxonomy, species):
    order_sort = {o["zh"]: o.get("sortOrder", 999) for o in taxonomy.get("orders", [])}
    family_seen = {}
    for sp in species:
        fam = sp.get("family") or {}
        zh = fam.get("zh")
        if not zh or zh in family_seen:
            continue
        family_seen[zh] = {
            "zh": zh,
            "en": fam.get("en") or zh,
            "orderZh": sp.get("order", {}).get("zh", ""),
        }
    families = []
    counters = {}
    for fam in sorted(family_seen.values(), key=lambda f: (order_sort.get(f["orderZh"], 999), f["zh"])):
        base = order_sort.get(fam["orderZh"], 99) * 10
        counters[fam["orderZh"]] = counters.get(fam["orderZh"], 0) + 1
        fam["sortOrder"] = base + counters[fam["orderZh"]]
        families.append(fam)
    taxonomy["families"] = families
    taxonomy["version"] = VERSION


def ensure_media(media, bird_id):
    item = media.setdefault(bird_id, {})
    item.setdefault("images", [])
    item.setdefault("sounds", [])
    item.setdefault("rangeMap", None)
    return item


def add_photos(species, media, max_species=None):
    updated = 0
    targets = []
    for sp in species:
        item = ensure_media(media, sp["birdId"])
        if len(item["images"]) < 3 and sp.get("speciesCode"):
            targets.append(sp)
    if max_species:
        targets = targets[:max_species]

    def fetch_one(sp):
        try:
            return sp, macaulay_photos(sp["speciesCode"], 3), None
        except Exception as exc:
            return sp, [], exc

    done = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(fetch_one, sp) for sp in targets]
        for future in as_completed(futures):
            sp, photos, exc = future.result()
            done += 1
            if exc:
                print(f"photo fetch failed {sp['birdId']}: {exc}", flush=True)
                continue
            item = ensure_media(media, sp["birdId"])
            existing_sources = {img.get("sourceUrl") for img in item["images"]}
            existing_urls = {img.get("url") for img in item["images"]}
            for photo in photos:
                source_url = photo.get("specimenUrl") or (f"https://macaulaylibrary.org/asset/{photo.get('assetId')}" if photo.get("assetId") else "")
                url = photo.get("largeUrl") or photo.get("mediaUrl") or photo.get("previewUrl")
                if not url or source_url in existing_sources or url in existing_urls:
                    continue
                item["images"].append({
                    "url": url,
                    "type": "photo",
                    "caption": sp["chineseName"],
                    "source": "Macaulay Library / eBird",
                    "sourceUrl": source_url,
                    "author": photo.get("userDisplayName") or "Macaulay Library contributor",
                    "license": photo.get("licenseType") or "见来源页面",
                })
                existing_sources.add(source_url)
                existing_urls.add(url)
                updated += 1
                if len(item["images"]) >= 3:
                    break
            if done % 25 == 0:
                print(f"processed photos: {done}/{len(targets)}", flush=True)
    print(f"added Macaulay/eBird images: {updated}", flush=True)


def main():
    species = read_json("species.json")
    taxonomy = read_json("taxonomy.json")
    media = read_json("media.json")
    metadata = read_json("metadata.json")
    taxonomy_by_sci = ebird_taxonomy()
    clean_species(species, taxonomy_by_sci)
    rebuild_taxonomy(taxonomy, species)
    add_photos(species, media)
    metadata["dataVersion"] = VERSION
    metadata["updatedAt"] = "2026-05-07"
    for src in ["Macaulay Library / eBird photos", "eBird API v2 taxonomy"]:
        if src not in metadata.setdefault("sources", []):
            metadata["sources"].append(src)
    write_json("species.json", species)
    write_json("taxonomy.json", taxonomy)
    write_json("media.json", media)
    write_json("metadata.json", metadata)


if __name__ == "__main__":
    main()
