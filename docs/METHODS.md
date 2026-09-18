# Relationship to the publication

Source reviewed: https://ijarsct.co.in/Paper19438.pdf (four pages, 417–420).

The paper names LR, KNN, SVM, kernel SVM, naive Bayes, decision trees, and random forests. It describes a broad pipeline and possible 70/30 or 80/20 splits. Its literature discussion reports other studies' findings; those values are not targets for this implementation.

This project adds explicit Python implementations, fixed initial hyperparameters, a dummy baseline, metrics, and provenance. Linear and RBF SVM instantiate the two SVM variants. Gaussian naive Bayes is one chosen variant, not an assertion that the paper specified it. The prototype fits imputation/encoding/scaling after splitting to avoid training on held-out statistics.

This is a new companion implementation, not a verified reproduction. The paper does not give one complete author-run dataset, configuration, and result table that this repository could reproduce exactly. No historical experiment logs or code were supplied. The software's 2026 creation date is not the article's publication date.

## Evaluation definitions

Macro metrics average per-class scores equally. Balanced accuracy averages class recall. Multiclass ROC-AUC uses one-vs-rest probabilities and equal class weights. Binary ROC-AUC uses the explicitly selected positive class. False-positive rate = false positives / all actual negatives. Attack recall = true positives / all actual positives. For binary evaluation, confirm that the negative class really is benign traffic.

Closed-set evaluation requires the same label set in both partitions. Unknown-attack evaluation needs a different protocol. The initial models are not tuned. SVC probability calibration uses only training data via the estimator's internal procedure. Scaling does not benefit every model equally but is kept consistent in this starter comparison.

Run metadata and predictions document the execution. Never label synthetic demo scores as findings from the article. Raw CSVs may contain sensitive information; review them and the outputs before sharing.
