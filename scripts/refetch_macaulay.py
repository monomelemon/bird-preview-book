import json
import requests
import time

species = json.load(open('data/species.json'))
media = json.load(open('data/media.json'))

total = 0
new_photos = 0
for sp in species:
    code = sp.get('speciesCode')
    if not code:
        continue
    bid = sp['birdId']
    cn = sp['chineseName']

    try:
        resp = requests.get(
            f'https://search.macaulaylibrary.org/api/v1/search?taxonCode={code}&mediaType=photo&pageSize=10',
            timeout=15
        )
        data = resp.json()
        results = data.get('results', {}).get('content', [])

        good = []
        for r in results:
            url = r.get('largeUrl') or r.get('mediaUrl', '')
            if not url:
                continue
            rating = float(r.get('rating', 0))
            rating_count = int(r.get('ratingCount', 0))
            if rating >= 3 or rating_count >= 5 or rating == 0:
                good.append({
                    'url': url,
                    'type': 'photo',
                    'caption': cn,
                    'source': 'Macaulay Library / eBird',
                    'sourceUrl': r.get('specimenUrl') or f'https://macaulaylibrary.org/asset/{r["assetId"]}',
                    'author': r.get('userDisplayName', ''),
                    'license': r.get('licenseType', 'eBird'),
                })
            if len(good) >= 3:
                break

        if good:
            media.setdefault(bid, {})['images'] = good
            new_photos += len(good)

        total += 1
        if total % 50 == 0:
            print(f'  Processed {total} species, {new_photos} new photos...')

        time.sleep(0.25)

    except Exception as e:
        print(f'  Error {bid} ({cn}): {e}')

print(f'Done. {total} species processed. {new_photos} new photos saved.')

json.dump(media, open('data/media.json', 'w'), ensure_ascii=False, indent=2)
print('media.json written')
