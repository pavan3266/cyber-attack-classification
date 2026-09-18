# Real data preparation

The demo uses scikit-learn `make_classification`; it has no cyber-physical meaning. No external dataset is bundled or downloaded automatically.

## UNSW-NB15 as an optional first experiment

Official source: https://research.unsw.edu.au/projects/unsw-nb15-dataset

Obtain the designated training and testing CSVs from the links on that page. Read its use terms and citation requirements. Keep files in a local `data/` directory, excluded from Git. Do not assume permission to redistribute.

The official page identifies 175,341 training records and 82,332 test records. Check the downloaded filenames and counts before running; do not infer the partition from a filename alone. The runner removes within-file feature duplicates and refuses feature overlap across partitions. Consequently, after a deduplication decision it is not automatically a like-for-like comparison with published full-partition scores.

For binary classification use `label` as the target and `--positive-label 1`. Exclude `attack_cat`, `label`, and `id` from predictors. For attack-category classification use `--label attack_cat`, exclude the binary label and ID, and omit `--positive-label`.

Example (run from the repository root):

```bash
python experiment.py \
  --train data/UNSW_NB15_training-set.csv \
  --test data/UNSW_NB15_testing-set.csv \
  --label label --positive-label 1 \
  --features dur,proto,service,state,spkts,dpkts,sbytes,dbytes \
  --models dummy_baseline,logistic_regression,decision_tree,random_forest \
  --output results/unsw-first-run
```

This feature list is deliberately small for a starter run. Selecting fewer features can collapse distinct traffic records into identical rows. If overlap or conflicting-label errors occur, review the full legitimate feature set and dataset structure. Do not delete difficult examples just to improve scores, and do not bypass the checks silently.

For stronger experiments, establish time/session/host separation, validation procedures, class weighting decisions, and a fixed feature list before inspecting test performance. Use a separate validation set or training-only cross-validation for tuning; this starter does neither automatically.

Cite the dataset creators and the required works listed on the official page. A citation to the companion article does not replace dataset citations.
