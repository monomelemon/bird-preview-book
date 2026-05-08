#!/usr/bin/env python3
"""Merge eBird provincial checklists into a national China species list.

Reads current data/species.json, fetches eBird CN-01 through CN-34 checklists,
merges distinct species codes, excludes subspecies/hybrid/spuh/domestic,
and writes updated data/species.json and data/metadata.json.

Usage:
  EBIRD_API_KEY='xxx' python3 scripts/merge_china_species.py
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VERSION = "v2-china-2026-05-07"

CN_REGIONS = [f"CN-{i:02d}" for i in range(1, 35)]  # CN-01 through CN-34
EXCLUDE_CATEGORIES = {"hybrid", "spuh", "domestic", "slash", "issf", "form"}

# Three-word names with category=species are valid (e.g. "Pterodroma ultima"), so
# we only exclude when category is non-species or name has >=4 words.
SUBSPECIES_PAT = re.compile(r"^(?:\S+\s+){3,}\S+$")  # 4+ words


def ebird_get(path: str, key: str, timeout: int = 60):
    url = f"https://api.ebird.org/v2/{path}"
    req = urllib.request.Request(url, headers={"X-eBirdApiToken": key})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return body


def fetch_taxonomy(key: str):
    """Fetch full eBird taxonomy (en + zh). Returns {sciName: taxonomy_item}."""
    print("[1/3] Fetching eBird taxonomy (en)...", flush=True)
    data = json.loads(ebird_get("ref/taxonomy/ebird?fmt=json", key))

    print("[2/3] Fetching eBird taxonomy (zh)...", flush=True)
    zh_data = json.loads(ebird_get("ref/taxonomy/ebird?fmt=json&locale=zh", key))
    zh_map = {item["sciName"]: item.get("comName", "") for item in zh_data}

    by_sci = {}
    for item in data:
        sci = item.get("sciName", "")
        category = item.get("category", "")
        # Skip non-species
        if category in EXCLUDE_CATEGORIES:
            continue
        if category == "species" and SUBSPECIES_PAT.match(sci):
            # 4+ word scientific names are subspecies/group even if category=species
            continue
        by_sci[sci] = {
            "sciName": sci,
            "comName": item.get("comName", ""),
            "speciesCode": item.get("speciesCode", ""),
            "order": item.get("order", ""),
            "familySciName": item.get("familySciName", "") or item.get("familyComName", ""),
            "familyComName": item.get("familyComName", ""),
            "comNameZh": zh_map.get(sci, ""),
        }
    print(f"  Taxonomy: {len(by_sci)} species-level taxa", flush=True)
    return by_sci


def fetch_checklists(key: str):
    """Fetch species lists for all CN regions in parallel."""
    print("[3/3] Fetching provincial checklists...", flush=True)

    def fetch_one(code):
        try:
            body = ebird_get(f"product/spplist/{code}", key)
            return code, json.loads(body), None
        except Exception as e:
            return code, [], str(e)

    all_codes = set()
    errors = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch_one, code) for code in CN_REGIONS]
        for future in as_completed(futures):
            code, codes, err = future.result()
            if err:
                errors.append(f"{code}: {err}")
            else:
                all_codes.update(codes)
            print(f"  {code}: {len(codes)} codes" + (" ERROR" if err else ""), flush=True)
            time.sleep(0.1)  # rate limit

    if errors:
        print(f"  Errors: {len(errors)} regions failed", flush=True)
    print(f"  Total unique species codes: {len(all_codes)}", flush=True)
    return all_codes


def merge(species_codes: set, taxonomy: dict, existing_species: list):
    """Merge new species into existing list, preserving old data."""
    existing_by_birdid = {s["birdId"]: s for s in existing_species}
    existing_sci = {s["scientificName"].lower(): s for s in existing_species}

    new_species = []
    for sci, tax in taxonomy.items():
        code = tax["speciesCode"]
        if code not in species_codes:
            continue

        bird_id = code  # use speciesCode as birdId
        sci_name = sci

        # Map eBird order names to taxonomy order keys
        order_map = {
            "Anseriformes": ("雁形目", "Anseriformes"),
            "Podicipediformes": ("䴙䴘目", "Podicipediformes"),
            "Gruiformes": ("鹤形目", "Gruiformes"),
            "Charadriiformes": ("鸻形目", "Charadriiformes"),
            "Pelecaniformes": ("鹈形目", "Pelecaniformes"),
            "Accipitriformes": ("鹰形目", "Accipitriformes"),
            "Coraciiformes": ("佛法僧目", "Coraciiformes"),
            "Passeriformes": ("雀形目", "Passeriformes"),
            "Strigiformes": ("鸮形目", "Strigiformes"),
            "Columbiformes": ("鸽形目", "Columbiformes"),
            "Galliformes": ("鸡形目", "Galliformes"),
            "Cuculiformes": ("鹃形目", "Cuculiformes"),
            "Piciformes": ("啄木鸟目", "Piciformes"),
            "Falconiformes": ("隼形目", "Falconiformes"),
            "Suliformes": ("鲣鸟目", "Suliformes"),
            "Bucerotiformes": ("犀鸟目", "Bucerotiformes"),
            "Psittaciformes": ("鹦形目", "Psittaciformes"),
            "Caprimulgiformes": ("夜鹰目", "Caprimulgiformes"),
            "Procellariiformes": ("鹱形目", "Procellariiformes"),
            "Gaviiformes": ("潜鸟目", "Gaviiformes"),
            "Phaethontiformes": ("鹲形目", "Phaethontiformes"),
            "Ciconiiformes": ("鹳形目", "Ciconiiformes"),
            "Otidiformes": ("鸨形目", "Otidiformes"),
            "Phoenicopteriformes": ("红鹳目", "Phoenicopteriformes"),
            "Apodiformes": ("雨燕目", "Apodiformes"),
            "Trogoniformes": ("咬鹃目", "Trogoniformes"),
            "Nyctibiiformes": ("林鸱目", "Nyctibiiformes"),
        }
        order_info = order_map.get(tax["order"], (tax["order"], tax["order"]))

        # Family: use familyComName as the en value, map zh if known
        fam_en = tax["familyComName"] or tax["familySciName"] or ""
        # The FAMILY_MAP will be applied by clean_legacy_data.py later
        fam_zh = fam_en

        # Chinese name
        cn_raw = tax["comNameZh"]
        if cn_raw and cn_raw != sci and cn_raw != tax["comName"]:
            cn_name = cn_raw
        else:
            cn_name = tax["comName"]  # fallback to English

        sp = {
            "birdId": bird_id,
            "chineseName": cn_name,
            "englishName": tax["comName"],
            "scientificName": sci_name,
            "aliases": [],
            "order": {"zh": order_info[0], "en": order_info[1]},
            "family": {"zh": fam_zh, "en": fam_en},
            "dataLevel": "C",
            "sourceRefs": ["eBird API v2 taxonomy", f"eBird CN-{len(species_codes)} provincial checklists"],
            "speciesCode": code,
            "updatedAt": "2026-05-07",
        }

        # Preserve existing data if this species already exists
        existing = existing_by_birdid.get(bird_id) or existing_sci.get(sci_name.lower())
        if existing:
            sp["dataLevel"] = existing.get("dataLevel", "C")
            sp["aliases"] = existing.get("aliases", [])
            sp["sourceRefs"] = list(set(existing.get("sourceRefs", []) + sp["sourceRefs"]))
            sp["updatedAt"] = "2026-05-07"

        new_species.append(sp)

    # Sort: first by order (sortOrder), then by chineseName
    ORDER_SORT = {
        "雁形目": 10, "䴙䴘目": 20, "鹤形目": 30, "鸻形目": 40, "鹈形目": 50,
        "鹰形目": 60, "佛法僧目": 70, "雀形目": 80, "鸮形目": 90, "鸽形目": 100,
        "鸡形目": 110, "鹃形目": 120, "啄木鸟目": 130, "隼形目": 140, "鲣鸟目": 150,
        "犀鸟目": 160, "鹦形目": 170, "夜鹰目": 180, "鹱形目": 190, "潜鸟目": 200,
        "鹲形目": 210, "鹳形目": 220, "鸨形目": 230, "红鹳目": 240, "雨燕目": 250,
        "咬鹃目": 260, "林鸱目": 270,
    }
    new_species.sort(key=lambda s: (
        ORDER_SORT.get(s["order"]["zh"], 999),
        s.get("chineseName", ""),
    ))

    return new_species


def main():
    key = os.environ.get("EBIRD_API_KEY", "").strip()
    if not key:
        print("ERROR: EBIRD_API_KEY environment variable required", file=sys.stderr)
        sys.exit(1)

    print(f"Target regions: {CN_REGIONS[0]} to {CN_REGIONS[-1]} ({len(CN_REGIONS)} regions)", flush=True)

    taxonomy = fetch_taxonomy(key)
    species_codes = fetch_checklists(key)
    existing_species = json.loads((DATA / "species.json").read_text(encoding="utf-8"))
    metadata = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))

    species = merge(species_codes, taxonomy, existing_species)

    # Validate
    ids = [s["birdId"] for s in species]
    assert len(ids) == len(set(ids)), f"Duplicate birdIds found: {len(ids)} total, {len(set(ids))} unique"
    for sp in species:
        assert sp.get("speciesCode"), f"Missing speciesCode: {sp['birdId']}"
        assert sp.get("chineseName"), f"Missing chineseName: {sp['birdId']}"
        assert sp.get("order", {}).get("zh"), f"Missing order: {sp['birdId']}"
        assert sp.get("family", {}).get("zh"), f"Missing family: {sp['birdId']}"

    sub_bad = [s for s in species if SUBSPECIES_PAT.match(s["scientificName"])]
    if sub_bad:
        print(f"WARNING: {len(sub_bad)} subspecies-like names found", flush=True)

    # Write
    (DATA / "species.json").write_text(
        json.dumps(species, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    metadata["dataVersion"] = VERSION
    metadata["updatedAt"] = "2026-05-07"
    if "eBird API v2 (China provincial checklists)" not in metadata.setdefault("sources", []):
        metadata["sources"].append("eBird API v2 (China provincial checklists)")
    (DATA / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nDone: {len(species)} species written to data/species.json", flush=True)


if __name__ == "__main__":
    main()
