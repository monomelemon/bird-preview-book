#!/usr/bin/env python3
"""Fetch Wikipedia summaries (zh→en) and write description/distribution into species.json.

Also backfills from existing `identification.json` Wikipedia fields so we can
recover text that was previously fetched but not merged into `species.json`.
"""

import json, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Import shared utilities
sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_utils import to_simplified

DIST_RE = re.compile(
    r"分布[：:\s][^\n]{10,150}|"
    r"分布[在於于][^\n]{10,150}|"
    r"[仅僅]?分布[於于]?[^\n]{10,150}|"
    r"[仅僅]?(?:主要|广泛|泛|廣)?分[布佈][在於于]?[^\n]{10,150}|"
    r"广布[在於于][^\n]{10,150}|"
    r"[仅僅]见[於于][^\n]{10,120}|"
    r"常见[於于][^\n]{10,120}|"
    r"繁殖[在於于][^\n]{10,120}|"
    r"[栖棲]息[在於于][^\n]{10,120}|"
    r"(?:地区|區域)特有[於于]?[^\n]{5,120}",
    re.IGNORECASE)

ASCII_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_identification_index(species, identification):
    by_bird = {}
    by_sci = {}
    bird_ids = {sp["birdId"] for sp in species}
    sci_names = {sp.get("scientificName") for sp in species}
    for key, item in identification.items():
        if not isinstance(item, dict):
            continue
        if key in bird_ids:
            by_bird[key] = item
        elif key in sci_names:
            by_sci[key] = item
    return by_bird, by_sci


def is_english_only_text(text):
    text = text or ""
    return bool(text and ASCII_RE.search(text) and not CJK_RE.search(text))


def fetch_wiki_extract(title, lang="zh"):
    q = urllib.parse.urlencode({
        "action": "query", "titles": title, "prop": "extracts",
        "exintro": "1", "explaintext": "1", "format": "json", "redirects": "1",
    })
    url = f"https://{lang}.wikipedia.org/w/api.php?{q}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "BirdPreviewBook/2.0 (educational; monomelemon/bird-preview-book)",
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        pages = data.get("query", {}).get("pages", {})
        for pid, page in pages.items():
            if pid != "-1" and page.get("extract") and len(page.get("extract", "")) > 30:
                return {"title": page["title"], "extract": to_simplified(page["extract"])}
    except Exception:
        pass
    return None


def extract_distribution(extract):
    if not extract:
        return None
    matches = DIST_RE.findall(extract)
    parts = [m.strip() for m in matches if len(m) > 8]
    if not parts:
        return None
    seen = set()
    unique = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return "；".join(unique[:2])


def backfill_local_wiki(species, identification_by_bird, identification_by_sci):
    stats = {
        "description_from_identification": 0,
        "distribution_from_identification": 0,
        "distribution_from_description": 0,
    }
    for sp in species:
        ident = identification_by_bird.get(sp["birdId"]) or identification_by_sci.get(sp.get("scientificName")) or {}
        summary = to_simplified(ident.get("wikipediaSummary", ""))
        explicit_dist = to_simplified(ident.get("wikipediaDistribution", ""))

        if not sp.get("description") and summary:
            sp["description"] = summary[:800]
            stats["description_from_identification"] += 1

        if sp.get("distribution"):
            continue

        if explicit_dist:
            sp["distribution"] = explicit_dist[:300]
            stats["distribution_from_identification"] += 1
            continue

        desc_dist = extract_distribution(to_simplified(sp.get("description", "")))
        if desc_dist:
            sp["distribution"] = desc_dist
            stats["distribution_from_description"] += 1
            continue

        summary_dist = extract_distribution(summary)
        if summary_dist:
            sp["distribution"] = summary_dist
            stats["distribution_from_identification"] += 1

    return stats


def main():
    limit = None
    local_only = "--local-only" in sys.argv
    refresh_english = "--refresh-english" in sys.argv
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])

    species = read_json("species.json")
    identification = read_json("identification.json")
    identification_by_bird, identification_by_sci = build_identification_index(species, identification)
    total = len(species) if limit is None else min(limit, len(species))
    print(f"fetching Wikipedia for {total} species (limit={limit})")

    species_index = {sp["birdId"]: sp for sp in species}
    local_stats = backfill_local_wiki(species, identification_by_bird, identification_by_sci)
    print(
        "local backfill:",
        f"desc+{local_stats['description_from_identification']}",
        f"dist+{local_stats['distribution_from_identification'] + local_stats['distribution_from_description']}",
        flush=True,
    )

    if local_only:
        with_desc = sum(1 for sp in species if sp.get("description"))
        with_dist = sum(1 for sp in species if sp.get("distribution"))
        write_json("species.json", species)
        print(f"local-only complete: {with_desc} with description, {with_dist} with distribution", flush=True)
        print("wrote species.json")
        return

    updated = 0
    done = 0

    def fetch_one(sp):
        cn = sp["chineseName"]
        eb = sp.get("englishName", "")
        sci = sp.get("scientificName", "")

        result = fetch_wiki_extract(cn, "zh")
        if not result:
            if eb and eb != cn:
                result = fetch_wiki_extract(eb, "zh")
        if not result:
            if sci and sci != cn:
                result = fetch_wiki_extract(sci, "zh")

        if not result and eb:
            result = fetch_wiki_extract(eb, "en")
        if not result and sci:
            result = fetch_wiki_extract(sci, "en")

        if not result:
            return sp["birdId"], None
        extract = result["extract"]
        dist = extract_distribution(extract)
        return sp["birdId"], {
            "description": extract[:800],
            "distribution": dist,
        }

    batch = [
        sp for sp in species[:total]
        if (
            not sp.get("description")
            or not sp.get("distribution")
            or (refresh_english and is_english_only_text(sp.get("description")))
        )
    ]
    total = len(batch)
    if total == 0:
        print("all targeted species already have description/distribution")
        return
    print(f"fetching Wikipedia for {total} species (skipping {len(species) - total} already complete)")

    batch_size = 25
    for i in range(0, len(batch), batch_size):
        chunk = batch[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(fetch_one, sp) for sp in chunk]
            for future in as_completed(futures):
                bird_id, wiki_data = future.result()
                if wiki_data and bird_id in species_index:
                    existing_desc = species_index[bird_id].get("description")
                    if not existing_desc or (refresh_english and is_english_only_text(existing_desc)):
                        species_index[bird_id]["description"] = wiki_data["description"]
                    if wiki_data["distribution"]:
                        species_index[bird_id]["distribution"] = wiki_data["distribution"]
                    updated += 1
                done += 1
                if done % 50 == 0:
                    print(f"  wiki: {done}/{total} (updated {updated})", flush=True)
        time.sleep(0.3)

    with_desc = sum(1 for sp in species if sp.get("description"))
    with_dist = sum(1 for sp in species if sp.get("distribution"))
    print(f"wikipedia complete: {total} species, {with_desc} with description, {with_dist} with distribution", flush=True)
    write_json("species.json", species)
    print("wrote species.json")


if __name__ == "__main__":
    main()
