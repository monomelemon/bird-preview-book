#!/usr/bin/env python3
"""Fetch Chinese Wikipedia summaries using MediaWiki action=query API (not REST)."""

import json, re, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

TRAD_TO_SIMP = str.maketrans({
    "\u51cd":"\u51bb","\u9d5d":"\u9e45","\u9d28":"\u9e2d","\u9901":"\u9e26","\u83de":"\u9e2f","\u9d60":"\u9e44",
    "\u9d70":"\u96d5","\u9df9":"\u9e70","\u9dc2":"\u9e5e","\u9df2":"\u9e6b","\u9d9a":"\u9e57","\u9d7b":"\u9e58",
    "\u9dfa":"\u9e6d","\u9db4":"\u9e64","\u9dd7":"\u9e25","\u9d74":"\u9e3b","\u9df8":"\u9e2c","\u9d10":"\u9e40",
    "\u9d2f":"\u9e5f","\u9d6f":"\u9e17","\u9d47":"\u9e2b","\u9d09":"\u9e26","\u9d46":"\u9e4a",
    "\u9de1":"\u9df9","\u9d51":"\u9d90","\u9d2f":"\u9e5f","\u9d26":"\u9e6a","\u9daf":"\u9e69","\u9d5e":"\u9dae",
    "\u96de":"\u9e21","\u9e3f":"\u4d59","\u9d4a":"\u4d58","\u9c44":"\u9e48","\u9d55":"\u9e2c","\u9ec3":"\u9ec4",
    "\u7063":"\u6e7e","\u7c53":"\u6ee8","\u8e7a":"\u8df7","\u7d05":"\u7ea2","\u85cd":"\u84dd","\u7da0":"\u7eff",
    "\u70cf":"\u4e4c","\u9cf3":"\u51e4","\u982d":"\u5934","\u9838":"\u9888","\u9577":"\u957f","\u8173":"\u811a",
    "\u7ff9":"\u7fd8","\u81c9":"\u8138","\u6975":"\u6781","\u8cca":"\u8d3c","\u8823":"\u86ce","\u6f5b":"\u6f5c",
    "\u9d58":"\u9e55","\u984d":"\u989d","\u9d3b":"\u9e3f","\u528d":"\u5251","\u5bec":"\u5bbd","\u68f2":"\u6816",
    "\u6f01":"\u6e14","\u797f":"\u79c3","\u7d30":"\u7ec6","\u7def":"\u7eef","\u8107":"\u80c1","\u84bc":"\u82cd",
    "\u8607":"\u82cf","\u8afe":"\u8bfa","\u907a":"\u9057","\u9802":"\u9876","\u7c11":"\u84d1","\u6771":"\u4e1c",
    "\u6b50":"\u6b27","\u4e9e":"\u4e9a","\u9077":"\u8fc1","\u9dba":"\u9e61","\u9d12":"\u9e30","\u9d49":"\u9e51",
    "\u9d6a":"\u9e4c","\u96f2":"\u4e91","\u83ef":"\u534e","\u81fa":"\u53f0","\u5ee3":"\u5e7f","\u96d9":"\u53cc",
    "\u5b78":"\u5b66","\u9ad4":"\u4f53","\u985e":"\u7c7b","\u7a2e":"\u79cd","\u9ce5":"\u9e1f","\u9cf4":"\u9e23",
    "\u89c0":"\u89c2","\u8a18":"\u8bb0","\u9304":"\u5f55","\u64da":"\u636e",
})

DIST_RE = re.compile(r"(\u5206\u5e03[\\uff1a:][^\\n]{10,100})|(\u5206\u5e03\u4e8e[^\\n]{10,100})|(\u5728[^\\n]{0,8}(\u4e2d\u56fd|\u4e2d\u570b|\u5927\u9646|\u5927\u9678|\u534e\u5317|\u534e\u5357|\u534e\u4e1c|\u4e1c\u5317|\u897f\u5357|\u897f\u5317)[^\\n]{5,100})", re.IGNORECASE)
CLEAN_RE = re.compile(r"\\[\\d+\\]|\\[\u4f86\u6e90\u8acb\u6c42\\]")

def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\\n")

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
            if pid != "-1" and page.get("extract") and len(page.get("extract","")) > 30:
                return {"title": page["title"], "extract": to_simplified(page["extract"])}
    except Exception:
        pass
    return None

def extract_distribution(extract):
    if not extract:
        return None
    text = extract
    matches = DIST_RE.findall(text)
    parts = []
    for m in matches:
        for g in m:
            if g and len(g) > 8:
                parts.append(g.strip())
    return "\\uff1b".join(parts[:2]) if parts else None

def main():
    species = read_json("species.json")
    wiki = read_json("identification.json")
    total = len(species)
    print(f"fetching Wikipedia for {total} species")
    updated = 0; done = 0

    def fetch_one(sp):
        cn = sp["chineseName"]
        result = fetch_wiki_extract(cn)
        if not result:
            eb = sp.get("englishName","")
            if eb and eb != cn:
                result = fetch_wiki_extract(eb)
        if not result:
            sci = sp.get("scientificName","")
            if sci and sci != cn:
                result = fetch_wiki_extract(sci)
        if not result:
            return sp["birdId"], None
        extract = result["extract"]
        dist = extract_distribution(extract)
        return sp["birdId"], {
            "wikipediaSummary": extract[:800],
            "wikipediaDistribution": dist,
            "wikipediaTitle": result["title"],
            "wikipediaUrl": f"https://zh.wikipedia.org/wiki/{urllib.parse.quote(result['title'])}",
            "wikipediaRetrievedAt": "2026-05-07",
            "wikipediaLicense": "CC BY-SA 4.0",
        }

    batch_size = 20
    for i in range(0, total, batch_size):
        batch = species[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=min(batch_size, 15)) as pool:
            futures = [pool.submit(fetch_one, sp) for sp in batch]
            for future in as_completed(futures):
                bird_id, wiki_data = future.result()
                if wiki_data:
                    ident = wiki.setdefault(bird_id, {})
                    ident.update(wiki_data)
                    ident.setdefault("keyPoints", [])
                    ident.setdefault("morphology", "暂无可靠数据")
                    ident.setdefault("habitat", "暂无可靠数据")
                    ident.setdefault("behavior", "暂无可靠数据")
                    ident.setdefault("sourceRefs", [])
                    updated += 1
                done += 1
                if done % 100 == 0:
                    print(f"  wiki: {done}/{total} (updated {updated})", flush=True)
        time.sleep(0.2)

    with_wiki = sum(1 for v in wiki.values() if v.get("wikipediaSummary"))
    with_dist = sum(1 for v in wiki.values() if v.get("wikipediaDistribution"))
    print(f"wikipedia complete: {total} species, {with_wiki} with summary, {with_dist} with distribution", flush=True)
    write_json("identification.json", wiki)

if __name__ == "__main__":
    main()
