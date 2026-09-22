# Decision log

| Date | Decision | Rationale / condition |
|---|---|---|
| 2026-09-22 | Use authorised KKBox/WSDM sources for an independent historical case study | Access and account agreement are confirmed. Restricted files and customer-level derivatives stay outside GitHub. |
| 2026-09-22 | Lead with renewal cohorts, reliability and commercial assumptions | The portfolio should demonstrate analytical ownership, not only model scores. Intervention value remains a scenario. |
| 2026-09-22 | Correct the original listening-file diagnosis | The 8 GB extraction was incomplete; a fresh 30.5 GB extraction matches archive size and passes strict parsing. Incomplete copies are quarantined. |
| 2026-09-22 | Use DuckDB 1.5.5 and versioned SQL | The full transaction pipeline produced 4,384,573 eligible records and passed assertions. Temporary spill files use a system temp directory outside OneDrive. |
| 2026-09-22 | Freeze original transactions plus March-only refreshed events as baseline | Preserves a single documented historical snapshot and extends February follow-up. Backdated refresh rows are a sensitivity case; neither version is asserted to be definitive operational truth. |
| 2026-09-22 | Collapse only exact duplicate analytical transaction rows | 3,339 original duplicate excess rows otherwise inflate counts and amounts. Raw source files remain untouched; non-identical same-day events retain source ordering. |
| 2026-09-22 | Reconstruct historical expiry-cohort labels | Supplied labels do not exactly reconcile. Baseline sample: 1,744 matches, 43 mismatches; 21 mismatches align after adding backdated refresh and 22 remain unexplained. No exact competition reproduction claim. |
| 2026-09-22 | Require seven-day intervention lead and full expiry-plus-30-day maturity | Supports a stated outreach population and prevents silent treatment of censored cases as non-churn. |
| 2026-09-22 | Implement calendar v1 | Training May–August 2016; selection October; calibration December; holdout February 2017. Every prior stage matures before the next scoring date. |
| 2026-09-22 | Limit claims to retrospective event-time analysis | Ingestion timestamps are absent. Do not assert verified historical operational availability or production readiness. Member snapshot attributes are deferred. |
| 2026-09-22 | Carry release sensitivity into milestone 3 | Baseline February churn is 5.5904% versus about 3.89% under full union. Later calibration/capacity conclusions must acknowledge source dependence; the final holdout must not choose the source policy. |
| 2026-09-22 | Keep model fitting behind the completed feature-table gate | Transaction features are implemented; listening integration, coverage/missingness and combined-table checks remain in milestone 2. |
| 2026-09-22 | Close milestone 1 with scoped GO to retrospective SQL analysis | All seven data files are audited, original log extraction is verified, historical cohort counts/maturity are demonstrated, and the implementation is checked. NO-GO for exact competition reproduction or verified operational availability; the 22 unexplained label mismatches and material release sensitivity remain explicit limitations. |

Remaining implementation decisions: listening anomalies and feature coverage, final feature-table handoff, training-only preprocessing, capacity policies and commercial assumptions. These are downstream work items, not requests for account access or user action.
