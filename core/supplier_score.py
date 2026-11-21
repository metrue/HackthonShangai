"""Supplier reliability score, 0-100, with the reasons behind it.

SAMPLE rule-based rating for the demo. Starts at 50 and adds or removes points:
  seller type   factory +10, store +3, middleman -5
  years active  >=10 +15, >=5 +10, >=2 +4, <2 -5
  badges        verified +8, trade assurance +7, onsite inspection +5, brand store +8,
                platform self-operated +10, source factory +5, TrustPass +3
  response rate >=90% +5, <75% -5
  repeat buyers >=30% +5, <10% -3
  disputes      high -10, medium -3, low +2
Missing data scores 0 and is listed as "not available". Clamped to 0-100.
Replace supplier_score() with the real model when it is ready: the UI only uses
supplier_score(), score_colour() and score_label().
"""

BADGE_POINTS = {"Verified supplier": 8, "Trade assurance": 7, "Onsite inspection": 5,
                "Brand official store": 8, "Platform self-operated": 10, "Source factory": 5,
                "TrustPass member": 3}


def supplier_score(s):
    """Return (score or None, [(reason, points), ...])."""
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

    for b in s.get("badges") or []:
        if b in BADGE_POINTS:
            add(f"Badge: {b}", BADGE_POINTS[b])

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
