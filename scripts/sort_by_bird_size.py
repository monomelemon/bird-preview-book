#!/usr/bin/env python3
"""Detect birds in photos via YOLO, sort images by bird proportion (largest first).

Requirements: pip install ultralytics opencv-python

For each species, analyzes all images and reorders them so the photo where
the bird occupies the largest proportion of the frame comes first.
"""

import json
import os
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import urllib.request
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE_DIR = Path("/tmp/bird_size_cache")
MODEL = None
MAX_WORKERS = 4


def get_model():
    global MODEL
    if MODEL is None:
        MODEL = YOLO("yolov8n.pt")
    return MODEL


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def download(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fname = CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()[:12]}.jpg"
    if fname.exists() and fname.stat().st_size > 1000:
        return str(fname)
    try:
        urllib.request.urlretrieve(url, fname)
        return str(fname) if fname.stat().st_size > 1000 else None
    except Exception:
        return None


def detect_bird_ratio(image_path):
    """Return the proportion of image occupied by the largest detected bird."""
    model = get_model()
    results = model(image_path, verbose=False)
    if not results or not results[0].boxes:
        return None

    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    total = h * w

    # Find the bird with the largest bounding box
    best_ratio = 0.0
    bird_class = 14  # COCO class ID for 'bird'
    for box in results[0].boxes:
        cls = int(box.cls[0].item()) if hasattr(box.cls[0], 'item') else int(box.cls[0])
        if cls == bird_class:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area = (x2 - x1) * (y2 - y1)
            ratio = area / total
            if ratio > best_ratio:
                best_ratio = ratio
    return best_ratio if best_ratio > 0 else None


def process_species(bird_id, images):
    """Re-order images by descending bird proportion."""
    if len(images) <= 1:
        return bird_id, images

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

    # Detect bird ratio per image
    scored = []
    for i, img in enumerate(images):
        ratio = 0.0
        path = paths.get(i)
        if path:
            try:
                r = detect_bird_ratio(path)
                if r is not None:
                    ratio = r
            except Exception:
                pass
        scored.append((ratio, img))

    # Sort by ratio descending
    scored.sort(key=lambda x: x[0], reverse=True)
    best_ratio = scored[0][0] if scored else 0
    reordered = [img for _, img in scored]

    print(f"  top={best_ratio:.1%}", flush=True)
    return bird_id, reordered


def main():
    media = read_json("media.json")
    species = {s["birdId"]: s for s in read_json("species.json")}

    changed = 0
    for bird_id, entry in list(media.items()):
        images = entry.get("images", [])
        if len(images) <= 1:
            continue
        sp = species.get(bird_id, {})
        print(f"{sp.get('chineseName', bird_id)} ({bird_id}) [{len(images)} images]", end="", flush=True)
        _, reordered = process_species(bird_id, images)
        if reordered != images:
            entry["images"] = reordered
            changed += 1
            print(" ← reordered")
        else:
            print("")

    if changed:
        write_json("media.json", media)
    print(f"\nDone: {changed} species reordered")


if __name__ == "__main__":
    main()
