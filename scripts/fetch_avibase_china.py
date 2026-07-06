#!/usr/bin/env python3
"""Fetch Avibase China checklist and write intermediate data file.

Parses the HTML checklist page to extract species with tags
(IUCN status, endemism, occurrence type) and Chinese names.
Writes data/avibase_china.json.

Usage:
  python3 scripts/fetch_avibase_china.py
"""

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

AVIBASE_URL = (
    "https://avibase.bsc-eoc.org/checklist.jsp"
    "?region=CN&list=clements&lang=ZH&format=text"
)

# Regex to parse HTML species row
# Group 1: English name, Group 2: avibaseid, Group 3: scientific name,
# Group 4: Chinese name, Group 5: status tags HTML
ROW_RE = re.compile(
    r"<tr[^>]*>\s*"
    r"<td>\s*(.+?)\s*</td>\s*"
    r"<td><a\s+href=\"species\.jsp\?avibaseid=([A-F0-9]+)\">\s*"
    r"<i>(.+?)</i></a></td>\s*"
    r"<td>(.*?)</td>\s*"
    r"<td>((?:(?!</td>).)*?)</td>\s*"
    r"</tr>",
    re.DOTALL,
)

# Order/family header row
ORDER_RE = re.compile(
    r"<td[^>]*><[^>]*>\s*<[^>]*>\s*<b>([A-Z]+):\s+(.+?)</b>",
    re.DOTALL,
)

# Strip HTML from tags cell, extract tag strings
TAG_STRIP_RE = re.compile(r"<[^>]+>")

# Tag mapping: Chinese text → tag key
TAG_MAP = {
    "稀见/偶见":           "rare",
    "外来物种":            "introduced",
    "消失":               "extirpated",
    "特有的":              "endemic",
    "仅在当地繁育的":       "breeding_endemic",
    "近乎本地特有":         "near_endemic",
    "极危":               "critically_endangered",
    "濒危":               "endangered",
    "易危":               "vulnerable",
    "近危":               "near_threatened",
}

# Tag labels in order of display priority (longest patterns first)
TAG_SORTED = sorted(TAG_MAP.keys(), key=lambda x: -len(x))

# Correct a small set of known Chinese-name issues from the upstream checklist.
CN_NAME_OVERRIDES = {
    "Buteo buteo": "欧亚鵟",
    "Tetraophasis szechenyii": "黄喉雉鹑",
    "Aegithalos iouschistos": "棕额长尾山雀",
}


def fetch_html(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "BirdPreviewBook/3.0 (educational; opensource)",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_tags(html_cell):
    """Extract tag keys from a status tag HTML cell."""
    text = TAG_STRIP_RE.sub("", html_cell).strip()
    if not text:
        return []
    tags = []
    remaining = text
    while remaining:
        found = False
        for pattern in TAG_SORTED:
            if remaining.startswith(pattern):
                tags.append(TAG_MAP[pattern])
                remaining = remaining[len(pattern):].lstrip()
                found = True
                break
        if not found:
            # Unknown text - skip one char
            remaining = remaining[1:].lstrip()
    return tags


def extract_order_blocks(html):
    """Split the HTML into blocks by order headers.
    Returns list of (order_en, family_en, html_block).
    """
    # Find order header positions
    ORDER_HEADER_RE = re.compile(
        r"<td[^>]*><P[^>]*>[^<]*<br[^>]*><b>([A-Z]+):\s+(.+?)</b>",
        re.DOTALL,
    )
    order_positions = []
    for m in ORDER_HEADER_RE.finditer(html):
        order_positions.append((m.start(), m.group(1), m.group(2)))

    if not order_positions:
        return [("Unknown", "Unknown", html)]

    blocks = []
    for i, (pos, order_name, family_name) in enumerate(order_positions):
        end = order_positions[i + 1][0] if i + 1 < len(order_positions) else len(html)
        blocks.append((order_name, family_name, html[pos:end]))
    return blocks


def parse_checklist(html):
    """Parse the full checklist HTML into structured data."""
    species_list = []

    blocks = extract_order_blocks(html)

    for order_name, family_name, block in blocks:
        for sp_m in ROW_RE.finditer(block):
            english_name = sp_m.group(1).strip()
            avibase_id = sp_m.group(2)
            scientific_name = sp_m.group(3).strip()
            chinese_name = sp_m.group(4).strip()
            chinese_name = CN_NAME_OVERRIDES.get(scientific_name, chinese_name)
            tags_html = sp_m.group(5)
            tags = parse_tags(tags_html)

            species_list.append({
                "avibaseId": avibase_id,
                "scientificName": scientific_name,
                "englishName": english_name,
                "chineseName": chinese_name,
                "order": order_name,
                "family": family_name,
                "tags": tags,
                "source": "Avibase",
            })

    return species_list


def main():
    print("[1/2] Fetching China checklist from Avibase...", flush=True)
    html = fetch_html(AVIBASE_URL)

    print("[2/2] Parsing HTML...", flush=True)
    species_list = parse_checklist(html)

    out_path = DATA / "avibase_china.json"
    out_path.write_text(
        json.dumps(species_list, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\nDone: {len(species_list)} species written to {out_path}")

    # Stats
    with_tags = sum(1 for s in species_list if s.get("tags"))
    tag_counts = {}
    for s in species_list:
        for t in s.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    print(f"Species with tags: {with_tags}/{len(species_list)}")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"  {tag}: {count}")

    # Orders
    orders = set(s.get("order") for s in species_list)
    print(f"Orders: {len(orders)}")
    for o in sorted(orders):
        count = sum(1 for s in species_list if s.get("order") == o)
        print(f"  {o}: {count} species")


if __name__ == "__main__":
    main()
