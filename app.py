import base64
import html
import json
import os
import random
import re
import time
from urllib.parse import quote, urlencode

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from catalog import CATEGORY_STYLE, PLATFORMS, SELLER_TYPES, get_product, search
from listing_parser import SAMPLE_LISTING, parse_listing
from pricing import (COUNTRIES, CURRENCIES, CURRENCY_NAMES, DUTY, MODE_LABEL, SYMBOL, TRANSIT_DAYS,
                     compare_modes, delivered, fx_rate, refresh_fx, score_colour, score_label,
                     supplier_score)
from translation_agent import plan_search
import llm
import messages as M

st.set_page_config(page_title="SourceScan – China sourcing search", page_icon="🔎", layout="centered",
                   initial_sidebar_state="collapsed")

NA = "not available"
VERMILION = "#E34234"
HEADLINE = "See where it costs less. Delivered."

# --------------------------------------------------------------------------- style (mobile-first)
st.markdown(
    f"""
<style>
[data-testid="stToolbar"], [data-testid="stDecoration"], footer {{display:none !important;}}
header[data-testid="stHeader"] {{background: transparent;}}
.block-container {{padding: 1.2rem 1rem 3rem; max-width: 760px;}}

.tag {{display:inline-block; padding:2px 10px; border-radius:999px; font-size:.75rem; font-weight:600;
      margin-right:6px; border:1px solid rgba(128,128,128,.35);}}
.tag-sample {{background:#FFF4CC; color:#7A5B00; border-color:#F0D78C;}}
.tag-est {{background:#E8F0FE; color:#1A4FB5; border-color:#B7CCF5;}}
.tag-na {{background:#F1F1F1; color:#666; border-color:#DDD;}}
.na {{color:#9ca3af; font-style:italic;}}
.muted {{color:#6b7280; font-size:.88rem;}}
.score-pill {{display:inline-block; padding:2px 10px; border-radius:999px; color:#fff; font-weight:700;
      font-size:.82rem;}}
.kv td {{padding:4px 14px 4px 0; vertical-align:top;}}
.kv td:first-child {{color:#6b7280; white-space:nowrap;}}
.dot {{display:inline-block; width:12px; height:12px; border-radius:50%; flex:none;}}
a.plain {{color:inherit; text-decoration:none;}}

/* ---------- results header */
.rh-back {{font-size:.9rem; color:#6b7280 !important; text-decoration:none;}}
.rh-q {{font-size:1.5rem; font-weight:800; margin:.3rem 0 0; line-height:1.2; word-break:break-word;}}
.rh-sub {{color:#6b7280; font-size:.9rem;}}

/* ---------- compact rows that stay side by side on phones (marked with .nowrap) */
div[data-testid="stHorizontalBlock"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .nowrap) {{
    flex-wrap:nowrap !important; gap:.6rem;}}
div[data-testid="stHorizontalBlock"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .nowrap) > div {{
    min-width:0 !important; width:auto !important; flex:1 1 0 !important;}}
div[data-testid="stHorizontalBlock"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .nowrap) > div:last-child {{
    flex:0 0 min(40%, 190px) !important;}}
.nowrap {{display:none;}}
div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdown"] .nowrap) {{display:none;}}

/* ---------- product list (Amazon-style) */
.plist {{margin:.2rem 0 .6rem;}}
a.pc {{display:flex; gap:12px; padding:14px 0; border-bottom:1px solid rgba(128,128,128,.18);
       color:inherit !important; text-decoration:none !important; -webkit-tap-highlight-color:transparent;}}
a.pc:hover .pc-title {{color:{VERMILION};}}
.pc-img {{flex:none; width:96px; height:96px; border-radius:12px; object-fit:cover;}}
.pc-body {{flex:1; min-width:0; display:flex; flex-direction:column; gap:5px;}}
.pc-title {{font-weight:600; line-height:1.3; display:-webkit-box; -webkit-line-clamp:2;
            -webkit-box-orient:vertical; overflow:hidden;}}
.pc-meta {{display:flex; flex-wrap:wrap; gap:6px; align-items:center;}}
.mk, .sc, .save, .best-tag {{display:inline-block; padding:1px 8px; border-radius:6px; font-size:.74rem;
       font-weight:700; color:#fff; line-height:1.6;}}
.save {{background:{VERMILION};}}
.best-tag {{background:#111827;}}
.pc-price {{font-size:1.5rem; font-weight:800; line-height:1.1; font-variant-numeric:tabular-nums;}}
.pc-price small {{font-size:.75rem; font-weight:500; color:#6b7280; margin-left:4px;}}
a.pc.top .pc-price {{color:{VERMILION};}}
.pc-na {{font-size:1rem; font-weight:600; color:#9ca3af; font-style:italic;}}
.pc-sub {{font-size:.78rem; color:#6b7280; line-height:1.35;}}
.list-count {{font-size:.85rem; color:#6b7280; padding-top:.55rem;}}
.foot {{font-size:.75rem; color:#9ca3af; padding:6px 0 4px; line-height:1.5;}}
@media (min-width: 640px) {{
  .pc-img {{width:128px; height:128px;}}
  .pc-price {{font-size:1.7rem;}}
}}

/* ---------- delivered price receipt (mobile-first) */
.rcpt {{margin:.4rem 0 .8rem;}}
.rr {{display:flex; justify-content:space-between; gap:12px; padding:9px 0;
      border-bottom:1px solid rgba(128,128,128,.18);}}
.rl {{flex:1; min-width:0; font-size:.95rem;}}
.rb {{display:block; color:#9ca3af; font-size:.78rem; line-height:1.35; margin-top:1px;}}
.ra {{text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums;}}
.ra-main {{display:block; font-weight:600;}}
.ra-per {{display:block; color:#9ca3af; font-size:.78rem;}}
.rr.rt {{border-bottom:none; border-top:2px solid currentColor; margin-top:2px;}}
.rr.rt .rl, .rr.rt .ra-main {{font-weight:800; font-size:1.1rem;}}
.rr.rt .ra-main {{color:{VERMILION};}}

/* ---------- messages */
.unread-badge {{display:inline-block; min-width:18px; padding:0 6px; border-radius:999px; background:{VERMILION};
               color:#fff; font-size:.72rem; font-weight:800; text-align:center; line-height:18px;}}
a.msg-link {{font-weight:600;}}
.chat {{display:flex; flex-direction:column; gap:10px; margin:.4rem 0 .8rem;}}
.b {{max-width:88%; padding:10px 12px; border-radius:16px; line-height:1.45; font-size:.95rem;
     word-break:break-word;}}
.b.me {{align-self:flex-end; background:#111827; color:#fff; border-bottom-right-radius:4px;}}
.b.them {{align-self:flex-start; background:var(--secondary-background-color, #f3f4f6);
          border-bottom-left-radius:4px;}}
.b-en {{margin-top:7px; padding-top:7px; border-top:1px solid rgba(128,128,128,.3);}}
.b-sub {{font-size:.74rem; color:#6b7280; margin-top:5px;}}
.b.me .b-sub {{color:#cbd5e1;}}
.mean {{margin-top:8px; background:#FFF7E6; color:#7A4B00; border-radius:10px; padding:6px 9px; font-size:.85rem;}}
.terms {{margin-top:7px; display:flex; flex-wrap:wrap; gap:5px;}}
.term {{font-size:.72rem; font-weight:700; padding:1px 8px; border-radius:6px; background:#E8F0FE; color:#1A4FB5;}}
.chat mark {{background:#FFE08A; color:inherit; padding:0 2px; border-radius:3px;}}
.typing {{align-self:flex-start; color:#6b7280; font-style:italic; font-size:.9rem; padding:4px 6px;}}
.chat-head {{margin-bottom:.3rem;}}
.chat-head .who {{font-size:1.2rem; font-weight:800; line-height:1.2;}}
.preview {{background:var(--secondary-background-color, #f3f4f6); border-radius:12px; padding:10px 12px;
           margin:.3rem 0 .5rem; font-size:.92rem;}}
.preview .bt {{color:#6b7280; font-size:.82rem; margin-top:5px;}}
.deal-row {{display:flex; justify-content:space-between; gap:10px; padding:7px 0; font-size:.88rem;
            border-bottom:1px solid rgba(128,128,128,.18);}}
.deal-row .v {{text-align:right; font-weight:600;}}
.deal-row.new .v {{color:{VERMILION};}}
.deal-row .src {{display:block; font-weight:400; font-size:.72rem; color:#9ca3af;}}
a.ib {{display:block; padding:12px 0; border-bottom:1px solid rgba(128,128,128,.18); color:inherit !important;
       text-decoration:none !important;}}
.ib-top {{display:flex; justify-content:space-between; gap:8px; align-items:baseline;}}
.ib-name {{font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
a.ib.unread .ib-name::before {{content:"●"; color:{VERMILION}; margin-right:6px;}}
.ib-time {{font-size:.75rem; color:#9ca3af; white-space:nowrap;}}
.ib-prod {{font-size:.82rem; color:#6b7280; margin:2px 0;}}
.ib-last {{font-size:.88rem; color:#4b5563; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
a.ib.unread .ib-last {{font-weight:600; color:inherit;}}

/* ---------- AI translation strip */
details.tr {{font-size:.85rem; margin:.35rem 0 .2rem;}}
details.tr summary {{cursor:pointer; list-style:none; color:#4b5563;}}
details.tr summary::-webkit-details-marker {{display:none;}}
details.tr summary::after {{content:" ›"; color:#9ca3af;}}
details.tr[open] summary::after {{content:" ⌄";}}
.tr-in {{padding:.4rem 0 .2rem .9rem; border-left:2px solid rgba(128,128,128,.25); color:#4b5563;
         line-height:1.6;}}
.tr-in a {{color:{VERMILION}; font-weight:600; text-decoration:none;}}
.tr-in ul {{margin:.1rem 0 .2rem 1rem; padding:0;}}

@media (min-width: 640px) {{
  .block-container {{padding-top: 2rem;}}
  .best {{padding:26px 28px 12px;}}
}}
</style>
""",
    unsafe_allow_html=True,
)

