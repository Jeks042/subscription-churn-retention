# Source validation findings

**22 September 2026 — interim decision: HOLD model fitting. Continue source and label validation. Issue #1 remains open.**

## Evidence completed

Authorised Kaggle access was confirmed and the competition agreement accepted following explicit user confirmation. Both label releases, both transaction releases, the member file, refreshed listening logs and the official Scala labeller were acquired locally. The original listening archive has not yet been confirmed complete.

| File | Rows | Distinct customers | Coverage / principal check |
|---|---:|---:|---|
| train.csv | 992,931 | 992,931 | 63,471 churn labels (6.3923%) |
| train_v2.csv | 970,960 | 970,960 | 87,330 churn labels (8.9942%) |
| transactions.csv | 21,547,746 | 2,363,626 | Event dates 2015-01-01 to 2017-02-28 |
| transactions_v2.csv | 1,431,009 | 1,197,050 | Event dates 2015-01-01 to 2017-03-31 |
| members_v3.csv | 6,769,473 | 6,769,473 | Registration dates 2004-03-26 to 2017-04-29 |
| user_logs_v2.csv | 18,396,362 | 1,103,894 | Listening dates 2017-03-01 to 2017-03-31 |

The label and transaction inventories scanned every row, found no malformed-width rows or missing fields, and recorded SHA-256 checksums locally. Label IDs are unique and labels are binary. Member/log SQL scans, checksums and key/date audits are also complete for the named files. Do not extrapolate these findings to the unscanned original logs.

## Material findings and implications

- **Repeated customers:** 881,701 IDs occur in both label releases; 45,990 have different outcomes. Releases must retain their cohort identity. A changed outcome across periods is not automatically an error.
- **Transaction multiplicity:** the original release has 3,339 exact duplicate excess rows and 256,003 customer-days with multiple transactions; the refreshed release has no exact duplicates and 27,942 such customer-days. Same-day ordering must be defined before selecting effective expiry. No rows have been deleted.
- **Release scope:** refreshed transactions include 361,187 pre-March rows absent as exact records from the original. Of these, 6,126 match an original row on every field except expiry. Treating v2 as a purely March increment would lose information; blindly merging versions also needs review.
- **Expiry anomalies:** 158,766 combined transaction rows have expiry before transaction date, including 152,304 cancellation rows and 6,462 non-cancellations. Observed expiry endpoints include 1970 and 2036. These are review flags, not automatic deletion rules.
- **Join coverage:** every supplied label customer appears somewhere in the combined transaction history. This is an all-time existence check, not proof of pre-cutoff feature coverage.
- **Member coverage and quality:** 4,429,505 rows have missing gender, 4,540,215 record age zero and 5,651 fall outside ages 0–100. The member snapshot includes future registrations relative to proposed scoring dates. Do not use it as an unrestricted point-in-time dimension.
- **Listening quality:** refreshed logs have unique customer/date keys and valid dates. There are 4,200 records above 86,400 listening seconds and 40 listening customers without member records. Review aggregation semantics and preserve missing-member groups.

## Label reconciliation

The supplied labeller uses renewal gap <30 days; gap >=30 is churn. It sorts same-day plan events and lets cancellations shorten expiry before the first renewal. Five synthetic tests cover these behaviours in addition to four inventory/key tests.

A deterministic sample of 2,000 IDs per label release was selected by MD5 ordering. For the original labels, using combined transaction history, January-only history and February expiries, 1,733 sample customers were eligible and fully observable. Of these, 1,708 matched and 25 disagreed; the other 267 lacked the required history or expiry eligibility. This is not a complete reconciliation.

For the refreshed labels under the March-expiry interpretation, 1,717 of 2,000 sample customers were censored at the observed March-end transaction boundary. Supplied labels may reflect outcomes unavailable in the released transaction history. This prevents independent reconstruction of those outcomes from these files alone.

Diagnostics also tested other periods and all-history windows. High agreement dominated by non-churn cases cannot establish the correct cohort mapping. No window was selected merely because it had the highest match percentage.

## Temporal decision

Do not assume the supplied releases form a deployable month-to-month split. Training labels must be fully known before the next scoring date. A [candidate historical calendar](../docs/temporal_feasibility.md) separates training, selection, calibration and final testing with maturity gaps; it remains provisional.

## Remaining gates

1. Complete and verify original listening-log acquisition and coverage.
2. Resolve transaction-version handling and explain remaining label mismatches.
3. Review anonymised local label examples against source ordering, without publishing customer histories.
4. Validate historical cohort counts and freeze eligibility, intervention lead time and time cutoffs.
5. Record the final GO/NO-GO decision for feature engineering.

Reproduction: [validation workflow](../docs/validation_workflow.md). Raw data, customer-level outputs, source labeller and local databases are excluded from the public repository. Figures above are aggregate diagnostics, not model performance or intervention impact.
