# Milestone 6 — Reproduction and portfolio publication

The scoped retrospective study is complete. The fresh source-to-commercial run passed all 15 stages, with headline counts and commercial scenarios unchanged. Detailed numerical refit differences are documented below; this is analytical reproduction, not bit-for-bit model reproduction. The original model freeze, evaluation and the seven published dashboard views remain the decision record.

Read the [portfolio case study](https://jeks042.github.io/subscription-churn-retention.html), [decision memo](decision_memo.md) and [dashboard evidence](milestone_5_findings.md).

## Fresh reproduction

The 23 September 2026 run used a new Python 3.13.7 environment, installed from the published analysis lock and dashboard requirements, and a separate checkout of `b7850c47c8c039ba10c93a3d7740a2dcd62fa385`. Source files were the previously authorised local files; source databases, features and model outputs were rebuilt into a new directory. No cached feature table or original fitted model bundle was used.

The run took **28.9 minutes**, excluding environment setup and final review. It produced **15.34 GiB** of private output, excluding the raw inputs, environment and temporary spill files. The Windows workstation has about 64 GiB installed RAM. A separate five-second process-tree monitor observed a peak working set of **5.00 GiB**; it started during listening ingestion and excludes earlier label/transaction stages. This is a sampled observation, not a tested minimum RAM requirement. DuckDB stages use explicit 3–4 GB memory limits and temporary spill outside OneDrive; model fitting has separate memory needs. Leave substantial free disk beyond the retained output size for spill and source extraction.

| Stage | Minutes | Result |
|---|---:|---|
| labels | 0.08 | Passed |
| transactions | 0.68 | Passed |
| listening audit | 15.67 | Passed |
| sql | 3.38 | Passed |
| listening features | 3.82 | Passed |
| label check | 0.08 | Passed |
| listening check | 0.17 | Passed |
| source sensitivity | 0.63 | Passed |
| fit | 2.53 | Passed |
| evaluate | 1.00 | Passed |
| model check | 0.18 | Passed |
| commercial | 0.53 | Passed |
| commercial check | 0.02 | Passed |
| tests | 0.07 | Passed |
| dashboard | 0.05 | Passed |

All 28 synthetic tests, 2,196 dashboard checks and 75 Microsoft schema validations passed. Independent checks again covered 7,000 sampled labels, 16,100 listening values, 96 model metrics and 5,604 commercial values.

Reconciliation compared 13 reports and 14,715 numeric values. Integer counts must match exactly; floating-point comparisons use absolute and relative tolerance `1e-8`. The strict comparison flagged 1,451 differences and remains nonzero; its tolerance was not loosened. Three duration-sum columns differ by at most 8.39e-9 seconds across the full rebuilt feature table; the other 35 predictors are identical. The combined optimiser stopped after 103 iterations rather than 105, with small score changes and individual records moving across some diagnostic bin and policy boundaries. All full-cohort 5/10/20% capture counts, precision, recall and lift remain exact; all 12 matched 10% risk-only/uniform scenario dictionaries also match exactly. The maximum net-contribution change across the wider 360 scenarios is 3.324 CU, with no profit-sign changes. The extra SQL-manifest keys are the later listening SQL files; every hash matches committed code. New timestamps, database/model serialization hashes and run-provenance hashes are excluded explicitly. The [machine-readable record](reproduction_verification.json) lists exclusions, packages, timings, the reconciliation review and every integer discrepancy. The locally generated `comparison.json` contains the full strict difference list. The review accepts the stated analytical result with numerical variation; it does not certify identical fitted parameters or customer lists.

This is a repeat of the frozen procedure for reproducibility, not another model-selection exercise. No holdout-informed tuning was performed. The report layout was preserved and its committed aggregates were checked; Desktop rendering, refresh and scenario selection were verified in milestone 5. The complete original listening source was rebuilt; the refreshed listening diagnostic and every exploratory milestone 1 investigation were not rerun because they do not feed the baseline pipeline.

## Publication and consistency review

- The final README leads with the decision and distinguishes full-cohort model evaluation from matched-population commercial scenarios.
- The portfolio case study is linked from the homepage and case-study index, and uses all seven dashboard views. Local desktop/mobile checks confirmed readable layout without horizontal page overflow and successful image loading.
- The published-tree review covered 196 files, including 108 JSON documents and 14 decoded Power BI aggregate payloads. No restricted source/extract files, executable fitted bundles or unresolved credential/identifier-pattern findings were found. Four `msno` key hits were aggregate missing-count fields. Pattern screening is not a guarantee against every secret type and does not constitute a forensic audit of all Git history.
- Windows Git line-ending conversion was fixed using `.gitattributes`, preserving original committed bytes and evidence hashes.

## Final decision and remaining boundaries

At 10% full-cohort capacity, 68,040 contacts capture 25,155 of 38,037 reconstructed churn outcomes: 66.13% recall, 36.97% precision and 6.61× lift. This does not mean those customers can be saved.

Commercial comparison uses 679,309 common customers and 67,930 contacts. Under assumed 60 CU retained contribution and 3.50 CU contact/offer cost, conditional break-even is 16.27% under baseline labels versus 24.94% under refreshed labels. A 20% assumed save rate gives +54,445 CU versus −47,087 CU. No campaign or realised savings has been measured.

The recommendation remains **validate operational data, source version, actual unit economics and treatment response before funding a controlled pilot**. Source dependence, unknown historical ingestion availability, 22 unexplained supplied-label differences, customer overlap across periods and weaker missing-record segments remain explicit limitations. The payment-based value index is a sensitivity proxy, not validated lifetime value. These boundaries are not removed by successfully reproducing the code.

## Reproduce or review

[Full workflow](../docs/reproduction_workflow.md) · [Delivery issue](https://github.com/Jeks042/subscription-churn-retention/issues/6) · [Progress](progress.md)
