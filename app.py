import base64
import json
from urllib.parse import quote

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from catalog import CATEGORY_STYLE, PLATFORMS, SELLER_TYPES, get_product, search
from listing_parser import SAMPLE_LISTING, parse_listing
from pricing import COUNTRIES, DUTY, FX, SYMBOL, delivered, score_colour, score_label, supplier_score

st.set_page_config(page_title="SourceScan – China sourcing search", page_icon="🔎", layout="wide")

NA = "not available"

# --------------------------------------------------------------------------- style
st.markdown(
    """
<style>
.block-container {padding-top: 2.2rem; max-width: 1200px;}
.hero-title {text-align:center; font-size: 2.6rem; font-weight: 800; margin: 1.5rem 0 0.2rem;}
.hero-sub {text-align:center; color: #6b7280; font-size: 1.1rem; margin-bottom: 1.4rem;}
.tag {display:inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.78rem;
      font-weight: 600; margin-right: 6px; border: 1px solid rgba(128,128,128,.35);}
.tag-sample {background: #FFF4CC; color: #7A5B00; border-color: #F0D78C;}
.tag-est {background: #E8F0FE; color: #1A4FB5; border-color: #B7CCF5;}
.tag-na {background: #F1F1F1; color: #666; border-color: #DDD;}
.platform-logo {display:inline-block; padding: 10px 22px; margin: 6px; border-radius: 10px;
      font-weight: 800; font-size: 1.15rem; letter-spacing: .5px; color: white;}
.price-big {font-size: 2rem; font-weight: 800; line-height: 1.1;}
.price-small {color: #6b7280; font-size: 0.9rem;}
.score-pill {display:inline-block; padding: 3px 12px; border-radius: 999px; color: white;
      font-weight: 700; font-size: 0.9rem;}
.na {color: #9ca3af; font-style: italic;}
.muted {color: #6b7280; font-size: 0.88rem;}
.kv td {padding: 4px 14px 4px 0; vertical-align: top;}
.kv td:first-child {color: #6b7280; white-space: nowrap;}
</style>
""",
    unsafe_allow_html=True,
)

PLATFORM_COLOURS = {"1688": "#FF6A00", "Taobao": "#FF4400", "JD": "#E1251B", "Yiwugo": "#1E73BE"}


# --------------------------------------------------------------------------- state
def init_state():
    defaults = dict(page="home", query="", qty=500, budget=0.0, country="Italy",
                    product_id=None, compare=[], pasted=None, pasted_text="")
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


init_state()
S = st.session_state


def go(page, **kw):
    S.page = page
    for k, v in kw.items():
        S[k] = v


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


def tag(text, kind="sample"):
    return f"<span class='tag tag-{kind}'>{text}</span>"


def score_pill(score):
    colour = score_colour(score)
    txt = f"{score}/100 · {score_label(score)}" if score is not None else NA
    return f"<span class='score-pill' style='background:{colour}'>{txt}</span>"


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
    c1, c2, c3, c4, _ = st.columns([1.3, 1, 1.3, 1.6, 3])
    c1.button("🔎 SourceScan", on_click=go, args=("home",), type="tertiary")
    c2.button("Search", on_click=go, args=("home",), key="nav_search")
    c3.button("Paste a listing", on_click=go, args=("paste",), key="nav_paste")
    if S.compare:
        c4.button(f"Compare ({len(S.compare)})", on_click=go, args=("compare",), key="nav_compare")


def sample_banner():
    st.markdown(
        tag("Sample catalog") + tag("Prices delivered = estimates", "est")
        + "<span class='muted'>Demo data, not live listings. Shipping, duty, VAT and exchange "
          "rates are simplified sample assumptions.</span>",
        unsafe_allow_html=True,
    )


