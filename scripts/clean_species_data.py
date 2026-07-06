#!/usr/bin/env python3
"""Clean species data: family names English→Chinese, traditional→simplified names, aliases, taxonomy rebuild."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"

# Import shared utilities
sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_utils import to_simplified

# ─── Family name English → Chinese mapping (ALL 104 families) ───
FAMILY_MAP = {
    # ── WATERFOWL (Anseriformes) ──
    "Ducks, Geese, and Waterfowl": "鸭科",
    # ── GREBES (Podicipediformes) ──
    "Grebes": "䴙䴘科",
    # ── GALLIFORMES ──
    "Guineafowl": "珠鸡科",
    "Pheasants, Grouse, and Allies": "雉科",
    # ── COLUMBIFORMES ──
    "Pigeons and Doves": "鸠鸽科",
    "Sandgrouse": "沙鸡科",
    # ── GRUIFORMES ──
    "Cranes": "鹤科",
    "Rails, Gallinules, and Coots": "秧鸡科",
    # ── CHARADRIIFORMES ──
    "Auks, Murres, and Puffins": "海雀科",
    "Buttonquail": "三趾鹑科",
    "Gulls, Terns, and Skimmers": "鸥科",
    "Ibisbill": "鹮嘴鹬科",
    "Jacanas": "水雉科",
    "Oystercatchers": "蛎鹬科",
    "Painted-Snipes": "彩鹬科",
    "Plovers and Lapwings": "鸻科",
    "Plovers": "鸻科",
    "Pratincoles and Coursers": "燕鸻科",
    "Sandpipers and Allies": "鹬科",
    "Skuas and Jaegers": "贼鸥科",
    "Stilts and Avocets": "反嘴鹬科",
    "Phalaropes": "瓣蹼鹬科",
    "Thick-knees": "石鸻科",
    # ── PELECANIFORMES ──
    "Herons, Egrets, and Bitterns": "鹭科",
    "Bitterns, Herons, Egrets": "鹭科",
    "Ibises and Spoonbills": "鹮科",
    "Pelicans": "鹈鹕科",
    # ── ACCIPITRIFORMES ──
    "Hawks, Eagles, and Kites": "鹰科",
    "Osprey": "鹗科",
    # ── STRIGIFORMES ──
    "Barn-Owls": "仓鸮科",
    "Owls": "鸱鸮科",
    # ── CORACIIFORMES ──
    "Bee-eaters": "蜂虎科",
    "Kingfishers": "翠鸟科",
    "Rollers": "佛法僧科",
    # ── PICIFORMES ──
    "Asian Barbets": "拟啄木鸟科",
    "Woodpeckers": "啄木鸟科",
    # ── FALCONIFORMES ──
    "Falcons and Caracaras": "隼科",
    # ── PASSERIFORMES ──
    "Accentors": "岩鹨科",
    "Bearded Reedling": "文须雀科",
    "Bulbuls": "鹎科",
    "Bush Warblers and Allies": "树莺科",
    "Cisticolas and Allies": "扇尾莺科",
    "Crows, Jays, and Magpies": "鸦科",
    "Jays, Magpies, Crows": "鸦科",
    "Cuckooshrikes": "山椒鸟科",
    "Cupwings": "短翅莺科",
    "Dippers": "河乌科",
    "Drongos": "卷尾科",
    "Fairy Flycatchers": "仙鹟科",
    "Finches, Euphonias, and Allies": "燕雀科",
    "Flowerpeckers": "啄花鸟科",
    "Grassbirds and Allies": "蝗莺科",
    "Ground Babblers and Allies": "画眉科",
    "Kinglets": "戴菊科",
    "Larks": "百灵科",
    "Laughingthrushes and Allies": "噪鹛科",
    "Leaf Warblers": "柳莺科",
    "Leafbirds": "叶鹎科",
    "Long-tailed Tits": "长尾山雀科",
    "Longspurs and Snow Buntings": "铁爪鹀科",
    "Monarch Flycatchers": "王鹟科",
    "Mockingbirds and Thrashers": "嘲鸫科",
    "New World Sparrows": "雀鹀科",
    "Nuthatches": "鳾科",
    "Old World Buntings": "鹀科",
    "Old World Flycatchers": "鹟科",
    "Old World Orioles": "黄鹂科",
    "Old World Parrots": "鹦鹉科",
    "Old World Sparrows": "雀科",
    "Parrotbills": "鸦雀科",
    "Parrotbills and Allies": "鸦雀科",
    "Penduline-Tits": "攀雀科",
    "Pipits and Wagtails": "鹡鸰科",
    "Pittas": "八色鸫科",
    "Reed Warblers and Allies": "苇莺科",
    "Shrikes": "伯劳科",
    "Spotted Elachura": "鹛莺科",
    "Starlings": "椋鸟科",
    "Sunbirds and Spiderhunters": "太阳鸟科",
    "Swallows": "燕科",
    "Sylviid Warblers and Allies": "莺鹛科",
    "Thrushes and Allies": "鸫科",
    "Tits, Chickadees, and Titmice": "山雀科",
    "Chickadees and Titmice": "山雀科",
    "Tree-Babblers, Scimitar-Babblers, and Allies": "林鹛科",
    "Treecreepers": "旋木雀科",
    "Vangas, Helmetshrikes, and Allies": "钩嘴鵙科",
    "Vangas, Helmetshrikes and Allies": "钩嘴鵙科",
    "Vireos, Shrike-Babblers, and Erpornis": "莺雀科",
    "Wagtails and Pipits": "鹡鸰科",
    "Wallcreeper": "旋壁雀科",
    "Waxbills and Allies": "梅花雀科",
    "Waxwings": "太平鸟科",
    "Wheatears and Chats": "鹟科",
    "White-eyes, Yuhinas, and Allies": "绣眼鸟科",
    "Whydahs and Indigobirds": "维达鸟科",
    "Wrens": "鹪鹩科",
    # ── NON-PASSERINE MISC ──
    "Albatrosses": "信天翁科",
    "Boobies and Gannets": "鲣鸟科",
    "Bustards": "鸨科",
    "Cockatoos": "凤头鹦鹉科",
    "Cormorants and Shags": "鸬鹚科",
    "Cuckoos": "杜鹃科",
    "Flamingos": "红鹳科",
    "Frigatebirds": "军舰鸟科",
    "Hoopoes": "戴胜科",
    "Hornbills": "犀鸟科",
    "Loons": "潜鸟科",
    "Nightjars and Allies": "夜鹰科",
    "Lorises, Potoos, Oilbird, Frogmouths, Nightjars": "蟆口鸱科",
    "Northern Storm-Petrels": "海燕科",
    "Southern Storm-Petrels": "海燕科",
    "Storm-Petrels": "海燕科",
    "Shearwaters and Petrels": "鹱科",
    "Storks": "鹳科",
    "Swifts": "雨燕科",
    "Trogons": "咬鹃科",
    "Tropicbirds": "鹲科",
    "Tyrant Flycatchers": "霸鹟科",
}

# ─── V1 birdId → species-specific overrides ───
V1_ALIASES = {
    "comkin1": ["普通翠鸟", "翠鸟", "alcedo_atthis"],
    "livbul1": ["白头鹎", "白头翁", "pycnonotus_sinensis"],
    "rbbmag": ["红嘴蓝鹊", "urocissa_erythroryncha"],
}

V1_CHINESE_NAME = {
    "comkin1": "普通翠鸟",
    "livbul1": "白头鹎",
    "rbbmag": "红嘴蓝鹊",
}


def read_json(name):
    with (DATA / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(name, obj):
    with (DATA / name).open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def has_chinese(text):
    return any("\u4e00" <= c <= "\u9fff" for c in (text or ""))


def has_ascii_alpha(text):
    return bool(re.search(r"[A-Za-z]", text or ""))


def simplify_name(text):
    return to_simplified(text)


def main():
    species = read_json("species.json")
    taxonomy = read_json("taxonomy.json")
    metadata = read_json("metadata.json")

    families_mapped = 0
    names_converted = 0
    aliases_added = 0
    family_set = {}  # family.en → {zh, orderZh}

    for sp in species:
        modified = False

        # ── 1. Fix family.zh English→Chinese ──
        family_zh = sp["family"]["zh"]
        family_en = sp["family"]["en"]
        if family_zh in FAMILY_MAP:
            new_zh = FAMILY_MAP[family_zh]
            if new_zh != family_zh:
                sp["family"]["zh"] = new_zh
                families_mapped += 1
                modified = True

        # ── 2. Convert chineseName traditional→simplified ──
        old_cn = sp.get("chineseName", "")
        if old_cn:
            new_cn = simplify_name(old_cn)
            if new_cn != old_cn:
                sp["chineseName"] = new_cn
                names_converted += 1
                modified = True

        # ── 3. Override specific V1 species chineseName ──
        if sp["birdId"] in V1_CHINESE_NAME:
            sp["chineseName"] = V1_CHINESE_NAME[sp["birdId"]]
            sp["family"]["zh"] = FAMILY_MAP.get(sp["family"]["zh"], sp["family"]["zh"])
            modified = True

        # ── 4. Fix chineseName "Black Scoter" and other English names ──
        chinese_name = sp.get("chineseName", "")
        english_name = sp.get("englishName", "")
        if not has_chinese(chinese_name) and has_chinese(english_name):
            # Rare: if englishName has Chinese, don't touch
            pass

        # ── 5. Add V1 aliases ──
        aliases = sp.setdefault("aliases", [])
        if sp["birdId"] in V1_ALIASES:
            for alias in V1_ALIASES[sp["birdId"]]:
                if alias not in aliases:
                    aliases.append(alias)
                    aliases_added += 1
                    modified = True

        # ── 6. Add original traditional name as alias if it differs ──
        if old_cn and to_simplified(old_cn) != old_cn and old_cn not in aliases:
            aliases.append(old_cn)
            aliases_added += 1
            modified = True

        # ── 7. Convert aliases to simplified ──
        new_aliases = []
        seen = set()
        for a in sp.get("aliases", []):
            a_simp = simplify_name(a)
            if a_simp and not has_ascii_alpha(a_simp) and a_simp not in seen:
                new_aliases.append(a_simp)
                seen.add(a_simp)
        sp["aliases"] = new_aliases

        # Deduplicate aliases against chineseName
        sp["aliases"] = [a for a in sp["aliases"] if a != sp.get("chineseName", "")]

        # ── 8. Convert order.zh to simplified if needed ──
        order_zh = sp.get("order", {}).get("zh", "")
        order_simp = simplify_name(order_zh)
        if order_simp != order_zh:
            sp["order"]["zh"] = order_simp

        # ── 9. Track families for taxonomy rebuild ──
        f_en = sp["family"]["en"]
        f_zh = sp["family"]["zh"]
        o_zh = sp["order"]["zh"]
        if f_en not in family_set:
            family_set[f_en] = {"zh": f_zh, "en": f_en, "orderZh": o_zh}

        sp["updatedAt"] = "2026-05-08"

    # ── 10. Rebuild taxonomy.json families ──
    # Map family English names to sort orders from original taxonomy
    old_sort = {}
    for f in taxonomy["families"]:
        old_sort[f["en"]] = f.get("sortOrder", 9999)

    new_families = []
    for i, (f_en, f_data) in enumerate(sorted(family_set.items())):
        zh = f_data["zh"]
        so = old_sort.get(f_en, 9000 + i)
        new_families.append({
            "zh": zh,
            "en": f_en,
            "orderZh": f_data["orderZh"],
            "sortOrder": so,
        })

    # Sort by sortOrder
    new_families.sort(key=lambda x: x["sortOrder"])
    taxonomy["families"] = new_families

    # ── 11. Update metadata ──
    metadata["dataVersion"] = "v2-fix-2026-05-08"
    metadata["updatedAt"] = "2026-05-08"

    # ── 12. Write output ──
    write_json("species.json", species)
    write_json("taxonomy.json", taxonomy)
    write_json("metadata.json", metadata)

    # ── Summary ──
    print(f"clean_species_data.py complete")
    print(f"  Species processed: {len(species)}")
    print(f"  Families mapped (EN→CN): {families_mapped}")
    print(f"  Names converted (trad→simp): {names_converted}")
    print(f"  Aliases added: {aliases_added}")
    print(f"  Families in taxonomy: {len(new_families)}")
    print(f"  Metadata version: v2-fix-2026-05-08")

    # Show examples
    for sp in species:
        if sp["birdId"] in V1_CHINESE_NAME:
            print(f"\n  Example {sp['birdId']}:")
            print(f"    chineseName: {sp['chineseName']}")
            print(f"    aliases: {sp['aliases']}")
            print(f"    family.zh: {sp['family']['zh']}")


if __name__ == "__main__":
    main()
