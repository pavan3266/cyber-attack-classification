# Validation of version 0.1.0

Executed with Python 3.12.14, scikit-learn 1.8.0, pandas 2.2.3, NumPy 2.3.5, matplotlib 3.10.8.

- All eight estimators completed the 600-row, three-class synthetic demo (480 train / 120 test).
- Five unit tests passed: target/proxy rejection, conflicting duplicates, train/test overlap, training-only imputation with unseen categories, and binary positive-class orientation.
- A separate 150-row synthetic fixture exercised CSV reading and explicit train/test files with binary metrics for the baseline and logistic regression.
- Notebook code cells passed syntax compilation; notebook execution itself was not tested.
- The comparison chart was visually inspected.

No real cybersecurity dataset was downloaded or evaluated. This validates starter software operation, not scientific validity, security efficacy, or reproduction of published findings.
