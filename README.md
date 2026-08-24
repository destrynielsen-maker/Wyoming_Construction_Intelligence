# Wyoming Construction Intelligence

Public building-permit prospecting for Wyoming, focused on new:

- single-family construction
- multifamily / apartments / townhomes / duplexes
- commercial and industrial construction

The project follows the same operating model as Utah, Idaho, and Colorado Construction Intelligence:

- scheduled public-data collection
- persistent permit history
- new-construction classification and opportunity scoring
- source-health monitoring
- sortable/filterable browser dashboard
- builder / GC rollups
- RSS feeds
- GitHub Actions + GitHub Pages

## Initial automated source

**Laramie County — monthly Building Permits Issued with Valuations reports**

Laramie County Planning & Development publishes official monthly permit reports organized by classification and purpose. The reports provide permit number, site address, date issued, and valuation, including explicit categories such as `COMMERCIAL NEW CONSTRUCTION` and `RESIDENTIAL NEW SINGLE FAMILY`.

The collector discovers current-year monthly reports from the official county page, uses verified direct report URLs as fallback, and validates each PDF contains the expected Laramie County identity before accepting any records.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m wyoming_permits.main
python -m http.server 8000 -d public
```

## GitHub Pages

Set **Settings → Pages → Source → GitHub Actions**.

The workflow runs every six hours, manually, and automatically after code changes reach `main`.
