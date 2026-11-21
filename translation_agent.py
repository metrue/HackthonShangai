"""AI query planner: turns a search in any European language into the query a
Chinese buyer would type on 1688 / Taobao / JD / Yiwugo.

Based on a colleague's translation agent, reduced to the part that improves
results. It never invents data:
  - no credentials or any API error -> returns (None, reason) and the app shows
    "translation not available"
  - no mock translations, no fake search results

Credentials: ANTHROPIC_API_KEY (env var or Streamlit secrets), or any other
credential the Anthropic SDK resolves on its own (e.g. an `ant auth login` profile).
"""

import json

MODEL = "claude-sonnet-5-5"

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


def plan_search(query, api_key=None):
    """Return (plan_dict, None) on success or (None, reason) when not available."""
    query = (query or "").strip()
    if not query:
        return None, "empty query"
    try:
        import anthropic
    except ImportError:
        return None, "the anthropic package is not installed"

    try:
        client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    except Exception as e:  # no credentials resolvable
        return None, f"no API credentials ({type(e).__name__})"

    params = dict(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
    )
    try:
        try:
            # Server-side fallback: if the model declines, the API retries on a fallback model.
            resp = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params)
        except (TypeError, anthropic.BadRequestError) as e:
            if "authentication" in str(e).lower():
                raise
            # SDK too old for `fallbacks`, or the platform doesn't offer it: plain request
            resp = client.messages.create(**params)
    except TypeError as e:
        if "authentication" in str(e).lower():
            return None, "no API key configured"
        return None, f"translation not available ({type(e).__name__})"
    except anthropic.AuthenticationError:
        return None, "invalid or missing API key"
    except anthropic.RateLimitError:
        return None, "rate limited, try again shortly"
    except anthropic.APIConnectionError:
        return None, "no connection to the translation service"
    except anthropic.APIStatusError as e:
        return None, f"translation service error ({e.status_code})"
    except Exception as e:  # e.g. no credentials found when sending
        return None, f"translation not available ({type(e).__name__})"

    if resp.stop_reason == "refusal":
        return None, "the model declined this query"
    if resp.stop_reason == "max_tokens":
        return None, "the answer was cut off"
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if not text:
        return None, "empty answer"
    try:
        plan = json.loads(text)
    except json.JSONDecodeError:
        return None, "unreadable answer"
    plan["alternative_queries_zh"] = [q for q in plan.get("alternative_queries_zh", []) if q][:3]
    plan["keywords_en"] = [k for k in plan.get("keywords_en", []) if k][:5]
    plan["clarify"] = [c for c in plan.get("clarify", []) if c][:2]
    return plan, None
