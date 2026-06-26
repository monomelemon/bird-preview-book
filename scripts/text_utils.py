#!/usr/bin/env python3
"""Shared text utilities for Chinese Traditional-to-Simplified conversion.

All data-ingestion scripts should import `to_simplified` from this module
instead of maintaining their own TRAD_TO_SIMP mapping.  This is the
single source of truth for the project.

For the JS/display layer (app.js), `toSimplified()` is kept for search-
query normalisation only — data leaving ingestion scripts is already
converted.
"""

# fmt: off
_TRAD_TO_SIMP = str.maketrans({
    # ---- birds (鸟字旁) ----
    "鳥": "鸟", "鳩": "鸠", "鳳": "凤", "鳴": "鸣",
    "鴉": "鸦", "鴒": "鸰", "鴛": "鸳", "鴦": "鸯",
    "鴨": "鸭", "鴴": "鸻", "鴻": "鸿", "鴿": "鸽",
    "鵐": "鹀", "鵑": "鹃", "鵜": "鹈", "鵝": "鹅",
    "鵠": "鹄", "鵡": "鹉", "鵪": "鹌", "鵬": "鹏",
    "鵯": "鹎", "鵰": "雕", "鵲": "鹊", "鶇": "鸫",
    "鶉": "鹑", "鶘": "鹕", "鶚": "鹗", "鶯": "莺",
    "鶲": "鹟", "鶴": "鹤", "鶺": "鹡", "鶻": "鹘",
    "鶿": "鹚", "鷀": "鹚", "鷂": "鹞", "鷓": "鹧",
    "鷗": "鸥", "鷚": "鹨", "鷦": "鹪", "鷯": "鹩",
    "鷲": "鹫", "鷸": "鹬", "鷹": "鹰", "鷺": "鹭",
    "䴙": "䴙", "鷿": "䴙", "䴘": "䴘", "鸊": "䴘",
    # ---- other bird-related ----
    "鴇": "鸨", "鴞": "鸮", "鴟": "鸱",
    "鸌": "鹱", "鸕": "鸬", "鸚": "鹦", "鸛": "鹳",
    # ---- animals ----
    "雞": "鸡", "貝": "贝",
    # ---- fish / water ----
    "鰹": "鲣", "鱗": "鳞", "魚": "鱼",
    # ---- common Traditional chars ----
    "凍": "冻", "黃": "黄", "灣": "湾", "濱": "滨",
    "蹺": "跷", "紅": "红", "藍": "蓝", "綠": "绿",
    "烏": "乌", "頭": "头", "頸": "颈",
    "長": "长", "腳": "脚", "翹": "翘", "臉": "脸",
    "極": "极", "賊": "贼", "蠣": "蛎",
    "潛": "潜", "額": "额", "劍": "剑", "寬": "宽",
    "棲": "栖", "漁": "渔", "禿": "秃", "細": "细",
    "緋": "绯", "脇": "胁", "蒼": "苍",
    "蘇": "苏", "諾": "诺", "遺": "遗", "頂": "顶",
    "簑": "蓑", "東": "东", "歐": "欧",
    "亞": "亚", "遷": "迁", "雲": "云", "華": "华",
    "臺": "台", "廣": "广", "雙": "双", "學": "学",
    "體": "体", "類": "类", "種": "种",
    "觀": "观", "記": "记", "錄": "录", "據": "据",
    "為": "为", "畫": "画", "點": "点",
    "門": "门", "鹽": "盐",
    "裏": "里", "裡": "里",
    # ---- common non-bird traditional chars ----
    "佈": "布", "於": "于", "見": "见", "僅": "仅", "匯": "汇",
    "區": "区", "帶": "带", "會": "会", "國": "国", "對": "对",
    # ---- misc ----
    "瀆": "渎", "雛": "雏", "鳾": "鳾", "塒": "埘",
    "雜": "杂", "嘴": "嘴", "斑": "斑",
})
# fmt: on


def to_simplified(text):
    """Convert Traditional Chinese characters to Simplified in *text*."""
    return str(text or "").translate(_TRAD_TO_SIMP)
