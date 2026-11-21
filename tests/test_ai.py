"""The shared AI wrapper, the query translation and the listing reader (API simulated)."""

import json
import time
from types import SimpleNamespace as NS
from unittest import mock

import anthropic

from core import ai, listing, query_translation

PLAN = {"detected_language": "Italian", "intent_en": "Canvas tote bags with a printed logo",
        "query_zh": "帆布袋定制logo", "query_zh_meaning_en": "custom logo canvas bag",
        "pinyin": "fānbù dài dìngzhì logo", "alternative_queries_zh": ["帆布手提袋 印logo"],
        "keywords_en": ["tote bag", "canvas"], "clarify": ["Canvas weight (e.g. 12 oz)"]}


def fake_response(stop="end_turn", text=json.dumps(PLAN)):
    # a thinking block FIRST: the colleague's original code read content[0].text and broke here
    return NS(stop_reason=stop, content=[NS(type="thinking", thinking=""), NS(type="text", text=text)])


def call_with(resp):
    client = mock.MagicMock()
    client.beta.messages.create.return_value = resp
    with mock.patch.object(anthropic, "Anthropic", return_value=client), \
         mock.patch.object(ai, "_api_key", "test-key"):
        return query_translation.plan_search("borsa di tela con logo"), client


def test_reads_text_block_after_thinking_and_uses_one_model():
    (plan, err), client = call_with(fake_response())
    assert err is None and plan["query_zh"] == "帆布袋定制logo"
    kw = client.beta.messages.create.call_args.kwargs
    assert kw["model"] == ai.MODEL == "claude-opus-5-5"
    assert kw["fallbacks"] == "default"
    assert kw["output_config"]["format"]["type"] == "json_schema"


def test_refusal_truncation_and_no_key_are_reported():
    assert call_with(fake_response(stop="refusal"))[0] == (None, "the request was declined")
    assert call_with(fake_response(stop="max_tokens"))[0] == (None, "the answer was cut off")
    ai.set_api_key(None)
    t = time.time()
    assert query_translation.plan_search("borsa") == (None, "no API key configured")
    assert time.time() - t < 0.5            # answered at once, without loading the SDK


# ---------------------------------------------------------------- listing reader
AI_LISTING = {
    "title_cn": "12安帆布手提袋 可定制logo", "title_en": "12 oz canvas tote bag, custom logo",
    "platform": "", "moq": 100, "tiers": [{"min_qty": 500, "price_cny": 7.2}, {"min_qty": 100, "price_cny": 8.5}],
    "material": "12 oz cotton canvas", "size": "38 x 42 cm", "weight_g": 180, "production_days": 15,
    "customisation": "Logo printing", "category": "bags",
    "supplier": {"name_cn": "温州某某袋业有限公司", "name_en": "", "city": "Wenzhou", "type": "factory",
                 "years": 11, "badges": ["Verified supplier"], "response_rate": 94, "repeat_buyer_rate": 0},
}


def test_read_screenshot_builds_a_card_without_inventing():
    with mock.patch.object(ai, "ask", return_value=(AI_LISTING, None)) as ask:
        card, err = listing.read_listing(image=b"\x89PNG fake", media_type="image/png",
                                         url="https://detail.1688.com/offer/612345.html")
    assert err is None
    content = ask.call_args.args[1][0]["content"]
    assert content[0]["type"] == "image" and content[0]["source"]["media_type"] == "image/png"
    assert card["platform"] == "1688"                       # from the link, since the AI left it empty
    assert card["tiers"] == [(100, 8.5), (500, 7.2)]        # sorted
    assert card["weight_kg"] == 0.18
    assert card["supplier"]["name"] is None                 # "" -> not available
    assert card["supplier"]["repeat_buyer_rate"] is None    # 0 -> not available


def test_rule_based_fallback_still_reads_text():
    card = listing.parse_listing(listing.SAMPLE_LISTING)
    assert card["moq"] == 100 and card["weight_kg"] == 0.18 and card["platform"] == "1688"
    assert card["material"].startswith("Pure cotton canvas")
