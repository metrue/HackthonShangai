"""AI query planner: turns a search in any European language into the query a
Chinese buyer would type on 1688 / Taobao / JD / Yiwugo.

Based on a colleague's translation agent, reduced to the part that improves
results. It never invents data: when the AI is not available it returns
(None, reason) and the app shows "Chinese query: not available".
"""

from core.ai import ask

SYSTEM_PROMPT = """You help European buyers search Chinese B2B and retail marketplaces \
(1688, Taobao, JD, Yiwugo).

Given a product search written in any European language:
1. Detect the language.
2. Understand the real buying intent (product, material, use, size, quantity hints).
3. Write the search query in Simplified Chinese the way a Chinese buyer would type it \
on 1688 or Taobao. Use the terms sellers actually put in listing titles; do not \
translate word for word.
4. Give 2-3 alternative Chinese queries (synonyms, common seller wording).
5. Give 2-5 short English keywords for the product type (e.g. "tote bag", "canvas").
6. List at most 2 points the buyer should clarify to get better offers \
(e.g. size, material grade, certification). Leave the list empty if nothing important is unclear.

All explanations must be in English. Never invent prices, suppliers or specifications."""

SCHEMA = {
    "type": "object",
    "properties": {
        "detected_language": {"type": "string"},
        "intent_en": {"type": "string"},
        "query_zh": {"type": "string"},
        "query_zh_meaning_en": {"type": "string"},
        "pinyin": {"type": "string"},
        "alternative_queries_zh": {"type": "array", "items": {"type": "string"}},
        "keywords_en": {"type": "array", "items": {"type": "string"}},
        "clarify": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["detected_language", "intent_en", "query_zh", "query_zh_meaning_en", "pinyin",
                 "alternative_queries_zh", "keywords_en", "clarify"],
    "additionalProperties": False,
}


TITLES_PROMPT = """Translate Chinese marketplace listing titles into short, natural English product
names for a European buyer (like a good Amazon title, max ~12 words). Drop marketing filler
(爆款, 热销, 厂家直销, 批发...) but keep material, size, capacity and other specs exactly.
Return one English title per input title, in the same order."""

TITLES_SCHEMA = {
    "type": "object",
    "properties": {"titles": {"type": "array", "items": {"type": "string"}}},
    "required": ["titles"],
    "additionalProperties": False,
}


def translate_titles(titles_zh):
    """English product names for a batch of Chinese titles: (list, None) or (None, reason)."""
    if not titles_zh:
        return [], None
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles_zh))
    out, err = ask(TITLES_PROMPT, [{"role": "user", "content": numbered}], schema=TITLES_SCHEMA, effort="low")
    if out is None:
        return None, err
    titles = out.get("titles") or []
    if len(titles) != len(titles_zh):
        return None, "the translation did not match the titles"
    return titles, None


def plan_search(query):
    """Return (plan_dict, None) on success or (None, reason) when not available."""
    query = (query or "").strip()
    if not query:
        return None, "empty query"
    plan, err = ask(SYSTEM_PROMPT, [{"role": "user", "content": query}], schema=SCHEMA, effort="low")
    if plan is None:
        return None, err
    plan["alternative_queries_zh"] = [q for q in plan.get("alternative_queries_zh", []) if q][:3]
    plan["keywords_en"] = [k for k in plan.get("keywords_en", []) if k][:5]
    plan["clarify"] = [c for c in plan.get("clarify", []) if c][:2]
    return plan, None
