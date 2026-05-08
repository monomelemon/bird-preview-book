#!/usr/bin/env python3
"""Filter Macaulay photos for quality (rating>=4, adult, >=400px). Refetch replacements for low-quality images."""

import json, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

def fetch_macaulay(code, page_size=10):
    q = urllib.parse.urlencode({"taxonCode": code, "mediaType": "photo", "pageSize": page_size})
    url = f"https://search.macaulaylibrary.org/api/v1/search?{q}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return (json.loads(r.read().decode()) or {}).get("results", {}).get("content", []) or []

def quality_pass(photo):
    try:
        rating = photo.get("rating")
        if rating is None:
            return False
        if float(rating) < 4.0:
            return False
    except:
        return False
    age = photo.get("age") or ""
    if age and "adult" not in age.lower():
        return False
    w = photo.get("width") or 0
    h = photo.get("height") or 0
    if max(w, h) < 400:
        return False
    return True

def best_fallback(photos):
    scored = []
    for p in photos:
        try: s = float(p.get("rating") or 0)
        except: s = 0
        w = p.get("width") or 0
        scored.append((s + (max(w, p.get("height") or 0) / 10000), p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None

def photo_to_entry(photo, sp_name):
    source_url = photo.get("specimenUrl") or (f"https://macaulaylibrary.org/asset/{photo.get('assetId')}" if photo.get("assetId") else "")
    url = photo.get("largeUrl") or photo.get("mediaUrl") or photo.get("previewUrl")
    if not url:
        return None
    return {
        "url": url,
        "type": "photo",
        "caption": sp_name,
        "source": "Macaulay Library / eBird",
        "sourceUrl": source_url,
        "author": photo.get("userDisplayName") or "Macaulay Library contributor",
        "license": photo.get("licenseType") or "见来源页面",
        "rating": photo.get("rating"),
        "age": photo.get("age"),
        "width": photo.get("width"),
        "height": photo.get("height"),
    }

def score_entry(entry):
    try: r = float(entry.get("rating") or 0)
    except: r = 0
    return r + max(entry.get("width") or 0, entry.get("height") or 0) / 10000

def main():
    species = read_json("species.json")
    media = read_json("media.json")
    sp_by_id = {s["birdId"]: s for s in species}
    sp_by_code = {}
    for s in species:
        if s.get("speciesCode"):
            sp_by_code[s["speciesCode"]] = s

    to_process = [k for k in media if k in sp_by_id and sp_by_id[k].get("speciesCode")]
    total = len(to_process)
    print(f"filtering photos for {total} species with Macaulay codes")

    def process_species(bird_id):
        sp = sp_by_id[bird_id]
        code = sp.get("speciesCode")
        if not code:
            return bird_id, media.get(bird_id, {}).get("images", []), 0
        try:
            photos = fetch_macaulay(code, 12)
        except Exception as e:
            print(f"  fetch failed {bird_id}: {e}", flush=True)
            return bird_id, media.get(bird_id, {}).get("images", []), 0
        passed = [p for p in photos if quality_pass(p)]
        entries = [photo_to_entry(p, sp["chineseName"]) for p in passed]
        entries = [e for e in entries if e is not None]
        existing = media.get(bird_id, {}).get("images", [])
        existing_urls = {img["url"] for img in existing}
        new_entries = [e for e in entries if e["url"] not in existing_urls]
        for e in new_entries:
            e.pop("rating", None)
            e.pop("age", None)
            e.pop("width", None)
            e.pop("height", None)
        combined = existing + new_entries
        if not combined and photos:
            best = best_fallback(photos)
            if best:
                e = photo_to_entry(best, sp["chineseName"])
                if e:
                    e.pop("rating", None); e.pop("age", None); e.pop("width", None); e.pop("height", None)
                    combined = [e]
        combined.sort(key=lambda x: score_entry(x), reverse=True)
        return bird_id, combined[:3] if len(combined) >= 3 else combined, len(new_entries)

    added = 0
    done = 0
    batch_size = 20
    target_ids = list(to_process)
    for i in range(0, len(target_ids), batch_size):
        batch = target_ids[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=min(batch_size, 15)) as pool:
            futures = {pool.submit(process_species, bid): bid for bid in batch}
            for future in as_completed(futures):
                bird_id, images, new_count = future.result()
                entry = media.setdefault(bird_id, {})
                entry["images"] = images
                entry.setdefault("sounds", [])
                entry.setdefault("rangeMap", None)
                added += new_count
                done += 1
                if done % 50 == 0:
                    print(f"  photos filtered: {done}/{total} (added {added})", flush=True)
        time.sleep(0.5)

    print(f"photo filter complete: {total} species, added {added} quality photos", flush=True)
    write_json("media.json", media)

if __name__ == "__main__":
    main()
