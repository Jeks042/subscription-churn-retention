# Milestone 3 evaluation plan — v1

Frozen before model fitting on 22 September 2026. This plan does not use final-holdout model results. Earlier source-validation counts are already public.

## Population and chronology

Use the milestone 2 feature allowlist and mature, lead-eligible labels. Train on May–August 2016, select on October, fit probability calibration on December, and evaluate on February 2017. Retain recurring customers; IDs are keys and deterministic tie breakers only. Assert unique customer/date keys, full label joins, finite features, exact calendar and label maturity before each next stage. No random split. No re-fitting the base models on later months.

## Models and selection

1. Training prevalence benchmark.
2. Renewal rule: four groups defined by any cancellation and absence of auto-renew flags in the prior 90 days. Estimate group risk on training with 100 pseudo-observations at training prevalence.
3. Transaction-recency logistic regression, one predictor.
4. Transaction-only logistic regression, 11 predictors.
5. Combined logistic regression, 38 predictors.

Apply signed log1p to the numeric predictors, then StandardScaler fitted on training only. Use L2 logistic regression, no class weighting or oversampling, solver lbfgs, tolerance 1e-7, maximum 1,000 iterations, and C in {0.01, 1}. Select C within each family by lowest October log loss. Select the simplest family within 0.5% of the lowest October log loss, in the order above. The ranking metric is a secondary assessment; do not choose a model or contact capacity using February outcomes. A nonlinear challenger is deferred: this milestone first establishes the value and limitations of transparent baselines.

Fit a predeclared sigmoid mapping of each nonconstant model's raw log odds to December outcomes (C=1,000,000, effectively unpenalised). Require a positive slope to preserve ranking. Update the constant benchmark to December prevalence. Report raw and calibrated performance; do not choose the calibration method on its fitting data. A near-constant/no-incremental-skill result is acceptable.

## Capacity, metrics and uncertainty

Freeze contact fractions at 5%, 10% and 20%. Select floor(fraction × population) by descending risk, breaking ties by a SHA-256 digest of customer ID. These are capacity scenarios, not recommended business budgets. Report selected counts, true/false positives, false negatives, precision, recall, lift, log loss, Brier score, average precision (AP, the chosen PR-AUC summary), ROC-AUC, prevalence and ten fixed-width calibration bins with counts. Include score deciles for readable calibration plots.

Use 200 seeded Poisson customer-bootstrap replicates for conditional 95% percentile intervals on final-test metrics and paired differences between the selected model and the best simple benchmark by October log loss. February contains one row per customer, so a customer cluster is one row; do not pool recurring customer/date observations as independent rows. Recompute capacity ranks under bootstrap multiplicities. These intervals condition on fitted models and the observed month: they omit training, future-period, source-truth and treatment-effect uncertainty.

## Prespecified diagnostics and sensitivity

- Report split population, prevalence, customer overlap with training and feature drift; evaluate no-listening-record, member-present/absent (diagnostic only), training-seen/unseen and capped-duration groups. Global targeting rates by segment accompany within-segment discrimination/calibration.
- Fit a combined logistic ablation that excludes duration totals and their missing indicators, leaving listening-day/recency and quality flags. Select C on October, calibrate December. This tests reliance on duration magnitudes/capping; it is not a reconstruction of uncapped seconds and cannot identify the correct cap.
- Freeze baseline source policy. Reconstruct full-union eligible labels for October, December and February using the existing independently checked cohort logic. Rescore no models: compare identical baseline predictions against both labels on the common eligible population, and report additions/removals. This isolates target/population sensitivity, not a full alternative-source retraining. Do not choose a source policy from February performance. Baseline probabilities may cease to be calibrated under alternative labels; do not repair them with holdout fitting.
- Report source-related prevalence, calibration and capacity changes explicitly. Preserve 22 unexplained supplied-label disagreements and unknown historical ingestion availability as limitations.

## Reproducibility and completion

Separate fit/freeze and final-evaluation commands. Save a hash of the plan, code, feature manifests, predictor lists, dependency versions and fitted bundle before accessing holdout labels. A holdout marker prevents accidental second evaluation into the same output directory. Publish only aggregate results, charts and reproducible code; scores, customer IDs, model artifacts and source data stay private. Models estimate reconstructed historical churn, not responsiveness to an offer, causal retention impact, savings or production readiness.

Method references: [scikit-learn calibration guidance](https://scikit-learn.org/1.7/modules/calibration.html), [StandardScaler](https://scikit-learn.org/1.7/modules/generated/sklearn.preprocessing.StandardScaler.html), and [average precision](https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.average_precision_score.html).
