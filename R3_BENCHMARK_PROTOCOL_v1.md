# R³∞ Longitudinal Capability Benchmark v1

## Goal
Measure actual capability change over time. A model or agent must not be considered improved because it claims improvement.

## Baseline dimensions
1. Accuracy — successful verified tasks / total tasks.
2. Reasoning — correctness of final solutions under an external rubric; internal chain-of-thought is not required as evidence.
3. Error detection — injected-error cases correctly identified.
4. Calibration — absolute gap between confidence and observed correctness.
5. Robustness — performance retained under controlled perturbations.
6. Generalization — success on held-out novel tasks.
7. Reproducibility — variance across repeated runs.
8. Efficiency — execution time, tool calls and compute/cost where measurable.
9. Regression — previously verified capabilities lost after a change.
10. Safety — critical/unsafe failure rate.

## Test sets
- CORE: immutable versioned regression suite.
- NOVEL: held-out tasks never used for optimization.
- ADVERSARIAL: deliberately difficult and failure-seeking cases.
- REAL_WORLD: representative project tasks with objective verification.

## Evaluation cycle
1. Freeze candidate configuration and commit.
2. Record model/configuration, benchmark version and data provenance.
3. Run CORE, NOVEL and ADVERSARIAL suites.
4. Repeat selected tasks to estimate variance.
5. Compare against the last accepted baseline.
6. Reject promotion on material CORE or safety regression.
7. Store the result as a machine-readable artifact.
8. Promote only when provenance, tests, regression checks and rollback are present.

## Minimum result record
`timestamp, commit, configuration, benchmark_version, dataset_version, task_count, accuracy, reasoning_score, error_detection_rate, calibration_error, robustness_score, novel_task_success, run_variance, execution_time_ms, tool_calls, regression_rate, safety_metrics`

## Interpretation
Improvement is a measured delta, not a narrative. When metrics conflict, preserve the full vector rather than collapsing it into one score. Any composite score must disclose its weighting.

## Safety boundary
Self-modification remains candidate generation plus sandboxed evaluation. No autonomous modification is considered validated solely by the system that proposed it.
