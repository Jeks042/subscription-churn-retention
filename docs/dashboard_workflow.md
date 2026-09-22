# Power BI reporting workflow

The report is a portable PBIP project with a PBIR report definition and an import semantic model in `model.bim`. Only published aggregates are embedded as JSON in Power Query M. There are no customer IDs, private source paths, external credentials or network data connections in the report.

## Reproduce

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.build_dashboard
.\.venv\Scripts\python.exe -m pip install -r requirements-dashboard.txt
.\.venv\Scripts\python.exe -m src.verify_dashboard --schemas
```

Close Power BI before rebuilding generated files. Open `dashboard/Retention.pbip`, keeping both adjacent project folders. Choose Home → Refresh to import the aggregates; a new clone has no cache. If prompted, keep the existing semantic model format with **Don't upgrade**. The builder is the source of truth for generated layouts and measures; manual Desktop changes are overwritten on rebuild. Do not commit `.pbi`, `.platform`, PBIX files or customer-level inputs.

The builder uses Python standard-library modules. The optional schema check uses pinned `jsonschema` and downloads public Microsoft schemas. Offline reconciliation works without `--schemas`.

## Model and filter contract

Fourteen tables retain their published grain and source references in table descriptions and `dashboard/build_manifest.json`. The 60-row Profiles table filters the 360-row Scenarios table through a unique profile key. Six Scenario choices filter the same fact table through scenario name. Both relationships are one-to-many and single-direction. Other diagnostic tables have independent grains; no fact-to-fact join multiplies rows.

The scenario explorer requires one source, capacity, policy, value case and scenario. Single-select slicers guide the selection. DAX also checks that exactly one profile, scenario choice and scenario row remain. Ambiguous selections return blank monetary cards and an explanatory status. Expected churn from summed probabilities may be fractional; source labels distinguish **predicted** from historical **observed** cases.

Most diagnostic measures also require one aggregate row. Totals across dates, models, capacities, sources or overlapping segments are suppressed. Commercial comparison measures explicitly select one source within a single scenario. These are alternative outcomes, never additive revenue.

## Measures and denominators

The [measure catalogue](../dashboard/measure_catalog.json) contains the actual DAX and formatting, including raw-column renames needed to avoid case-insensitive name collisions. The [aggregate tables](../dashboard/aggregates) are readable inputs to the embedded M payloads.

| Quantity | Definition |
|---|---|
| Observed churn rate | Reconstructed mature churn / eligible customers for the displayed cohort or segment. |
| Precision | Reconstructed churn in the ranked list / contacted customers. |
| Recall | Reconstructed churn in the ranked list / all reconstructed churn in that population. |
| Lift | Precision / population churn rate. |
| Predicted risk | Mean frozen, December-calibrated probability. |
| Conditional scenario benefit | Assumed save fraction × churn-weighted retained contribution. |
| Absolute scenario benefit | Assumed absolute retention effect × retained contribution across all contacts. |
| Hypothetical net CU | Scenario benefit minus contact, incentive and assumed fixed costs. |
| Break-even conditional saves | Total cost / churn-weighted retained contribution. |
| Break-even absolute effect | Total cost / retained contribution across all contacts. |

The 1 February 2017 full-baseline population has 680,401 customers. The matched source comparison has 679,309. Seven cohort counts are customer/date snapshots; customers recur. Segment pairs partition February customers, but all eight overlapping groups cannot be summed. Calibration bands have unequal counts, available in the Calibration aggregate.

## Verification record

Power BI Desktop 2.157.1354.0 opened the project and refreshed all 14 embedded tables without external data access. The overview, cohort/segment, model, commercial and experiment pages were visually inspected. The overview displayed 680,401, 5.59%, 66.13% and 36.97%, agreeing with source analysis. Matched source precision displayed 35.85% versus 23.39%.

The independent dashboard check passes **2,196 checks**, covering source hashes, embedded payload equality, primary keys, relationship direction, every visual field reference, guard structure, denominator identities and independently recalculated economics for all 360 named scenarios. **75 Power BI documents** pass Microsoft's published JSON schemas. All **28 existing analysis tests** pass. These structural checks do not by themselves prove every possible user interaction; rendered page and selected-filter checks complement them.

## Limits and references

All six final pages were visually reviewed. The explorer showed blank monetary cards when alternatives remained ambiguous. Selecting matched baseline, 10%, risk-only, uniform and reference 20% conditional saves displayed 67,930 contacts, +54,445 CU net, 237,755 CU cost and 16.27% break-even. Screenshots record both initial and selected states.

No cloud report was published and no intervention was launched. Retrospective event dates do not prove ingestion availability. The reconstructed outcome has source dependence and 22 unresolved supplied-label differences. Conditional model intervals exclude source and treatment uncertainty. CU assumptions, value proxies and power planning remain hypothetical.

Format references: [Microsoft PBIP overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [PBIR report structure](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [semantic model project structure](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset). These explain the portable file format, not the analytical conclusions.
