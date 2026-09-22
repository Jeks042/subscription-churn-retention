# Retention executive report

Open **[Retention.pbip](Retention.pbip)** in Power BI Desktop after downloading or cloning the repository. Keep the adjacent `Retention.Report` and `Retention.SemanticModel` folders together. On a fresh machine choose **Home → Refresh** to import the embedded aggregate tables. No Kaggle files, credentials or private paths are needed for this report.

If Desktop offers to upgrade the semantic model to TMDL, choose **Don't upgrade** to preserve this generated `model.bim` format. Local Desktop caches are deliberately excluded from GitHub.

## Pages

1. Overview — the supported decision and historical capacity trade-off.
2. Cohorts and segments — date-specific denominators and weak-coverage segments.
3. Model reliability — calibrated baselines, calibration and matched source sensitivity.
4. Commercial sensitivity — six alternative scenarios, baseline versus full-union labels.
5. Scenario explorer — select one source, capacity, policy, value and scenario. Cards stay blank when the selection is ambiguous.
6. Experiment and gates — proposed endpoints, planning size and evidence needed before launch.

CU means generic assumed currency units. Observed churn, predicted expected churn and hypothetical savings are different quantities. No campaign was executed.

Read the [decision memo](../reports/decision_memo.md), [milestone findings](../reports/milestone_5_findings.md) and [reproduction / verification notes](../docs/dashboard_workflow.md). Public [aggregate tables](aggregates), the [measure catalogue](measure_catalog.json) and [build manifest](build_manifest.json) provide traceability. Screenshots are in [screenshots](screenshots).
