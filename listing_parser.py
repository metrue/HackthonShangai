"""Rule-based extraction from pasted listing text.

Only values that are literally found in the text are returned. Anything not
found stays None and is shown as "not available" in the app.
"""
import re

# Small glossary for a word-by-word English rendering of Chinese titles.
GLOSSARY = [
    ("托特包", "tote bag"), ("手提袋", "tote bag"), ("购物袋", "shopping bag"), ("帆布袋", "canvas bag"),
    ("帆布", "canvas"), ("无纺布", "non-woven"), ("背包", "backpack"), ("双肩包", "backpack"),
    ("保温杯", "insulated bottle"), ("保温壶", "insulated bottle"), ("水杯", "water bottle"),
    ("水壶", "water bottle"), ("马克杯", "mug"), ("咖啡杯", "coffee cup"), ("陶瓷", "ceramic"),
    ("玻璃", "glass"), ("不锈钢", "stainless steel"), ("手机壳", "phone case"), ("硅胶", "silicone"),
    ("透明", "clear"), ("防摔", "shockproof"), ("磁吸", "magnetic"), ("瑜伽垫", "yoga mat"),
    ("加厚", "thick"), ("防滑", "non-slip"), ("灯带", "LED strip"), ("纯棉", "pure cotton"),
    ("棉", "cotton"), ("定制", "custom"), ("批发", "wholesale"), ("环保", "eco-friendly"),
    ("便携", "portable"), ("大容量", "large capacity"), ("礼品", "gift"), ("广告", "promotional"),
    ("真空", "vacuum"), ("双层", "double-wall"), ("印花", "printed"), ("拉链", "zipper"),
]

CATEGORY_HINTS = [
    ("bags", ["托特包", "手提袋", "购物袋", "帆布袋", "背包", "双肩包", "tote", "bag"]),
    ("drinkware", ["保温杯", "保温壶", "水杯", "水壶", "bottle", "tumbler"]),
    ("ceramics", ["马克杯", "咖啡杯", "陶瓷", "mug", "ceramic"]),
    ("phone accessories", ["手机壳", "phone case"]),
    ("sports", ["瑜伽垫", "yoga"]),
    ("lighting", ["灯带", "led strip", "led"]),
]

CITIES = {
    "义乌": "Yiwu", "广州": "Guangzhou", "深圳": "Shenzhen", "杭州": "Hangzhou", "宁波": "Ningbo",
    "温州": "Wenzhou", "东莞": "Dongguan", "泉州": "Quanzhou", "金华": "Jinhua", "上海": "Shanghai",
    "苏州": "Suzhou", "青岛": "Qingdao", "厦门": "Xiamen", "中山": "Zhongshan", "佛山": "Foshan",
    "永康": "Yongkang", "南通": "Nantong", "汕头": "Shantou", "台州": "Taizhou", "北京": "Beijing",
}

BADGES = [
    ("实力商家", "Verified supplier"), ("深度验厂", "Onsite inspection"), ("源头工厂", "Source factory"),
    ("交易保障", "Trade assurance"), ("买家保障", "Trade assurance"), ("诚信通", "TrustPass member"),
    ("官方旗舰店", "Brand official store"), ("京东自营", "Platform self-operated"),
]

NUM = r"(\d+(?:\.\d+)?)"


def _first(patterns, text, flags=re.I):
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            return m
    return None


def translate_title(cn):
    if not cn:
        return None
    if not re.search(r"[一-鿿]", cn):
        return cn.strip()  # already latin text
    found = []  # (position in title, english word)
    rest = cn
    for zh, en in GLOSSARY:
        idx = rest.find(zh)
        if idx >= 0:
            found.append((idx, en))
            rest = rest.replace(zh, "\0" * len(zh))
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9.+\-]*|\d+(?:\.\d+)?(?:ml|cm|mm|L)(?![A-Za-z])", cn):
        found.append((m.start(), m.group(0)))
    seen, out = set(), []
    for _, w in sorted(found):
        if w.lower() not in seen:
            seen.add(w.lower())
            out.append(w)
    return " ".join(out).capitalize() if out else None


