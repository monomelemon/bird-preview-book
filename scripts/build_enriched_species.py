#!/usr/bin/env python3
"""Build enriched species.json by merging Avibase data with existing species.

Usage:
  python3 scripts/build_enriched_species.py [--dry-run]
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Order name mapping: Avibase English → (Chinese zh, English en)
ORDER_MAP = {
    "ANSERIFORMES":       ("雁形目", "Anseriformes"),
    "PODICIPEDIFORMES":   ("䴙䴘目", "Podicipediformes"),
    "GRUIFORMES":         ("鹤形目", "Gruiformes"),
    "CHARADRIIFORMES":    ("鸻形目", "Charadriiformes"),
    "PELECANIFORMES":     ("鹈形目", "Pelecaniformes"),
    "ACCIPITRIFORMES":    ("鹰形目", "Accipitriformes"),
    "CORACIIFORMES":      ("佛法僧目", "Coraciiformes"),
    "PASSERIFORMES":      ("雀形目", "Passeriformes"),
    "STRIGIFORMES":       ("鸮形目", "Strigiformes"),
    "COLUMBIFORMES":      ("鸽形目", "Columbiformes"),
    "GALLIFORMES":        ("鸡形目", "Galliformes"),
    "CUCULIFORMES":       ("鹃形目", "Cuculiformes"),
    "PICIFORMES":         ("啄木鸟目", "Piciformes"),
    "FALCONIFORMES":      ("隼形目", "Falconiformes"),
    "SULIFORMES":         ("鲣鸟目", "Suliformes"),
    "BUCEROTIFORMES":     ("犀鸟目", "Bucerotiformes"),
    "PSITTACIFORMES":     ("鹦形目", "Psittaciformes"),
    "CAPRIMULGIFORMES":   ("夜鹰目", "Caprimulgiformes"),
    "PROCELLARIIFORMES":  ("鹱形目", "Procellariiformes"),
    "GAVIIFORMES":        ("潜鸟目", "Gaviiformes"),
    "PHAETHONTIFORMES":   ("鹲形目", "Phaethontiformes"),
    "CICONIIFORMES":      ("鹳形目", "Ciconiiformes"),
    "OTIDIFORMES":        ("鸨形目", "Otidiformes"),
    "PHOENICOPTERIFORMES": ("红鹳目", "Phoenicopteriformes"),
    "APODIFORMES":        ("雨燕目", "Apodiformes"),
    "TROGONIFORMES":      ("咬鹃目", "Trogoniformes"),
    "PODARGIFORMES":      ("蛙嘴夜鹰目", "Podargiformes"),
    "PTEROCLIFORMES":     ("沙鸡目", "Pterocliformes"),
}

ORDER_SORT = {
    "雁形目": 10, "鸡形目": 20, "鸽形目": 30, "沙鸡目": 40,
    "鸨形目": 50, "鹃形目": 60, "夜鹰目": 70, "蛙嘴夜鹰目": 80,
    "雨燕目": 90, "鹤形目": 100, "鸻形目": 110, "潜鸟目": 120,
    "鹲形目": 130, "红鹳目": 140, "䴙䴘目": 150,
    "鹱形目": 160, "鹳形目": 170, "鲣鸟目": 180, "鹈形目": 190,
    "鹰形目": 200, "鸮形目": 210, "咬鹃目": 220, "犀鸟目": 230,
    "佛法僧目": 240, "啄木鸟目": 250, "隼形目": 260,
    "鹦形目": 270, "雀形目": 280,
}

# From existing merge_china_species.py
FAMILY_MAP = {}  # populated on the fly from existing data


def load_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def _gen_bird_id(sci_name, avibase_id, existing_list):
    """Generate a unique birdId from scientific name for Avibase-only species."""
    parts = sci_name.lower().replace("'", "").replace("-", "").split()
    base = parts[0][:4] + parts[1][:4] if len(parts) >= 2 else (parts[0][:8] if parts else "avsp")
    # Ensure uniqueness
    existing_ids = {s.get("birdId", "") for s in existing_list}
    bird_id = base
    suffix = 1
    while bird_id in existing_ids:
        bird_id = f"{base}{suffix}"
        suffix += 1
    return bird_id


def build_family_map(existing_species):
    """Build family en→zh mapping from existing data."""
    for s in existing_species:
        fam_en = s.get("family", {}).get("en", "")
        fam_zh = s.get("family", {}).get("zh", "")
        if fam_en and fam_zh and fam_en not in FAMILY_MAP:
            FAMILY_MAP[fam_en] = fam_zh


def merge_species(existing_species, avibase_species, dry_run=False):
    """Merge Avibase species into existing species list."""
    # Index existing by scientific name (case-insensitive)
    existing_by_sci = {}
    for s in existing_species:
        key = s["scientificName"].lower().strip()
        existing_by_sci[key] = s

    # Track match stats
    stats = {"matched": 0, "new": 0, "no_cn_name": 0,
             "total_existing": len(existing_species),
             "total_avibase": len(avibase_species)}

    # Track existing species that are NOT in Avibase
    avibase_sci_set = {a["scientificName"].lower().strip() for a in avibase_species}
    not_in_avibase = []
    for s in existing_species:
        if s["scientificName"].lower().strip() not in avibase_sci_set:
            not_in_avibase.append(s)
    stats["not_covered"] = len(not_in_avibase)

    result = []
    processed_sci = set()

    for avi in avibase_species:
        sci = avi["scientificName"].lower().strip()
        processed_sci.add(sci)
        existing = existing_by_sci.get(sci)

        if existing:
            # MATCH: enrich existing with Avibase data
            stats["matched"] += 1
            sp = dict(existing)  # preserve all existing fields

            # Update/add Avibase data
            sp["avibaseId"] = avi["avibaseId"]

            # Only update Chinese name if existing is in English
            if _is_english_name(sp.get("chineseName", "")):
                sp["chineseName"] = avi["chineseName"]

            # Merge tags
            sp["iucnStatus"] = _extract_iucn(avi.get("tags", []))
            sp["endemism"] = _extract_endemism(avi.get("tags", []))
            sp["occurrenceType"] = _extract_occurrence(avi.get("tags", []))

            # Update English name if Avibase has better.
            # Keep aliases for Chinese alternate names only; old English names are not aliases.
            if avi.get("englishName") and avi["englishName"] != sp.get("englishName", ""):
                sp["englishName"] = avi["englishName"]

            # Update source refs
            sp.setdefault("sourceRefs", [])
            if "Avibase" not in sp["sourceRefs"]:
                sp["sourceRefs"].append("Avibase")

        else:
            # NEW SPECIES: create from Avibase data
            stats["new"] += 1
            order_zh, order_en = ORDER_MAP.get(avi["order"], (avi["order"], avi["order"]))

            fam_en = avi["family"]
            fam_zh = FAMILY_MAP.get(fam_en, fam_en)

            bird_id = _gen_bird_id(avi["scientificName"], avi["avibaseId"], result)

            cn = avi.get("chineseName", "")
            if not cn or cn == avi["englishName"]:
                stats["no_cn_name"] += 1
                cn = avi["englishName"]

            sp = {
                "birdId": bird_id,
                "chineseName": cn,
                "englishName": avi["englishName"],
                "scientificName": avi["scientificName"],
                "aliases": [],
                "order": {"zh": order_zh, "en": order_en},
                "family": {"zh": fam_zh, "en": fam_en},
                "dataLevel": "E",
                "sourceRefs": ["Avibase"],
                "speciesCode": "",
                "avibaseId": avi["avibaseId"],
                "iucnStatus": _extract_iucn(avi.get("tags", [])),
                "endemism": _extract_endemism(avi.get("tags", [])),
                "occurrenceType": _extract_occurrence(avi.get("tags", [])),
                "updatedAt": "2026-06-30",
            }

        result.append(sp)

    # Preserve existing species NOT in Avibase (exotic/pet species)
    for s in existing_species:
        sci = s["scientificName"].lower().strip()
        if sci not in processed_sci:
            sp = dict(s)
            sp.setdefault("occurrenceType", "exotic")
            result.append(sp)
            stats["preserved"] = stats.get("preserved", 0) + 1

    # Sort by order, then chineseName
    result.sort(key=lambda s: (
        ORDER_SORT.get(s.get("order", {}).get("zh", "雀形目"), 999),
        s.get("chineseName", ""),
    ))

    return result, stats, not_in_avibase


def _is_english_name(name):
    """Check if a name appears to be English rather than Chinese."""
    if not name:
        return True
    for ch in name:
        if '\u4e00' <= ch <= '\u9fff':
            return False
    return True


def _extract_iucn(tags):
    for t in ["critically_endangered", "endangered", "vulnerable", "near_threatened"]:
        if t in tags:
            return t
    return None


def _extract_endemism(tags):
    for t in ["endemic", "breeding_endemic", "near_endemic"]:
        if t in tags:
            return t
    return None


def _extract_occurrence(tags):
    for t in ["rare", "introduced", "extirpated"]:
        if t in tags:
            return t
    return None


def main():
    dry_run = "--dry-run" in sys.argv

    print("[1/4] Loading existing species...", flush=True)
    existing_species = load_json("species.json")
    print(f"  Loaded {len(existing_species)} species", flush=True)

    print("[2/4] Building family map from existing data...", flush=True)
    build_family_map(existing_species)

    print("[3/4] Loading Avibase data...", flush=True)
    avibase_species = load_json("avibase_china.json")
    print(f"  Loaded {len(avibase_species)} species", flush=True)

    print("[4/4] Merging species...", flush=True)
    result, stats, not_covered = merge_species(
        existing_species, avibase_species, dry_run=dry_run,
    )

    print(f"\n=== Coverage Report ===")
    print(f"  Existing species: {stats['total_existing']}")
    print(f"  Avibase species:  {stats['total_avibase']}")
    print(f"  Matched (in both): {stats['matched']}")
    print(f"  New (Avibase only): {stats['new']}")
    print(f"  Preserved (exotic, not in Avibase): {stats.get('preserved', 0)}")
    print(f"  Total merged: {len(result)}")
    print(f"  New species lacking CN name: {stats['no_cn_name']}")

    if not_covered:
        print(f"\n  Species in existing but NOT in Avibase ({len(not_covered)}):")
        for s in sorted(not_covered, key=lambda x: x.get("chineseName", ""))[:20]:
            print(f"    - {s['chineseName']} ({s['scientificName']})")

    # Tag stats
    tag_stats = {"iucnStatus": 0, "endemism": 0, "occurrenceType": 0}
    for s in result:
        if s.get("iucnStatus"): tag_stats["iucnStatus"] += 1
        if s.get("endemism"): tag_stats["endemism"] += 1
        if s.get("occurrenceType"): tag_stats["occurrenceType"] += 1

    print(f"\n  Tag coverage:")
    print(f"    IUCN status: {tag_stats['iucnStatus']}/{len(result)}")
    print(f"    Endemism: {tag_stats['endemism']}/{len(result)}")
    print(f"    Occurrence type: {tag_stats['occurrenceType']}/{len(result)}")

    if dry_run:
        print("\n[DRY RUN] No files written.")
        return

    out_path = DATA / "species.json"
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nWritten {len(result)} species to {out_path}")


if __name__ == "__main__":
    main()
