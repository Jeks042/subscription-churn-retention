# Source validation findings

**22 September 2026 — Milestones 1 and 2 complete for retrospective SQL analysis. The combined feature table and training-only preprocessing are verified. Predictive evaluation and source-version sensitivity are next.**

## Source evidence

Authenticated Kaggle access and competition agreement acceptance are complete. The labeller, both label releases, both transaction releases, members and both listening-log releases were acquired locally. Source rows, customer histories and databases remain outside GitHub.

| File | Rows | Distinct customers | Coverage / check |
|---|---:|---:|---|
| train.csv | 992,931 | 992,931 | 63,471 churn labels (6.3923%) |
| train_v2.csv | 970,960 | 970,960 | 87,330 churn labels (8.9942%) |
| transactions.csv | 21,547,746 | 2,363,626 | 2015-01-01 through 2017-02-28 |
| transactions_v2.csv | 1,431,009 | 1,197,050 | 2015-01-01 through 2017-03-31 |
| members_v3.csv | 6,769,473 | 6,769,473 | Registration 2004-03-26 through 2017-04-29 |
| user_logs_v2.csv | 18,396,362 | 1,103,894 | 2017-03-01 through 2017-03-31 |
| user_logs.csv | 392,106,543 | 5,234,111 | 2015-01-01 through 2017-02-28; all 26 months audited |

Correction: the earlier six-field row at line 103,280,203 was at the end of an incomplete local extraction (8,037,335,040 bytes), not evidence of a malformed upstream record. A fresh extraction exited successfully and matches the archive's uncompressed size exactly. The incomplete copy and hardlink are quarantined with .incomplete extensions. No row was silently repaired or discarded. The audit now rejects a CSV whose size differs from the archive listing.

Full label/transaction scans found no malformed-width rows or missing fields and recorded SHA-256 hashes. IDs in each label release are unique and labels are binary. Both listening releases passed strict parsing and have unique customer/date keys, no missing keys and no invalid dates. The original release's complete SHA-256 is recorded with its full audit.

Source evidence: [label/transaction inventory](source_inventory.json), [refreshed log and member audit](refreshed_log_member_audit.json), and [complete original log audit](original_log_audit.json). All contain aggregates and metadata, not customer rows.

## Material findings

- **Repeated customers:** 881,701 IDs occur in both label releases; 45,990 have different labels. Keep cohort identity.
- **Transaction multiplicity:** original data have 3,339 exact duplicate excess rows and 256,003 customer-days with multiple transactions; refreshed data have zero exact duplicates and 27,942 such days. SQL collapses only identical analytical rows and preserves source ordering.
- **Backdated refresh:** 361,187 pre-March v2 rows are absent as exact records from the original. Of these, 6,126 match an original row except expiry. A full union changes historical outcomes.
- **Expiry anomalies:** combined releases have 158,766 rows with expiry before event date: 152,304 cancellations and 6,462 non-cancellations. Values extending to 1970 and 2036 are retained as quality flags.
- **Label join coverage:** every supplied label customer has some transaction history. This alone does not establish pre-scoring coverage.
- **Member snapshot:** 4,429,505 missing genders, 4,540,215 ages of zero and 5,651 ages outside 0–100. Future registrations and unknown historical availability prevent unrestricted use of this snapshot as predictors.
- **Refreshed listening logs:** unique customer/date keys, valid dates, 4,200 rows above 86,400 seconds and 40 customers without a member record. Listening seconds are recorded activity, not validated wall-clock duration.
- **Original listening logs:** 61,493 rows have negative seconds, 142,993 exceed 86,400 seconds, and 170,178 listening customers lack a member record. Preserve these quality/missing-member groups. Listening feature construction must explicitly flag anomalous durations and document its aggregation/sensitivity treatment; source records were not deleted.

## Label definition and reconciliation

The supplied labeller uses renewal gap <30 days; gap >=30 is churn. It orders same-day plans and allows cancellations to shorten expiry before the first renewal. [Synthetic examples](../docs/label_examples.md) explain the boundary and lead-time rules.

Using original history plus March-only refresh, all pre-scoring history and February expiries, 1,787 of a deterministic 2,000-customer original-label sample were eligible and mature. There were 1,744 matches and 43 mismatches; 208 were outside the expiry cohort and five lacked pre-scoring history. Including backdated refresh records reconciles 21 of the 43 mismatches. The other 22 are not explained by that change or a January-only history filter. These comparisons do not prove the underlying cause of every disagreement.

The earlier January-only/full-union diagnostic reconciled 1,708 of 1,733 eligible sampled customers. These figures use different definitions and must not be substituted for the baseline counts above. For March-expiry refreshed labels, 1,717 of 2,000 cases lacked mature follow-up at March end.

Consequently, supplied labels are diagnostic only. The SQL study uses explicitly reconstructed historical outcomes, not concatenated competition labels or an exact-reproduction claim. Independent SQL/Python implementations agree on all 7,000 sampled lead-eligible customer/date records; that establishes implementation consistency, not undisclosed source truth.

## Temporal and version decision

Machine-readable evidence: [release sensitivity](source_version_sensitivity.json), [supplied-label differences](label_differences.json), [SQL run manifest](sql_build_summary.json), and [independent SQL/Python check](sql_reconstruction_check.json). These files contain aggregates only.

[Calendar v1](../docs/temporal_feasibility.md) contains 4,384,573 eligible records across seven scoring dates, with seven-day intervention lead and complete expiry-plus-30-day follow-up. Training, selection, calibration and holdout are separated by maturity gaps. No model is fitted.

The baseline freezes original transaction history and adds March-only v2 for February follow-up. The full union is a sensitivity case. February has 680,401 eligible customers and 38,037 churn outcomes under baseline versus 679,310 and 26,420 under full union. This material dependence must be addressed in later model evaluation; no version is claimed to be definitive operational truth.

There are no ingestion timestamps. Dates establish a retrospective event-time study, not proof of operational availability at the historical scoring date. Member attributes are deferred. The [SQL workflow](../docs/sql_workflow.md) records every feature, source convention and assertion.

## GO/NO-GO and handoff

**GO to the retrospective SQL case study:** access, extraction integrity, source grains/keys, temporal coverage, explicit label construction, source-version sensitivity and calendar feasibility are documented. The full SQL runner exits cleanly, passes all assertions and writes its source/code manifest. It stages 21,544,407 original rows and 1,069,822 March refreshed rows after exact deduplication. Thirteen synthetic tests pass; the separate 7,000-record implementation comparison has no disagreements.

**NO-GO for an exact competition-label reproduction or production-readiness claim:** 22 supplied-label mismatches remain unexplained, backdated release records materially change outcomes, and ingestion availability is unknown. These are recorded study limits rather than silently marked resolved. The original requirement is narrowed to a transparent retrospective cohort analysis, with these restrictions carried into milestone 3.

Milestone 1 is complete as a feasibility decision for that scoped study. Milestone 2 is now complete: listening features, anomaly/coverage/missingness flags, combined-table checks and training-only fills are implemented and verified. All seven scoring dates have 90 source calendar days of listening coverage; individual observation and missingness are reported in [milestone 2 findings](milestone_2_findings.md). No predictive model, financial uplift or intervention result has been produced.

Reproduction: [validation workflow](../docs/validation_workflow.md). Public figures are aggregate diagnostics, not predictive performance or intervention impact.
