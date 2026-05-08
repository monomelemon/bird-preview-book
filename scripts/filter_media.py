#!/usr/bin/env python3
"""Filter media.json: prioritize Macaulay/eBird photos, flag non-photo illustrations, keep max 3 images per bird."""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MEDIA_PATH = os.path.join(PROJECT_DIR, "data", "media.json")

with open(MEDIA_PATH, encoding="utf-8") as f:
    media = json.load(f)

birds_trimmed = 0
images_removed = 0
images_flagged = 0

for bird_id, data in media.items():
    images = data.get("images", [])
    if not images:
        continue

    # Sort: Macaulay/eBird first, then Wikimedia/others
    images.sort(
        key=lambda img: 0
        if "Macaulay" in img.get("source", "")
        or "ebird" in img.get("source", "").lower()
        else 1
    )

    # Flag non-photo images from non-Macaulay sources
    for img in images:
        if "Macaulay" not in img.get("source", "") and "ebird" not in img.get(
            "source", ""
        ).lower():
            img_type = img.get("type", "")
            if img_type != "photo":
                img["note"] = "待确认是否为实物照片"
                images_flagged += 1

    # Keep max 3
    if len(images) > 3:
        images_removed += len(images) - 3
        data["images"] = images[:3]
        birds_trimmed += 1
    else:
        data["images"] = images

with open(MEDIA_PATH, "w", encoding="utf-8") as f:
    json.dump(media, f, ensure_ascii=False, indent=2)

print(f"Done filtering media")
print(f"  Birds trimmed (over 3 images): {birds_trimmed}")
print(f"  Images removed: {images_removed}")
print(f"  Images flagged for review: {images_flagged}")
