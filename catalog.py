"""Sample catalog.

Every record here is SAMPLE data written for demonstration. It does not come
from a live listing on any platform. Fields set to None are genuinely unknown
and are displayed as "not available" in the app.
"""

PLATFORMS = ["1688", "Taobao", "JD", "Yiwugo"]
SELLER_TYPES = ["factory", "store", "middleman"]

# Category -> emoji + colour used for the placeholder image
CATEGORY_STYLE = {
    "bags": ("👜", "#E8D5B7"),
    "drinkware": ("🥤", "#BFDDF2"),
    "phone accessories": ("📱", "#D6CCF0"),
    "sports": ("🧘", "#C8E6C9"),
    "ceramics": ("☕", "#F3D3C6"),
    "lighting": ("💡", "#FFF1B8"),
    "unknown": ("📦", "#E0E0E0"),
}


def _p(**kw):
    return kw


PRODUCTS = [
    # ---------------- Tote bags ----------------
    _p(
        id="TB-01", category="bags",
        title_en="Heavy canvas tote bag, 12 oz, custom logo print",
        title_cn="12安帆布手提袋 可定制logo 环保购物袋",
        keywords="tote bag canvas shopping bag cotton",
        platform="1688", moq=100,
        tiers=[(100, 8.50), (500, 7.20), (2000, 6.10)],
        material="12 oz cotton canvas", size="38 x 42 cm, handles 60 cm",
        weight_kg=0.18, production_days=12,
        customisation="Logo screen print (up to 4 colours), custom size, custom label",
        supplier=dict(
            name="Cangnan Huiyuan Bag Factory", name_cn="苍南汇源袋业厂",
            city="Wenzhou", type="factory", years=11,
            badges=["Verified supplier", "Trade assurance", "Onsite inspection"],
            response_rate=94, repeat_buyer_rate=36, disputes="low",
        ),
    ),
    _p(
        id="TB-02", category="bags",
        title_en="Cotton tote bag with inner pocket, plain natural colour",
        title_cn="纯棉帆布袋 带内袋 素色",
        keywords="tote bag cotton canvas shopping bag",
        platform="Yiwugo", moq=300,
        tiers=[(300, 6.80), (1000, 5.90)],
        material="Cotton canvas (weight not stated)", size="35 x 40 cm",
        weight_kg=0.15, production_days=7,
        customisation="Logo print on request",
        supplier=dict(
            name="Yiwu Leyi Trading Co., Ltd.", name_cn="义乌乐艺贸易有限公司",
            city="Yiwu", type="middleman", years=4,
            badges=["Trade assurance"],
            response_rate=81, repeat_buyer_rate=18, disputes="medium",
        ),
    ),
    _p(
        id="TB-03", category="bags",
        title_en="Non-woven tote bag, laminated, promotional",
        title_cn="覆膜无纺布手提袋 广告袋",
        keywords="tote bag non-woven promotional shopping bag",
        platform="1688", moq=1000,
        tiers=[(1000, 1.60), (5000, 1.25), (20000, 1.05)],
        material="Laminated non-woven polypropylene, 100 g/m²", size="30 x 40 x 10 cm",
        weight_kg=0.05, production_days=10,
        customisation="Full-colour logo print, custom size",
        supplier=dict(
            name="Wenzhou Pinyou Packaging Co., Ltd.", name_cn="温州品优包装有限公司",
            city="Wenzhou", type="factory", years=15,
            badges=["Verified supplier", "Trade assurance"],
            response_rate=97, repeat_buyer_rate=42, disputes="low",
        ),
    ),
    _p(
        id="TB-04", category="bags",
        title_en="Canvas tote bag with zipper, printed pattern",
        title_cn="帆布拉链托特包 印花",
        keywords="tote bag canvas zipper",
        platform="Taobao", moq=1,
        tiers=[(1, 19.90), (50, 16.50)],
        material="Polyester-cotton canvas", size="40 x 33 cm",
        weight_kg=None,  # not stated on the sample listing
        production_days=None,
        customisation=None,
        supplier=dict(
            name="Xiaomu Bag Shop", name_cn="小木包包店",
            city="Guangzhou", type="store", years=3,
            badges=[],
            response_rate=None, repeat_buyer_rate=None, disputes=None,
        ),
    ),
    # ---------------- Water bottles ----------------
    _p(
        id="WB-01", category="drinkware",
        title_en="Stainless steel insulated water bottle, 500 ml, double wall",
        title_cn="304不锈钢真空保温杯 500ml 双层",
        keywords="water bottle insulated stainless steel thermos flask",
        platform="1688", moq=50,
        tiers=[(50, 22.00), (300, 18.50), (1000, 15.80)],
        material="304 stainless steel, PP lid", size="7 x 25 cm, 500 ml",
        weight_kg=0.32, production_days=15,
        customisation="Laser logo engraving, custom colour (MOQ 300), gift box",
        supplier=dict(
            name="Yongkang Jiahe Cup Industry Co., Ltd.", name_cn="永康市嘉禾杯业有限公司",
            city="Yongkang", type="factory", years=9,
            badges=["Verified supplier", "Trade assurance"],
            response_rate=92, repeat_buyer_rate=31, disputes="low",
        ),
    ),
    _p(
        id="WB-02", category="drinkware",
        title_en="Tritan sports water bottle, 750 ml, BPA-free",
        title_cn="Tritan运动水杯 750ml 不含BPA",
        keywords="water bottle sports plastic tritan",
        platform="Yiwugo", moq=120,
        tiers=[(120, 9.80), (600, 8.40)],
        material="Tritan copolyester", size="7.5 x 26 cm, 750 ml",
        weight_kg=0.16, production_days=8,
        customisation="Logo print",
        supplier=dict(
            name="Yiwu Shuyi Daily Goods Store", name_cn="义乌舒逸日用品商行",
            city="Yiwu", type="store", years=6,
            badges=["Trade assurance"],
            response_rate=88, repeat_buyer_rate=22, disputes="low",
        ),
    ),
    _p(
        id="WB-03", category="drinkware",
        title_en="Insulated water bottle, 1 L, with straw lid",
        title_cn="大容量保温水壶 1L 吸管盖",
        keywords="water bottle insulated stainless steel straw",
        platform="JD", moq=1,
        tiers=[(1, 59.00), (20, 52.00)],
        material="316 stainless steel inner, 304 outer", size="9 x 28 cm, 1 L",
        weight_kg=0.48, production_days=None,
        customisation="not offered",
        supplier=dict(
            name="Hanshi Official Flagship Store", name_cn="涵氏官方旗舰店",
            city="Hangzhou", type="store", years=8,
            badges=["Brand official store"],
            response_rate=99, repeat_buyer_rate=None, disputes="low",
        ),
    ),
    _p(
        id="WB-04", category="drinkware",
        title_en="Glass water bottle with silicone sleeve, 550 ml",
        title_cn="高硼硅玻璃水杯 硅胶套 550ml",
        keywords="water bottle glass silicone",
        platform="1688", moq=200,
        tiers=[(200, 7.50), (1000, 6.30)],
        material="Borosilicate glass, silicone sleeve, bamboo lid", size="6.5 x 23 cm, 550 ml",
        weight_kg=0.36, production_days=18,
        customisation="Logo on sleeve or lid",
        supplier=dict(
            name="Hejian Mingliang Glassware Trading", name_cn="河间明亮玻璃制品商贸",
            city="Hejian", type="middleman", years=2,
            badges=[],
            response_rate=67, repeat_buyer_rate=9, disputes="high",
        ),
    ),
    # ---------------- Phone cases ----------------
    _p(
        id="PC-01", category="phone accessories",
        title_en="Clear shockproof TPU phone case, custom print",
        title_cn="透明防摔TPU手机壳 可定制图案",
        keywords="phone case clear tpu shockproof cover",
        platform="1688", moq=50,
        tiers=[(50, 3.20), (500, 2.40), (3000, 1.90)],
        material="TPU", size="Fits major iPhone / Samsung models",
        weight_kg=0.03, production_days=5,
        customisation="UV print custom artwork, custom packaging",
        supplier=dict(
            name="Shenzhen Kaisheng Electronic Accessories Factory", name_cn="深圳凯晟电子配件厂",
            city="Shenzhen", type="factory", years=7,
            badges=["Verified supplier", "Trade assurance"],
            response_rate=90, repeat_buyer_rate=28, disputes="low",
        ),
    ),
    _p(
        id="PC-02", category="phone accessories",
        title_en="Liquid silicone phone case, microfibre lining",
        title_cn="液态硅胶手机壳 内衬超细纤维",
        keywords="phone case silicone cover",
        platform="Taobao", moq=1,
        tiers=[(1, 15.80), (100, 11.00)],
        material="Liquid silicone, microfibre", size="iPhone models only",
        weight_kg=0.035, production_days=None,
        customisation=None,
        supplier=dict(
            name="Guoguo Digital Store", name_cn="果果数码小店",
            city="Shenzhen", type="store", years=2,
            badges=[],
            response_rate=76, repeat_buyer_rate=12, disputes="medium",
        ),
    ),
    _p(
        id="PC-03", category="phone accessories",
        title_en="Magnetic phone case compatible with MagSafe",
        title_cn="磁吸手机壳 兼容MagSafe",
        keywords="phone case magnetic magsafe",
        platform="Yiwugo", moq=100,
        tiers=[(100, 6.50), (500, 5.60)],
        material="PC + TPU, magnet ring", size="iPhone 13–16 series",
        weight_kg=0.045, production_days=7,
        customisation="Logo print",
        supplier=dict(
            name="Yiwu Xinchuang Import & Export Co., Ltd.", name_cn="义乌新创进出口有限公司",
            city="Yiwu", type="middleman", years=5,
            badges=["Trade assurance"],
            response_rate=85, repeat_buyer_rate=20, disputes="low",
        ),
    ),
    # ---------------- Yoga mats ----------------
    _p(
        id="YM-01", category="sports",
        title_en="TPE yoga mat, 6 mm, double-layer, non-slip",
        title_cn="TPE双层瑜伽垫 6mm 防滑",
        keywords="yoga mat tpe fitness exercise",
        platform="1688", moq=50,
        tiers=[(50, 28.00), (300, 24.50), (1000, 21.00)],
        material="TPE", size="183 x 61 cm, 6 mm",
        weight_kg=0.95, production_days=10,
        customisation="Custom colour, logo print, custom strap",
        supplier=dict(
            name="Nantong Yujia Sports Goods Co., Ltd.", name_cn="南通瑜佳体育用品有限公司",
            city="Nantong", type="factory", years=12,
            badges=["Verified supplier", "Trade assurance", "Onsite inspection"],
            response_rate=95, repeat_buyer_rate=38, disputes="low",
        ),
    ),
    _p(
        id="YM-02", category="sports",
        title_en="NBR yoga mat, 10 mm thick, with carry strap",
        title_cn="NBR加厚瑜伽垫 10mm 带绑带",
        keywords="yoga mat nbr thick fitness exercise",
        platform="Taobao", moq=1,
        tiers=[(1, 39.00), (30, 33.00)],
        material="NBR foam", size="183 x 61 cm, 10 mm",
        weight_kg=0.85, production_days=None,
        customisation=None,
        supplier=dict(
            name="Lekang Sports Store", name_cn="乐康运动专营店",
            city="Hangzhou", type="store", years=5,
            badges=[],
            response_rate=91, repeat_buyer_rate=19, disputes="low",
        ),
    ),
    _p(
        id="YM-03", category="sports",
        title_en="Natural rubber + PU yoga mat, 4 mm, alignment lines",
        title_cn="天然橡胶PU瑜伽垫 4mm 体位线",
        keywords="yoga mat rubber pu fitness",
        platform="1688", moq=20,
        tiers=[(20, 78.00), (200, 69.00)],
        material="Natural rubber base, PU top layer", size="185 x 68 cm, 4 mm",
        weight_kg=2.4, production_days=20,
        customisation="Laser engraved logo, custom print",
        supplier=dict(
            name="Dongguan Ruibang Rubber Products Co., Ltd.", name_cn="东莞瑞邦橡胶制品有限公司",
            city="Dongguan", type="factory", years=None,
            badges=["Trade assurance"],
            response_rate=None, repeat_buyer_rate=25, disputes="low",
        ),
    ),
    # ---------------- Ceramic mugs ----------------
    _p(
        id="MG-01", category="ceramics",
        title_en="Ceramic mug, 350 ml, sublimation blank, white",
        title_cn="350ml陶瓷马克杯 热转印白杯",
        keywords="mug ceramic coffee cup sublimation",
        platform="1688", moq=144,
        tiers=[(144, 4.20), (1008, 3.60), (5040, 3.10)],
        material="Ceramic with sublimation coating", size="8.2 x 9.5 cm, 350 ml",
        weight_kg=0.34, production_days=15,
        customisation="Full-colour sublimation print, custom gift box",
        supplier=dict(
            name="Liling Huaxin Ceramics Factory", name_cn="醴陵华鑫陶瓷厂",
            city="Liling", type="factory", years=18,
            badges=["Verified supplier", "Trade assurance", "Onsite inspection"],
            response_rate=93, repeat_buyer_rate=45, disputes="low",
        ),
    ),
    _p(
        id="MG-02", category="ceramics",
        title_en="Matte glazed ceramic mug with wooden lid, 400 ml",
        title_cn="哑光釉陶瓷杯 木盖 400ml",
        keywords="mug ceramic coffee cup matte",
        platform="Yiwugo", moq=96,
        tiers=[(96, 9.50), (480, 8.20)],
        material="Stoneware ceramic, beech wood lid", size="9 x 10 cm, 400 ml",
        weight_kg=0.42, production_days=12,
        customisation="Logo decal",
        supplier=dict(
            name="Yiwu Taoyuan Homeware Store", name_cn="义乌陶源家居商行",
            city="Yiwu", type="store", years=3,
            badges=["Trade assurance"],
            response_rate=79, repeat_buyer_rate=15, disputes="medium",
        ),
    ),
    _p(
        id="MG-03", category="ceramics",
        title_en="Ceramic coffee mug gift set (2 mugs + spoons)",
        title_cn="陶瓷咖啡杯礼盒套装 两杯两勺",
        keywords="mug ceramic coffee cup gift set",
        platform="JD", moq=1,
        tiers=[(1, 69.00), (10, 62.00)],
        material="Ceramic, stainless steel spoons", size="300 ml per mug",
        weight_kg=1.1, production_days=None,
        customisation="not offered",
        supplier=dict(
            name="Jingyan Homeware JD Self-run Store", name_cn="景燕家居京东自营",
            city=None, type="store", years=None,
            badges=["Platform self-operated"],
            response_rate=None, repeat_buyer_rate=None, disputes="low",
        ),
    ),
    # ---------------- LED strips ----------------
    _p(
        id="LS-01", category="lighting",
        title_en="RGB LED strip light 5 m, USB, app + remote control",
        title_cn="RGB LED灯带 5米 USB 手机APP+遥控",
        keywords="led strip light rgb usb lighting",
        platform="1688", moq=20,
        tiers=[(20, 14.50), (200, 12.20), (1000, 10.50)],
        material="Flexible PCB, 5050 SMD LEDs, silicone coating", size="5 m x 10 mm",
        weight_kg=0.22, production_days=7,
        customisation="Custom packaging, private label app (MOQ 3,000)",
        supplier=dict(
            name="Zhongshan Guming Lighting Co., Ltd.", name_cn="中山古明照明有限公司",
            city="Zhongshan", type="factory", years=8,
            badges=["Verified supplier", "Trade assurance"],
            response_rate=89, repeat_buyer_rate=27, disputes="low",
        ),
    ),
    _p(
        id="LS-02", category="lighting",
        title_en="Warm white LED strip 10 m, 12 V, with adapter",
        title_cn="暖白LED灯带 10米 12V 含电源",
        keywords="led strip light warm white lighting",
        platform="Taobao", moq=1,
        tiers=[(1, 45.00), (20, 38.00)],
        material="2835 SMD LEDs", size="10 m x 8 mm",
        weight_kg=0.55, production_days=None,
        customisation=None,
        supplier=dict(
            name="Liangliang Lighting Shop", name_cn="亮亮灯饰店",
            city="Zhongshan", type="store", years=1,
            badges=[],
            response_rate=72, repeat_buyer_rate=8, disputes="medium",
        ),
    ),
    _p(
        id="LS-03", category="lighting",
        title_en="COB LED strip, 5 m, high density, 24 V",
        title_cn="COB高密度灯带 5米 24V",
        keywords="led strip light cob lighting",
        platform="Yiwugo", moq=50,
        tiers=[(50, 18.00), (500, 15.50)],
        material="COB LEDs, flexible PCB", size="5 m x 8 mm",
        weight_kg=0.20, production_days=None,
        customisation="Custom length",
        supplier=dict(
            name="Yiwu Guanghui Electrical Trading", name_cn="义乌光辉电器商贸",
            city="Yiwu", type="middleman", years=3,
            badges=[],
            response_rate=None, repeat_buyer_rate=None, disputes=None,
        ),
    ),
]


def get_product(pid):
    for p in PRODUCTS:
        if p["id"] == pid:
            return p
    return None


def search(query):
    """Simple keyword match over the sample catalog."""
    q = (query or "").lower().strip()
    if not q:
        return list(PRODUCTS)
    tokens = [t.rstrip("s") for t in q.replace(",", " ").split() if len(t) > 1]
    stop = {"a", "an", "the", "for", "with", "and", "of", "to", "in", "custom", "cheap", "bulk"}
    tokens = [t for t in tokens if t not in stop] or tokens
    results = []
    for p in PRODUCTS:
        hay = f"{p['title_en']} {p['keywords']} {p['category']}".lower()
        hits = sum(1 for t in tokens if t in hay)
        if hits:
            results.append((hits, p))
    if not results:
        return []
    best = max(h for h, _ in results)
    # keep products that match at least half of the best hit count
    return [p for h, p in results if h >= max(1, best / 2)]
