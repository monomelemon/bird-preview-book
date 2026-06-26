#!/usr/bin/env python3
"""Image quality filter: same-photographer dedup + Laplacian blur + screen photo detection."""

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

# Screen photo detection thresholds
SCREEN_CORNER_STD_MIN = 60.0    # high corner variance (camera UI text)
SCREEN_SATURATION_MAX = 30.0    # low saturation (screen washout)


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def download(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    cache_path = CACHE_DIR / f"{url_hash}.jpg"
    if cache_path.exists():
        return str(cache_path)
    try:
        urllib.request.urlretrieve(url, cache_path)
        return str(cache_path)
    except Exception:
        return None


def compute_sharpness(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    return cv2.Laplacian(img, cv2.CV_64F).var()


def detect_screen_photo(path):
    """Check if photo appears to be a screen capture (low saturation, camera UI artifacts)."""
    img = cv2.imread(path)
    if img is None:
        return False
    h, w = img.shape[:2]

    # Check bottom-right corner for camera UI elements (text, icons, date stamps)
    corner = img[-60:, -200:] if h > 60 and w > 200 else img
    corner_gray = cv2.cvtColor(corner, cv2.COLOR_BGR2GRAY)
    corner_std = float(np.std(corner_gray))

    # Check overall color saturation (screen photos tend to be washed out)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    saturation = float(np.mean(hsv[:, :, 1]))

    return corner_std >= SCREEN_CORNER_STD_MIN and saturation <= SCREEN_SATURATION_MAX


def process_photos(images):
    """Deduplicate by photographer + detect blur + detect screen photos."""
    seen_authors = set()
    valid = []

    # Download images in parallel
    paths = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(download, img["url"]): i for i, img in enumerate(images)}
        for f in as_completed(futures):
            idx = futures[f]
            try:
                paths[idx] = f.result()
            except Exception:
                paths[idx] = None

    # Score images
    scored = []
    for i, img in enumerate(images):
        path = paths.get(i)
        if not path:
            continue

        sharp = compute_sharpness(path)
        if sharp is None:
            continue

        is_screen = detect_screen_photo(path)

        entry = dict(img)
        entry["_sharp"] = sharp
        entry["_screen"] = is_screen
        scored.append(entry)

    # Same-photographer dedup: keep sharpest per author
    author_best = {}
    for e in scored:
        author = e.get("author", "")
        if author not in author_best or e["_sharp"] > author_best[author]["_sharp"]:
            author_best[author] = e

    # Sort by sharpness, mark blur and screen
    result = []
    for e in sorted(author_best.values(), key=lambda x: x["_sharp"], reverse=True):
        note = e.get("note", "")
        if e["_sharp"] < BLUR_THRESHOLD and "画质较低" not in note:
            note = "画质较低，待替换"
        if e["_screen"] and "翻拍" not in note:
            note = f"{note}；疑似翻拍屏幕照片" if note else "疑似翻拍屏幕照片"
        e.pop("_sharp", None)
        e.pop("_screen", None)
        if note:
            e["note"] = note
        result.append(e)

    return result


def main():
    media = read_json("media.json")

    total_removed = 0
    total_blur = 0
    total_screen = 0

    for bird_id, item in media.items():
        images = item.get("images", [])
        if not images:
            continue

        new_images = process_photos(images)
        old_count = len(images)
        new_count = len(new_images)

        # Count notes
        screen_count = sum(1 for i in new_images if "翻拍" in (i.get("note") or ""))
        blur_count = sum(1 for i in new_images if "画质较低" in (i.get("note") or ""))

        if old_count != new_count:
            removed = old_count - new_count
            total_removed += removed
        total_blur += blur_count
        total_screen += screen_count

        item["images"] = new_images[:3]  # Cap at 3

        sp_name = read_json("species.json")
        sp_name = next((s.get("chineseName", bird_id) for s in sp_name if s["birdId"] == bird_id), bird_id)
        if screen_count or blur_count or old_count != new_count:
            print(f"  {sp_name}: {old_count}→{new_count} blur={blur_count} screen={screen_count}")

    write_json("media.json", media)
    print(f"\nDone: removed {total_removed} duplicates, {total_blur} blur, {total_screen} screen photos")


if __name__ == "__main__":
    main()