# =========================================================================== HOME
def page_home():
    st.markdown("<div class='hero-title'>Find it in China. See the real price.</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-sub'>One search across Chinese wholesale and retail platforms — "
                "every price shown delivered to your door.</div>", unsafe_allow_html=True)

    _, mid, _ = st.columns([0.6, 4, 0.6])
    with mid:
        with st.container(border=True):
            with st.form("search_form", border=False):
                query = st.text_input("What are you looking for?", value=S.query,
                                      placeholder="e.g. canvas tote bag, insulated water bottle, yoga mat…")
                c1, c2, c3, c4 = st.columns([1, 1.2, 1.4, 1])
                qty = c1.number_input("Quantity", min_value=1, value=int(S.qty), step=50)
                budget = c2.number_input("Max budget per unit (optional)", min_value=0.0,
                                         value=float(S.budget), step=0.5,
                                         help="Delivered price per unit, in the currency of the "
                                              "delivery country. Leave at 0 for no limit.")
                countries = list(COUNTRIES)
                country = c3.selectbox("Delivery country", countries, index=countries.index(S.country))
                c4.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
                submitted = c4.form_submit_button("Search", type="primary", use_container_width=True)
            if submitted:
                go("results", query=query, qty=int(qty), budget=float(budget), country=country,
                   compare=[])
                st.rerun()

        st.markdown("<div style='text-align:center;margin-top:1.2rem' class='muted'>We search</div>",
                    unsafe_allow_html=True)
        logos = "".join(f"<span class='platform-logo' style='background:{PLATFORM_COLOURS[p]}'>{p}</span>"
                        for p in PLATFORMS)
        st.markdown(f"<div style='text-align:center'>{logos}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;margin-top:.6rem'>{tag('Sample catalog')}"
                    "<span class='muted'>Platform names shown as text badges. Results come from a "
                    "demo catalog, not a live search.</span></div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("<div class='muted' style='text-align:center'>Try: "
                    "<b>tote bag</b> · <b>water bottle</b> · <b>phone case</b> · <b>yoga mat</b> · "
                    "<b>mug</b> · <b>LED strip</b></div>", unsafe_allow_html=True)


# =========================================================================== RESULTS
def enrich(products):
    rows = []
    for p in products:
        d = delivered(p, S.qty, S.country)
        score, _ = supplier_score(p.get("supplier"))
        rows.append(dict(p=p, d=d, score=score))
    return rows