PLATFORM_COLOURS = {"1688": "#FF6A00", "Taobao": "#F5A623", "JD": "#7B3FE4", "Yiwugo": "#1E73BE"}

# --------------------------------------------------------------------------- state (mirrored in the URL)
S = st.session_state
DEFAULTS = dict(view="home", q="", qty=500, budget=0.0, country="Italy", cur="EUR", pid=None, cmp=[],
                conv=None)
VIEWS = ("home", "results", "detail", "compare", "paste", "inbox", "chat")


def init_state():
    if S.get("_init"):
        return
    S._init = True
    qp = st.query_params
    for k, v in DEFAULTS.items():
        S[k] = v
    try:
        if qp.get("view") in VIEWS:
            S.view = qp["view"]
        S.conv = qp.get("conv") or None
        S.q = qp.get("q", "")
        S.qty = max(1, int(qp.get("qty", DEFAULTS["qty"])))
        S.budget = max(0.0, float(qp.get("budget", 0)))
        if qp.get("country") in COUNTRIES:
            S.country = qp["country"]
        if qp.get("cur") in CURRENCIES:
            S.cur = qp["cur"]
        S.pid = qp.get("pid") or None
        S.cmp = [x for x in (qp.get("cmp") or "").split(",") if get_product(x)][:3]
    except (ValueError, TypeError):
        pass
    S.setdefault("pasted", None)
    S.setdefault("pasted_text", "")
    S.convs = M.load_conversations()  # demo storage: conversations survive a page reload


def state_params(**over):
    p = dict(view=S.view, q=S.q, qty=S.qty, country=S.country, cur=S.cur)
    if S.budget:
        p["budget"] = S.budget
    if S.pid:
        p["pid"] = S.pid
    if S.cmp:
        p["cmp"] = ",".join(S.cmp)
    if S.conv and S.view == "chat":
        p["conv"] = S.conv
    p.update(over)
    return {k: v for k, v in p.items() if v not in (None, "")}


def link(**over):
    return "?" + urlencode(state_params(**over))


def sync_url():
    want = {k: str(v) for k, v in state_params().items()}
    if dict(st.query_params) != want:
        st.query_params.from_dict(want)


def go(view, **kw):
    S.view = view
    for k, v in kw.items():
        S[k] = v


def bound(widget, label, name, **kw):
    """Widget whose value lives in S[name] and survives page changes."""
    wkey = f"_w_{name}"
    S[wkey] = S[name]

    def _copy():
        if S[wkey] is not None:  # e.g. a deselected segmented control keeps the old value
            S[name] = S[wkey]
    return widget(label, key=wkey, on_change=_copy, **kw)


init_state()
sync_url()
refresh_fx()  # live ECB rates, refreshed at most every 6 h (15 min after a failure)


def currency_label(c):
    return f"{SYMBOL[c].strip()} {CURRENCY_NAMES[c]}" if SYMBOL[c].strip() != c else f"{c} · {CURRENCY_NAMES[c]}"


# --------------------------------------------------------------------------- helpers
def money(v, sym, decimals=2):
    if v is None:
        return NA
    return f"{sym}{v:,.{decimals}f}"


def units(n):
    return f"{n:,} unit" + ("" if n == 1 else "s")


def cny(v):
    return NA if v is None else f"¥{v:,.2f}"


def val(v, suffix=""):
    if v is None or v == "" or v == []:
        return f"<span class='na'>{NA}</span>"
    return f"{v}{suffix}"


def esc(s):
    return html.escape(str(s)) if s is not None else ""


def tag(text, kind="sample"):
    return f"<span class='tag tag-{kind}'>{text}</span>"


def fx_line(currency):
    """Where the exchange rate comes from, always visible next to converted prices."""
    from pricing import fx_info
    info = fx_info()
    rate = f"1 CNY = {SYMBOL[currency]}{fx_rate(currency):,.4f}"
    if currency == "CNY":
        return "Prices in Chinese yuan, no conversion"
    if info["live"]:
        return f"{rate} · ECB reference rate of {info['date']}"
    return f"{rate} · sample rate (live ECB rate unavailable)"


def fx_line_short():
    from pricing import fx_info
    info = fx_info()
    if S.cur == "CNY":
        return "prices in CNY"
    return f"ECB rate {info['date']}" if info["live"] else "sample exchange rate"


def score_pill(score):
    colour = score_colour(score)
    txt = f"{score}/100 · {score_label(score)}" if score is not None else NA
    return f"<span class='score-pill' style='background:{colour}'>{txt}</span>"


def dot(platform):
    return f"<span class='dot' style='background:{PLATFORM_COLOURS.get(platform, '#999')}'></span>"


