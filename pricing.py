"""Delivered-price model and supplier score.

All rates below are SAMPLE assumptions for a demo. They are simplified and
must not be used as customs, tax or freight quotes.
"""

# Sample exchange rates: units of local currency per 1 CNY
FX = {"EUR": 0.128, "GBP": 0.109, "USD": 0.139, "CAD": 0.193, "AUD": 0.213}
SYMBOL = {"EUR": "€", "GBP": "£", "USD": "$", "CAD": "C$", "AUD": "A$"}

# region: used for duty lookup. duty_base: "CIF" = product + shipping, "FOB" = product only
COUNTRIES = {
    "Italy":          dict(currency="EUR", region="EU", vat=0.22, tax_name="VAT", duty_base="CIF", freight_cny_kg=42),
    "Germany":        dict(currency="EUR", region="EU", vat=0.19, tax_name="VAT", duty_base="CIF", freight_cny_kg=40),
    "France":         dict(currency="EUR", region="EU", vat=0.20, tax_name="VAT", duty_base="CIF", freight_cny_kg=41),
    "Spain":          dict(currency="EUR", region="EU", vat=0.21, tax_name="VAT", duty_base="CIF", freight_cny_kg=42),
    "Netherlands":    dict(currency="EUR", region="EU", vat=0.21, tax_name="VAT", duty_base="CIF", freight_cny_kg=40),
    "United Kingdom": dict(currency="GBP", region="UK", vat=0.20, tax_name="VAT", duty_base="CIF", freight_cny_kg=44),
    "United States":  dict(currency="USD", region="US", vat=0.00, tax_name="Sales tax (not included)", duty_base="FOB", freight_cny_kg=46),
    "Canada":         dict(currency="CAD", region="CA", vat=0.05, tax_name="GST", duty_base="FOB", freight_cny_kg=50),
    "Australia":      dict(currency="AUD", region="AU", vat=0.10, tax_name="GST", duty_base="CIF", freight_cny_kg=52),
}

# Sample import duty rates by category and region (simplified, not legal advice)
DUTY = {
    "bags":              dict(EU=0.037, UK=0.04, US=0.176, CA=0.155, AU=0.05),
    "drinkware":         dict(EU=0.032, UK=0.04, US=0.034, CA=0.065, AU=0.05),
    "phone accessories": dict(EU=0.027, UK=0.02, US=0.034, CA=0.065, AU=0.05),
    "sports":            dict(EU=0.027, UK=0.02, US=0.046, CA=0.07, AU=0.05),
    "ceramics":          dict(EU=0.12, UK=0.12, US=0.06, CA=0.07, AU=0.05),
    "lighting":          dict(EU=0.037, UK=0.02, US=0.039, CA=0.07, AU=0.05),
}

DOMESTIC_CHINA_CNY_KG = 2.0   # supplier -> consolidation warehouse
HANDLING_CNY = 150.0          # per shipment: export handling, paperwork


def unit_price_cny(tiers, qty):
    """Price per unit for a quantity, from the tier table (sorted by min qty)."""
    if not tiers:
        return None
    tiers = sorted(tiers)
    price = tiers[0][1]
    for min_q, p in tiers:
        if qty >= min_q:
            price = p
    return price


def delivered(product, qty, country):
    """Return a dict of cost lines in local currency. None = not available."""
    c = COUNTRIES[country]
    fx = FX[c["currency"]]
    qty = max(1, int(qty))
    unit_cny = unit_price_cny(product.get("tiers"), qty)
    weight = product.get("weight_kg")
    duty_rate = DUTY.get(product.get("category") or "", {}).get(c["region"])

    product_cny = unit_cny * qty if unit_cny is not None else None
    shipping_cny = (
        qty * weight * (c["freight_cny_kg"] + DOMESTIC_CHINA_CNY_KG) + HANDLING_CNY
        if weight is not None else None
    )
    if product_cny is None or duty_rate is None:
        duty_cny = None
    elif c["duty_base"] == "CIF":
        duty_cny = duty_rate * (product_cny + shipping_cny) if shipping_cny is not None else None
    else:
        duty_cny = duty_rate * product_cny
    if None in (product_cny, shipping_cny, duty_cny):
        vat_cny = None
    else:
        vat_cny = c["vat"] * (product_cny + shipping_cny + duty_cny)
    parts = (product_cny, shipping_cny, duty_cny, vat_cny)
    total_cny = sum(parts) if None not in parts else None

    def conv(v):
        return None if v is None else v * fx

    return dict(
        currency=c["currency"], symbol=SYMBOL[c["currency"]], qty=qty,
        unit_cny=unit_cny, duty_rate=duty_rate, vat_rate=c["vat"], tax_name=c["tax_name"],
        duty_base=c["duty_base"], freight_cny_kg=c["freight_cny_kg"],
        below_moq=(product.get("moq") is not None and qty < product["moq"]),
        product=conv(product_cny), shipping=conv(shipping_cny), duty=conv(duty_cny),
        vat=conv(vat_cny), total=conv(total_cny),
        per_unit=None if total_cny is None else conv(total_cny) / qty,
        product_per_unit=None if unit_cny is None else conv(unit_cny),
    )


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
