#!/usr/bin/env python3
"""Fetch Macaulay audio for species with speciesCode, storing URLs in media.json."""

import json, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

def fetch_audio(code, page_size=5):
    q = urllib.parse.urlencode({"taxonCode": code, "mediaType": "audio", "pageSize": page_size})
    url = f"https://search.macaulaylibrary.org/api/v1/search?{q}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return (json.loads(r.read().decode()) or {}).get("results", {}).get("content", []) or []

def audio_to_entry(audio, sp_name):
    source_url = audio.get("specimenUrl") or (f"https://macaulaylibrary.org/asset/{audio.get('assetId')}" if audio.get("assetId") else "")
    url = audio.get("mediaUrl") or audio.get("largeUrl") or audio.get("previewUrl")
    if not url:
        return None
    return {
        "url": url,
        "type": audio.get("mediaType") or "audio",
        "caption": sp_name,
        "source": "Macaulay Library / eBird",
        "sourceUrl": source_url,
        "author": audio.get("userDisplayName") or "Macaulay Library contributor",
        "license": audio.get("licenseType") or "见来源页面",
    }

def main():
    species = read_json("species.json")
    media = read_json("media.json")
    sp_by_id = {s["birdId"]: s for s in species}
    targets = [s for s in species if s.get("speciesCode")]
    targets = targets[:816]
    total = len(targets)
    print(f"fetching audio for up to {total} species")

    added = 0
    done = 0
    errors = 0
    batch_size = 30

    for i in range(0, total, batch_size):
        batch = targets[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=min(batch_size, 15)) as pool:
            def fetch_one(sp):
                entry = media.setdefault(sp["birdId"], {})
                entry.setdefault("images", [])
                entry.setdefault("sounds", [])
                entry.setdefault("rangeMap", None)
                if len(entry["sounds"]) >= 4:
                    return sp["birdId"], 0, True
                try:
                    audios = fetch_audio(sp["speciesCode"], 5)
                except Exception as e:
                    return sp["birdId"], 0, (False, str(e))
                new_audio = 0
                existing_urls = {s["url"] for s in entry["sounds"]}
                for a in audios:
                    ae = audio_to_entry(a, sp["chineseName"])
                    if ae and ae["url"] not in existing_urls:
                        entry.setdefault("sounds", []).append(ae)
                        existing_urls.add(ae["url"])
                        new_audio += 1
                        if len(entry["sounds"]) >= 4:
                            break
                return sp["birdId"], new_audio, True

            futures = [pool.submit(fetch_one, sp) for sp in batch]
            for future in as_completed(futures):
                _, n, ok = future.result()
                added += n
                done += 1
                if not ok:
                    errors += 1
                if done % 100 == 0:
                    print(f"  audio: {done}/{total} (added {added}, err {errors})", flush=True)
        time.sleep(0.3)

    with_audio = sum(1 for v in media.values() if v.get("sounds"))
    total_sounds = sum(len(v.get("sounds", [])) for v in media.values())
    print(f"audio complete: {total} species, {with_audio} with audio, {total_sounds} sounds, {errors} errors", flush=True)
    write_json("media.json", media)

if __name__ == "__main__":
    main()
