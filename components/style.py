"""All CSS of the app, mobile-first (375px first, then wider screens)."""

import streamlit as st

VERMILION = "#E34234"

CSS = f"""
<style>
[data-testid="stToolbar"], [data-testid="stDecoration"], footer {{display:none !important;}}
header[data-testid="stHeader"] {{background: transparent;}}
.block-container {{padding: 1.2rem 1rem 3rem; max-width: 760px;}}

.tag {{display:inline-block; padding:2px 10px; border-radius:999px; font-size:.75rem; font-weight:600;
      margin-right:6px; border:1px solid rgba(128,128,128,.35);}}
.tag-sample {{background:#FFF4CC; color:#7A5B00; border-color:#F0D78C;}}
.tag-est {{background:#E8F0FE; color:#1A4FB5; border-color:#B7CCF5;}}
.tag-na {{background:#F1F1F1; color:#666; border-color:#DDD;}}
.tag-ok {{background:#E7F5EA; color:#1E6B2E; border-color:#B7DFC0;}}
.na {{color:#9ca3af; font-style:italic;}}
.muted {{color:#6b7280; font-size:.88rem;}}
.score-pill {{display:inline-block; padding:2px 10px; border-radius:999px; color:#fff; font-weight:700;
      font-size:.82rem;}}
.kv td {{padding:4px 14px 4px 0; vertical-align:top;}}
.kv td:first-child {{color:#6b7280; white-space:nowrap;}}
a.plain {{color:inherit; text-decoration:none;}}
.nav {{display:flex; gap:18px; align-items:center; flex-wrap:wrap; margin-bottom:.6rem; font-size:.92rem;}}

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

/* ---------- home: three-way bar (Link paste · Sourcing · Messages) */
.st-key-home_tab button {{min-width:0 !important; min-height:2.6rem; padding:0 .3rem !important;
    font-weight:600;}}
.st-key-home_tab button p {{font-size:.82rem !important; white-space:nowrap;}}
@media (min-width: 480px) {{ .st-key-home_tab button p {{font-size:.95rem !important;}} }}

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
.src-tag {{display:inline-block; padding:0 7px; border-radius:6px; font-size:.7rem; font-weight:700;
           line-height:1.7; color:#6b7280; border:1px solid #d1d5db;}}
.src-tag.live {{color:#1E6B2E; border-color:#9fd3ab; background:#E7F5EA;}}
.best-tag {{background:#111827;}}
.pc-price {{font-size:1.5rem; font-weight:800; line-height:1.1; font-variant-numeric:tabular-nums;}}
.pc-price small {{font-size:.75rem; font-weight:500; color:#6b7280; margin-left:4px;}}
a.pc.top .pc-price {{color:{VERMILION};}}
.pc-na {{font-size:1rem; font-weight:600; color:#9ca3af; font-style:italic;}}
.pc-sub {{font-size:.78rem; color:#6b7280; line-height:1.35;}}
.list-count {{font-size:.85rem; color:#6b7280; padding-top:.55rem;}}
.foot {{font-size:.75rem; color:#9ca3af; padding:6px 0 4px; line-height:1.5;}}

/* ---------- delivered price receipt */
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

/* ---------- orders */
.tl {{list-style:none; padding:0; margin:.5rem 0 .8rem;}}
.tl li {{position:relative; padding:0 0 14px 24px; font-size:.92rem; line-height:1.3;}}
.tl li::before {{content:""; position:absolute; left:3px; top:3px; width:11px; height:11px; border-radius:50%;
                background:#d1d5db;}}
.tl li::after {{content:""; position:absolute; left:8px; top:16px; bottom:0; width:1px; background:#e5e7eb;}}
.tl li:last-child::after {{display:none;}}
.tl li.done::before {{background:#2E7D32;}}
.tl li.now::before {{background:{VERMILION}; box-shadow:0 0 0 3px rgba(227,66,52,.25);}}
.tl li.todo {{color:#9ca3af;}}
.tl .t {{display:block; color:#9ca3af; font-size:.74rem;}}
a.oc {{display:block; padding:12px 0; border-bottom:1px solid rgba(128,128,128,.18); color:inherit !important;
       text-decoration:none !important;}}

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
  .pc-img {{width:128px; height:128px;}}
  .pc-price {{font-size:1.7rem;}}
}}
</style>
"""

HOME_CSS = f"""
<style>
.block-container {{max-width: 620px;}}
.hero-wrap {{min-height: 14vh; display:flex; align-items:flex-end; justify-content:center;}}
.hero-title {{text-align:center; font-weight:900; line-height:1.1; letter-spacing:-.02em;
             font-size: clamp(2rem, 9vw, 3rem); margin: 0 0 1.2rem;}}
.hero-sub {{text-align:center; color:#6b7280; margin:-.6rem 0 1rem; font-size:.95rem;}}
div[data-testid="stTextInput"] input {{font-size:1.15rem; height:3.6rem; padding:0 1.1rem;
             border-radius:16px;}}
div[data-testid="stTextInput"] > div {{border-radius:16px;}}
div[data-testid="stForm"] {{border:none; padding:0;}}
div[data-testid="stFormSubmitButton"] button {{height:3.2rem; border-radius:14px; font-size:1.05rem;
             font-weight:700; background:{VERMILION}; border-color:{VERMILION};}}
div[data-testid="stForm"] div[data-testid="stSelectbox"] label p {{font-size:.78rem; color:#6b7280;}}
div[data-testid="stForm"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
             min-height:2.3rem; font-size:.9rem;}}
.hero-foot {{text-align:center; color:#9ca3af; font-size:.8rem; margin-top:1.4rem; line-height:1.8;}}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def inject_home():
    st.markdown(HOME_CSS, unsafe_allow_html=True)


def wide():
    st.markdown("<style>.block-container {max-width:1100px;}</style>", unsafe_allow_html=True)