def _image_uri(p, square=False):
    emoji, colour = CATEGORY_STYLE.get(p.get("category") or "unknown", CATEGORY_STYLE["unknown"])
    w, h = (220, 220) if square else (300, 220)
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>
<rect width='{w}' height='{h}' rx='14' fill='{colour}'/>
<text x='{w/2}' y='{h/2 + 25}' font-size='86' text-anchor='middle'>{emoji}</text>
<text x='{w/2}' y='{h - 20}' font-size='15' text-anchor='middle' fill='#555' font-family='sans-serif'>Sample image</text>
</svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def image_html(p, height=150):
    return (f"<img src='{_image_uri(p)}' "
            f"style='width:100%;max-height:{height}px;object-fit:contain;border-radius:12px'/>")


def platform_search_url(platform, keywords):
    kw = quote(keywords or "")
    return {
        "1688": f"https://s.1688.com/selloffer/offer_search.htm?keywords={kw}",
        "Taobao": f"https://s.taobao.com/search?q={kw}",
        "JD": f"https://search.jd.com/Search?keyword={kw}",
        "Yiwugo": "https://www.yiwugo.com/",
    }.get(platform)


def search_link(p):
    """Sample products have no real listing; offer a platform search instead."""
    return platform_search_url(p.get("platform"), p.get("title_cn") or p.get("title_en"))


# --------------------------------------------------------------------------- AI query translation
def get_api_key():
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:  # no secrets.toml
        return None


class _PlanUnavailable(Exception):
    pass


@st.cache_data(ttl=24 * 3600, show_spinner=False, max_entries=500)
def _cached_plan(query, _api_key):
    plan, reason = plan_search(query, _api_key)
    if plan is None:
        raise _PlanUnavailable(reason)  # failures are not cached, so a fixed key works at once
    return plan


def translated(query):
    """(plan, None) or (None, reason). One API call per distinct query per day."""
    if not query:
        return None, None
    try:
        return _cached_plan(query, get_api_key()), None
    except _PlanUnavailable as e:
        return None, str(e)


def translation_strip(plan, reason, via_translation):
    """One quiet line under the search title; details fold out on tap/hover."""
    if plan is None:
        if reason:
            st.markdown(f"<div class='muted' style='font-size:.8rem'>Chinese query: "
                        f"<span class='na'>{NA}</span> · {esc(reason)}</div>", unsafe_allow_html=True)
        return
    zh = esc(plan["query_zh"])
    links = " · ".join(
        f"<a href='{platform_search_url(p, plan['query_zh'])}' target='_blank' rel='noopener'>{p} ↗</a>"
        for p in ("1688", "Taobao", "JD"))
    alts = " · ".join(esc(a) for a in plan["alternative_queries_zh"]) or NA
    tips = "".join(f"<li>{esc(c)}</li>" for c in plan["clarify"])
    matched = " · matched via translation" if via_translation else ""
    st.markdown(
        f"<details class='tr'><summary>Searched as <b>{zh}</b> "
        f"<span class='muted'>· {esc(plan['query_zh_meaning_en'])}{matched}</span></summary>"
        f"<div class='tr-in'>"
        f"<div>{esc(plan['pinyin'])} · {esc(plan['detected_language'])}</div>"
        f"<div>Intent: {esc(plan['intent_en'])}</div>"
        f"<div>Alternatives: {alts}</div>"
        f"<div>Search it live: {links}</div>"
        + (f"<div>To get better offers, tell suppliers:<ul>{tips}</ul></div>" if tips else "")
        + f"<div>{tag('AI translation — check before sending', 'est')}</div>"
        f"</div></details>",
        unsafe_allow_html=True,
    )


def unread_count():
    return sum(1 for c in S.convs.values() for m in c["messages"]
               if m["role"] == "supplier" and not m.get("read"))


def messages_link():
    n = unread_count()
    badge = f" <span class='unread-badge'>{n}</span>" if n else ""
    return f"<a class='plain msg-link' href='{link(view='inbox', pid=None)}' target='_self'>💬 Messages{badge}</a>"


def nav_bar():
    """Small top bar for inner pages (not shown on the home screen)."""
    items = [f"<a class='plain' href='{link(view='home', pid=None)}' target='_self'><b>🔎 SourceScan</b></a>",
             f"<a class='plain muted' href='{link(view='paste')}' target='_self'>Paste a listing</a>",
             messages_link()]
    if len(S.cmp) >= 2:
        items.append(f"<a class='plain muted' href='{link(view='compare')}' target='_self'>Compare ({len(S.cmp)})</a>")
    st.markdown("<div style='display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin-bottom:.6rem'>"
                + "".join(items) + "</div>", unsafe_allow_html=True)


def sample_banner():
    st.markdown(
        tag("Sample catalog") + tag("Delivered prices are estimates", "est"),
        unsafe_allow_html=True,
    )


# =========================================================================== HOME
def page_home():
    st.markdown(
        """
<style>
.block-container {max-width: 620px;}
.hero-wrap {min-height: 22vh; display:flex; align-items:flex-end; justify-content:center;}
.hero-title {text-align:center; font-weight:900; line-height:1.1; letter-spacing:-.02em;
             font-size: clamp(2rem, 9vw, 3rem); margin: 0 0 1.2rem;}
div[data-testid="stTextInput"] input {font-size:1.15rem; height:3.6rem; padding:0 1.1rem;
             border-radius:16px;}
div[data-testid="stTextInput"] > div {border-radius:16px;}
div[data-testid="stForm"] {border:none; padding:0;}
div[data-testid="stFormSubmitButton"] button {height:3.2rem; border-radius:14px; font-size:1.05rem;
             font-weight:700; background:#E34234; border-color:#E34234;}
div[data-testid="stForm"] div[data-testid="stSelectbox"] label p {font-size:.78rem; color:#6b7280;}
div[data-testid="stForm"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
             min-height:2.3rem; font-size:.9rem;}
.hero-foot {text-align:center; color:#9ca3af; font-size:.8rem; margin-top:1.4rem; line-height:1.8;}
.hero-foot a {color:#6b7280;}
</style>""",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div style='text-align:right;font-size:.88rem'>{messages_link()}</div>"
                f"<div class='hero-wrap'><div class='hero-title'>{HEADLINE}</div></div>",
                unsafe_allow_html=True)

    with st.form("search_form", border=False):
        query = st.text_input("What are you looking for?", value=S.q, label_visibility="collapsed",
                              placeholder="What are you looking for?")
        c_country, c_cur = st.columns([1.7, 1])
        with c_country:
            st.markdown("<span class='nowrap'></span>", unsafe_allow_html=True)
            countries = list(COUNTRIES)
            country = st.selectbox("Deliver to", countries, index=countries.index(S.country))
        with c_cur:
            cur = st.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(S.cur),
                               format_func=lambda c: f"{SYMBOL[c].strip()} {c}" if SYMBOL[c].strip() != c else c)
        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)
    if submitted:
        go("results", q=query.strip(), country=country, cur=cur or S.cur, pid=None, cmp=[])
        st.rerun()

    st.markdown(
        "<div class='hero-foot'>Searching 1688 · Taobao · JD · Yiwugo "
        f"{tag('Sample catalog')}<br>"
        f"<a href='{link(view='paste')}' target='_self'>or paste a listing</a></div>",
        unsafe_allow_html=True,
    )


# =========================================================================== RESULTS
def enrich(products):
    rows = []
    for p in products:
        d = delivered(p, S.qty, S.country, S.cur)
        score, _ = supplier_score(p.get("supplier"))
        rows.append(dict(p=p, d=d, score=score,
                         ok=d["per_unit"] is not None and not d["below_moq"]))
    return rows


