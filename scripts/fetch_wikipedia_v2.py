#!/usr/bin/env python3
"""Fetch Chinese Wikipedia summaries and write description/distribution into species.json."""

import json, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TRAD_TO_SIMP = str.maketrans({
    "凍": "冻", "鵝": "鹅", "鴨": "鸭", "鴛": "鸳", "鴦": "鸯", "鵠": "鹄", "鵰": "雕", "鷹": "鹰",
    "鷂": "鹞", "鷲": "鹫", "鶚": "鹗", "鶻": "鹘",
    "鷺": "鹭", "鶴": "鹤", "鷗": "鸥", "鴴": "鸻", "鷸": "鹬", "鵐": "鹀", "鶲": "鹟",
    "鵯": "鹎", "鶇": "鸫", "鴉": "鸦", "鵲": "鹊",
    "鴟": "鸱", "鵑": "鹃", "鶯": "莺", "鷦": "鹪", "鷯": "鹩", "鴞": "鸮", "雞": "鸡",
    "鷿": "\u4d59", "鸊": "\u4d58", "鵜": "鹈", "鸕": "鸬",
    "黃": "黄", "灣": "湾", "濱": "滨", "蹺": "跷", "紅": "红", "藍": "蓝", "綠": "绿",
    "烏": "乌", "鳳": "凤", "頭": "头", "頸": "颈",
    "長": "长", "腳": "脚", "翹": "翘", "臉": "脸", "極": "极", "賊": "贼", "蠣": "蛎",
    "潛": "潜", "鶘": "鹕", "額": "额", "鴻": "鸿", "劍": "剑", "寬": "宽",
    "棲": "栖", "漁": "渔", "禿": "秃", "細": "细", "緋": "绯", "脇": "胁", "蒼": "苍",
    "蘇": "苏", "諾": "诺", "遺": "遗", "頂": "顶", "簑": "蓑", "東": "东", "歐": "欧",
    "亞": "亚", "遷": "迁", "鶺": "鹡", "鴒": "鸰", "鶉": "鹑", "鵪": "鹌",
    "雲": "云", "華": "华", "臺": "台", "廣": "广", "雙": "双", "學": "学", "體": "体",
    "類": "类", "種": "种", "鳥": "鸟", "鳴": "鸣", "觀": "观", "記": "记", "錄": "录", "據": "据",
    "鳩": "鸠", "鴿": "鸽", "鸌": "鹱", "鸛": "鹳",
})

DIST_RE = re.compile(
    r"(\u5206\u5e03[\uff1a:][^\n]{10,100})|"
    r"(\u5206\u5e03\u4e8e[^\n]{10,100})|"
    r"(\u5728[^\n]{0,8}(\u4e2d\u56fd|\u4e2d\u570b|\u5927\u9646|\u5927\u9678|"
    r"\u534e\u5317|\u534e\u5357|\u534e\u4e1c|\u4e1c\u5317|\u897f\u5357|\u897f\u5317)[^\n]{5,100})",
    re.IGNORECASE)


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def to_simplified(text):
    return str(text or "").translate(TRAD_TO_SIMP)


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
    parts = []
    for m in matches:
        for g in m:
            if g and len(g) > 8:
                parts.append(g.strip())
    return "\uff1b".join(parts[:2]) if parts else None


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
    batch_size = 20
    for i in range(0, len(batch), batch_size):
        chunk = batch[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=min(batch_size, 15)) as pool:
            futures = [pool.submit(fetch_one, sp) for sp in chunk]
            for future in as_completed(futures):
                bird_id, wiki_data = future.result()
                if wiki_data and bird_id in species_index:
                    species_index[bird_id]["description"] = wiki_data["description"]
                    if wiki_data["distribution"]:
                        species_index[bird_id]["distribution"] = wiki_data["distribution"]
                    updated += 1
                done += 1
                if done % 25 == 0:
                    print(f"  wiki: {done}/{total} (updated {updated})", flush=True)
        time.sleep(0.2)

    with_desc = sum(1 for sp in species if sp.get("description"))
    with_dist = sum(1 for sp in species if sp.get("distribution"))
    print(f"wikipedia complete: {total} species, {with_desc} with description, {with_dist} with distribution", flush=True)
    write_json("species.json", species)
    print("wrote species.json")


if __name__ == "__main__":
    main()
