# SourceScan

Skyscanner-style search for Chinese sourcing platforms (1688, Taobao, JD, Yiwugo).
Every price is shown **delivered** (product + shipping + duty + VAT), not the price on the original site.

> Demo: results come from a **sample catalog**. Freight, duty, VAT and exchange rates are simplified
> sample assumptions and are labelled as estimates in the app. Missing data is shown as "not available".

## Pages

- **Home / Search** – what you need, quantity, optional max budget per unit, delivery country
- **Results** – sort by lowest delivered price / highest reliability / lowest MOQ; sidebar filters
  (platform, seller type, minimum score, maximum MOQ); select 2–3 products to compare
- **Product detail** – product specs and price tiers, delivered-price breakdown with editable quantity,
  supplier score with reasons, ready-to-send Chinese message + English translation
- **Compare** – side-by-side table of delivered price, MOQ, lead time and score
- **Paste a listing** – paste listing text, click Analyze, get the same product page

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## AI query translation (optional)

With an Anthropic API key, each search is rewritten the way a Chinese buyer would type it
(e.g. "borsa di tela con logo" -> `帆布袋定制logo`), with alternatives, tips for suppliers and live
search links for 1688 / Taobao / JD. Searches in Italian, German, French… also match the catalog.
Without a key the app works as before and shows "Chinese query: not available".

Set the key in one of these ways (never commit it):

```bash
# environment variable
export ANTHROPIC_API_KEY=sk-ant-...
# or .streamlit/secrets.toml (already in .gitignore)
ANTHROPIC_API_KEY = "sk-ant-..."
```

One API call per distinct search per day (results are cached), model `claude-sonnet-5-5`.

## Files

- `app.py` – Streamlit UI and navigation
- `catalog.py` – sample product catalog and search
- `pricing.py` – delivered-price model and supplier score
- `listing_parser.py` – rule-based extraction from pasted listing text
- `translation_agent.py` – AI query translation for Chinese marketplaces (optional, needs an API key)
