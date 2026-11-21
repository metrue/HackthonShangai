"""Read listings from Yiwugo's public search (PR #1, Minghe Huang).

sellPrice on the search API is fen: 640 is ¥6.40 on the product page.
Fields the listing does not include stay None so the app can show "not available".

NOTE: this reads Yiwugo's website search endpoints, not an official API. It can stop
working whenever Yiwugo changes its site, and automated access may conflict with
Yiwugo's terms. Turn it off with the environment variable YIWUGO_LIVE=0: the app then
uses only the sample catalog.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def enabled() -> bool:
    """Live Yiwugo search is on unless YIWUGO_LIVE is 0 / false / off / no."""
    return os.getenv("YIWUGO_LIVE", "1").strip().lower() not in {"0", "false", "off", "no"}


def yuan_from_fen(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        yuan = round(float(value) / 100.0, 2)
    except (TypeError, ValueError):
        return None
    if yuan <= 0:
        return None
    return yuan


def _get(url: str, headers: dict | None = None, opener=None, timeout: int = 8) -> str:
    req_headers = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
    if headers:
        req_headers.update(headers)
    request = urllib.request.Request(url, headers=req_headers)
    open_fn = opener.open if opener else urllib.request.urlopen
    with open_fn(request, timeout=timeout) as response:
        return response.read(120000).decode("utf-8", "replace")


def _is_ad(item: dict) -> bool:
    return str(item.get("isAd")).lower() in {"1", "true"}


def _attr(attrs: dict, names: tuple[str, ...]) -> str | None:
    for name in names:
        value = attrs.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def listing_from_api(item: dict, detail: dict | None) -> dict | None:
    """Catalog-shaped product. None when the search row has no positive price."""
    price = yuan_from_fen(item.get("sellPrice"))
    product_id = item.get("id")
    if price is None or not product_id:
        return None
    try:
        moq = int(item["startNum"]) if item.get("startNum") is not None else None
    except (TypeError, ValueError):
        moq = None
    attrs: dict[str, str] = {}
    years = None
    tiers: list[tuple[int, float]] = []
    if detail:
        inner = detail.get("detail") or {}
        for row in inner.get("productExtendList") or []:
            name = str(row.get("name") or "").strip()
            value = str(row.get("value") or "").strip()
            if name and value and name not in attrs:
                attrs[name] = value
        if detail.get("years") not in (None, ""):
            try:
                years = int(detail["years"])
            except (TypeError, ValueError):
                years = None
        for row in inner.get("sdiProductsPriceList") or []:
            fen = row.get("conferPrice")
            if fen in (None, 0, "0"):
                fen = row.get("sellPrice")
            yuan = yuan_from_fen(fen)
            if yuan is None:
                continue
            start = row.get("startNumber") or moq or 1
            try:
                start = int(start)
            except (TypeError, ValueError):
                start = moq or 1
            tiers.append((start, yuan))
    if not tiers:
        tiers = [(moq or 1, price)]
    title = str(item.get("title") or "").strip() or None
    shop = str(item.get("shopName") or "").strip() or None
    picture = str(item.get("picture1") or "").strip() or None
    return {
        "id": f"yw-{product_id}",
        "live": True,
        "platform": "Yiwugo",
        "category": None,
        "title_en": None,
        "title_cn": title,
        "keywords": title or "",
        "moq": moq,
        "tiers": tiers,
        "material": _attr(attrs, ("材质", "购物篮材质")),
        "size": _attr(attrs, ("尺寸", "规格", "尺码")),
        "weight_kg": None,
        "production_days": None,
        "customisation": _attr(attrs, ("加印LOGO", "加工定制")),
        "picture": picture,
        "url": f"https://www.yiwugo.com/product/detail/{product_id}.html",
        "supplier": {
            "name": shop,
            "name_cn": shop,
            "city": None,
            "type": None,
            "years": years,
            "badges": [],
            "response_rate": None,
            "repeat_buyer_rate": None,
            "disputes": None,
        },
    }


def _detail(product_id: str, csrf: str, referer: str) -> dict | None:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    raw = _get(
        f"https://www.yiwugo.com/api/product/detail.htm?productId={product_id}",
        headers={"Referer": referer, "x-csrf-token": csrf, "Accept": "application/json"},
        opener=opener,
    )
    content = json.loads(raw).get("content")
    return content if isinstance(content, dict) else None


def search(query: str, limit: int = 8) -> list[dict]:
    """Priced listings from the first page of Yiwugo search, in the site's order."""
    query = (query or "").strip()
    if not query:
        return []
    page = "https://www.yiwugo.com/search?q=" + urllib.parse.quote(query)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    html = _get(page, opener=opener)
    match = re.search(r'"csrf":"([^"]+)"', html)
    if not match:
        return []
    csrf = match.group(1)
    api = "https://www.yiwugo.com/api/search/s.htm?" + urllib.parse.urlencode({
        "q": query,
        "appid": "6",
        "cpage": "1",
        "pageSize": "20",
        "checkLabel": "1",
        "searchMethod": "embedding",
        "source": "pc",
    })
    raw = _get(
        api,
        headers={"Referer": page, "x-csrf-token": csrf, "Accept": "application/json"},
        opener=opener,
    )
    items = (json.loads(raw).get("content") or {}).get("prslist") or []
    chosen = []
    for item in items:
        if _is_ad(item) or yuan_from_fen(item.get("sellPrice")) is None:
            continue
        chosen.append(item)
        if len(chosen) >= limit:
            break
    details: dict[str, dict | None] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {
            str(item["id"]): pool.submit(_detail, str(item["id"]), csrf, page)
            for item in chosen
        }
        for pid, job in jobs.items():
            try:
                details[pid] = job.result()
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
                details[pid] = None
    offers = []
    for item in chosen:
        offer = listing_from_api(item, details.get(str(item["id"])))
        if offer:
            offers.append(offer)
    return offers