def parse_listing(text):
    t = text or ""
    lines = [l.strip() for l in t.splitlines() if l.strip()]

    # Title: first line that is not a URL and not a price line
    title_cn = None
    for l in lines:
        is_url = re.match(r"^(https?://|www\.)", l, re.I)
        is_price = re.search(r"[¥￥]", l) or re.match(r"^[≥>\d\s\-~～至件个pcs]+$", l, re.I)
        has_words = re.search(r"[一-鿿A-Za-z]{2,}", l)
        if not is_url and not is_price and has_words:
            title_cn = l[:120]
            break

    url_m = re.search(r"https?://[^\s]+", t)
    url = url_m.group(0) if url_m else None
    platform = None
    if url:
        for key, name in [("1688.com", "1688"), ("taobao.com", "Taobao"), ("tmall.com", "Taobao"),
                          ("jd.com", "JD"), ("yiwugo.com", "Yiwugo")]:
            if key in url:
                platform = name
    if platform is None:
        for key, name in [("1688", "1688"), ("淘宝", "Taobao"), ("taobao", "Taobao"),
                          ("京东", "JD"), ("义乌购", "Yiwugo"), ("yiwugo", "Yiwugo")]:
            if key.lower() in t.lower():
                platform = name
                break

    # Price tiers: "100-499件 ¥12.5", "≥500件 ¥10"
    tiers = []
    for m in re.finditer(r"(\d+)\s*(?:-|~|～|至)\s*\d+\s*(?:件|个|只|pcs|pieces)?\s*[:：]?\s*[¥￥]\s*" + NUM, t, re.I):
        tiers.append((int(m.group(1)), float(m.group(2))))
    for m in re.finditer(r"(?:≥|>=|>|大于等于)\s*(\d+)\s*(?:件|个|只|pcs|pieces)?\s*[:：]?\s*[¥￥]\s*" + NUM, t, re.I):
        tiers.append((int(m.group(1)), float(m.group(2))))
    moq_m = _first([
        r"(\d+)\s*(?:件|个|只|pcs|pieces)?\s*起(?:批|订|售)",
        r"(?:MOQ|起订量|起批量|最小起订)\s*[:：]?\s*(\d+)",
    ], t)
    moq = int(moq_m.group(1)) if moq_m else None
    if not tiers:
        price_m = _first([r"[¥￥]\s*" + NUM, NUM + r"\s*(?:元|CNY|RMB)"], t)
        if price_m:
            tiers = [(moq or 1, float(price_m.group(1)))]
    tiers = sorted(set(tiers))
    if moq is None and tiers and len(tiers) > 1:
        moq = tiers[0][0]

    weight = None
    w_m = _first([
        r"(?:重量|毛重|净重|weight)\s*[:：]?\s*" + NUM + r"\s*(kg|公斤|千克|g|克)",
        NUM + r"\s*(kg|公斤|千克)",
    ], t)
    if w_m:
        v, unit = float(w_m.group(1)), w_m.group(2).lower()
        weight = v / 1000 if unit in ("g", "克") else v

    def field(keys):
        m = re.search(r"(?:" + keys + r")\s*[:：]\s*([^\n]+)", t, re.I)
        return m.group(1).strip()[:100] if m else None

    material = field("材质|材料|面料|material")
    if material and re.search(r"[一-鿿]", material):
        en = translate_title(material)
        material = f"{en} (original: {material})" if en else f"English: {'not available'} (original: {material})"
    size = field("尺寸|规格|大小|size|dimensions")

    prod_m = _first([
        r"(?:交期|发货时间|生产周期|lead time|production time)\s*[:：]?\s*(\d+)",
        r"(\d+)\s*(?:天|days?)\s*(?:内)?(?:发货|交货|出货)",
    ], t)
    production_days = int(prod_m.group(1)) if prod_m else None

    custom = None
    custom_terms = {"定制": "custom orders", "OEM": "OEM", "ODM": "ODM", "logo": "logo", "LOGO": "logo",
                    "来图": "made to your design", "来样": "made to your sample"}
    custom_hits = [en for zh, en in custom_terms.items() if zh in t]
    if custom_hits:
        custom = "Mentioned in listing: " + ", ".join(dict.fromkeys(custom_hits))

    name_m = _first([r"([一-鿿A-Za-z（）()]{2,30}(?:有限公司|厂|商行|店))",
                     r"(?:supplier|company|店铺|公司)\s*[:：]\s*([^\n]+)"], t)
    supplier_name_cn = name_m.group(1).strip() if name_m else None

    city = None
    for zh, en in CITIES.items():
        if zh in t:
            city = en
            break
    if city is None:
        for en in CITIES.values():
            if re.search(r"\b" + en + r"\b", t, re.I):
                city = en
                break

    years_m = _first([r"(?:经营|入驻|成立|开店)\D{0,4}(\d{1,2})\s*年", r"(\d{1,2})\s*年(?:老店|诚信通)",
                      r"(\d{1,2})\s*years?"], t)
    years = int(years_m.group(1)) if years_m else None

    seller_type = None
    if any(k in t for k in ["工厂", "厂家", "生产厂", "源头", "制造", "factory", "manufacturer"]):
        seller_type = "factory"
    elif any(k in t for k in ["贸易", "进出口", "商贸", "trading"]):
        seller_type = "middleman"
    elif any(k in t for k in ["店", "旗舰店", "商行", "store", "shop"]):
        seller_type = "store"

    badges = list(dict.fromkeys(en for zh, en in BADGES if zh in t))

    rr_m = _first([r"(?:回复率|响应率|response rate)\s*[:：]?\s*" + NUM + r"\s*%"], t)
    rb_m = _first([r"(?:回头率|复购率|repeat buyer rate)\s*[:：]?\s*" + NUM + r"\s*%"], t)

    category = None
    low = t.lower()
    for cat, hints in CATEGORY_HINTS:
        if any(h.lower() in low for h in hints):
            category = cat
            break

    return dict(
        id="PASTED", category=category,
        title_en=translate_title(title_cn), title_cn=title_cn, keywords="",
        platform=platform, moq=moq, tiers=tiers,
        material=material, size=size, weight_kg=weight, production_days=production_days,
        customisation=custom, url=url,
        supplier=dict(
            name=None, name_cn=supplier_name_cn, city=city, type=seller_type, years=years,
            badges=badges,
            response_rate=round(float(rr_m.group(1))) if rr_m else None,
            repeat_buyer_rate=round(float(rb_m.group(1))) if rb_m else None,
            disputes=None,
        ),
    )


SAMPLE_LISTING = """12安加厚帆布手提袋 可定制logo 环保购物袋 批发
https://detail.1688.com/offer/000000000000.html
100-499件 ¥8.50
500-1999件 ¥7.20
≥2000件 ¥6.10
100件起批
材质：12安纯棉帆布
尺寸：38*42cm
重量：180g
付款后15天内发货
支持来图定制 OEM
温州苍南某某袋业有限公司  生产厂家  实力商家  经营11年
回头率 36%  响应率 94%"""