def page_results():
    sym = SYMBOL[COUNTRIES[S.country]["currency"]]
    base = search(S.query)
    rows = enrich(base)

    # ---- sidebar filters
    with st.sidebar:
        st.header("Filters")
        f_platform = st.multiselect("Platform", PLATFORMS, default=PLATFORMS)
        f_type = st.multiselect("Seller type", SELLER_TYPES, default=SELLER_TYPES,
                                format_func=lambda t: {"factory": "Factory", "store": "Store",
                                                       "middleman": "Middleman / trading co."}[t])
        f_score = st.slider("Minimum supplier score", 0, 100, 0, step=5)
        max_moq_all = max([r["p"]["moq"] or 0 for r in rows] + [1])
        f_moq = st.number_input("Maximum MOQ", min_value=1, value=int(max_moq_all), step=50)
        show_over = st.checkbox("Show results over budget", value=False, disabled=not S.budget)
        st.divider()
        st.caption("Supplier score is a sample rule-based rating (seller type, years active, badges, "
                   "response and repeat-buyer rates, disputes). Products with unknown score are kept "
                   "only when minimum score is 0.")

    def keep(r):
        p = r["p"]
        if p["platform"] not in f_platform:
            return False
        if p["supplier"].get("type") not in f_type:
            return False
        if f_score > 0 and (r["score"] is None or r["score"] < f_score):
            return False
        if p["moq"] is not None and p["moq"] > f_moq:
            return False
        return True

    filtered = [r for r in rows if keep(r)]
    over_budget = []
    if S.budget:
        over_budget = [r for r in filtered if r["d"]["per_unit"] is not None and r["d"]["per_unit"] > S.budget]
        if not show_over:
            filtered = [r for r in filtered if r not in over_budget]

    # ---- summary
    with st.container(border=True):
        c1, c2 = st.columns([3, 1.2])
        q = S.query.strip() or "all products"
        budget_txt = f" · budget ≤ {money(S.budget, sym)}/unit" if S.budget else ""
        c1.markdown(f"#### “{q}”")
        c1.markdown(f"<span class='muted'>{S.qty:,} units · delivered to {S.country}{budget_txt} · "
                    f"{len(filtered)} of {len(rows)} results shown</span>", unsafe_allow_html=True)
        c2.button("✏️ Change search", on_click=go, args=("home",), use_container_width=True)
    sample_banner()

    sort = st.radio("Sort by", ["Lowest delivered price", "Highest reliability", "Lowest MOQ"],
                    horizontal=True)
    big = 10 ** 12
    if sort == "Lowest delivered price":
        filtered.sort(key=lambda r: r["d"]["per_unit"] if r["d"]["per_unit"] is not None else big)
    elif sort == "Highest reliability":
        filtered.sort(key=lambda r: -(r["score"] if r["score"] is not None else -1))
    else:
        filtered.sort(key=lambda r: r["p"]["moq"] if r["p"]["moq"] is not None else big)

    if not base:
        st.warning(f"No products in the sample catalog match “{S.query}”. "
                   "Try tote bag, water bottle, phone case, yoga mat, mug or LED strip.")
        return
    if not filtered:
        st.info("No results match the current filters.")
        if over_budget and not show_over:
            st.caption(f"{len(over_budget)} result(s) are over your budget — tick "
                       "“Show results over budget” in the sidebar.")
        return
    if over_budget and not show_over:
        st.caption(f"{len(over_budget)} result(s) hidden because they are over your budget.")

    for r in filtered:
        result_card(r, sym)


def result_card(r, sym):
    p, d, score = r["p"], r["d"], r["score"]
    with st.container(border=True):
        c_img, c_info, c_price = st.columns([1.1, 2.8, 1.5])
        with c_img:
            st.markdown(image_html(p, 140), unsafe_allow_html=True)
        with c_info:
            st.markdown(f"**{p['title_en']}**")
            plat_col = PLATFORM_COLOURS.get(p["platform"], "#555")
            seller = (p["supplier"].get("type") or NA).capitalize()
            st.markdown(
                f"<span class='tag' style='background:{plat_col};color:white;border:none'>{p['platform']}</span>"
                f"<span class='muted'>{seller} · {val(p['supplier'].get('city'))}</span>",
                unsafe_allow_html=True)
            moq_txt = units(p["moq"]) if p["moq"] is not None else f"<span class='na'>{NA}</span>"
            st.markdown(f"MOQ: **{moq_txt}**", unsafe_allow_html=True)
            if d["below_moq"]:
                st.markdown(tag(f"Your quantity ({S.qty:,}) is below MOQ", "na"), unsafe_allow_html=True)
            st.markdown(f"Supplier score: {score_pill(score)}", unsafe_allow_html=True)
        with c_price:
            if d["per_unit"] is not None:
                st.markdown(f"<div class='price-big'>{money(d['per_unit'], sym)}</div>"
                            f"<div class='muted'>per unit, delivered {tag('estimate', 'est')}</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='price-big na' style='font-size:1.3rem'>{NA}</div>"
                            "<div class='muted'>delivered price — missing data (e.g. weight)</div>",
                            unsafe_allow_html=True)
            st.markdown(f"<div class='price-small'>Original: {cny(d['unit_cny'])} / unit on {p['platform']}</div>",
                        unsafe_allow_html=True)
            st.button("View details", key=f"view_{p['id']}", type="primary", use_container_width=True,
                      on_click=go, args=("detail",), kwargs=dict(product_id=p["id"]))
            in_cmp = p["id"] in S.compare
            full = len(S.compare) >= 3 and not in_cmp
            st.checkbox("Compare", value=in_cmp, key=f"cmp_{p['id']}", disabled=full,
                        on_change=toggle_compare, args=(p["id"],),
                        help="Select up to 3 products" if full else None)


