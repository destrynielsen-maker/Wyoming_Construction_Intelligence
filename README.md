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

**City of Gillette — EnerGov Permit Points (ArcGIS)**

The City of Gillette exposes a public ArcGIS feature layer synchronized from EnerGov with permit number, type, status, address, valuation, square footage, description, applied date, issue date, owner, and a direct Citizen Self Service link.

The collector retains a rolling ~18 months of issued permits to keep the working dataset prospecting-focused while persistent history can grow over time.

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
