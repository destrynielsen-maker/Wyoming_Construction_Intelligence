# Wyoming Permit / Prospecting Source Directory

This is the rep-facing source directory. Use permit sources to confirm that construction is actually moving; use planning/development sources to identify projects earlier in the sales cycle.

| Market | Direct source | Type / rep use |
|---|---|---|
| **Gillette** | https://www.gillettewy.gov/Departments/Development-Services | EnerGov Citizen Self Service for permit/plan searches. Strong citywide permit and development research. |
| **Cheyenne** | https://www.cheyennecity.org/Your-Government/Departments/Compliance-Department/Building-Permitting-Licensing | City Building Safety page links to OpenGov. Public search can be used to research building permit records by address. |
| **Cheyenne OpenGov** | https://cheyennewy.viewpointcloud.com/ | Public permit / planning portal. Useful for known-address or project research and early planning applications. |
| **Laramie County — monthly permit reports** | https://www.laramiecountywy.gov/County-Government/County-Departments/Planning-Development | **Primary automated source.** Official monthly Building Permits Issued with Valuations reports, organized by classification/purpose with permit number, site address, issue date and valuation. |
| **Laramie County — SmartGov** | https://co-laramie-wy.smartgovcommunity.com/Public/Home | Permit center for permit printouts, status and parcel/project research; useful after a monthly report identifies a prospect. |
| **City of Laramie** | https://www.cityoflaramie.org/211/Building-Department-Code-Administration | Building department links to Civic Access for permit searches. |
| **City of Laramie — reports** | https://www.cityoflaramie.org/1161/Building-Department-Reports | Monthly building snapshots and annual permit reports. Good market pulse. |
| **City of Laramie — planning** | https://cityoflaramie.org/223/Application-Information-Fees-Submittal-S | Current planning projects plus Civic Access. Use this before building permits to catch projects earlier. |
| **Casper** | https://eg.casperwy.gov/EnerGov_Prod/selfservice/City%20of%20Casper | EnerGov Citizen Self Service. Public permit/project research. |
| **Teton County / Jackson Hole** | https://co-teton-wy.smartgovcommunity.com/Public/Home | SmartGov permit/property research. High-value residential and commercial market. |
| **Teton County records** | https://www.tetoncountywy.gov/1199/Planning-Building-Records | Official instructions for finding building and planning records via SmartGov and GIS. |
| **Teton County activity archive** | https://www.tetoncountywy.gov/Archive.aspx?AMID=55 | Building Permit Activity reports archive. Useful for historical / trend work; verify recency before prospecting. |
| **Teton County planning** | https://www.tetoncountywy.gov/559/Planning | Current projects and planning application materials; one of the best early-project sources in the state. |
| **Sheridan** | https://www.sheridanwy.gov/government/building | Permit & Licensing Portal and building information. |
| **Sheridan planning** | https://www.sheridanwy.gov/government/planning/development_process_information | OpenGov planning applications and development process information. |
| **Campbell County** | https://www.campbellcountywy.gov/284/Public-Works | County Building, Planning & Zoning information for territory outside Gillette. |

## Recommended rep routine

### Southeast Wyoming
Cheyenne → Laramie County → City of Laramie

### Northeast Wyoming
Gillette → Campbell County → Sheridan

### Central Wyoming
Casper / Natrona market

### High-value resort / custom market
Teton County / Jackson Hole

Capture:

`project → permit → address → owner/developer → builder/GC → units → valuation → issue date → source link`

Treat multiple permits by one builder in one development as one account opportunity, not unrelated leads.

### Town of Jackson public report replay (disabled research only)

The Town's [public report menu](https://twn-jackson-wy.smartgovcommunity.com/Public/ReportsView)
offers **Issued Permits By Department**, with two dates and no login.
The report includes records submitted **or** issued in the period, and repeat
review cycles, not a complete count of new-building issuances by itself.
It is a separate issuer from unincorporated Teton County.

Supply an official PDF saved separately. Poppler `pdftotext` must be installed.
The opt-in CLI does not fetch, store or publish permits and is not registered:

```sh
PYTHONPATH=src python -m wyoming_permits.jackson_town_issued_preview /path/to/report.pdf --start 2026-11-16 --end 2026-11-22
```

Two official PDFs were retrieved through the public report form URLs and
replayed offline on Nov 26, 2026. Nov 9–15: 18 building detail rows / 16 IDs /
5 distinct in-window issued IDs (three addenda, one plumbing, one mechanical);
no new-building candidates. Nov 16–22: 21 rows / 17 IDs / 14 distinct in-window
issued IDs through Nov 20. B26-0204 and B26-0205 each repeat three cycles and
were each recorded once as manual-review-only new single-family candidates,
issued Nov 17. No contractor column or inferred contractor; no sales leads
automatically qualified. No raw source data is included in the repository.
Both five/six-page PDFs were roughly 86 MB. This is not a validation of scheduled
transport, longer windows, every report layout, or production coverage.
