"""Live Yiwugo listings (PR #1) prepared for the app.

- search results are cached for 10 minutes; failures are not cached and are reported
- every live listing gets an English name: AI translation when available, otherwise the
  small glossary (marked approximate), otherwise the Chinese title with a note
- the category is guessed from the title (for the duty rate)
- Yiwugo listings have no weight: the buyer can add it on the product page; it is kept
  per product for the session, marked "user-provided" and used in the results list too
"""

import streamlit as st

from components.state import S
from core import listing, query_translation, yiwugo
from core.catalog import get_product


class _LiveUnavailable(Exception):
    pass


@st.cache_data(ttl=600, show_spinner=False, max_entries=200)
def _fetch(query):
    try:
        return yiwugo.search(query)
    except Exception as e:  # network, blocked, site changed
        raise _LiveUnavailable(type(e).__name__) from e


@st.cache_data(ttl=24 * 3600, show_spinner=False, max_entries=2000)
def _ai_titles(titles):
    out, err = query_translation.translate_titles(list(titles))
    if out is None:
        raise _LiveUnavailable(err)
    return out


def _english_titles(items):
    titles = tuple(p.get("title_cn") or "" for p in items)
    try:
        names = _ai_titles(titles)
        source = "ai"
    except _LiveUnavailable:
        names = [listing.translate_title(t) for t in titles]
        source = "glossary"
    for p, name in zip(items, names):
        if name:
            p["title_en"], p["title_en_source"] = name, source


def live_search(query):
    """(items, None) or ([], reason). Items are catalog-shaped products with live=True."""
    if not yiwugo.enabled():
        return [], "off"
    query = (query or "").strip()
    if not query:
        return [], None
    try:
        # details fetched in the background since the search are used when already there
        items = [yiwugo.with_details(dict(p), wait=False) for p in _fetch(query)]
    except _LiveUnavailable as e:
        return [], f"Yiwugo did not respond ({e})"
    _english_titles(items)
    for p in items:
        p["category"] = p.get("category") or listing.guess_category(p.get("title_cn"))
        p["category_guessed"] = p["category"] is not None
    S.live_products = {p["id"]: p for p in items}
    return items, None


def with_buyer_details(p):
    """The product with the weight/category the buyer added (live listings only)."""
    extra = (S.get("live_extra") or {}).get(p.get("id"))
    if not p.get("live") or not extra:
        return p
    p = dict(p)
    if extra.get("weight_kg") and p.get("weight_kg") is None:
        p["weight_kg"], p["weight_user"] = extra["weight_kg"], True
    if extra.get("category"):
        p["category"], p["category_guessed"] = extra["category"], False
    return p


def set_buyer_details(pid, weight_kg=None, category=None):
    extra = S.setdefault("live_extra", {})
    extra[pid] = {"weight_kg": weight_kg, "category": category}


def _detailed(p):
    """Live listing with its details (usually already prefetched in the background)."""
    if not p.get("live") or p.get("details_loaded"):
        return p
    with st.spinner("Loading the listing details from Yiwugo…"):
        p = yiwugo.with_details(p, wait=True)
    S.setdefault("live_products", {})[p["id"]] = p
    return p


def find_product(pid):
    """A catalog product or a live listing (re-read from Yiwugo after a page reload)."""
    found = get_product(pid) or (S.get("live_products") or {}).get(pid)
    if not found and str(pid or "").startswith("yw-"):
        query = (S.get("yiwugo_q") or S.q or "").strip()
        if query:
            with st.spinner("Reading the Yiwugo listing…"):
                live_search(query)
            found = (S.get("live_products") or {}).get(pid)
    return with_buyer_details(_detailed(found)) if found else None
