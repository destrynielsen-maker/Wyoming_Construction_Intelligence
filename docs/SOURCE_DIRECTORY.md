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

## Teton County, WY — public application preview (not a production feed)

The [County archive](https://www.tetoncountywy.gov/Archive.aspx?AMID=55) labels its
monthly activity PDFs **Date Submitted**, not **Date Issued**. The reports have
an owner column and do not identify a contractor. Neither owner nor address /
free-text description is included in this pilot. This is not Town of Jackson
coverage. The [Town permit portal](https://twn-jackson-wy.smartgovcommunity.com/Public/Home)
requests registration for permit activity; no automated collection from it was
attempted. The Town's [official planning register](https://jacksonwy.gov/m/newsflash/Home/Detail/1249)
is a separate source for entitlement-stage qualification, not an issued feed.

This opt-in CLI prints JSON and does not join the existing collector registry,
write any history/artifact, classify applications as permits or deploy anything:

```sh
PYTHONPATH=src python -m wyoming_permits.teton_application_preview --months 2 --summary
```

If live access fails, the command fails closed. For independently downloaded,
official public archive files, supply `--index-file` and `--report-dir` with PDF
names based on the archive item's numeric ADID (e.g. `782.pdf`). The command
does not reclassify issuance or treat offline success as live source success.

Validation on November 26, 2026: the official HTML and selected PDFs were
downloaded using curl. Requests-based live CLI received 404 at the index in
this environment; unattended live collection is **not validated**. The same
CLI in explicit offline mode parsed 11 unique August (ADID 782) and 36 unique
July (ADID 781) applications: 47 unique IDs, newest submission August 31
(87 days old; stale), no contractor column and no counts of issued permits.
No raw source PDFs, private records, or generated output are committed.
