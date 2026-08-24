from __future__ import annotations
from datetime import datetime, timezone, timedelta
import requests
from .base import CollectionResult, new_session
from ..models import Permit

class GilletteCollector:
    name = "Gillette"
    freshness_days = 14
    layer_url = "https://services1.arcgis.com/t1pOARESVtLutuqb/arcgis/rest/services/Energov_Permit_Points/FeatureServer/0"
    query_url = layer_url + "/query"
    source_url = layer_url
    fields = ["Permit", "Type", "Prefix", "Status_1", "PIN", "Address", "District", "VALUE", "SqFt", "DESCRIPTION", "APPLYDATE", "ISSUEDATE", "PMPERMITID", "Owner", "CSS_url"]

    def collect(self, session: requests.Session | None = None) -> CollectionResult:
        session = session or new_session(); permits: list[Permit] = []; offset = 0; page_size = 2000
        cutoff = (datetime.now(timezone.utc) - timedelta(days=550)).date().isoformat()
        while True:
            params = {"where": "ISSUEDATE IS NOT NULL", "outFields": ",".join(self.fields), "returnGeometry": "false", "orderByFields": "ISSUEDATE DESC", "resultOffset": offset, "resultRecordCount": page_size, "f": "json"}
            response = session.get(self.query_url, params=params, timeout=60); response.raise_for_status(); payload = response.json()
            if "error" in payload: raise RuntimeError(f"Gillette ArcGIS error: {payload['error']}")
            features = payload.get("features", [])
            if not features: break
            for feature in features:
                permit = self._from_attributes(feature.get("attributes", {}))
                if not permit: continue
                if permit.issued_date < cutoff:
                    return CollectionResult(self.name, permits, self.layer_url, "Official City of Gillette EnerGov Permit Points ArcGIS layer; rolling ~18 months")
                permits.append(permit)
            if len(features) < page_size: break
            offset += len(features)
            if offset > 100_000: raise RuntimeError("Gillette pagination safety limit exceeded")
        return CollectionResult(self.name, permits, self.layer_url, "Official City of Gillette EnerGov Permit Points ArcGIS layer; rolling ~18 months")

    def _from_attributes(self, a: dict) -> Permit | None:
        issued = self._date(a.get("ISSUEDATE")); number = str(a.get("Permit") or "").strip()
        if not issued or not number: return None
        description = str(a.get("DESCRIPTION") or "").strip(); permit_type = str(a.get("Type") or "").strip(); prefix = str(a.get("Prefix") or "").strip(); district = str(a.get("District") or "").strip(); css_url = str(a.get("CSS_url") or "").strip()
        return Permit(state="WY", jurisdiction=self.name, permit_number=number, issued_date=issued, permit_type=permit_type, building_use=prefix or district or None, project_name=description or None, address=str(a.get("Address") or "").strip(), valuation=self._number(a.get("VALUE")), owner=str(a.get("Owner") or "").strip() or None, status=str(a.get("Status_1") or "").strip() or None, source_name="City of Gillette EnerGov Permit Points", source_url=css_url or self.layer_url, raw={**a, "description": description, "prefix": prefix, "district": district, "sqft": self._number(a.get("SqFt")), "pin": a.get("PIN"), "applied_date": self._date(a.get("APPLYDATE"))})

    @staticmethod
    def _date(value):
        if value in (None, ""): return None
        try: return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).date().isoformat()
        except (TypeError, ValueError, OSError): return None
    @staticmethod
    def _number(value):
        if value in (None, ""): return None
        try: return float(str(value).replace("$", "").replace(",", "").strip())
        except ValueError: return None
