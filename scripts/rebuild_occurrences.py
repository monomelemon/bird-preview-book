#!/usr/bin/env python3
"""
Rebuilds data/occurrences.json from GBIF province+month data,
preserving V1 manual city-level records.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROVINCE_CODE_MAP: dict[str, str] = {
    "北京": "110000",
    "天津": "120000",
    "河北": "130000",
    "山西": "140000",
    "内蒙古": "150000",
    "辽宁": "210000",
    "吉林": "220000",
    "黑龙江": "230000",
    "上海": "310000",
    "江苏": "320000",
    "浙江": "330000",
    "安徽": "340000",
    "福建": "350000",
    "江西": "360000",
    "山东": "370000",
    "河南": "410000",
    "湖北": "420000",
    "湖南": "430000",
    "广东": "440000",
    "广西": "450000",
    "海南": "460000",
    "重庆": "500000",
    "四川": "510000",
    "贵州": "520000",
    "云南": "530000",
    "西藏": "540000",
    "陕西": "610000",
    "甘肃": "620000",
    "青海": "630000",
    "宁夏": "640000",
    "新疆": "650000",
}


def load_gbif_raw() -> dict[str, dict[str, list[int]]]:
    with open(ROOT / "data" / "gbif_raw.json", encoding="utf-8") as f:
        return json.load(f)


BIRDID_MAPPING = {
    "himantopus_himantopus": "bkwsti",
    "recurvirostra_avosetta": "pieavo1",
    "charadrius_dubius": "lirplo",
    "charadrius_alexandrinus": "kenplo1",
    "pluvialis_squatarola": "bkbplo",
    "actitis_hypoleucos": "comsan",
    "tringa_totanus": "comred1",
    "tringa_nebularia": "comgre",
    "pluvialis_fulva": "pagplo",
    "charadrius_mongolus": "lessap2",
    "limosa_lapponica": "batgod",
    "limosa_limosa": "bktgod",
    "numenius_madagascariensis": "faecur",
    "numenius_arquata": "eurcur",
    "calidris_tenuirostris": "grekno",
    "calidris_canutus": "redkno",
    "calidris_acuminata": "shtsan",
    "calidris_ruficollis": "rensti",
    "tringa_stagnatilis": "marsan",
    "tringa_glareola": "woosan",
    "tringa_erythropus": "spored",
    "xenus_cinereus": "tersan",
    "tringa_brevipes": "gyttat1",
}


def extract_v1_city_records() -> list[dict]:
    try:
        result = subprocess.run(
            ["git", "show", "08cba9d:data/occurrences.json"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
        )
        all_records = json.loads(result.stdout)
        city_records = [r for r in all_records if r.get("locationLevel") == "city"]

        mapped_records = []
        for record in city_records:
            old_id = record.get("birdId", "")
            if old_id in BIRDID_MAPPING:
                record["birdId"] = BIRDID_MAPPING[old_id]

            record["reliability"] = "high"
            marker = "manual: Wild Beijing Nanpu 2011"
            if marker not in record.get("sourceRefs", []):
                record["sourceRefs"] = list(record.get("sourceRefs", [])) + [marker]

            mapped_records.append(record)

        return mapped_records
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to extract V1 data: {e}", file=sys.stderr)
        print("Make sure commit 08cba9d exists in this repository.", file=sys.stderr)
        return []


def build_gbif_records(gbif_data: dict[str, dict[str, list[int]]]) -> list[dict]:
    records: list[dict] = []
    for bird_id, provinces in gbif_data.items():
        for province_name, months in provinces.items():
            if not months:
                continue

            province_code = PROVINCE_CODE_MAP.get(province_name)
            if not province_code:
                print(
                    f"WARNING: Unknown province '{province_name}' for {bird_id}, skipping.",
                    file=sys.stderr,
                )
                continue

            records.append({
                "recordId": f"gbif_{bird_id}_{province_code}",
                "birdId": bird_id,
                "locationCode": province_code,
                "locationName": province_name,
                "locationLevel": "province",
                "months": sorted(months),
                "presence": "confirmed",
                "abundance": "unknown",
                "habitats": [],
                "sourceRefs": ["GBIF.org (2026-05-08)"],
                "reliability": "medium",
            })

    return records


def merge_occurrences(
    v1_records: list[dict], gbif_records: list[dict]
) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    merged: list[dict] = []

    for record in v1_records:
        seen.add((record["birdId"], record["locationCode"]))
        merged.append(record)

    for record in gbif_records:
        key = (record["birdId"], record["locationCode"])
        if key not in seen:
            seen.add(key)
            merged.append(record)

    return merged


def update_metadata() -> None:
    meta_path = ROOT / "data" / "metadata.json"
    with open(meta_path, encoding="utf-8") as f:
        metadata = json.load(f)

    metadata["dataVersion"] = "v2-fix-2026-05-08"
    metadata["updatedAt"] = "2026-05-08"

    gbif_source = "GBIF.org (2026-05-08) occurrence data"
    if gbif_source not in metadata.get("sources", []):
        metadata["sources"] = list(metadata.get("sources", [])) + [gbif_source]

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Updated metadata.json -> dataVersion: {metadata['dataVersion']}")


def validate(output_records: list[dict]) -> bool:
    errors: list[str] = []

    national = [r for r in output_records if r.get("locationLevel") == "national"]
    if national:
        errors.append(f"Found {len(national)} national-level records (should be 0)")

    ids = [r["recordId"] for r in output_records]
    dupes = sorted({rid for rid in ids if ids.count(rid) > 1})
    if dupes:
        errors.append(f"Duplicate recordIds: {dupes}")

    empty_months = [r["recordId"] for r in output_records if not r.get("months")]
    if empty_months:
        errors.append(f"Records with empty months: {empty_months}")

    required = [
        "recordId", "birdId", "locationCode", "locationName",
        "locationLevel", "months", "presence", "abundance",
        "habitats", "sourceRefs", "reliability",
    ]
    for r in output_records:
        missing = [f for f in required if f not in r]
        if missing:
            errors.append(f"Record {r['recordId']} missing fields: {missing}")

    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return False

    levels: dict[str, int] = {}
    for r in output_records:
        lv = r.get("locationLevel", "unknown")
        levels[lv] = levels.get(lv, 0) + 1

    v1_count = sum(
        1 for r in output_records
        if any("manual: Wild Beijing Nanpu" in s for s in r.get("sourceRefs", []))
    )

    print("VALIDATION PASSED.")
    print(f"  Total records: {len(output_records)}")
    for lv, count in sorted(levels.items()):
        print(f"  - {lv}: {count}")
    print(f"  V1 manual records preserved: {v1_count}")

    return True


def main() -> None:
    print("=== Rebuilding occurrences.json ===")

    print("[1/4] Loading GBIF raw data...")
    gbif_data = load_gbif_raw()
    print(f"  Loaded {len(gbif_data)} species with GBIF data")

    print("[2/4] Extracting V1 manual city records from git...")
    v1_records = extract_v1_city_records()
    print(f"  Extracted {len(v1_records)} V1 city-level records")

    print("[3/4] Building GBIF province records...")
    gbif_records = build_gbif_records(gbif_data)
    print(f"  Built {len(gbif_records)} GBIF province records")

    print("[4/4] Merging and deduplicating...")
    merged = merge_occurrences(v1_records, gbif_records)

    species_list = json.loads((ROOT / "data" / "species.json").read_text(encoding="utf-8"))
    valid_ids = {s["birdId"] for s in species_list}
    filtered = [r for r in merged if r.get("birdId", "") in valid_ids]
    removed = len(merged) - len(filtered)
    if removed:
        print(f"  Filtered out {removed} records for non-existent birdIds")
    merged = filtered

    print(f"  Merged total: {len(merged)} records")

    print("=== Validating ===")
    if not validate(merged):
        print("Validation failed, not writing output.", file=sys.stderr)
        sys.exit(1)

    output_path = ROOT / "data" / "occurrences.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Written {len(merged)} records to {output_path}")

    print("=== Updating metadata.json ===")
    update_metadata()

    print("=== Done ===")


if __name__ == "__main__":
    main()
