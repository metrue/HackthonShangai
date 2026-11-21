# SourceScan

Find a product on Chinese marketplaces (1688, Taobao, JD, Yiwugo) and see the **real delivered
price**: product + shipping + insurance + duty + customs + VAT, not the price on the original site.

> Demo: results come from a **sample catalog** (no scraping). Freight, duty and VAT are simplified
> sample estimates, labelled as such in the app; the exchange rate is the live ECB rate when
> available. Missing data is shown as "not available", never made up. Payments are simulated.

## The three sections (bar at the top of the home page)

| 🔗 Link paste | 🔎 Sourcing (default) | 💬 Messages |
|---|---|---|
| Paste a link: a link to a sample-catalog product opens its full analysis; for any other link, add a screenshot or the page text and the AI reads it | Search in any language → translated for Chinese marketplaces → Amazon-style list with delivered prices and supplier scores | Chat with suppliers in your language; they read business Chinese; replies are translated and explained |

From a product page: delivered price per shipping method (sea, rail, air, express) with the full
breakdown, supplier score with reasons, **Contact supplier**, and **Order** → checkout with a
simulated 30% deposit / 70% balance → order tracking.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

AI features (query translation, messages, reading screenshots) need an Anthropic API key; without
it the app still works and says "not available" where the AI would be used:

```toml
# .streamlit/secrets.toml (git-ignored)   or   export ANTHROPIC_API_KEY=...
ANTHROPIC_API_KEY = "sk-ant-..."
```

One model for every AI feature: `claude-opus-5-5` (change `MODEL` in `core/ai.py`).

## Tests

```bash
pip install pytest
python -m pytest
```

The tests simulate the AI and never call the network.

## Code layout

```
app.py                 page setup + router
core/                  business logic, no UI
  catalog.py           sample catalog (data/catalog.json), search, demo links
  pricing.py           delivered price: ECB rates, shipping modes, duty, VAT
  supplier_score.py    supplier reliability score (sample rules; replace with the real model)
  ai.py                the one Anthropic API wrapper ("not available" reasons instead of errors)
  query_translation.py search -> Chinese buyer query
  messages.py          chat: outgoing translation, simulated supplier, reply analysis, deal terms
  listing.py           Link paste: AI reading of screenshot/text + rule-based fallback
  orders.py            orders and the simulated payment flow
components/            app state + URL, CSS, shared UI pieces
views/                 one module per page (home, results, product, link_paste, messages, checkout, compare)
data/catalog.json      20 sample products
tests/                 pytest suite
```

Conversations and orders are saved to `conversations.json` / `orders.json` (git-ignored) so the
demo survives a page reload.
