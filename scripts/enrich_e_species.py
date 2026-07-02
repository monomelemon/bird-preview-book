#!/usr/bin/env python3
"""Enrich dataLevel E species with images (iNaturalist via GBIF) and sounds (Xeno-Canto via GBIF).

Uses GBIF occurrence search API (public, no key needed) to find media by scientific name.
"""

import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

UA = "BirdPreviewBook/2.0 (educational; monomelemon/bird-preview-book)"

GBIF_SEARCH = "https://api.gbif.org/v1/occurrence/search"


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def api_get(url, retries=3, timeout=30):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result is None:
                    raise Exception("empty response")
                return result
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(2 ** attempt)
    return {}


def search_gbif_media(scientific_name, media_type="StillImage", limit=10):
    """Search GBIF occurrences for media of a given type."""
    params = {
        "scientificName": scientific_name,
        "mediaType": media_type,
        "limit": limit,
    }
    url = f"{GBIF_SEARCH}?{urllib.parse.urlencode(params)}"
    return api_get(url)


def extract_images(results, chinese_name):
    """Extract image entries from GBIF occurrence results."""
    entries = []
    seen_urls = set()
    for r in results:
        for m in r.get("media", []):
            if m.get("type") != "StillImage":
                continue
            url = m.get("identifier", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            record_url = (f"https://www.gbif.org/occurrence/{r.get('key')}"
                          if r.get("key") else "")

            entries.append({
                "url": url,
                "type": "photo",
                "caption": chinese_name,
                "source": "GBIF / iNaturalist",
                "sourceUrl": record_url,
                "author": m.get("creator", "") or "iNaturalist contributor",
                "license": m.get("license", "") or "见来源页面",
            })
            if len(entries) >= 3:
                return entries
    return entries


def extract_sounds(results, chinese_name):
    """Extract sound entries from GBIF occurrence results."""
    entries = []
    seen_urls = set()
    for r in results:
        for m in r.get("media", []):
            if m.get("type") != "Sound":
                continue
            url = m.get("identifier", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            record_url = (f"https://www.gbif.org/occurrence/{r.get('key')}"
                          if r.get("key") else "")

            entries.append({
                "url": url,
                "type": "audio",
                "caption": chinese_name,
                "source": "GBIF / Xeno-Canto",
                "sourceUrl": record_url,
                "author": m.get("creator", "") or "Xeno-Canto contributor",
                "license": m.get("license", "") or "见来源页面",
            })
            if len(entries) >= 4:
                return entries
    return entries


def ensure_media_entry(media, bird_id):
    item = media.setdefault(bird_id, {})
    item.setdefault("images", [])
    item.setdefault("sounds", [])
    item.setdefault("rangeMap", None)
    return item


def process_species(sp, media):
    """Fetch images and sounds for one species via GBIF."""
    bid = sp["birdId"]
    cn = sp["chineseName"]
    sci = sp.get("scientificName", "")

    if not sci:
        return bid, {"images": 0, "sounds": 0, "error": "no scientific name"}

    entry = ensure_media_entry(media, bid)
    result = {"images": 0, "sounds": 0}
    existing_img_urls = {img["url"] for img in entry["images"]}
    existing_snd_urls = {s["url"] for s in entry["sounds"]}

    # Fetch images if needed
    if len(entry["images"]) < 3:
        try:
            gbif_result = search_gbif_media(sci, "StillImage", 10)
            images = extract_images(gbif_result.get("results", []), cn)
            for img in images:
                if img["url"] not in existing_img_urls:
                    entry["images"].append(img)
                    existing_img_urls.add(img["url"])
                    result["images"] += 1
        except Exception as e:
            result["error"] = str(e)[:80]

    # Fetch sounds if needed
    if len(entry["sounds"]) < 4:
        try:
            gbif_result = search_gbif_media(sci, "Sound", 10)
            sounds = extract_sounds(gbif_result.get("results", []), cn)
            for snd in sounds:
                if snd["url"] not in existing_snd_urls:
                    entry["sounds"].append(snd)
                    existing_snd_urls.add(snd["url"])
                    result["sounds"] += 1
        except Exception as e:
            if "error" not in result:
                result["error"] = str(e)[:80]

    return bid, result


def main():
    species = read_json("species.json")
    media = read_json("media.json")

    e_all = [s for s in species if s.get("dataLevel") == "E"]
    # Skip already-processed species (those already in media.json)
    e_species = [s for s in e_all if s["birdId"] not in media]
    total = len(e_species)
    print(f"Total E-level species: {len(e_all)}, already have media: {len(e_all) - total}, to process: {total}")
    print(f"Species in media.json: {len(media)}")
    if total == 0:
        print("All E species already have media entries. Nothing to do.")
        e_species = e_all
        total = len(e_all)
    print(f"Fetching images (StillImage) + sounds (Sound) from GBIF...\n")

    # Stats
    added_images = 0
    added_sounds = 0
    errors = 0
    done = 0
    batch_size = 10  # 10 concurrent, then 0.5s delay

    for i in range(0, total, batch_size):
        batch = e_species[i:i + batch_size]

        with ThreadPoolExecutor(max_workers=batch_size) as pool:
            futures = [pool.submit(process_species, sp, media) for sp in batch]
            for future in as_completed(futures):
                bid, res = future.result()
                added_images += res.get("images", 0)
                added_sounds += res.get("sounds", 0)
                if "error" in res:
                    errors += 1
                done += 1
                if done % 50 == 0:
                    print(f"  {done}/{total} | images: +{added_images} | sounds: +{added_sounds} | errors: {errors}",
                          flush=True)

        # Rate limiting
        time.sleep(0.5)

        # Periodic save every 200 species
        if (i + batch_size) % 200 == 0:
            write_json("media.json", media)

    # Final save
    write_json("media.json", media)

    # Summary
    e_with_media = sum(1 for s in e_species if s["birdId"] in media)
    e_with_images = sum(1 for s in e_species
                        if s["birdId"] in media and media[s["birdId"]].get("images"))
    e_with_sounds = sum(1 for s in e_species
                        if s["birdId"] in media and media[s["birdId"]].get("sounds"))
    total_images = sum(len(v.get("images", [])) for v in media.values())
    total_sounds = sum(len(v.get("sounds", [])) for v in media.values())

    print(f"\n=== Summary ===")
    print(f"E species total: {total}")
    print(f"E with any media: {e_with_media}/{total}")
    print(f"E with images: {e_with_images}/{total}")
    print(f"E with sounds: {e_with_sounds}/{total}")
    print(f"Total images (all): {total_images}")
    print(f"Total sounds (all): {total_sounds}")
    print(f"Images added this run: {added_images}")
    print(f"Sounds added this run: {added_sounds}")
    print(f"Errors: {errors}")
    print(f"media.json entries: {len(media)}")
    print("Done.")


if __name__ == "__main__":
    main()
