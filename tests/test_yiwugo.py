"""Live Yiwugo listings (PR #1). Yiwugo prices are fen on the wire and yuan on the page.
Missing facts stay empty. No test calls yiwugo.com: search results are simulated."""

from unittest import mock

from conftest import page_text, run_app
from core import query_translation
from core.yiwugo import listing_from_api, yuan_from_fen

ITEM = {"id": 940179442, "title": "帆布手提袋", "sellPrice": 430, "startNum": 1000,
        "shopName": "义乌市天汇制袋厂", "picture1": "http://img.example/bag.jpg", "isAd": "0"}
DETAIL = {"years": 5, "detail": {"productExtendList": [{"name": "材质", "value": "帆布"},
                                                       {"name": "尺寸", "value": "按要求定制"}],
                                 "sdiProductsPriceList": [{"startNumber": 1000, "conferPrice": 430}]}}


def live_listing():
    return listing_from_api(ITEM, DETAIL)


def test_fen_is_yuan_on_the_page():
    assert yuan_from_fen(640) == 6.4
    assert yuan_from_fen(0) is None
    assert yuan_from_fen(None) is None


def test_listing_uses_seller_material_and_leaves_unknowns_empty():
    listing = live_listing()
    assert listing["live"] is True and listing["platform"] == "Yiwugo"
    assert listing["tiers"] == [(1000, 4.3)]
    assert listing["material"] == "帆布" and listing["size"] == "按要求定制"
    assert listing["weight_kg"] is None and listing["title_en"] is None
    assert listing["title_cn"] == "帆布手提袋"
    assert listing["supplier"]["years"] == 5 and listing["supplier"]["type"] is None
    assert listing["url"] == "https://www.yiwugo.com/product/detail/940179442.html"
    assert listing_from_api({"id": 1, "title": "无价", "sellPrice": None}, None) is None


def test_results_and_product_page_use_the_live_listing(no_ai):
    with mock.patch("core.yiwugo.search", return_value=[live_listing()]):
        results = page_text(run_app({"view": "results", "q": "帆布手提袋", "qty": "1000"}))
        detail = page_text(run_app({"view": "detail", "pid": "yw-940179442", "q": "帆布手提袋",
                                    "yq": "帆布手提袋", "qty": "1000"}))
    assert "¥4.30" in results and "/unit on Yiwugo" in results
    assert "<span class='src-tag live'>Live</span>" in results and "listings read from yiwugo.com" in results
    assert "Canvas tote bag" in results                                 # English name (glossary, no AI)
    assert "Live Yiwugo listing" in detail and "This listing has no weight" in detail
    assert "Category guessed from the title: bags" in detail


def test_live_listings_sorted_by_listing_price(no_ai):
    cheap = listing_from_api(dict(ITEM, id=1, sellPrice=200), None)
    dear = listing_from_api(dict(ITEM, id=2, sellPrice=350), None)
    with mock.patch("core.yiwugo.search", return_value=[dear, cheap]):
        t = page_text(run_app({"view": "results", "q": "帆布袋", "qty": "1000"}))
    assert t.index("¥2.00") < t.index("¥3.50")


def test_english_names_from_ai_when_available(no_ai):
    with mock.patch("core.yiwugo.search", return_value=[live_listing()]), \
         mock.patch.object(query_translation, "translate_titles",
                           return_value=(["Canvas tote bag, custom print"], None)):
        t = page_text(run_app({"view": "results", "q": "tote bag", "qty": "1000"}))
    assert "Canvas tote bag, custom print" in t


def test_buyer_weight_gives_the_delivered_price(no_ai):
    with mock.patch("core.yiwugo.search", return_value=[live_listing()]):
        at = run_app({"view": "detail", "pid": "yw-940179442", "q": "帆布手提袋", "yq": "帆布手提袋",
                      "qty": "1000"})
        at.number_input(key="lw_yw-940179442").set_value(180).run()
        assert not at.exception, at.exception
        t = page_text(at)
        assert "180 g <span class='tag tag-est'>user-provided</span>" in t
        assert "Total delivered" in t and not at.button(key="order_yw-940179442").disabled
        # the weight is reused in the results list: now a delivered price
        at.query_params.update({"view": "results"})
        at.session_state["view"] = "results"
        at.run()
        assert "/unit delivered" in page_text(at)


def test_live_search_reports_failure_and_can_be_switched_off(no_ai, monkeypatch):
    with mock.patch("core.yiwugo.search", side_effect=TimeoutError()):
        t = page_text(run_app({"view": "results", "q": "tote bag"}))
    assert "Live Yiwugo listings: <span class='na'>not available</span> · Yiwugo did not respond (TimeoutError)" in t
    assert t.count("class='mk'") == 4                                    # sample catalog still shown
    assert t.count("<span class='src-tag'>Sample</span>") == 4          # ...and labelled as sample

    monkeypatch.setenv("YIWUGO_LIVE", "0")
    with mock.patch("core.yiwugo.search", side_effect=AssertionError("must not be called")):
        t = page_text(run_app({"view": "results", "q": "tote bag"}))
    assert "yiwugo.com" not in t and "Live Yiwugo" not in t