def why_not(r):
    if r["d"]["below_moq"]:
        return f"Needs at least {units(r['p']['moq'])} (MOQ) — you asked for {S.qty:,}"
    return "Delivered price not available — the listing has no weight, so shipping can't be estimated"


def product_card(r, sym, top=False, saving=None):
    """One product, Amazon-style: photo, English name, marketplace tag, supplier score,
    final delivered price. The whole card opens the product page."""
    p, d, score = r["p"], r["d"], r["score"]
    plat = p.get("platform") or NA
    tags = [f"<span class='mk' style='background:{PLATFORM_COLOURS.get(plat, '#6b7280')}'>{esc(plat)}</span>",
            f"<span class='sc' style='background:{score_colour(score)}'>Supplier "
            f"{score if score is not None else 'n/a'}{'/100' if score is not None else ''}</span>"]
    if r["ok"]:
        price = (f"<div class='pc-price'>{money(d['per_unit'], sym)}<small>/unit delivered</small></div>")
        moq = f"{p['moq']:,}" if p.get("moq") is not None else NA
        sub = (f"{money(d['total'], sym, 0)} for {units(S.qty)} · {d['mode_label']}, "
               f"{d['transit_days']} days · MOQ {moq}")
    else:
        price = f"<div class='pc-na'>Delivered price {NA}</div>"
        sub = why_not(r)
    badges = ""
    if top:
        badges = "<span class='best-tag'>Best price</span>"
        if saving:
            badges += f"<span class='save'>Save {saving:.0f}%</span>"
    return (f"<a class='pc{' top' if top else ''}' href='{link(view='detail', pid=p['id'])}' target='_self'>"
            f"<img class='pc-img' src='{_image_uri(p, square=True)}' alt=''/>"
            f"<div class='pc-body'>"
            f"<div class='pc-title'>{esc(p.get('title_en') or NA)}</div>"
            f"<div class='pc-meta'>{''.join(tags)}</div>"
            f"{price}"
            + (f"<div class='pc-meta'>{badges}</div>" if badges else "")
            + f"<div class='pc-sub'>{sub}</div>"
            f"</div></a>")


def page_results():
    sym = SYMBOL[S.cur]
    plan, reason = None, None
    if S.q:
        with st.spinner("Translating your search for Chinese marketplaces…"):
            plan, reason = translated(S.q)
    base, via_translation = [], False
    if plan and plan["keywords_en"]:
        # the AI's English product keywords match the catalog better than raw text
        # (e.g. "borsa di tela con logo" -> "tote bag", "canvas")
        base = search(" ".join(plan["keywords_en"]))
        via_translation = bool(base) and plan["detected_language"].lower() != "english"
    if not base:
        base = search(S.q)
    rows = enrich(base)

    # ---- sidebar filters (collapsed by default, out of the way on mobile)
    with st.sidebar:
        st.header("Filters")
        f_platform = st.multiselect("Platform", PLATFORMS, default=PLATFORMS)
        f_type = st.multiselect("Seller type", SELLER_TYPES, default=SELLER_TYPES,
                                format_func=lambda t: {"factory": "Factory", "store": "Store",
                                                       "middleman": "Middleman / trading co."}[t])
        f_score = st.slider("Minimum supplier score", 0, 100, 0, step=5)
        max_moq_all = max([r["p"]["moq"] or 0 for r in rows] + [1])
        f_moq = st.number_input("Maximum MOQ", min_value=1, value=int(max_moq_all), step=50)
        st.caption("Supplier score is a sample rule-based rating. Products with unknown score are kept "
                   "only when minimum score is 0.")

    def keep(r):
        p = r["p"]
        if p["platform"] not in f_platform or p["supplier"].get("type") not in f_type:
            return False
        if f_score > 0 and (r["score"] is None or r["score"] < f_score):
            return False
        return not (p["moq"] is not None and p["moq"] > f_moq)

    filtered = [r for r in rows if keep(r)]
    over_budget = []
    if S.budget:
        over_budget = [r for r in filtered if r["ok"] and r["d"]["per_unit"] > S.budget]
        filtered = [r for r in filtered if r not in over_budget]

    # ---- header
    q = esc(S.q) or "All products"
    budget_txt = f" · max {money(S.budget, sym)}/unit" if S.budget else ""
    st.markdown(
        f"<div style='display:flex;justify-content:space-between'>"
        f"<a class='rh-back' href='{link(view='home', pid=None)}' target='_self'>← New search</a>"
        f"<span style='font-size:.9rem'>{messages_link()}</span></div>"
        f"<div class='rh-q'>“{q}”</div>"
        f"<div class='rh-sub'>{S.qty:,} units · to {S.country} · {S.cur}{budget_txt}</div>",
        unsafe_allow_html=True,
    )
    translation_strip(plan, reason, via_translation)
    with st.popover("Change quantity, country, currency", use_container_width=False):
        bound(st.number_input, "Quantity", "qty", min_value=1, step=50)
        bound(st.selectbox, "Delivery country", "country", options=list(COUNTRIES))
        bound(st.selectbox, "Currency", "cur", options=CURRENCIES, format_func=currency_label)
        bound(st.number_input, f"Max budget per unit ({S.cur}, 0 = none)", "budget", min_value=0.0, step=0.5)

    if not base:
        st.warning(f"No products in the sample catalog match “{S.q}”. "
                   "Try tote bag, water bottle, phone case, yoga mat, mug or LED strip.")
        return
    if not filtered:
        st.info("No results match the current filters or budget.")
        return

    # ---- count + sort, side by side even on a phone
    c_count, c_sort = st.columns([1, 1.25])
    with c_count:
        st.markdown("<span class='nowrap'></span>", unsafe_allow_html=True)
        st.markdown(f"<div class='list-count'>{len(filtered)} products"
                    + (f" · {len(over_budget)} over budget hidden" if over_budget else "") + "</div>",
                    unsafe_allow_html=True)
    with c_sort:
        sort = st.selectbox("Sort by", ["Lowest price", "Best supplier score", "Lowest MOQ"],
                            label_visibility="collapsed")
    big = 10 ** 12
    keyfn = {
        "Lowest price": lambda r: r["d"]["per_unit"],
        "Best supplier score": lambda r: -(r["score"] if r["score"] is not None else -1),
        "Lowest MOQ": lambda r: r["p"]["moq"] if r["p"]["moq"] is not None else big,
    }[sort]
    # products without a delivered price at this quantity always go last
    priced = sorted((r for r in filtered if r["ok"]), key=keyfn)
    unpriced = [r for r in filtered if not r["ok"]]

    best = min(priced, key=lambda r: r["d"]["per_unit"], default=None)
    saving = None
    if best and len(priced) > 1:
        hi = max(r["d"]["per_unit"] for r in priced)
        saving = (hi - best["d"]["per_unit"]) / hi * 100 if hi > 0 else None

    st.markdown(
        "<div class='plist'>"
        + "".join(product_card(r, sym, top=r is best, saving=saving) for r in priced + unpriced)
        + "</div>"
        f"<div class='foot'>Prices include shipping (cheapest method for {S.qty:,} units), duty, VAT and "
        f"customs, estimated · {fx_line_short()} · Supplier scores are sample values for now · "
        f"Sample catalog</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Compare products"):
        opts = {r["p"]["id"]: f"{r['p']['platform']} · {r['p']['title_en'][:40]}" for r in filtered}
        picked = st.multiselect("Pick 2–3 products", list(opts), default=[x for x in S.cmp if x in opts],
                                format_func=opts.get, max_selections=3)
        if st.button("Compare", disabled=len(picked) < 2):
            go("compare", cmp=picked)
            st.rerun()


