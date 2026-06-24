#!/usr/bin/env python3
"""Image quality filter: same-photographer dedup + Laplacian variance blur detection."""

import json
import os
import time
import hashlib
from pathlib import Path
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import cv2
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

BLUR_THRESHOLD = 100.0
CACHE_DIR = Path("/tmp/ml_image_cache")
MAX_WORKERS = 12


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def asset_id_from_url(url):
    parts = url.split("/")
    for p in parts:
        if p.isdigit() and len(p) >= 8:
            return p
    return None


def download_image(url):
    asset_id = asset_id_from_url(url) or hashlib.md5(url.encode()).hexdigest()[:12]
    cache_path = CACHE_DIR / f"{asset_id}.jpg"
    if cache_path.exists():
        return str(cache_path), asset_id

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BirdPreviewBook/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception:
        return None, asset_id

    cache_path.write_bytes(data)
    return str(cache_path), asset_id


def compute_sharpness(path):
    """Laplacian variance — higher = sharper. <BLUR_THRESHOLD = blurry."""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    h, w = img.shape
    if w < 200 or h < 200:
        img = cv2.resize(img, (max(w, 200), max(h, 200)))
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


def score_image_tasks(images):
    tasks = []
    for idx, img in enumerate(images):
        url = img.get("url", "")
        if not url:
            tasks.append((idx, None, None))
            continue
        path, aid = download_image(url)
        if path:
            try:
                sharp = compute_sharpness(path)
            except Exception:
                sharp = 0.0
            tasks.append((idx, sharp, aid))
        else:
            tasks.append((idx, None, aid))
    return tasks


def process_species_batch(batch):
    results = {}
    for bird_id, images in batch:
        tasks = score_image_tasks(images)
        scored = []
        for idx, sharp, aid in tasks:
            img = images[idx]
            scored.append((sharp or 0.0, img, aid))

        # Same-photographer dedup: keep only the sharpest per author
        author_best = {}
        uncredited_count = 0
        for s, img, aid in scored:
            author = img.get("author", "").strip()
            if not author:
                uncredited_count += 1
                author = f"__uncredited_{uncredited_count}"
            if author in author_best:
                if s > author_best[author][0]:
                    author_best[author] = (s, img, aid)
            else:
                author_best[author] = (s, img, aid)

        dup_removed = len(scored) - len(author_best)
        deduped = list(author_best.values())
        deduped.sort(key=lambda x: x[0], reverse=True)

        new_images = []
        blurry_count = 0
        for sharp, img, aid in deduped[:3]:
            entry = dict(img)
            if sharp < BLUR_THRESHOLD:
                entry["note"] = "画质较低，待替换"
                blurry_count += 1
            else:
                entry.pop("note", None)
            new_images.append(entry)

        results[bird_id] = {
            "images": new_images,
            "dup_removed": dup_removed,
            "blurry": blurry_count,
        }
    return results


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    media = read_json("media.json")
    species = read_json("species.json")
    sp_names = {s["birdId"]: s["chineseName"] for s in species}

    items = []
    for bird_id, entry in media.items():
        images = entry.get("images", [])
        if len(images) >= 2:
            items.append((bird_id, images))

    total = len(items)
    print(f"Processing {total} species with {sum(len(imgs) for _, imgs in items)} images...")

    all_results = {}
    total_dup = 0
    total_blur = 0

    batch_size = 30
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(process_species_batch, [b]): b[0] for b in batch}
            for future in as_completed(futures):
                results = future.result()
                for bid, r in results.items():
                    cn = sp_names.get(bid, bid)
                    total_dup += r["dup_removed"]
                    total_blur += r["blurry"]
                    all_results[bid] = r

                    flags = []
                    if r["dup_removed"]:
                        flags.append(f"去重{r['dup_removed']}张")
                    if r["blurry"]:
                        flags.append(f"{r['blurry']}张模糊")
                    if flags:
                        print(f"  {cn} ({bid}): {', '.join(flags)}")

        done = min(i + batch_size, total)
        print(f"  progress: {done}/{total}, dup={total_dup}, blur={total_blur}")

        if len(items) > batch_size:
            time.sleep(0.3)

    # Apply results to media
    for bid, r in all_results.items():
        media[bid]["images"] = r["images"]

    write_json("media.json", media)

    kept = sum(len(v.get("images", [])) for v in media.values())
    print(f"\nDone. {total_dup} same-photographer duplicates removed, {total_blur} blurry images flagged.")
    print(f"Total images kept: {kept}")

    # Print summary for the two species of interest
    print("\n=== Verification ===")
    for bid in ["dalpel1", "gwfgoo"]:
        if bid in media:
            cn = sp_names.get(bid, bid)
            images = media[bid].get("images", [])
            print(f"\n{cn} ({bid}): {len(images)} images")
            for i, img in enumerate(images):
                note = f" [{img.get('note')}]" if img.get("note") else ""
                print(f"  [{i}] {img['author']}{note}")


if __name__ == "__main__":
    main()
