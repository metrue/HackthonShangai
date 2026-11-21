"""Home: a three-way bar — Link paste (left) · Sourcing (centre, default) · Messages (right)."""

import streamlit as st

from components import style
from components.state import S, TABS, go, link
from components.ui import currency_short, tag, unread_count
from core.pricing import COUNTRIES, CURRENCIES
from views.link_paste import render_link_paste
from views.messages import render_inbox

HEADLINE = "See where it costs less. Delivered."


def _tab_label(t):
    n = unread_count()
    return {"link": "🔗 Link paste", "search": "🔎 Sourcing",
            "messages": f"💬 Messages{f' ({n})' if n else ''}"}[t]


def _tab_changed():
    if S.get("home_tab"):
        S.tab = S.home_tab


def home_bar():
    S["home_tab"] = S.tab
    st.segmented_control("Section", list(TABS), key="home_tab", format_func=_tab_label, required=True,
                         on_change=_tab_changed, label_visibility="collapsed", width="stretch")


def search_tab():
    st.markdown(f"<div class='hero-wrap'><div class='hero-title'>{HEADLINE}</div></div>",
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
            cur = st.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(S.cur), format_func=currency_short)
        submitted = st.form_submit_button("Search", type="primary", width="stretch")
    if submitted:
        go("results", q=query.strip(), country=country, cur=cur or S.cur, pid=None, cmp=[])
        st.rerun()
    st.markdown("<div class='hero-foot'>Searching 1688 · Taobao · JD · Yiwugo "
                f"{tag('Sample catalog')}</div>", unsafe_allow_html=True)


def link_tab():
    st.markdown("<div class='hero-wrap' style='min-height:6vh'><div class='hero-title' style='font-size:clamp(1.7rem,7vw,2.4rem)'>"
                "Paste a link. Get the real price.</div></div>"
                "<div class='hero-sub'>From 1688, Taobao, JD or Yiwugo: product, delivered price and supplier "
                "in one page.</div>", unsafe_allow_html=True)
    render_link_paste()


def messages_tab():
    st.markdown("<div class='hero-wrap' style='min-height:6vh'><div class='hero-title' style='font-size:clamp(1.7rem,7vw,2.4rem)'>"
                "Your suppliers</div></div>"
                "<div class='hero-sub'>You write in your language, they read Chinese.</div>",
                unsafe_allow_html=True)
    render_inbox()
    if S.orders:
        st.markdown(f"<div class='hero-foot'><a href='{link(view='orders', order=None)}' target='_self'>"
                    f"📦 Your orders ({len(S.orders)})</a></div>", unsafe_allow_html=True)


def page_home():
    style.inject_home()
    home_bar()
    {"link": link_tab, "search": search_tab, "messages": messages_tab}[S.tab]()
