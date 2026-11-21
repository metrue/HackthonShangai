"""Reliability score, 0-100, from the shop facts a listing actually includes.

Each fact is scored 0-100 on its own. The result is the weighted average of the
facts that are present. A missing fact is listed as "not available" and left out
of the average. Nothing here is filled in.

Yiwugo integrity points are Yiwugo's own total. This file scales 20,000 points to
100 so they can sit beside the other facts. That scale is ours, not Yiwugo's grade.
"""

BADGE_POINTS = {"Verified supplier": 8, "Trade assurance": 7, "Onsite inspection": 5,
                "Brand official store": 8, "Platform self-operated": 10, "Source factory": 5,
                "TrustPass member": 3}

# weight of each fact in the average
W_YEARS = 18
W_TYPE = 8
W_INTEGRITY = 22
W_LICENSE = 8
W_INVOICE = 6
W_REFUND = 6
W_FACTORY = 6
W_BOOTH = 8
W_REVIEWS = 14
W_DEALS = 12
W_UNITS = 8
W_ONLINE = 4
W_BADGES = 10
W_RESPONSE = 10
W_REPEAT = 8
W_DISPUTES = 12

INTEGRITY_FULL = 20000  # our scale: this many Yiwugo points = 100
MIN_KNOWN_FACTORS = 2


def _years_score(years):
    return max(0, min(100, round(years / 12 * 100)))


def _integrity_score(points):
    return max(0, min(100, round(points / INTEGRITY_FULL * 100)))


def _deal_score(n):
    if n <= 0:
        return 30
    if n < 50:
        return 45
    if n < 200:
        return 60
    if n < 1000:
        return 75
    return 90


def _repeat_score(rate):
    if rate >= 40:
        return 90
    if rate >= 25:
        return 75
    if rate >= 10:
        return 55
    return 35


def _badge_score(badges):
    raw = sum(BADGE_POINTS.get(b, 0) for b in badges)
    if raw <= 0:
        return 40
    return max(0, min(100, raw * 4))


def supplier_score(s):
    """Return (score or None, [(reason, factor_score or None), ...]).

    factor_score is that fact's own 0-100 mark. None means the fact was missing
    and was not part of the average. The score is None when fewer than two facts
    are present, so a bare shop name does not become a middling 50.
    """
    if not s:
        return None, [("No supplier data available", None)]
    reasons = []
    weighted = 0.0
    weight = 0

    def add(text, factor, w):
        nonlocal weighted, weight
        reasons.append((text, factor))
        if factor is None:
            return
        weighted += factor * w
        weight += w

    years = s.get("years")
    if years is None:
        add("Years on the platform: not available", None, W_YEARS)
    else:
        mark = _years_score(years)
        add(f"Years on the platform: {years} → {mark}/100", mark, W_YEARS)

    kind = s.get("type")
    type_mark = {"factory": 85, "store": 65, "middleman": 40}.get(kind)
    if type_mark is None:
        add("Seller type: not available", None, W_TYPE)
    else:
        add(f"Seller type: {kind} → {type_mark}/100", type_mark, W_TYPE)

    points = s.get("integrity_points")
    if points is None:
        add("Yiwugo integrity points: not available", None, W_INTEGRITY)
    else:
        mark = _integrity_score(points)
        add(f"Yiwugo integrity points: {points:,} → {mark}/100 on our scale "
            f"({INTEGRITY_FULL:,} points = 100)", mark, W_INTEGRITY)

    _flag(add, "Shop license", s.get("license_on_file"), W_LICENSE, "on file", "not confirmed", 100, 35)
    _flag(add, "Invoices", s.get("invoice"), W_INVOICE, "offered", "not offered", 100, 40)
    _flag(add, "Quick refund", s.get("quick_refund"), W_REFUND, "offered", "not offered", 100, 45)
    _flag(add, "Factory address", s.get("factory_on_file"), W_FACTORY, "on file", "not on file", 100, 40)

    booth = s.get("market_booth")
    if booth:
        shown = booth if len(booth) <= 42 else booth[:42] + "…"
        add(f"Wholesale booth: {shown} → 100/100", 100, W_BOOTH)
    else:
        add("Wholesale booth: not available", None, W_BOOTH)

    avg = s.get("review_avg")
    if avg is None:
        add("Review average: not available", None, W_REVIEWS)
    else:
        mark = max(0, min(100, round(avg / 5 * 100)))
        add(f"Review average: {avg:g}/5 → {mark}/100", mark, W_REVIEWS)

    deals = s.get("listing_deals")
    if deals is None:
        add("Completed deals on this listing: not available", None, W_DEALS)
    else:
        mark = _deal_score(deals)
        add(f"Completed deals on this listing: {deals:,} → {mark}/100", mark, W_DEALS)

    units = s.get("listing_units_sold")
    if units is None:
        add("Units sold on this listing: not available", None, W_UNITS)
    else:
        mark = _deal_score(units)
        add(f"Units sold on this listing: {units:,} → {mark}/100", mark, W_UNITS)

    _flag(add, "Online ordering", s.get("online_order"), W_ONLINE, "offered", "not offered", 80, 50)

    badges = s.get("badges")
    if not badges:
        add("Badges: not available", None, W_BADGES)
    else:
        mark = _badge_score(badges)
        add(f"Badges: {', '.join(badges)} → {mark}/100", mark, W_BADGES)

    response = s.get("response_rate")
    if response is None:
        add("Response rate: not available", None, W_RESPONSE)
    else:
        mark = max(0, min(100, round(response)))
        add(f"Response rate: {response:g}% → {mark}/100", mark, W_RESPONSE)

    repeat = s.get("repeat_buyer_rate")
    if repeat is None:
        add("Repeat buyers: not available", None, W_REPEAT)
    else:
        mark = _repeat_score(repeat)
        add(f"Repeat buyers: {repeat:g}% → {mark}/100", mark, W_REPEAT)

    disputes = s.get("disputes")
    dispute_mark = {"low": 90, "medium": 55, "high": 20}.get(disputes)
    if dispute_mark is None:
        add("Dispute history: not available", None, W_DISPUTES)
    else:
        add(f"Dispute history: {disputes} → {dispute_mark}/100", dispute_mark, W_DISPUTES)

    known = sum(1 for _, factor in reasons if factor is not None)
    if known < MIN_KNOWN_FACTORS or weight == 0:
        return None, [("Not enough supplier data to score this seller yet", None)] + reasons
    return round(weighted / weight), reasons


def _flag(add, label, value, w, yes, no, yes_mark, no_mark):
    if value is True:
        add(f"{label}: {yes} → {yes_mark}/100", yes_mark, w)
    elif value is False:
        add(f"{label}: {no} → {no_mark}/100", no_mark, w)
    else:
        add(f"{label}: not available", None, w)


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
