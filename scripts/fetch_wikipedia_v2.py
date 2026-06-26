#!/usr/bin/env python3
"""Fetch Chinese Wikipedia summaries and write description/distribution into species.json."""

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


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fetch_wiki_extract(title):
    q = urllib.parse.urlencode({
        "action": "query", "titles": title, "prop": "extracts",
        "exintro": "1", "explaintext": "1", "format": "json", "redirects": "1",
    })
    url = f"https://zh.wikipedia.org/w/api.php?{q}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "BirdPreviewBook/2.0 (educational; monomelemon/bird-preview-book)",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
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


def main():
    limit = None
    if len(sys.argv) > 1 and sys.argv[1].startswith("--limit="):
        limit = int(sys.argv[1].split("=")[1])

    species = read_json("species.json")
    total = len(species) if limit is None else min(limit, len(species))
    print(f"fetching Wikipedia for {total} species (limit={limit})")

    species_index = {sp["birdId"]: sp for sp in species}
    updated = 0
    done = 0

    def fetch_one(sp):
        cn = sp["chineseName"]
        result = fetch_wiki_extract(cn)
        if not result:
            eb = sp.get("englishName", "")
            if eb and eb != cn:
                result = fetch_wiki_extract(eb)
        if not result:
            sci = sp.get("scientificName", "")
            if sci and sci != cn:
                result = fetch_wiki_extract(sci)
        if not result:
            return sp["birdId"], None
        extract = result["extract"]
        dist = extract_distribution(extract)
        return sp["birdId"], {
            "description": extract[:800],
            "distribution": dist,
        }

    batch = species[:total]
    batch_size = 8
    for i in range(0, len(batch), batch_size):
        chunk = batch[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(fetch_one, sp) for sp in chunk]
            for future in as_completed(futures):
                bird_id, wiki_data = future.result()
                if wiki_data and bird_id in species_index:
                    species_index[bird_id]["description"] = wiki_data["description"]
                    if wiki_data["distribution"]:
                        species_index[bird_id]["distribution"] = wiki_data["distribution"]
                    updated += 1
                done += 1
                if done % 50 == 0:
                    print(f"  wiki: {done}/{total} (updated {updated})", flush=True)
        time.sleep(1.0)

    with_desc = sum(1 for sp in species if sp.get("description"))
    with_dist = sum(1 for sp in species if sp.get("distribution"))
    print(f"wikipedia complete: {total} species, {with_desc} with description, {with_dist} with distribution", flush=True)
    write_json("species.json", species)
    print("wrote species.json")


if __name__ == "__main__":
    main()
