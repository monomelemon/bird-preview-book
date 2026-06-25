#!/usr/bin/env python3
"""Fetch high-quality photos from iNaturalist to replace blurry/missing ones."""
import json
import os
import time
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

import numpy as np
import cv2
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

BLUR_THRESHOLD = 100.0
CACHE_DIR = Path("/tmp/inat_photo_cache")
INAT_SEARCH = "https://api.inaturalist.org/v1/search"
INAT_OBS = "https://api.inaturalist.org/v1/observations"
UA = "BirdPreviewBook/1.0"
MAX_WORKERS = 6


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def api_get(url, params=None, retries=3):
    if params:
        url = f"{url}?{urlencode(params)}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(1)


def search_taxon(scientific_name):
    """Search iNaturalist for a taxon by scientific name, return taxon_id or None."""
    try:
        result = api_get(INAT_SEARCH, {"q": scientific_name, "sources": "taxa"})
        for r in result.get("results", []):
            if r.get("type") == "Taxon" and r.get("record", {}).get("name", "").lower() == scientific_name.lower():
                taxon = r["record"]
                if taxon.get("rank") == "species":
                    return taxon["id"]
        return None
    except Exception:
        return None


def get_photos(taxon_id, per_page=15):
    """Fetch observation photos from iNaturalist — one per observation."""
    photos = []
    seen_obs = set()
    try:
        result = api_get(INAT_OBS, {
            "taxon_id": taxon_id,
            "has[]": "photos",
            "quality_grade": "research",
            "per_page": per_page,
            "order": "desc",
            "order_by": "votes",
        })
        for obs in result.get("results", []):
            obs_id = obs.get("id")
            if obs_id in seen_obs:
                continue
            seen_obs.add(obs_id)
            obs_photos = obs.get("observation_photos", obs.get("photos", []))
            if not obs_photos:
                continue
            p = obs_photos[0]
            photo = p.get("photo", p)
            raw_url = photo.get("url", "")
            if not raw_url:
                continue
            url = raw_url.replace("/square.", "/large.").replace("/square/", "/large/")
            photos.append({
                "url": url,
                "author": photo.get("attribution", "").replace("(c) ", "").split(",")[0].strip(),
                "license": photo.get("license_code", ""),
                "sourceUrl": f"https://www.inaturalist.org/observations/{obs_id}",
                "source": "iNaturalist",
            })
    except Exception as e:
        print(f"    iNat fetch error for taxon {taxon_id}: {e}", flush=True)
    return photos


def download_image(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    cache_path = CACHE_DIR / f"{url_hash}.jpg"
    if cache_path.exists():
        return str(cache_path)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        cache_path.write_bytes(data)
        return str(cache_path)
    except Exception:
        return None


def compute_sharpness(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    h, w = img.shape
    if w < 200 or h < 200:
        img = cv2.resize(img, (max(w, 200), max(h, 200)))
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


def score_candidates(candidates, existing_urls, existing_authors):
    valid = []
    tasks = []
    for c in candidates[:6]:
        if c["url"] in existing_urls:
            continue
        if c["author"] in existing_authors:
            continue
        tasks.append(c)
        if len(tasks) >= 6:
            break
    if not tasks:
        return []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {}
        for c in tasks:
            futures[pool.submit(download_image, c["url"])] = c
        for future in as_completed(futures):
            c = futures[future]
            try:
                path = future.result()
                if path:
                    sharp = compute_sharpness(path)
                    if sharp >= BLUR_THRESHOLD:
                        valid.append((sharp, c))
            except Exception:
                pass

    valid.sort(key=lambda x: x[0], reverse=True)
    return valid


def process_species(bird_id, chinese_name, scientific_name, existing_images):
    """Fetch new photos, score them, merge with existing best photos."""
    taxon_id = search_taxon(scientific_name)
    if not taxon_id:
        return bird_id, existing_images, 0, 0

    candidates = get_photos(taxon_id)
    if not candidates:
        return bird_id, existing_images, 0, 0

    existing_urls = {img["url"] for img in existing_images}
    existing_authors = {img.get("author", "") for img in existing_images}

    scored = score_candidates(candidates, existing_urls, existing_authors)

    # Merge: keep the best photos (existing sharp first, then new)
    final = []
    remaining_slots = 3

    # Keep existing sharp photos
    for img in existing_images:
        if remaining_slots <= 0:
            break
        if img.get("note") == "画质较低，待替换":
            continue
        final.append(img)
        remaining_slots -= 1

    # Fill remaining slots with best new photos
    for _, img in scored:
        if remaining_slots <= 0:
            break
        entry = {
            "url": img["url"],
            "type": "photo",
            "caption": chinese_name,
            "source": "iNaturalist",
            "sourceUrl": img["sourceUrl"],
            "author": img["author"],
            "license": img["license"],
        }
        final.append(entry)
        remaining_slots -= 1

    # If still have slots, keep existing blurry photos as fallback
    if remaining_slots > 0:
        for img in existing_images:
            if remaining_slots <= 0:
                break
            if img.get("note") == "画质较低，待替换":
                final.append(img)
                remaining_slots -= 1

    new_count = sum(1 for img in final if img.get("source") == "iNaturalist")
    return bird_id, final, len(candidates), new_count


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    media = read_json("media.json")
    species = read_json("species.json")
    sp_by_id = {s["birdId"]: s for s in species}

    needs_photos = []
    for bird_id, entry in media.items():
        sp = sp_by_id.get(bird_id)
        if not sp:
            continue
        images = entry.get("images", [])
        good = [img for img in images if img.get("note") != "画质较低，待替换"]
        n_good = len(good)
        n_blurry = len(images) - n_good
        if n_good >= 3:
            continue
        if n_good <= 1 or n_blurry > 0:
            severity = 0 if n_good == 0 else 1 if n_good == 1 and n_blurry > 0 else 2
            needs_photos.append((severity, bird_id, sp["chineseName"], sp["scientificName"], images))

    needs_photos.sort(key=lambda x: (x[0], x[1]))
    print(f"Processing {len(needs_photos)} species (priority: 0=no good photos, 1=blurry+1 good)", flush=True)

    total_new = 0
    total_updated = 0

    for i, (severity, bid, cn, sci, existing) in enumerate(needs_photos):
        bid, new_images, candidates_found, added = process_species(bid, cn, sci, existing)
        if added > 0:
            media[bid]["images"] = new_images
            old_count = len(existing)
            total_new += added
            total_updated += 1
            print(f"  [{i+1}/{len(needs_photos)}] {cn} ({bid}): {old_count}→{len(new_images)}, +{added} iNat", flush=True)
        elif i % 10 == 0:
            print(f"  [{i+1}/{len(needs_photos)}] {cn} ({bid}): no change", flush=True)

        time.sleep(0.3)

        if (i + 1) % 2 == 0:
            write_json("media.json", media)

    write_json("media.json", media)

    kept = sum(len(v.get("images", [])) for v in media.values())
    print(f"\nDone. {total_new} new iNat photos across {total_updated} species. Total images: {kept}", flush=True)

    print("\n=== 卷羽鹈鹕 & 白额雁 ===", flush=True)
    for bid in ["dalpel1", "gwfgoo"]:
        if bid in media:
            cn = sp_by_id[bid]["chineseName"]
            images = media[bid].get("images", [])
            print(f"{cn} ({bid}): {len(images)} images", flush=True)
            for i, img in enumerate(images):
                note = f" [{img.get('note')}]" if img.get("note") else ""
                print(f"  [{i}] {img['author']} ({img.get('source','')}){note}", flush=True)


if __name__ == "__main__":
    main()