def toggle_compare(pid):
    if pid in S.compare:
        S.compare = [x for x in S.compare if x != pid]
    elif len(S.compare) < 3:
        S.compare = S.compare + [pid]


# =========================================================================== DETAIL
def kv_table(pairs):
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in pairs)
    return f"<table class='kv'>{rows}</table>"


def copy_button(text, key):
    payload = json.dumps(text)
    components.html(
        f"""
<button id="b" style="padding:8px 18px;border-radius:8px;border:1px solid #ccc;background:#fff;
 font-weight:600;cursor:pointer;font-family:sans-serif">📋 Copy</button>
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
        height=48,
    )


def contact_message(p, qty, country):
    s = p.get("supplier") or {}
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


COUNTRY_CN = {"Italy": "意大利", "Germany": "德国", "France": "法国", "Spain": "西班牙", "Netherlands": "荷兰",
              "United Kingdom": "英国", "United States": "美国", "Canada": "加拿大", "Australia": "澳大利亚"}


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
                st.markdown(f"<span class='muted'>Original title: {p['title_cn']}</span>", unsafe_allow_html=True)
            moq = units(p["moq"]) if p.get("moq") is not None else None
            weight = f"{p['weight_kg']*1000:,.0f} g" if p.get("weight_kg") is not None else None
            if weight and p.get("weight_user"):
                weight += " " + tag("user-provided", "est")
            prod = f"{p['production_days']} days" if p.get("production_days") is not None else None
            st.markdown(kv_table([
                ("Platform", val(p.get("platform"))),
                ("Material", val(p.get("material"))),
                ("Size", val(p.get("size"))),
                ("Weight (per unit)", val(weight)),
                ("MOQ", val(moq)),
                ("Production time", val(prod)),
                ("Customisation", val(p.get("customisation"))),
            ]), unsafe_allow_html=True)

        st.markdown("**Price tiers** (as listed by the seller)")
        if p.get("tiers"):
            fx = FX[COUNTRIES[S.country]["currency"]]
            sym = delivered(p, 1, S.country)["symbol"]
            tiers = sorted(p["tiers"])
            rows = []
            for i, (mq, price) in enumerate(tiers):
                upper = f"{tiers[i+1][0]-1:,}" if i + 1 < len(tiers) else "+"
                rng = f"{mq:,} – {upper}" if upper != "+" else f"{mq:,}+"
                rows.append({"Quantity": rng, "Price (CNY)": f"¥{price:,.2f}",
                             f"≈ {COUNTRIES[S.country]['currency']} (sample FX)": f"{sym}{price*fx:,.2f}"})
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
        d = delivered(p, qty, country)
        sym = d["symbol"]
        if d["below_moq"]:
            st.warning(f"{qty:,} units is below the MOQ of {p['moq']:,}. The seller may refuse or "
                       "charge more; the lowest listed tier price is used.")

        def per(v):
            return None if v is None else v / qty

        duty_lbl = (f"Import duty ({d['duty_rate']*100:.1f}% on {'product + shipping' if d['duty_base']=='CIF' else 'product value'})"
                    if d["duty_rate"] is not None else "Import duty (rate not available for this category)")
        vat_lbl = f"{d['tax_name']} ({d['vat_rate']*100:.0f}%)"
        lines = [
            ("Product", d["product"], f"{cny(d['unit_cny'])}/unit × {qty:,}"),
            ("Shipping", d["shipping"],
             f"Air freight ¥{d['freight_cny_kg']}/kg + China domestic + ¥150 handling" if p.get("weight_kg") is not None
             else "needs weight — not available"),
            (duty_lbl, d["duty"], "estimate"),
            (vat_lbl, d["vat"], "estimate"),
        ]
        table = pd.DataFrame(
            [{"Cost": n, "Total": money(v, sym), "Per unit": money(per(v), sym, 3), "Basis": b} for n, v, b in lines]
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
            st.markdown(f"#### {name or NA}")
            if s.get("name") and s.get("name_cn"):
                st.markdown(f"<span class='muted'>{s['name_cn']}</span>", unsafe_allow_html=True)
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
            link = search_link(p)
            if link:
                st.link_button(f"Search similar items on {p['platform']} ↗", link)


def page_detail():
    p = get_product(S.product_id)
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
    prods = [get_product(pid) for pid in S.compare if get_product(pid)]
    if len(prods) < 2:
        st.info("Select 2 or 3 products with the “Compare” box on the results page.")
        return
    st.markdown(f"<span class='muted'>{S.qty:,} units delivered to {S.country}</span>", unsafe_allow_html=True)
    cols = st.columns(len(prods))
    data = {}
    for c, p in zip(cols, prods):
        d = delivered(p, S.qty, S.country)
        score, _ = supplier_score(p["supplier"])
        with c:
            with st.container(border=True):
                st.markdown(image_html(p, 110), unsafe_allow_html=True)
                st.markdown(f"**{p['title_en']}**")
                st.button("View details", key=f"cmpview_{p['id']}", on_click=go, args=("detail",),
                          kwargs=dict(product_id=p["id"]), use_container_width=True)
                st.button("Remove", key=f"cmprm_{p['id']}", on_click=toggle_compare, args=(p["id"],),
                          use_container_width=True)
        data[f"{p['title_en'][:38]}… ({p['platform']})"] = {
            "Delivered price / unit (est.)": money(d["per_unit"], d["symbol"]),
            "Total delivered (est.)": money(d["total"], d["symbol"]),
            "Seller price / unit (CNY)": cny(d["unit_cny"]),
            "MOQ": f"{p['moq']:,}" if p["moq"] is not None else NA,
            "Lead time (production)": f"{p['production_days']} days" if p["production_days"] is not None else NA,
            "Supplier score": f"{score}/100 ({score_label(score)})" if score is not None else NA,
            "Seller type": (p["supplier"].get("type") or NA).capitalize(),
            "Platform": p["platform"],
        }
    st.dataframe(pd.DataFrame(data), use_container_width=True)


# =========================================================================== PASTE
def page_paste():
    st.header("Paste a listing")
    st.markdown("Paste the text of a product page from 1688, Taobao, JD or Yiwugo (title, prices, MOQ, "
                "specs, shop info). We extract what is there and build the same product page. "
                "Anything we can't find is shown as **not available**.")
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            text = st.text_area("Listing text", value=S.pasted_text, height=260,
                                placeholder="Paste the listing text here…")
            if st.button("Use an example listing"):
                S.pasted_text = SAMPLE_LISTING
                st.rerun()
        with c2:
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

    with st.expander("Add details we could not find (optional)", expanded=p.get("weight_kg") is None or p.get("category") is None):
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


def scroll_to_top_on_view_change():
    view = f"{S.page}:{S.product_id if S.page == 'detail' else ''}"
    if S.get("_last_view") != view:
        S._last_view = view
        components.html(
            "<script>const d = window.parent.document;"
            "const m = d.querySelector('[data-testid=\"stMain\"]') || d.querySelector('section.main');"
            "if (m) m.scrollTo(0, 0); window.parent.scrollTo(0, 0);</script>",
            height=0,
        )


# =========================================================================== MAIN
nav_bar()
scroll_to_top_on_view_change()
page = S.page
if page == "home":
    page_home()
elif page == "results":
    page_results()
elif page == "detail":
    page_detail()
elif page == "compare":
    page_compare()
elif page == "paste":
    page_paste()
