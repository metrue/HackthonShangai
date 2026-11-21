"""Orders with a SIMULATED payment flow (no real money, no card data is ever asked for).

Flow, as in real China sourcing: 30% deposit -> production -> 70% balance before
shipping -> shipped. Amounts are the delivered price split into what is paid to the
supplier (product, 30/70) and what is paid on arrival (shipping, duty, VAT, customs).
Orders are kept in orders.json for the demo, like conversations.
"""

import json
import os
import time
import uuid

STORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "orders.json")

DEPOSIT_PCT = 30

STEPS = [
    ("placed", "Order placed"),
    ("deposit_paid", "Deposit paid · production started"),
    ("production_done", "Production finished · balance due"),
    ("balance_paid", "Balance paid · ready to ship"),
    ("shipped", "Shipped"),
]
STATUS_LABEL = dict(STEPS)


def new_order(product, qty, country, currency, d, unit_price_cny, negotiated, conv_id=None):
    """d = pricing.delivered() result computed with unit_price_cny."""
    supplier_part = d["product"]                      # paid to the supplier, 30/70
    on_arrival = None if d["total"] is None else d["total"] - d["product"]
    deposit = None if supplier_part is None else supplier_part * DEPOSIT_PCT / 100
    return {
        "id": "SO-" + uuid.uuid4().hex[:6].upper(),
        "pid": product["id"],
        "product": product.get("title_en"),
        "platform": product.get("platform"),
        "supplier": (product.get("supplier") or {}).get("name"),
        "qty": qty, "country": country, "currency": currency,
        "unit_price_cny": unit_price_cny, "negotiated": negotiated, "conv": conv_id,
        "mode_label": d["mode_label"], "transit_days": d["transit_days"],
        "lead_days": product.get("production_days"),
        "supplier_total": supplier_part, "deposit": deposit,
        "balance": None if supplier_part is None else supplier_part - deposit,
        "on_arrival": on_arrival, "total": d["total"], "per_unit": d["per_unit"],
        "status": "placed", "payments": [],
        "history": [("placed", time.time())],
        "created": time.time(),
    }


def _pay(order, what, amount):
    order["payments"].append({"what": what, "amount": amount, "currency": order["currency"],
                              "ref": "SIM-" + uuid.uuid4().hex[:8].upper(), "ts": time.time()})


def pay_deposit(order):
    if order["status"] == "placed":
        _pay(order, f"Deposit ({DEPOSIT_PCT}%)", order["deposit"])
        _advance(order, "deposit_paid")
    return order


def finish_production(order):
    """Demo control: the supplier reports production finished."""
    if order["status"] == "deposit_paid":
        _advance(order, "production_done")
    return order


def pay_balance(order):
    if order["status"] == "production_done":
        _pay(order, f"Balance ({100 - DEPOSIT_PCT}%)", order["balance"])
        _advance(order, "balance_paid")
    return order


def ship(order):
    """Demo control: the supplier hands the goods to the forwarder."""
    if order["status"] == "balance_paid":
        _advance(order, "shipped")
    return order


def _advance(order, status):
    order["status"] = status
    order["history"].append((status, time.time()))


def paid_total(order):
    return sum(p["amount"] or 0 for p in order["payments"])


def load_orders():
    try:
        with open(STORE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_orders(orders):
    try:
        tmp = STORE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=1)
        os.replace(tmp, STORE)
    except OSError:
        pass