# =========================================================================== DETAIL
def kv_table(pairs):
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in pairs)
    return f"<table class='kv'>{rows}</table>"


def open_conversation(p, qty, country):
    """Contact supplier: open the existing chat for this product, or start one with the
    product, quantity, country and delivered price loaded as context."""
    existing = next((c for c in S.convs.values()
                     if c["pid"] == p["id"] and c.get("product") == p.get("title_en")), None)
    if existing:
        conv = existing
    else:
        d = delivered(p, qty, country, S.cur)
        conv = M.new_conversation(p, qty, country, S.cur, d["per_unit"])
        conv["card"] = {k: v for k, v in p.items()}  # product card snapshot (pasted listings too)
        S.convs[conv["id"]] = conv
        M.save_conversations(S.convs)
        S[f"draft_{conv['id']}"] = M.quick_action_text("Ask for quote", qty, country, p.get("moq"))
    go("chat", conv=conv["id"])


def render_detail(p, source="catalog"):
    key = p["id"]
    s = p.get("supplier") or {}

    # ---- 1. Product page
    st.subheader("1 · Product")
    with st.container(border=True):
        c_img, c_info = st.columns([1, 2])
        with c_img:
            st.markdown(image_html(p, 260), unsafe_allow_html=True)
            if source == "catalog":
                st.markdown(tag("Sample catalog"), unsafe_allow_html=True)
            else:
                st.markdown(tag("Extracted from pasted text", "est"), unsafe_allow_html=True)
        with c_info:
            st.markdown(f"### {p.get('title_en') or NA}")
            if source != "catalog" and p.get("title_en"):
                st.markdown(tag("Glossary translation — approximate", "est"), unsafe_allow_html=True)
            if p.get("title_cn"):
                st.markdown(f"<span class='muted'>Original title: {esc(p['title_cn'])}</span>",
                            unsafe_allow_html=True)
            moq = units(p["moq"]) if p.get("moq") is not None else None
            weight = f"{p['weight_kg']*1000:,.0f} g" if p.get("weight_kg") is not None else None
            if weight and p.get("weight_user"):
                weight += " " + tag("user-provided", "est")
            prod = f"{p['production_days']} days" if p.get("production_days") is not None else None
            st.markdown(kv_table([
                ("Platform", val(p.get("platform"))),
                ("Material", val(esc(p.get("material")) or None)),
                ("Size", val(esc(p.get("size")) or None)),
                ("Weight (per unit)", val(weight)),
                ("MOQ", val(moq)),
                ("Production time", val(prod)),
                ("Customisation", val(esc(p.get("customisation")) or None)),
            ]), unsafe_allow_html=True)

        st.markdown("**Price tiers** (as listed by the seller)")
        if p.get("tiers"):
            fx, sym = fx_rate(S.cur), SYMBOL[S.cur]
            tiers = sorted(p["tiers"])
            rows = []
            for i, (mq, price) in enumerate(tiers):
                rng = f"{mq:,} – {tiers[i+1][0]-1:,}" if i + 1 < len(tiers) else f"{mq:,}+"
                row = {"Quantity": rng, "Price (CNY)": f"¥{price:,.2f}"}
                if S.cur != "CNY":
                    row[f"≈ {S.cur}"] = f"{sym}{price*fx:,.2f}"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=False)
            st.caption(fx_line(S.cur))
        else:
            st.markdown(f"<span class='na'>{NA}</span>", unsafe_allow_html=True)

    # ---- 2. Delivered price
    st.subheader("2 · Delivered price")
    with st.container(border=True):
        c1, c2 = st.columns([1, 1.3])
        qty = c1.number_input("Quantity", min_value=1, value=int(S.qty), step=50, key=f"qty_{key}")
        countries = list(COUNTRIES)
        country = c2.selectbox("Delivery country", countries, index=countries.index(S.country),
                               key=f"country_{key}")
        sym = SYMBOL[S.cur]

        # shipping method: cheapest first, each with its transit time and price
        by_mode = {d["mode"]: d for d in compare_modes(p, qty, country, S.cur)}

        def mode_name(m):
            d_ = by_mode[m]
            price = money(d_["per_unit"], sym) + "/unit" if d_["per_unit"] is not None else NA
            return f"{MODE_LABEL[m]} · {TRANSIT_DAYS[m]} days · {price}"

        mode = st.radio("Shipping method (cheapest first)", list(by_mode), format_func=mode_name,
                        key=f"mode_{key}_{country}_{qty}")
        d = by_mode[mode]
        if d["below_moq"]:
            st.warning(f"{qty:,} units is below the MOQ of {p['moq']:,}. The seller may refuse or "
                       "charge more; the lowest listed tier price is used.")

        def per(v):
            return None if v is None else v / qty

        if d["duty_pct"] is None:
            duty_lbl, duty_basis = "Import duty", "rate not available for this product category"
        else:
            duty_lbl = f"Import duty ({d['duty_pct']:g}%)"
            duty_basis = "on product value" if d["duty_on_goods_only"] else "on product + shipping + insurance"
        kg = f"{d['charged_kg']:,.1f} kg chargeable" if d["charged_kg"] is not None else "needs weight — not available"
        lines = [
            ("Product", d["product"], f"{cny(d['unit_cny'])}/unit × {qty:,}"),
            (f"Shipping · {d['mode_label']}", d["shipping"], f"{kg} + China domestic transport"),
            ("Insurance (0.5%)", d["insurance"], "of product value"),
            (duty_lbl, d["duty"], duty_basis),
            ("Customs clearance", d["clearance"],
             "included by the courier" if d["clearance"] == 0 else "broker fee per shipment"),
            (f"{d['tax_name']} ({d['vat_pct']:g}%)" if d["vat_pct"] else d["tax_name"], d["vat"],
             "on all of the above" if d["vat_pct"] else ""),
        ]
        def amount(v, per_v, strong=False):
            if v is None:
                return f"<span class='na'>{NA}</span>"
            return (f"<span class='ra-main'>{money(v, sym)}</span>"
                    f"<span class='ra-per'>{money(per_v, sym, 3)}/unit</span>")

        rows_html = "".join(
            f"<div class='rr'><div class='rl'>{esc(n)}<span class='rb'>{esc(b)}</span></div>"
            f"<div class='ra'>{amount(v, per(v))}</div></div>" for n, v, b in lines)
        st.markdown(
            f"<div class='rcpt'>{rows_html}"
            f"<div class='rr rt'><div class='rl'>Total delivered<span class='rb'>{units(qty)} · "
            f"{d['mode_label'].lower()}, {d['transit_days']} days</span></div>"
            f"<div class='ra'>{amount(d['total'], d['per_unit'])}</div></div></div>",
            unsafe_allow_html=True)
        st.markdown(f"<div class='muted'>Price on the original listing: {cny(d['unit_cny'])}/unit "
                    f"≈ {money(d['product_per_unit'], sym)}</div>", unsafe_allow_html=True)
        for n in d["notes"]:
            st.caption(f"• {n}")
        st.markdown(tag("Estimated", "est") + f"<span class='muted'>{fx_line(S.cur)}. Freight, duty and "
                    "VAT are sample estimates, not a quote: real costs depend on HS code, box size, "
                    "incoterms and the forwarder.</span>", unsafe_allow_html=True)

    # ---- 3. Supplier
    st.subheader("3 · Supplier")
    with st.container(border=True):
        score, reasons = supplier_score(s)
        c1, c2 = st.columns([1.2, 1])
        with c1:
            name = s.get("name") or s.get("name_cn")
            st.markdown(f"#### {esc(name) or NA}")
            if s.get("name") and s.get("name_cn"):
                st.markdown(f"<span class='muted'>{esc(s['name_cn'])}</span>", unsafe_allow_html=True)
            years = f"{s['years']} years" if s.get("years") is not None else None
            badges = " ".join(tag(b, "est") for b in s.get("badges") or []) or None
            st.markdown(kv_table([
                ("City", val(s.get("city"))),
                ("Type", val((s.get("type") or "").capitalize() or None)),
                ("Years active", val(years)),
                ("Badges", val(badges)),
                ("Response rate", val(None if s.get("response_rate") is None else f"{s['response_rate']:.0f}%")),
                ("Repeat buyers", val(None if s.get("repeat_buyer_rate") is None else f"{s['repeat_buyer_rate']:.0f}%")),
            ]), unsafe_allow_html=True)
        with c2:
            st.markdown(f"Reliability score<br>{score_pill(score)}", unsafe_allow_html=True)
            st.caption("Sample score — starts at 50, adjusted by the factors below.")
            for text, pts in reasons:
                if pts > 0:
                    st.markdown(f"✅ {text} (**+{pts}**)")
                elif pts < 0:
                    st.markdown(f"⚠️ {text} (**{pts}**)")
                else:
                    st.markdown(f"<span class='muted'>• {text}</span>", unsafe_allow_html=True)

    # ---- 4. Contact
    st.subheader("4 · Contact the supplier")
    with st.container(border=True):
        st.markdown("Chat with the supplier here: you write in English (or your language), they read "
                    "natural business Chinese, and every reply comes back translated and explained.")
        st.button("💬 Contact supplier", type="primary", key=f"contact_{key}",
                  on_click=open_conversation, args=(p, qty, country))
        st.markdown("**Original listing**")
        if p.get("url"):
            st.link_button(f"Open original listing on {p.get('platform') or 'source site'} ↗", p["url"])
        else:
            st.markdown(f"Original listing link: <span class='na'>{NA}</span> "
                        f"{tag('Sample catalog') if source == 'catalog' else ''}", unsafe_allow_html=True)
            slink = search_link(p)
            if slink:
                st.link_button(f"Search similar items on {p['platform']} ↗", slink)


