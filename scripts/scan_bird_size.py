#!/usr/bin/env python3
"""Dry-run: detect bird proportion in all images, report species where
reordering would improve thumbnail quality (bird taking up more of the frame).

Requirements: pip install torch torchvision opencv-python numpy pandas tqdm scipy
(also needs ultralytics/yolov5 via torch.hub)
"""

import json
import os
import hashlib
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import urllib.request

import cv2
import torch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE_DIR = Path("/tmp/bird_size_cache")
BIRD_CLS = 14  # COCO class for 'bird'


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def download(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fname = CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()[:12]}.jpg"
    # Check other caches too
    for alt_cache in ["/tmp/ml_image_cache", "/tmp/inat_photo_cache"]:
        alt_fname = Path(alt_cache) / fname.name
        if alt_fname.exists() and alt_fname.stat().st_size > 1000:
            return str(alt_fname)
    if fname.exists() and fname.stat().st_size > 1000:
        return str(fname)
    try:
        urllib.request.urlretrieve(url, fname)
        return str(fname) if fname.stat().st_size > 1000 else None
    except Exception:
        return None


def main():
    media = read_json("media.json")
    species = {s["birdId"]: s for s in read_json("species.json")}
    torch.hub.set_dir('/tmp/torch_hub')

    # Collect all unique image URLs
    url_to_ids = defaultdict(list)
    for bird_id, entry in media.items():
        for i, img in enumerate(entry.get("images", [])):
            url_to_ids[img["url"]].append((bird_id, i))

    print(f"Photos: {len(url_to_ids)} unique URLs across {len(media)} species")

    # Download all images in parallel
    print("Downloading...")
    paths = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download, url): url for url in url_to_ids}
        for i, f in enumerate(as_completed(futures)):
            url = futures[f]
            try:
                paths[url] = f.result()
            except Exception:
                paths[url] = None
            if (i + 1) % 200 == 0:
                print(f"  downloaded {i + 1}/{len(url_to_ids)}")
    print(f"  done: {sum(1 for v in paths.values() if v)} downloadable")

    # Load model
    print("Loading YOLOv5...")
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True,
                           trust_repo=True, verbose=False)

    # Batch inference
    print("Detecting birds...")
    url_ratios = {}
    urls = list(url_to_ids.keys())
    batch_size = 8
    t0 = time.time()

    for start in range(0, len(urls), batch_size):
        batch_urls = urls[start:start + batch_size]
        batch_imgs = []
        valid_indices = []
        for j, url in enumerate(batch_urls):
            path = paths.get(url)
            if path:
                img = cv2.imread(path)
                if img is not None:
                    batch_imgs.append(img)
                    valid_indices.append(j)

        if batch_imgs:
            heights = [img.shape[0] for img in batch_imgs]
            widths = [img.shape[1] for img in batch_imgs]
            results = model(batch_imgs, size=640)

            for idx, det in enumerate(results.xyxy):
                url_idx = valid_indices[idx]
                url = batch_urls[url_idx]
                h = heights[idx]
                w = widths[idx]
                total = h * w

                birds = []
                for d in det.cpu().numpy():
                    if int(d[5]) == BIRD_CLS:
                        area = (d[2] - d[0]) * (d[3] - d[1])
                        ratio = area / total * 100
                        birds.append((d[4], ratio))
                if birds:
                    birds.sort(key=lambda x: -x[1])
                    url_ratios[url] = {
                        "conf": float(birds[0][0]),
                        "ratio": float(birds[0][1]),
                    }

        elapsed = time.time() - t0
        processed = min(start + batch_size, len(urls))
        if processed % 100 == 0 or processed == len(urls):
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = (len(urls) - processed) / rate if rate > 0 else 0
            print(f"  {processed}/{len(urls)} ({rate:.0f}/s) est. {remaining/60:.1f}min left")

    # Analyze: which species would change?
    report = []
    improved = 0
    degraded = 0
    unchanged = 0

    for bird_id, entry in sorted(media.items()):
        images = entry.get("images", [])
        if len(images) <= 1:
            continue

        scored = []
        for i, img in enumerate(images):
            r = url_ratios.get(img["url"])
            ratio = r["ratio"] if r else 0.0
            conf = r["conf"] if r else 0.0
            scored.append((ratio, conf, i))

        scored.sort(key=lambda x: (-x[0], -x[1]))
        current_first_ratio = scored[0][0] if scored[0][2] == 0 else None
        best_ratio = max(s[0] for s in scored)
        best_idx = max(range(len(scored)), key=lambda i: scored[i][0])

        if best_idx != 0 and best_ratio > 0:
            # Worth swapping if best is at least 50% larger or >3pp bigger
            gain = best_ratio - scored[0][0] if scored[0][2] == 0 else best_ratio
            if gain > 3 or (scored[0][2] == 0 and best_ratio > scored[0][0] * 1.5):
                sp = species.get(bird_id, {})
                old_ratio = f"{scored[0][0]:.1f}%" if scored[0][2] == 0 else "N/A"
                report.append({
                    "birdId": bird_id,
                    "name": sp.get("chineseName", bird_id),
                    "current_top": f"{images[0]['author']} ({old_ratio})",
                    "better_pick": f"{images[best_idx]['author']} ({best_ratio:.1f}%)",
                    "gain": gain,
                })
                improved += 1
            else:
                unchanged += 1
        else:
            unchanged += 1

    report.sort(key=lambda r: -r["gain"])

    print(f"\n{'='*70}")
    print(f"RESULTS: {improved} species would improve, {unchanged} already optimal")
    print(f"{'='*70}")
    for r in report[:30]:
        print(f"  {r['name']} ({r['birdId']}): +{r['gain']:.1f}pp")
        print(f"    当前首位: {r['current_top']}")
        print(f"    建议替换: {r['better_pick']}")
    if len(report) > 30:
        print(f"  ... and {len(report) - 30} more")

    # Save detailed report
    report_path = DATA / "bird_size_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nFull report: {report_path}")


if __name__ == "__main__":
    main()
