"""Yiwugo prices are fen on the wire and yuan on the page. Missing facts stay empty."""

from yiwugo import listing_from_api, yuan_from_fen


def test_fen_is_yuan_on_the_page():
    assert yuan_from_fen(640) == 6.4
    assert yuan_from_fen(0) is None
    assert yuan_from_fen(None) is None


def test_listing_uses_seller_material_and_leaves_unknowns_empty():
    item = {
        "id": 940179442,
        "title": "帆布手提袋",
        "sellPrice": 430,
        "startNum": 1000,
        "shopName": "义乌市天汇制袋厂",
        "picture1": "http://img.example/bag.jpg",
        "isAd": "0",
    }
    detail = {
        "years": 5,
        "detail": {
            "productExtendList": [
                {"name": "材质", "value": "帆布"},
                {"name": "尺寸", "value": "按要求定制"},
            ],
            "sdiProductsPriceList": [{"startNumber": 1000, "conferPrice": 430}],
        },
    }
    listing = listing_from_api(item, detail)
    assert listing["live"] is True
    assert listing["platform"] == "Yiwugo"
    assert listing["tiers"] == [(1000, 4.3)]
    assert listing["material"] == "帆布"
    assert listing["size"] == "按要求定制"
    assert listing["weight_kg"] is None
    assert listing["title_en"] is None
    assert listing["title_cn"] == "帆布手提袋"
    assert listing["supplier"]["years"] == 5
    assert listing["supplier"]["type"] is None
    assert listing["url"] == "https://www.yiwugo.com/product/detail/940179442.html"
    assert listing_from_api({"id": 1, "title": "无价", "sellPrice": None}, None) is None