def page_detail():
    p = get_product(S.pid)
    st.button("← Back to results", on_click=go, args=("results",))
    if not p:
        st.error("Product not found.")
        return
    sample_banner()
    render_detail(p, "catalog")


# =========================================================================== COMPARE
def page_compare():
    st.button("← Back to results", on_click=go, args=("results",))
    st.header("Compare")
    sample_banner()
    prods = [get_product(pid) for pid in S.cmp if get_product(pid)]
    if len(prods) < 2:
        st.info("Pick 2 or 3 offers under “All offers” on the results page.")
        return
    st.markdown(f"<span class='muted'>{S.qty:,} units delivered to {S.country} · {S.cur}</span>",
                unsafe_allow_html=True)
    data = {}
    for p in prods:
        d = delivered(p, S.qty, S.country, S.cur)
        score, _ = supplier_score(p["supplier"])
        data[f"{p['platform']} · {p['title_en'][:30]}…"] = {
            "Delivered / unit (est.)": money(d["per_unit"], d["symbol"]),
            "Total delivered (est.)": money(d["total"], d["symbol"]),
            "Seller price / unit": cny(d["unit_cny"]),
            "Shipping": f"{d['mode_label']} · {d['transit_days']} days" if d["mode"] else NA,
            "MOQ": f"{p['moq']:,}" if p["moq"] is not None else NA,
            "Lead time": f"{p['production_days']} days" if p["production_days"] is not None else NA,
            "Supplier score": f"{score}/100 ({score_label(score)})" if score is not None else NA,
            "Seller type": (p["supplier"].get("type") or NA).capitalize(),
        }
    st.dataframe(pd.DataFrame(data), use_container_width=True)
    st.markdown(" · ".join(f"<a href='{link(view='detail', pid=p['id'])}' target='_self'>"
                           f"{p['platform']} details →</a>" for p in prods), unsafe_allow_html=True)


# =========================================================================== PASTE
def page_paste():
    st.header("Paste a listing")
    st.markdown("Paste the text of a product page from 1688, Taobao, JD or Yiwugo. We extract what is "
                "there and build the same product page. Anything we can't find is shown as **not available**.")
    with st.container(border=True):
        text = st.text_area("Listing text", value=S.pasted_text, height=240,
                            placeholder="Paste the listing text here…")
        if st.button("Use an example listing"):
            S.pasted_text = SAMPLE_LISTING
            st.rerun()
        shot = st.file_uploader("…or upload a screenshot", type=["png", "jpg", "jpeg", "webp"])
        if shot:
            st.image(shot, use_container_width=True)
            st.info("Reading text from screenshots is not available yet in this version. "
                    "Please also paste the text so we can analyze it.")
        analyze = st.button("Analyze", type="primary")
    if analyze:
        S.pasted_text = text
        if not text.strip():
            st.warning("Paste some listing text first.")
            S.pasted = None
        else:
            S.pasted = parse_listing(text)
    p = S.pasted
    if not p:
        return

    with st.expander("Add details we could not find (optional)",
                     expanded=p.get("weight_kg") is None or p.get("category") is None):
        st.caption("Values you enter here are marked as user-provided and used for the delivered price.")
        c1, c2 = st.columns(2)
        w = c1.number_input("Weight per unit (g)", min_value=0, value=int((p.get("weight_kg") or 0) * 1000), step=10)
        cats = ["(not set)"] + list(DUTY)
        cat = c2.selectbox("Product category (for duty rate)", cats,
                           index=cats.index(p["category"]) if p.get("category") in cats else 0)
    p = dict(p)
    new_w = w / 1000 if w > 0 else None
    if new_w != p.get("weight_kg"):
        p["weight_kg"], p["weight_user"] = new_w, new_w is not None
    p["category"] = None if cat == "(not set)" else cat

    found = sum(1 for k in ["title_cn", "platform", "moq", "material", "size", "weight_kg", "production_days"]
                if S.pasted.get(k) is not None) + (1 if S.pasted.get("tiers") else 0)
    st.success(f"Analysis done — {found} of 8 key product fields found in the text.")
    render_detail(p, "pasted")


# =========================================================================== MESSAGES
def ago(ts):
    s = max(0, time.time() - ts)
    if s < 60:
        return "now"
    if s < 3600:
        return f"{int(s // 60)} min"
    if s < 86400:
        return time.strftime("%H:%M", time.localtime(ts))
    return time.strftime("%d %b", time.localtime(ts))


def page_inbox():
    st.header("Messages")
    convs = sorted(S.convs.values(), key=lambda c: c["updated"], reverse=True)
    if not convs:
        st.info("No conversations yet. Open a product and tap “Contact supplier”.")
        return
    rows = []
    for c in convs:
        last = c["messages"][-1] if c["messages"] else None
        if last is None:
            preview = "<span class='na'>No messages yet — your draft is ready</span>"
        elif last["role"] == "buyer":
            preview = "You: " + esc(last.get("en") or "")
        else:
            preview = esc((last.get("analysis") or {}).get("en") or last["zh"])
        unread = any(m["role"] == "supplier" and not m.get("read") for m in c["messages"])
        rows.append(
            f"<a class='ib{' unread' if unread else ''}' href='{link(view='chat', conv=c['id'])}' target='_self'>"
            f"<div class='ib-top'><span class='ib-name'>{esc(c['supplier'] or NA)}</span>"
            f"<span class='ib-time'>{ago(c['updated'])}</span></div>"
            f"<div class='ib-prod'><span class='mk' style='background:{PLATFORM_COLOURS.get(c['platform'], '#6b7280')}'>"
            f"{esc(c['platform'] or NA)}</span> {esc(c['product'] or NA)}</div>"
            f"<div class='ib-last'>{preview}</div></a>")
    st.markdown("".join(rows), unsafe_allow_html=True)


