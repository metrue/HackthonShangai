"""Landed (delivered) cost of a product bought on a Chinese marketplace.

Built on the team's landed-cost model:
  - exchange rates live from the ECB (frankfurter API, free, no key), refreshed
    every 6 hours, with a fallback table when the request fails
  - four shipping modes (sea, rail, air, express) with transit times,
    volumetric weight, insurance and customs clearance
Changes for the site:
  - minimum chargeable weight per mode, so small orders are not priced at a
    fraction of a sea container
  - customs clearance depends on the mode (express couriers include it)
  - no made-up duty: an unknown category gives "not available"
  - missing data never hides the rest of the breakdown: each line can be None

Everything except the ECB rate is a SAMPLE ESTIMATE for the demo, not a quote.
Edit the tables to update them (EU duty rates: check TARIC).
"""

import json
import threading
import time
import urllib.request

# ---------------------------------------------------------------------------
# EXCHANGE RATES: 1 CNY in each currency
# ---------------------------------------------------------------------------

FALLBACK_FX = {
    "EUR": 0.12, "GBP": 0.105, "USD": 0.14, "CHF": 0.113, "NOK": 1.45, "SEK": 1.33,
    "DKK": 0.90, "PLN": 0.51, "CZK": 3.00, "HUF": 47.0, "RON": 0.61, "ISK": 17.4,
}
CURRENCIES = ["EUR", "GBP", "USD", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "ISK", "CNY"]
CURRENCY_NAMES = {
    "EUR": "Euro", "GBP": "British pound", "USD": "US dollar", "CHF": "Swiss franc",
    "SEK": "Swedish krona", "NOK": "Norwegian krone", "DKK": "Danish krone", "PLN": "Polish złoty",
    "CZK": "Czech koruna", "HUF": "Hungarian forint", "RON": "Romanian leu", "ISK": "Icelandic króna",
    "CNY": "Chinese yuan",
}
SYMBOL = {c: f"{c} " for c in CURRENCIES} | {"EUR": "€", "GBP": "£", "USD": "$", "CNY": "¥"}

FX_URLS = [
    "https://api.frankfurter.app/latest?from=CNY&to={symbols}",
    "https://api.frankfurter.dev/v1/latest?base=CNY&symbols={symbols}",
]
FX_OK_TTL = 6 * 3600      # keep a live rate for 6 hours
FX_FAIL_TTL = 15 * 60     # after a failure, retry in 15 minutes (never block every page)

_fx = dict(FALLBACK_FX, CNY=1.0)
_fx_info = {"source": "sample rate (live rate not loaded)", "date": None, "live": False}
_fx_checked = None
_fx_lock = threading.Lock()


def refresh_fx(timeout=3):
    """Load live ECB rates if the cached ones are stale. Safe to call on every page."""
    global _fx_checked
    with _fx_lock:
        ttl = FX_OK_TTL if _fx_info["live"] else FX_FAIL_TTL
        if _fx_checked is not None and time.monotonic() - _fx_checked < ttl:
            return _fx_info
        _fx_checked = time.monotonic()
        symbols = ",".join(FALLBACK_FX)
        for url in FX_URLS:
            try:
                with urllib.request.urlopen(url.format(symbols=symbols), timeout=timeout) as r:
                    data = json.loads(r.read().decode())
                rates = {cur: float(v) for cur, v in data["rates"].items() if cur in FALLBACK_FX}
                if rates:
                    _fx.update(rates)
                    _fx_info.update(source="ECB", date=data.get("date"), live=True)
                    return _fx_info
            except Exception:
                continue
        if not _fx_info["live"]:
            _fx_info.update(source="sample rate (live ECB rate unavailable)", date=None)
        return _fx_info


def fx_rate(currency):
    return _fx[currency]


def fx_info():
    return dict(_fx_info)


# ---------------------------------------------------------------------------
# COUNTRIES: local currency, VAT %, duty region, shipping zone
# ---------------------------------------------------------------------------

