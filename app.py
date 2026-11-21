import base64
import html
import json
from urllib.parse import quote, urlencode

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from catalog import CATEGORY_STYLE, PLATFORMS, SELLER_TYPES, get_product, search
from listing_parser import SAMPLE_LISTING, parse_listing
from pricing import (COUNTRIES, CURRENCIES, DUTY, FX, SYMBOL, delivered, score_colour,
                     score_label, supplier_score)

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

/* ---------- best price card */
.best {{border:1px solid rgba(128,128,128,.25); border-radius:20px; padding:20px 18px 10px;
        background: var(--secondary-background-color, #fafafa); margin:.6rem 0 1rem;}}
.eyebrow {{text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; font-weight:700; color:#6b7280;}}
.best-price {{color:{VERMILION}; font-weight:900; font-size:clamp(2.8rem, 15vw, 4.2rem); line-height:1;
              margin:.25rem 0 .35rem; letter-spacing:-.02em;}}
.best-price .per {{font-size:1rem; font-weight:600; color:#6b7280; letter-spacing:0; margin-left:4px;}}
.best-line {{display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:1.05rem; font-weight:700;}}
.save {{background:{VERMILION}; color:#fff; border-radius:999px; padding:4px 12px; font-size:.9rem;
        font-weight:800;}}
.save-sub {{color:#6b7280; font-size:.85rem; margin-top:.35rem;}}

/* ---------- range bar */
.range {{position:relative; margin:22px 4px 6px; height:26px;}}
.range .track {{position:absolute; top:11px; left:0; right:0; height:4px; border-radius:4px;
               background:linear-gradient(90deg, {VERMILION} 0%, #d1d5db 35%, #d1d5db 100%);}}
.range .pt {{position:absolute; top:6px; width:14px; height:14px; margin-left:-7px; border-radius:50%;
            border:2px solid #fff; box-shadow:0 0 0 1px rgba(0,0,0,.15);}}
.range .pt.lowest {{top:4px; width:18px; height:18px; margin-left:-9px; border:2px solid #fff;
                 box-shadow:0 0 0 2px {VERMILION}; z-index:2;}}
.rlabels {{display:flex; justify-content:space-between; font-size:.78rem; color:#6b7280; margin:4px 0 8px;}}
.rlabels b {{color:{VERMILION};}}

/* ---------- platform rows: details on hover (desktop) / tap (mobile) */
.plist {{margin-top:6px;}}
.prow {{border-top:1px solid rgba(128,128,128,.18); outline:none; cursor:pointer;
        -webkit-tap-highlight-color:transparent;}}
.pmain {{display:flex; align-items:center; gap:10px; padding:13px 2px; min-height:48px;}}
.pname {{font-weight:600; flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
.pname small {{font-weight:400; color:#6b7280;}}
.pprice {{font-weight:800; font-variant-numeric:tabular-nums;}}
.prow.is-best .pprice {{color:{VERMILION};}}
.chev {{color:#9ca3af; transition:transform .2s; font-size:.9rem;}}
.pmore {{max-height:0; overflow:hidden; transition:max-height .25s ease; font-size:.88rem; color:#4b5563;}}
.pmore-in {{padding:0 2px 14px 22px; line-height:1.55;}}
.pmore a {{color:{VERMILION}; font-weight:700; text-decoration:none;}}
.prow:hover .pmore, .prow:focus .pmore, .prow:focus-within .pmore {{max-height:320px;}}
.prow:hover .chev, .prow:focus .chev, .prow:focus-within .chev {{transform:rotate(90deg);}}
.foot {{font-size:.75rem; color:#9ca3af; padding:10px 0 4px;}}

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
DEFAULTS = dict(view="home", q="", qty=500, budget=0.0, country="Italy", cur="EUR", pid=None, cmp=[])


def init_state():
    if S.get("_init"):
        return
    S._init = True
    qp = st.query_params
    for k, v in DEFAULTS.items():
        S[k] = v
    try:
        if qp.get("view") in ("home", "results", "detail", "compare", "paste"):
            S.view = qp["view"]
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


def state_params(**over):
    p = dict(view=S.view, q=S.q, qty=S.qty, country=S.country, cur=S.cur)
    if S.budget:
        p["budget"] = S.budget
    if S.pid:
        p["pid"] = S.pid
    if S.cmp:
        p["cmp"] = ",".join(S.cmp)
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


def score_pill(score):
    colour = score_colour(score)
    txt = f"{score}/100 · {score_label(score)}" if score is not None else NA
    return f"<span class='score-pill' style='background:{colour}'>{txt}</span>"


def dot(platform):
    return f"<span class='dot' style='background:{PLATFORM_COLOURS.get(platform, '#999')}'></span>"


def image_html(p, height=150):
    emoji, colour = CATEGORY_STYLE.get(p.get("category") or "unknown", CATEGORY_STYLE["unknown"])
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='300' height='220' viewBox='0 0 300 220'>
<rect width='300' height='220' rx='14' fill='{colour}'/>
<text x='150' y='125' font-size='86' text-anchor='middle'>{emoji}</text>
<text x='150' y='200' font-size='15' text-anchor='middle' fill='#555' font-family='sans-serif'>Sample image</text>
</svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode()
    return (f"<img src='data:image/svg+xml;base64,{b64}' "
            f"style='width:100%;max-height:{height}px;object-fit:contain;border-radius:12px'/>")


def search_link(p):
    """Sample products have no real listing; offer a platform search instead."""
    kw = quote(p.get("title_cn") or p.get("title_en") or "")
    return {
        "1688": f"https://s.1688.com/selloffer/offer_search.htm?keywords={kw}",
        "Taobao": f"https://s.taobao.com/search?q={kw}",
        "JD": f"https://search.jd.com/Search?keyword={kw}",
        "Yiwugo": "https://www.yiwugo.com/",
    }.get(p.get("platform"))


def nav_bar():
    """Small top bar for inner pages (not shown on the home screen)."""
    items = [f"<a class='plain' href='{link(view='home', pid=None)}' target='_self'><b>🔎 SourceScan</b></a>",
             f"<a class='plain muted' href='{link(view='paste')}' target='_self'>Paste a listing</a>"]
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
.hero-foot {text-align:center; color:#9ca3af; font-size:.8rem; margin-top:1.4rem; line-height:1.8;}
.hero-foot a {color:#6b7280;}
</style>""",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div class='hero-wrap'><div class='hero-title'>{HEADLINE}</div></div>",
                unsafe_allow_html=True)

    with st.form("search_form", border=False):
        query = st.text_input("What are you looking for?", value=S.q, label_visibility="collapsed",
                              placeholder="What are you looking for?")
        cur = st.segmented_control("Currency", CURRENCIES, default=S.cur, label_visibility="collapsed",
                                   format_func=lambda c: f"{SYMBOL[c]} {c}" if SYMBOL[c] != c else c)
        submitted = st.form_submit_button("Search", type="primary", use_container_width=True)
    if submitted:
        go("results", q=query.strip(), cur=cur or S.cur, pid=None, cmp=[])
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


def row_details(r, sym, extra=""):
    """Hidden part of a row: shown on hover (desktop) or tap (mobile)."""
    p, d = r["p"], r["d"]
    q = d["qty"]
    if r["ok"]:
        taxes = (d["duty"] or 0) + (d["vat"] or 0)
        costs = (f"Product {money(d['product'] / q, sym)} · Shipping {money(d['shipping'] / q, sym)} · "
                 f"Duty + tax {money(taxes / q, sym)} <span class='muted'>per unit, est.</span><br>")
    else:
        costs = f"<span class='na'>{why_not(r)}</span><br>"
    moq = units(p["moq"]) if p.get("moq") is not None else f"<span class='na'>{NA}</span>"
    return (f"<div class='pmore'><div class='pmore-in'>"
            f"<b>{esc(p['title_en'])}</b><br>{costs}"
            f"MOQ {moq} · {(p['supplier'].get('type') or NA).capitalize()} · {score_pill(r['score'])}<br>"
            f"{extra}<a href='{link(view='detail', pid=p['id'])}' target='_self'>View details →</a>"
            f"</div></div>")


def offer_row(r, sym, label, is_best=False, extra=""):
    price = money(r["d"]["per_unit"], sym) if r["ok"] else f"<span class='na'>{NA}</span>"
    return (f"<div class='prow{' is-best' if is_best else ''}' tabindex='0'>"
            f"<div class='pmain'>{dot(r['p']['platform'])}<span class='pname'>{label}</span>"
            f"<span class='pprice'>{price}</span><span class='chev'>›</span></div>"
            f"{row_details(r, sym, extra)}</div>")


def best_card(rows, sym):
    """Lowest delivered price + saving + range bar + one row per platform."""
    by_platform = {}
    for r in rows:
        by_platform.setdefault(r["p"]["platform"], []).append(r)
    priced = {}
    for plat, rs in by_platform.items():
        ok = [r for r in rs if r["ok"]]
        if ok:
            priced[plat] = min(ok, key=lambda r: r["d"]["per_unit"])

    if not priced:
        st.markdown("<div class='best'><div class='eyebrow'>Lowest delivered price</div>"
                    f"<div class='best-price' style='font-size:2rem;color:#9ca3af'>{NA}</div>"
                    "<div class='muted'>None of the matching offers has a delivered price at this quantity. "
                    "Open “All offers” below to see why.</div></div>", unsafe_allow_html=True)
        return

    ranked = sorted(priced.items(), key=lambda kv: kv[1]["d"]["per_unit"])
    best_plat, best = ranked[0]
    worst_plat, worst = ranked[-1]
    lo, hi = best["d"]["per_unit"], worst["d"]["per_unit"]

    # saving vs the most expensive platform
    if len(ranked) > 1 and hi > lo:
        pct = (hi - lo) / hi * 100
        save_badge = f"<span class='save'>Save {pct:.0f}%</span>"
        save_sub = (f"{money(hi - lo, sym)} less per unit than {worst_plat} · "
                    f"<b>{money((hi - lo) * S.qty, sym, 0)}</b> on {S.qty:,} units")
    else:
        save_badge = "<span class='tag tag-na'>Only platform with a price</span>"
        save_sub = "No other platform to compare with for this search"

    # range bar
    span = hi - lo
    pts = []
    for plat, r in reversed(ranked):  # draw best last so it sits on top
        x = 50 if span == 0 else 3 + 94 * (r["d"]["per_unit"] - lo) / span
        cls = "pt lowest" if plat == best_plat else "pt"
        pts.append(f"<span class='{cls}' style='left:{x:.1f}%;background:{PLATFORM_COLOURS[plat]}' "
                   f"title='{plat}: {money(r['d']['per_unit'], sym)}'></span>")
    range_html = (f"<div class='range'><div class='track'></div>{''.join(pts)}</div>"
                  f"<div class='rlabels'><span><b>{money(lo, sym)}</b> lowest</span>"
                  f"<span>highest {money(hi, sym)}</span></div>")

    # one row per platform: priced first, then platforms with offers but no usable price
    rows_html = []
    for plat, r in ranked:
        n_more = len(by_platform[plat]) - 1
        extra = f"<span class='muted'>+{n_more} more offer{'s' if n_more > 1 else ''} on {plat}</span><br>" if n_more else ""
        rows_html.append(offer_row(r, sym, plat, is_best=plat == best_plat, extra=extra))
    for plat, rs in by_platform.items():
        if plat not in priced:
            rows_html.append(offer_row(rs[0], sym, plat))

    st.markdown(
        f"<div class='best'>"
        f"<div class='eyebrow'>Lowest delivered price</div>"
        f"<div class='best-price'>{money(lo, sym)}<span class='per'>/unit</span></div>"
        f"<div class='best-line'>{dot(best_plat)}<span>{best_plat}</span>{save_badge}</div>"
        f"<div class='save-sub'>{save_sub}</div>"
        f"{range_html}"
        f"<div class='plist'>{''.join(rows_html)}</div>"
        f"<div class='foot'>Estimated price incl. shipping, duty and tax · Sample catalog · "
        f"tap or hover a platform for details</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def page_results():
    sym = SYMBOL[S.cur]
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
        f"<a class='rh-back' href='{link(view='home', pid=None)}' target='_self'>← New search</a>"
        f"<div class='rh-q'>“{q}”</div>"
        f"<div class='rh-sub'>{S.qty:,} units · to {S.country} · {S.cur}{budget_txt}</div>",
        unsafe_allow_html=True,
    )
    with st.popover("Quantity · country · currency · budget", use_container_width=False):
        bound(st.number_input, "Quantity", "qty", min_value=1, step=50)
        bound(st.selectbox, "Delivery country", "country", options=list(COUNTRIES))
        bound(st.segmented_control, "Currency", "cur", options=CURRENCIES)
        bound(st.number_input, f"Max budget per unit ({S.cur}, 0 = none)", "budget", min_value=0.0, step=0.5)

    if not base:
        st.warning(f"No products in the sample catalog match “{S.q}”. "
                   "Try tote bag, water bottle, phone case, yoga mat, mug or LED strip.")
        return
    if not filtered:
        st.info("No results match the current filters or budget.")
        return

    best_card(filtered, sym)

    # ---- everything else stays folded away
    with st.expander(f"All {len(filtered)} offers"
                     + (f" · {len(over_budget)} hidden over budget" if over_budget else "")):
        sort = st.radio("Sort by", ["Lowest delivered price", "Highest reliability", "Lowest MOQ"],
                        horizontal=True, label_visibility="collapsed")
        big = 10 ** 12
        if sort == "Lowest delivered price":
            filtered.sort(key=lambda r: r["d"]["per_unit"] if r["ok"] else big)
        elif sort == "Highest reliability":
            filtered.sort(key=lambda r: -(r["score"] if r["score"] is not None else -1))
        else:
            filtered.sort(key=lambda r: r["p"]["moq"] if r["p"]["moq"] is not None else big)
        best_id = min((r for r in filtered if r["ok"]), key=lambda r: r["d"]["per_unit"],
                      default={"p": {"id": None}})["p"]["id"]
        st.markdown(
            "<div class='plist'>" + "".join(
                offer_row(r, sym, f"{r['p']['platform']} <small>· {esc(r['p']['title_en'])}</small>",
                          is_best=r["p"]["id"] == best_id)
                for r in filtered) + "</div>",
            unsafe_allow_html=True,
        )
        st.write("")
        opts = {r["p"]["id"]: f"{r['p']['platform']} · {r['p']['title_en'][:40]}" for r in filtered}
        picked = st.multiselect("Compare 2–3 offers", list(opts), default=[x for x in S.cmp if x in opts],
                                format_func=opts.get, max_selections=3)
        if st.button("Compare", disabled=len(picked) < 2):
            go("compare", cmp=picked)
            st.rerun()


# =========================================================================== DETAIL
def kv_table(pairs):
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in pairs)
    return f"<table class='kv'>{rows}</table>"


def copy_button(text, key):
    payload = json.dumps(text)
    components.html(
        f"""
<button id="b" style="padding:10px 20px;border-radius:10px;border:1px solid #ccc;background:#fff;
 font-weight:600;cursor:pointer;font-family:sans-serif;font-size:15px">📋 Copy</button>
<span id="m" style="font-family:sans-serif;color:#2E7D32;margin-left:8px"></span>
<script>
const txt = {payload};
document.getElementById('b').onclick = async () => {{
  let ok = false;
  try {{ await navigator.clipboard.writeText(txt); ok = true; }} catch (e) {{}}
  if (!ok) {{
    const ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta);
    ta.select(); try {{ ok = document.execCommand('copy'); }} catch (e) {{}} ta.remove();
  }}
  document.getElementById('m').textContent = ok ? 'Copied!' : 'Copy failed — select the text manually';
}};
</script>""",
        height=52,
    )


COUNTRY_CN = {"Italy": "意大利", "Germany": "德国", "France": "法国", "Spain": "西班牙", "Netherlands": "荷兰",
              "United Kingdom": "英国", "United States": "美国", "Canada": "加拿大", "Australia": "澳大利亚"}


def contact_message(p, qty, country):
    cn_title = p.get("title_cn") or "贵司产品"
    cn = (f"您好！我对贵司的“{cn_title}”很感兴趣。\n"
          f"我计划采购 {qty} 件，需要发货到{COUNTRY_CN.get(country, country)}。\n"
          "请问：\n"
          f"1. {qty} 件的最优单价是多少？\n"
          "2. 生产周期和发货时间需要多久？\n"
          "3. 可以先寄样品吗？样品费和运费是多少？\n"
          "4. 是否支持定制logo和包装？\n"
          "谢谢！期待您的回复。")
    en = (f"Hello! I am interested in your product “{p.get('title_en') or cn_title}”.\n"
          f"I plan to buy {qty} units, to be shipped to {country}.\n"
          "Could you tell me:\n"
          f"1. What is your best unit price for {qty} units?\n"
          "2. How long are production and shipping?\n"
          "3. Can you send a sample first? What are the sample and shipping costs?\n"
          "4. Do you support custom logo and packaging?\n"
          "Thank you! Looking forward to your reply.")
    return cn, en


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
            fx, sym = FX[S.cur], SYMBOL[S.cur]
            tiers = sorted(p["tiers"])
            rows = []
            for i, (mq, price) in enumerate(tiers):
                rng = f"{mq:,} – {tiers[i+1][0]-1:,}" if i + 1 < len(tiers) else f"{mq:,}+"
                rows.append({"Quantity": rng, "Price (CNY)": f"¥{price:,.2f}",
                             f"≈ {S.cur} (sample FX)": f"{sym}{price*fx:,.2f}"})
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=False)
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
        d = delivered(p, qty, country, S.cur)
        sym = d["symbol"]
        if d["below_moq"]:
            st.warning(f"{qty:,} units is below the MOQ of {p['moq']:,}. The seller may refuse or "
                       "charge more; the lowest listed tier price is used.")

        def per(v):
            return None if v is None else v / qty

        duty_lbl = (f"Import duty ({d['duty_rate']*100:.1f}% on "
                    f"{'product + shipping' if d['duty_base'] == 'CIF' else 'product value'})"
                    if d["duty_rate"] is not None else "Import duty (rate not available for this category)")
        vat_lbl = f"{d['tax_name']} ({d['vat_rate']*100:.0f}%)"
        lines = [
            ("Product", d["product"], f"{cny(d['unit_cny'])}/unit × {qty:,}"),
            ("Shipping", d["shipping"],
             f"Air freight ¥{d['freight_cny_kg']}/kg + China domestic + ¥150 handling"
             if p.get("weight_kg") is not None else "needs weight — not available"),
            (duty_lbl, d["duty"], "estimate"),
            (vat_lbl, d["vat"], "estimate"),
        ]
        table = pd.DataFrame(
            [{"Cost": n, "Total": money(v, sym), "Per unit": money(per(v), sym, 3), "Basis": b}
             for n, v, b in lines]
            + [{"Cost": "TOTAL delivered", "Total": money(d["total"], sym),
                "Per unit": money(d["per_unit"], sym, 3), "Basis": ""}]
        )
        st.dataframe(table, hide_index=True, use_container_width=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Delivered price per unit", money(d["per_unit"], sym))
        m2.metric("Total delivered", money(d["total"], sym))
        m3.metric("Seller price per unit", money(d["product_per_unit"], sym),
                  help="Converted from CNY at the sample exchange rate")
        st.markdown(tag("Estimated", "est") + "<span class='muted'>Sample freight, duty, VAT and FX rates. "
                    "Real quotes depend on HS code, incoterms, volume weight and the forwarder.</span>",
                    unsafe_allow_html=True)

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
        cn, en = contact_message(p, qty, country)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Message in Chinese** (send this)")
            st.text_area("Chinese message", cn, height=210, key=f"cn_{key}_{qty}_{country}",
                         label_visibility="collapsed")
            copy_button(cn, key)
        with c2:
            st.markdown("**English translation** (for you)")
            st.text_area("English translation", en, height=210, key=f"en_{key}_{qty}_{country}",
                         label_visibility="collapsed")
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


scroll_to_top_on_view_change()
if S.view == "home":
    page_home()
elif S.view == "results":
    page_results()
else:
    nav_bar()
    {"detail": page_detail, "compare": page_compare, "paste": page_paste}.get(S.view, page_home)()