# ---- AI calls with caching (failures are never cached)
class _AIUnavailable(Exception):
    pass


@st.cache_data(show_spinner=False, max_entries=2000)
def _translate_cached(text, tone, context_json):
    out, err = M.translate_outgoing(text, tone, json.loads(context_json))
    if out is None:
        raise _AIUnavailable(err)
    return out


@st.cache_data(show_spinner=False, max_entries=2000)
def _analyze_cached(text_zh, context_json):
    out, err = M.analyze_incoming(text_zh, json.loads(context_json))
    if out is None:
        raise _AIUnavailable(err)
    return out


def highlight_zh(text, highlights):
    """Escape the supplier text and mark the key-term substrings the analysis found."""
    out = esc(text)
    parts = sorted({esc(h) for h in highlights or [] if h and h in text}, key=len, reverse=True)
    if parts:
        out = re.sub("|".join(re.escape(p) for p in parts), lambda m: f"<mark>{m.group(0)}</mark>", out)
    return out.replace("\n", "<br>")


TERM_LABELS = {"unit_price_cny": "Price", "moq_units": "MOQ", "lead_time": "Lead time",
               "payment_terms": "Payment", "sample_cost": "Sample", "shipping_terms": "Shipping",
               "customization": "Customization", "seller_type": "Seller", "certifications": "Certificates"}


def term_chips(terms):
    chips = []
    for k, label in TERM_LABELS.items():
        v = (terms or {}).get(k)
        if v in (None, "", 0, 0.0):
            continue
        if k == "unit_price_cny":
            q = terms.get("price_for_quantity")
            v = f"¥{v:g}" + (f" @ {q:,} pcs" if q else "")
        elif k == "moq_units":
            v = f"{v:,} pcs"
        chips.append(f"<span class='term'>{label}: {esc(v)}</span>")
    return f"<div class='terms'>{''.join(chips)}</div>" if chips else ""


def bubble(m):
    t = ago(m["ts"])
    if m["role"] == "buyer":
        return (f"<div class='b me'>{esc(m['zh']).replace(chr(10), '<br>')}"
                f"<div class='b-sub'>You wrote: {esc(m.get('en') or '')} · {t}</div></div>")
    a = m.get("analysis")
    if not a:
        return (f"<div class='b them'>{esc(m['zh']).replace(chr(10), '<br>')}"
                f"<div class='b-sub'>Translation not available — {esc(m.get('analysis_error') or '')} · {t}</div></div>")
    return (f"<div class='b them'>{highlight_zh(m['zh'], a.get('highlights'))}"
            f"<div class='b-en'>{esc(a['en'])}</div>"
            f"<div class='mean'><b>What they mean:</b> {esc(a['meaning'])}</div>"
            f"{term_chips(a.get('terms'))}<div class='b-sub'>{t}</div></div>")


def _set_draft(conv_id, text):
    S[f"draft_{conv_id}"] = text


def _quick_action(conv):
    key = f"qa_{conv['id']}"
    name = S.get(key)
    if name:
        S[f"draft_{conv['id']}"] = M.quick_action_text(name, conv["qty"], conv["country"],
                                                       conv["context"].get("listed_moq"))
        S[key] = None  # pills act as one-shot buttons


def _preview(conv):
    cid = conv["id"]
    text = (S.get(f"draft_{cid}") or "").strip()
    tone = S.get(f"tone_{cid}") or "polite"
    if not text:
        S[f"prev_{cid}"] = {"error": "Write a message first."}
        return
    try:
        out = _translate_cached(text, tone, json.dumps(conv["context"], ensure_ascii=False, sort_keys=True))
        S[f"prev_{cid}"] = {"src": text, "tone": tone, **out}
    except _AIUnavailable as e:
        S[f"prev_{cid}"] = {"error": f"Translation not available — {e}"}


def _send(conv):
    cid = conv["id"]
    prev = S.get(f"prev_{cid}") or {}
    conv["messages"].append({"role": "buyer", "en": prev["src"], "zh": prev["zh"],
                             "back_en": prev["back_en"], "tone": prev["tone"], "ts": time.time()})
    conv["updated"] = time.time()
    conv["pending"] = True
    S[f"draft_{cid}"] = ""
    S[f"prev_{cid}"] = None
    M.save_conversations(S.convs)


def _recalc(conv):
    """Delivered price with the negotiated unit price (and MOQ) instead of the listing's."""
    deal, card = conv["deal"], conv["card"]
    new_card = dict(card)
    new_card["tiers"] = [[1, deal["unit_price_cny"]]]
    if deal.get("moq_units"):
        new_card["moq"] = deal["moq_units"]
    qty = max(conv["qty"], deal.get("price_for_quantity") or 0)
    before = delivered(card, qty, conv["country"], S.cur)
    after = delivered(new_card, qty, conv["country"], S.cur)
    conv["recalc"] = {"qty": qty, "cur": S.cur, "before": before["per_unit"], "after": after["per_unit"],
                      "before_total": before["total"], "after_total": after["total"],
                      "mode": after["mode_label"], "days": after["transit_days"], "ts": time.time()}
    M.save_conversations(S.convs)


def deal_panel(conv):
    deal, ctx, sym = conv["deal"], conv["context"], SYMBOL[S.cur]
    listing = {
        "unit_price_cny": f"¥{ctx['listed_unit_price_cny']:g}" if ctx.get("listed_unit_price_cny") else None,
        "moq_units": f"{ctx['listed_moq']:,} pcs" if ctx.get("listed_moq") else None,
        "lead_time": f"{conv['card'].get('production_days')} days" if conv["card"].get("production_days") else None,
        "customization": conv["card"].get("customisation"),
    }
    rows = []
    for k, label in M.DEAL_FIELDS:
        v = deal.get(k)
        if v not in (None, "", 0):
            if k == "unit_price_cny":
                q = deal.get("price_for_quantity")
                v = f"¥{v:g}" + (f" @ {q:,} pcs" if q else "")
            elif k == "moq_units":
                v = f"{v:,} pcs"
            cell = f"{esc(v)}<span class='src'>from chat</span>"
            cls = " new" if k in deal.get("updated", []) else ""
        elif listing.get(k):
            cell, cls = f"{esc(listing[k])}<span class='src'>listing</span>", ""
        else:
            cell, cls = f"<span class='na'>not discussed yet</span>", ""
        rows.append(f"<div class='deal-row{cls}'><span>{label}</span><span class='v'>{cell}</span></div>")
    st.markdown("**Deal terms**" + "".join(rows), unsafe_allow_html=True)

    can = bool(deal.get("unit_price_cny"))
    st.button("Recalculate delivered price", key=f"recalc_{conv['id']}", disabled=not can,
              on_click=_recalc, args=(conv,), use_container_width=True,
              help=None if can else "Available once the supplier quotes a unit price")
    r = conv.get("recalc")
    if r and r["cur"] == S.cur:
        diff = "" if not (r["before"] and r["after"]) else f" ({(r['after'] - r['before']) / r['before'] * 100:+.1f}%)"
        st.markdown(
            f"<div class='rcpt'><div class='rr'><div class='rl'>Listing price<span class='rb'>delivered, "
            f"{r['qty']:,} units</span></div><div class='ra'><span class='ra-main'>{money(r['before'], sym)}</span>"
            f"<span class='ra-per'>{money(r['before_total'], sym, 0)} total</span></div></div>"
            f"<div class='rr rt'><div class='rl'>Negotiated<span class='rb'>{esc(r['mode'])}, {r['days']} days"
            f"{diff}</span></div><div class='ra'><span class='ra-main'>{money(r['after'], sym)}</span>"
            f"<span class='ra-per'>{money(r['after_total'], sym, 0)} total</span></div></div></div>",
            unsafe_allow_html=True)

    st.markdown("**Still to ask**")
    for k, label, question in M.CHECKLIST:
        done = deal.get(k) not in (None, "", 0)
        if done:
            st.markdown(f"✅ {label}")
        else:
            st.button(f"☐ {label} — ask", key=f"ask_{k}_{conv['id']}", on_click=_set_draft,
                      args=(conv["id"], question), type="tertiary")