COUNTRIES = {
    "Italy":          {"currency": "EUR", "vat": 22.0, "duty": "EU", "zone": "EU"},
    "Germany":        {"currency": "EUR", "vat": 19.0, "duty": "EU", "zone": "EU"},
    "France":         {"currency": "EUR", "vat": 20.0, "duty": "EU", "zone": "EU"},
    "Spain":          {"currency": "EUR", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "Portugal":       {"currency": "EUR", "vat": 23.0, "duty": "EU", "zone": "EU"},
    "Netherlands":    {"currency": "EUR", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "Sweden":         {"currency": "SEK", "vat": 25.0, "duty": "EU", "zone": "EU"},
    "Denmark":        {"currency": "DKK", "vat": 25.0, "duty": "EU", "zone": "EU"},
    "Poland":         {"currency": "PLN", "vat": 23.0, "duty": "EU", "zone": "EU"},
    "Czech Republic": {"currency": "CZK", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "Hungary":        {"currency": "HUF", "vat": 27.0, "duty": "EU", "zone": "EU"},
    "Romania":        {"currency": "RON", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "United Kingdom": {"currency": "GBP", "vat": 20.0, "duty": "UK", "zone": "UK"},
    "Switzerland":    {"currency": "CHF", "vat": 8.1,  "duty": "CH", "zone": "EFTA"},
    "Norway":         {"currency": "NOK", "vat": 25.0, "duty": "NO", "zone": "EFTA"},
    "Iceland":        {"currency": "ISK", "vat": 24.0, "duty": "IS", "zone": "IS"},
    "United States":  {"currency": "USD", "vat": 0.0,  "duty": "US", "zone": "US"},
}

# ---------------------------------------------------------------------------
# IMPORT DUTY % by catalog category and duty region (sample values, verify)
# Switzerland has no duty on industrial goods since 2024; Norway and Iceland
# charge none on most industrial goods (textiles can be an exception).
# A category missing here gives "not available", never a guessed rate.
# ---------------------------------------------------------------------------

DUTY_RATES = {
    "bags":              {"EU": 3.7, "UK": 4.0, "CH": 0.0, "NO": 8.0, "IS": 0.0, "US": 6.3},
    "drinkware":         {"EU": 3.2, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 3.4},
    "sports":            {"EU": 2.7, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 4.6},
    "lighting":          {"EU": 2.7, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 3.9},
    "ceramics":          {"EU": 12.0, "UK": 12.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 6.0},
    "phone accessories": {"EU": 2.7, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 3.4},
}
DUTY = DUTY_RATES  # categories list used by the paste-a-listing page

# ---------------------------------------------------------------------------
# SHIPPING China -> zone, CNY per chargeable kg (sample estimates)
# ---------------------------------------------------------------------------

MODES = ["express", "air", "rail", "sea"]
MODE_LABEL = {"sea": "Sea freight", "rail": "Rail freight", "air": "Air freight", "express": "Express courier"}
SHIPPING_CNY_PER_KG = {
    "sea":     {"EU": 1.5, "UK": 1.7, "EFTA": 1.8, "IS": 2.2, "US": 1.8},   # ~1500 CNY/m3 LCL
    "rail":    {"EU": 6,   "UK": 7,   "EFTA": 7,   "IS": None, "US": None},
    "air":     {"EU": 35,  "UK": 38,  "EFTA": 37,  "IS": 42,  "US": 40},
    "express": {"EU": 60,  "UK": 62,  "EFTA": 62,  "IS": 70,  "US": 65},
}
TRANSIT_DAYS = {"sea": "35–45", "rail": "18–25", "air": "7–12", "express": "4–7"}
VOLUMETRIC_DIVISOR = {"sea": 1000, "rail": 3000, "air": 6000, "express": 5000}  # cm3 per kg
# Smallest shipment each mode bills: sea LCL 1 m3, rail ~100 kg, air 45 kg break, express 0.5 kg
MIN_CHARGEABLE_KG = {"sea": 1000, "rail": 100, "air": 45, "express": 0.5}
# Broker fee per shipment; express couriers clear customs as part of the service
CLEARANCE_CNY = {"sea": 600.0, "rail": 600.0, "air": 600.0, "express": 0.0}

DOMESTIC_CHINA_CNY_PER_KG = 2.0     # supplier -> forwarder warehouse (real weight)
INSURANCE_PCT = 0.5                 # % of goods value


# ---------------------------------------------------------------------------
# CALCULATION
# ---------------------------------------------------------------------------

def unit_price_cny(tiers, qty):
    """Tiers [(min_qty, price_cny), ...] -> unit price for this quantity."""
    if not tiers:
        return None
    tiers = sorted(tiers)
    price = tiers[0][1]
    for min_q, p in tiers:
        if qty >= min_q:
            price = p
    return price


def _chargeable_kg(weight_kg, size_cm, mode):
    if not size_cm:
        return weight_kg
    l, w, h = size_cm
    return max(weight_kg, l * w * h / VOLUMETRIC_DIVISOR[mode])


def _sum(*vals):
    return None if any(v is None for v in vals) else sum(vals)


def _landed_cny(product, qty, country, mode):
    """All amounts in CNY. Returns None if the mode doesn't serve this country."""
    c = COUNTRIES[country]
    rate = SHIPPING_CNY_PER_KG[mode][c["zone"]]
    if rate is None:
        return None
    unit = unit_price_cny(product.get("tiers"), qty)
    goods = None if unit is None else unit * qty
    weight = product.get("weight_kg")

    if weight is None:
        shipping = charged_kg = None
    else:
        real_kg = _chargeable_kg(weight, product.get("size_cm"), mode) * qty
        charged_kg = max(real_kg, MIN_CHARGEABLE_KG[mode])
        shipping = charged_kg * rate + weight * qty * DOMESTIC_CHINA_CNY_PER_KG
    insurance = None if goods is None else goods * INSURANCE_PCT / 100
    clearance = CLEARANCE_CNY[mode]

    duty_pct = DUTY_RATES.get(product.get("category") or "", {}).get(c["duty"])
    if duty_pct is None or goods is None:
        duty = None
    elif c["duty"] == "US":                       # US: duty on goods value only
        duty = goods * duty_pct / 100
    else:                                         # elsewhere: on goods + freight + insurance
        base = _sum(goods, shipping, insurance)
        duty = None if base is None else base * duty_pct / 100
    vat_base = _sum(goods, shipping, insurance, duty, clearance)
    vat = None if vat_base is None else vat_base * c["vat"] / 100
    total = None if vat_base is None else vat_base + vat

    return dict(mode=mode, unit=unit, goods=goods, shipping=shipping, insurance=insurance,
                duty=duty, clearance=clearance, vat=vat, total=total, duty_pct=duty_pct,
                charged_kg=charged_kg, min_applied=charged_kg is not None
                and charged_kg == MIN_CHARGEABLE_KG[mode] and MIN_CHARGEABLE_KG[mode] > 0.5)


def available_modes(country):
    zone = COUNTRIES[country]["zone"]
    return [m for m in MODES if SHIPPING_CNY_PER_KG[m][zone] is not None]


def delivered(product, qty, country, currency=None, mode="auto"):
    """Delivered cost in `currency` (default: the country's). mode="auto" picks the
    cheapest mode for this order. Any value can be None = not available."""
    c = COUNTRIES[country]
    currency = currency or c["currency"]
    fx = _fx[currency]
    qty = max(1, int(qty))

    options = [r for r in (_landed_cny(product, qty, country, m) for m in available_modes(country)) if r]
    if mode != "auto":
        chosen = next((r for r in options if r["mode"] == mode), None)
    else:
        priced = [r for r in options if r["total"] is not None]
        chosen = min(priced, key=lambda r: r["total"]) if priced else None
    if chosen is None:
        chosen = options[0]  # no full price possible: still show the partial breakdown
        mode_known = False
    else:
        mode_known = True

    def conv(v):
        return None if v is None else v * fx

    notes = []
    if product.get("moq") is not None and qty < product["moq"]:
        notes.append(f"Quantity below the MOQ of {product['moq']:,}: the lowest listed tier price is used")
    if chosen["min_applied"]:
        notes.append(f"Small shipment: {MODE_LABEL[chosen['mode']].lower()} bills at least "
                     f"{MIN_CHARGEABLE_KG[chosen['mode']]:,.0f} kg")
    if product.get("weight_kg") is not None and not product.get("size_cm"):
        notes.append("Box size not available: volumetric weight not checked")
    if c["duty"] == "US":
        notes.append("US: state sales tax not included; extra tariffs on Chinese goods may apply")

    m = chosen["mode"]
    return dict(
        currency=currency, symbol=SYMBOL[currency], qty=qty, country=country,
        mode=m if mode_known else None, mode_label=MODE_LABEL[m], transit_days=TRANSIT_DAYS[m],
        unit_cny=chosen["unit"], below_moq=product.get("moq") is not None and qty < product["moq"],
        duty_pct=chosen["duty_pct"], duty_on_goods_only=c["duty"] == "US",
        vat_pct=c["vat"], tax_name="Sales tax (not included)" if c["duty"] == "US" else "VAT",
        product=conv(chosen["goods"]), shipping=conv(chosen["shipping"]),
        insurance=conv(chosen["insurance"]), duty=conv(chosen["duty"]),
        clearance=conv(chosen["clearance"]), vat=conv(chosen["vat"]), total=conv(chosen["total"]),
        per_unit=None if chosen["total"] is None else conv(chosen["total"]) / qty,
        product_per_unit=conv(chosen["unit"]),
        charged_kg=chosen["charged_kg"], notes=notes,
        fx_rate=fx, fx=fx_info(),
    )


def compare_modes(product, qty, country, currency=None):
    """Delivered cost for every mode serving the country, cheapest first (unknown last)."""
    out = [delivered(product, qty, country, currency, m) for m in available_modes(country)]
    return sorted(out, key=lambda d: d["total"] if d["total"] is not None else float("inf"))


# ---------------------------------------------------------------------------
# SUPPLIER SCORE
# ---------------------------------------------------------------------------

def supplier_score(s):
    """Sample reliability score 0-100 with the reasons behind it."""
    if not s:
        return None, [("No supplier data available", 0)]
    score = 50
    reasons = []

    def add(text, pts):
        nonlocal score
        score += pts
        reasons.append((text, pts))

    t = s.get("type")
    if t == "factory":
        add("Manufacturer (factory): direct source, fewer markups", 10)
    elif t == "store":
        add("Store / retailer: reseller, usually higher prices", 3)
    elif t == "middleman":
        add("Trading company / middleman: extra layer between you and the factory", -5)
    else:
        reasons.append(("Seller type: not available", 0))

    y = s.get("years")
    if y is None:
        reasons.append(("Years active: not available", 0))
    elif y >= 10:
        add(f"{y} years active", 15)
    elif y >= 5:
        add(f"{y} years active", 10)
    elif y >= 2:
        add(f"{y} years active", 4)
    else:
        add(f"Only {y} year(s) active", -5)

    badge_pts = {"Verified supplier": 8, "Trade assurance": 7, "Onsite inspection": 5,
                 "Brand official store": 8, "Platform self-operated": 10, "Source factory": 5,
                 "TrustPass member": 3}
    for b in s.get("badges") or []:
        if b in badge_pts:
            add(f"Badge: {b}", badge_pts[b])

    r = s.get("response_rate")
    if r is None:
        reasons.append(("Response rate: not available", 0))
    elif r >= 90:
        add(f"Response rate {r}%", 5)
    elif r < 75:
        add(f"Low response rate {r}%", -5)
    else:
        add(f"Response rate {r}%", 0)

    rb = s.get("repeat_buyer_rate")
    if rb is None:
        reasons.append(("Repeat buyer rate: not available", 0))
    elif rb >= 30:
        add(f"Repeat buyer rate {rb}%", 5)
    elif rb < 10:
        add(f"Low repeat buyer rate {rb}%", -3)
    else:
        add(f"Repeat buyer rate {rb}%", 0)

    d = s.get("disputes")
    if d is None:
        reasons.append(("Dispute history: not available", 0))
    elif d == "high":
        add("High dispute rate", -10)
    elif d == "medium":
        add("Some disputes reported", -3)
    else:
        add("Low dispute rate", 2)

    return max(0, min(100, score)), reasons


def score_colour(score):
    if score is None:
        return "#9E9E9E"
    if score >= 80:
        return "#2E7D32"
    if score >= 60:
        return "#F9A825"
    return "#C62828"


def score_label(score):
    if score is None:
        return "not available"
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"