def page_chat():
    conv = S.convs.get(S.conv)
    st.markdown("<style>.block-container {max-width:1100px;}</style>", unsafe_allow_html=True)
    if not conv:
        st.warning("Conversation not found.")
        st.markdown(f"<a href='{link(view='inbox')}' target='_self'>← All messages</a>", unsafe_allow_html=True)
        return
    cid = conv["id"]

    # opening the chat marks supplier messages as read
    if any(m["role"] == "supplier" and not m.get("read") for m in conv["messages"]):
        for m in conv["messages"]:
            m["read"] = True
        M.save_conversations(S.convs)

    st.markdown(
        f"<div class='chat-head'><a class='rh-back' href='{link(view='inbox')}' target='_self'>← All messages</a>"
        f"<div class='who'>{esc(conv['supplier'] or NA)}</div>"
        f"<div class='muted'><span class='mk' style='background:{PLATFORM_COLOURS.get(conv['platform'], '#6b7280')}'>"
        f"{esc(conv['platform'] or NA)}</span> {esc(conv['product'] or NA)} · {conv['qty']:,} units to "
        f"{esc(conv['country'])}"
        + (f" · listed delivered price {money(conv['delivered_at_start'] * fx_rate(S.cur) / fx_rate(conv['currency']), SYMBOL[S.cur])}/unit"
           if conv.get("delivered_at_start") else "")
        + "</div></div>", unsafe_allow_html=True)

    c_chat, c_deal = st.columns([1.75, 1], gap="large")
    with c_chat:
        st.markdown("<div class='chat'>" + "".join(bubble(m) for m in conv["messages"]) + "</div>",
                    unsafe_allow_html=True)

        # ---- supplier reply (with a short "typing…" pause)
        if conv.get("pending"):
            st.markdown("<div class='chat'><div class='typing'>typing…</div></div>", unsafe_allow_html=True)
            start = time.time()
            reply, err = M.simulate_supplier_reply(conv["messages"], conv["persona"])
            if reply is None:
                conv["pending"] = False
                conv["error"] = f"Message delivered, but the reply could not be loaded — {err}"
                M.save_conversations(S.convs)
                st.rerun()
            ctx = dict(conv["context"], current_deal={k: v for k, v in conv["deal"].items() if k != "updated"})
            try:
                analysis = _analyze_cached(reply, json.dumps(ctx, ensure_ascii=False, sort_keys=True))
                a_err = None
            except _AIUnavailable as e:
                analysis, a_err = None, str(e)
            wait = random.uniform(1, 3) - (time.time() - start)
            if wait > 0:
                time.sleep(wait)
            conv["messages"].append({"role": "supplier", "zh": reply, "analysis": analysis,
                                     "analysis_error": a_err, "ts": time.time(), "read": True})
            if analysis:
                conv["deal"] = M.update_deal_terms(conv["deal"], analysis.get("terms"))
            conv["pending"] = False
            conv["error"] = None
            conv["updated"] = time.time()
            M.save_conversations(S.convs)
            st.rerun()
        if conv.get("error"):
            st.warning(conv["error"])

        # ---- suggested replies for the latest supplier message
        last = conv["messages"][-1] if conv["messages"] else None
        if last and last["role"] == "supplier" and last.get("analysis"):
            sugg = last["analysis"].get("suggestions") or []
            if sugg:
                st.caption("Suggested replies — tap to use as a draft")
                for i, s_ in enumerate(sugg[:3]):
                    st.button(s_, key=f"sugg_{cid}_{len(conv['messages'])}_{i}", on_click=_set_draft,
                              args=(cid, s_), use_container_width=True)

        # ---- composer
        st.pills("Quick actions", list(M.QUICK_ACTIONS), key=f"qa_{cid}", on_change=_quick_action,
                 args=(conv,), label_visibility="collapsed")
        st.text_area("Your message", key=f"draft_{cid}", height=110,
                     placeholder="Write in English or any language…", label_visibility="collapsed")
        tone_key = f"tone_{cid}"
        S.setdefault(tone_key, "polite")
        st.segmented_control("Tone", ["polite", "neutral", "firm"], key=tone_key,
                             format_func=str.capitalize)
        prev = S.get(f"prev_{cid}")
        draft_now = (S.get(f"draft_{cid}") or "").strip()
        fresh = bool(prev and not prev.get("error") and prev.get("src") == draft_now
                     and prev.get("tone") == S.get(tone_key))
        if prev and prev.get("error"):
            st.warning(prev["error"])
        elif fresh:
            st.markdown(f"<div class='preview'><b>Will be sent:</b><br>{esc(prev['zh']).replace(chr(10), '<br>')}"
                        f"<div class='bt'>Means: {esc(prev['back_en'])}</div></div>", unsafe_allow_html=True)
        b1, b2 = st.columns([1.3, 1])
        with b1:
            st.markdown("<span class='nowrap'></span>", unsafe_allow_html=True)
            st.button("Preview in Chinese", key=f"pv_{cid}", on_click=_preview, args=(conv,),
                      use_container_width=True, disabled=not draft_now)
        with b2:
            st.button("Send", key=f"send_{cid}", type="primary", on_click=_send, args=(conv,),
                      use_container_width=True, disabled=not fresh or bool(conv.get("pending")))
        if draft_now and not fresh:
            st.caption("Preview the Chinese version first, then send.")

    with c_deal:
        with st.container(border=True):
            deal_panel(conv)


# =========================================================================== MAIN
def scroll_to_top_on_view_change():
    view = f"{S.view}:{S.pid if S.view == 'detail' else ''}"
    if S.get("_last_view") != view:
        S._last_view = view
        components.html(
            "<script>const d = window.parent.document;"
            "const m = d.querySelector('[data-testid=\"stMain\"]') || d.querySelector('section.main');"
            "if (m) m.scrollTo(0, 0); window.parent.scrollTo(0, 0);</script>",
            height=0,
        )


llm.set_api_key(get_api_key())
scroll_to_top_on_view_change()
if S.view == "home":
    page_home()
elif S.view == "results":
    page_results()
else:
    nav_bar()
    {"detail": page_detail, "compare": page_compare, "paste": page_paste,
     "inbox": page_inbox, "chat": page_chat}.get(S.view, page_home)()
