"""Post-publication companion experiment; demo data are entirely synthetic."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.datasets import make_classification
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay, precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier


def demo_data(seed=42, samples=600):
    x, y = make_classification(n_samples=samples, n_features=10, n_informative=6,
        n_redundant=2, n_classes=3, n_clusters_per_class=1,
        weights=[.6, .25, .15], random_state=seed)
    frame = pd.DataFrame(x, columns=[f'feature_{i}' for i in range(10)])
    rng = np.random.default_rng(seed)
    frame['protocol_example'] = rng.choice(['tcp', 'udp', 'icmp'], samples)
    frame.loc[rng.choice(samples, samples // 20, replace=False), 'feature_0'] = np.nan
    # Neutral names avoid suggesting these generated classes represent real attacks.
    frame['label'] = np.array(['synthetic_class_0', 'synthetic_class_1', 'synthetic_class_2'])[y]
    return frame


def load_csv(path):
    frame = pd.read_csv(path)
    frame.columns = frame.columns.str.strip()
    if frame.columns.duplicated().any():
        raise ValueError('Duplicate column names after stripping whitespace.')
    return frame


def prepare(frame, label, features):
    if not features or len(set(features)) != len(features):
        raise ValueError('Provide a nonempty list of unique feature columns.')
    if label in features:
        raise ValueError('The target cannot also be a feature.')
    # Common IDS target proxies and identifiers must not enter the predictors.
    forbidden = {'id', 'label', 'attack_cat', 'attack', 'class', 'target', 'category'}
    bad = [c for c in features if c.lower() in forbidden]
    if bad:
        raise ValueError(f'Remove identifier/target-like features: {bad}')
    missing = set(features + [label]) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if frame[label].isna().any() or frame[label].astype(str).str.strip().eq('').any():
        raise ValueError('Target labels must not be missing or blank.')
    x = frame[features].copy().replace([np.inf, -np.inf], np.nan)
    for c in x.select_dtypes(exclude='number').columns:
        x[c] = x[c].map(lambda v: str(v) if pd.notna(v) else np.nan)
    y = frame[label].astype(str).str.strip()
    if y.nunique() < 2:
        raise ValueError('At least two classes are required.')
    return x, y


def unique_rows(x, y):
    hashes = pd.util.hash_pandas_object(x, index=False)
    pairs = pd.DataFrame({'hash': hashes.to_numpy(), 'label': y.to_numpy()})
    if pairs.groupby('hash')['label'].nunique().gt(1).any():
        raise ValueError('Identical feature rows have conflicting labels. Resolve before training.')
    keep = ~hashes.duplicated()
    return x.loc[keep].reset_index(drop=True), y.loc[keep].reset_index(drop=True), int((~keep).sum())


def validate_split(x_train, x_test, y_train, y_test):
    a = set(pd.util.hash_pandas_object(x_train, index=False))
    b = set(pd.util.hash_pandas_object(x_test, index=False))
    if a & b:
        raise ValueError('Identical feature rows overlap training and test sets. Resolve leakage explicitly.')
    if set(y_train) != set(y_test):
        raise ValueError('Train/test class sets differ. This closed-set benchmark requires every class in both.')
    if len(x_train) < 5:
        raise ValueError('At least five training rows are needed for KNN.')


def preprocessor(x):
    numeric = list(x.select_dtypes(include='number').columns)
    categorical = [c for c in x if c not in numeric]
    blocks = []
    if numeric:
        blocks.append(('numeric', Pipeline([
            ('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
            ('scale', StandardScaler())]), numeric))
    if categorical:
        blocks.append(('categorical', Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False,
                                    max_categories=30))]), categorical))
    return ColumnTransformer(blocks)


def models(seed):
    return {
        'dummy_baseline': DummyClassifier(strategy='most_frequent'),
        'logistic_regression': LogisticRegression(max_iter=3000, random_state=seed),
        'knn': KNeighborsClassifier(n_neighbors=5),
        'linear_svm': SVC(kernel='linear', probability=True, random_state=seed),
        'rbf_svm': SVC(kernel='rbf', probability=True, random_state=seed),
        'naive_bayes': GaussianNB(),
        'decision_tree': DecisionTreeClassifier(max_depth=12, random_state=seed),
        'random_forest': RandomForestClassifier(n_estimators=100, max_depth=16,
                                               random_state=seed, n_jobs=1),
    }


def metrics(y, predictions, probabilities, classes, positive=None):
    precision, recall, f1, _ = precision_recall_fscore_support(y, predictions,
        average='macro', zero_division=0)
    result = dict(accuracy=float(accuracy_score(y, predictions)),
        balanced_accuracy=float(balanced_accuracy_score(y, predictions)),
        precision_macro=float(precision), recall_macro=float(recall), f1_macro=float(f1))
    if len(classes) == 2:
        if positive not in classes:
            raise ValueError('Binary tasks require --positive-label matching the attack class.')
        index = list(classes).index(positive)
        binary_y = np.asarray(y) == positive
        binary_pred = np.asarray(predictions) == positive
        tn, fp, fn, tp = confusion_matrix(binary_y, binary_pred, labels=[False, True]).ravel()
        result.update(roc_auc=float(roc_auc_score(binary_y, probabilities[:, index])),
            false_positive_rate=float(fp / (fp + tn)),
            attack_recall=float(tp / (tp + fn)))
    else:
        result['roc_auc_ovr_macro'] = float(roc_auc_score(y, probabilities,
            labels=classes, multi_class='ovr', average='macro'))
    return result


def run(args):
    if args.demo:
        source = demo_data(args.seed)
        features = [c for c in source if c != 'label']
        x, y = prepare(source, 'label', features)
        data_kind = 'SYNTHETIC DEMO - not cybersecurity benchmark evidence'
        provenance = {'generator': 'sklearn.datasets.make_classification', 'samples': 600}
    else:
        if not args.train or not args.features:
            raise ValueError('Use --demo, or provide --train and --features.')
        features = [c.strip() for c in args.features.split(',')]
        x, y = prepare(load_csv(args.train), args.label, features)
        data_kind = 'USER-SUPPLIED CSV - dataset provenance requires author verification'
        provenance = {'train_sha256': hashlib.sha256(Path(args.train).read_bytes()).hexdigest()}
    x, y, removed = unique_rows(x, y)
    if args.test:
        if args.demo:
            raise ValueError('--test cannot be combined with --demo.')
        xt, yt = prepare(load_csv(args.test), args.label, features)
        xt, yt, removed_test = unique_rows(xt, yt)
        xtr, ytr = x, y
        split = 'supplied train/test files; duplicates within each file removed'
        provenance['test_sha256'] = hashlib.sha256(Path(args.test).read_bytes()).hexdigest()
    else:
        xtr, xt, ytr, yt = train_test_split(x, y, test_size=args.test_size,
            stratify=y, random_state=args.seed)
        removed_test = 0
        split = 'stratified random holdout after deduplication; not temporal or host-independent'
    validate_split(xtr, xt, ytr, yt)
    if ytr.nunique() == 2 and args.positive_label not in set(ytr):
        raise ValueError('Set --positive-label to the exact attack label, e.g. 1.')
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory is not empty; choose a new path to preserve previous runs.')
    output.mkdir(parents=True, exist_ok=True)
    chosen = models(args.seed)
    names = args.models.split(',') if args.models else list(chosen)
    if set(names) - set(chosen):
        raise ValueError(f'Unknown models. Choose from {list(chosen)}')
    meta = {'data_kind': data_kind, 'source': provenance, 'seed': args.seed,
        'split': split, 'train_rows': len(xtr), 'test_rows': len(xt),
        'duplicates_removed_train_source': removed, 'duplicates_removed_test': removed_test,
        'features': features, 'positive_label': args.positive_label,
        'class_counts_train': ytr.value_counts().to_dict(),
        'class_counts_test': yt.value_counts().to_dict(),
        'versions': {'python': platform.python_version(), 'sklearn': sklearn.__version__,
                     'pandas': pd.__version__, 'numpy': np.__version__},
        'models': {n: chosen[n].get_params() for n in names},
        'scope': 'Post-publication companion. Results are not results from the 2024 article.'}
    (output / 'run_metadata.json').write_text(json.dumps(meta, indent=2))
    records = []
    for name in names:
        pipeline = Pipeline([('preprocess', preprocessor(xtr)), ('model', chosen[name])])
        start = time.perf_counter()
        pipeline.fit(xtr, ytr)
        fit_seconds = time.perf_counter() - start
        start = time.perf_counter()
        predictions = pipeline.predict(xt)
        predict_seconds = time.perf_counter() - start
        probabilities = pipeline.predict_proba(xt)
        classes = pipeline.classes_
        values = metrics(yt, predictions, probabilities, classes, args.positive_label)
        records.append({'model': name, **values, 'fit_seconds': fit_seconds,
                        'predict_seconds': predict_seconds})
        (output / f'{name}_report.json').write_text(json.dumps(
            classification_report(yt, predictions, output_dict=True, zero_division=0), indent=2))
        pd.DataFrame({'actual': yt.to_numpy(), 'predicted': predictions}).to_csv(
            output / f'{name}_predictions.csv', index=False)
        fig, ax = plt.subplots(figsize=(8, 6))
        ConfusionMatrixDisplay.from_predictions(yt, predictions, labels=classes,
            ax=ax, colorbar=False, xticks_rotation=30)
        ax.set_title(f'{name}\n' + ('SYNTHETIC DEMO' if args.demo else 'Supplied CSV experiment'))
        fig.tight_layout()
        fig.savefig(output / f'{name}_confusion.png', dpi=150)
        plt.close(fig)
    results = pd.DataFrame(records)
    results.to_csv(output / 'metrics.csv', index=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(results['model'], results['f1_macro'], color='#287c8e')
    ax.set_xlim(0, 1)
    ax.set_xlabel('Macro F1')
    ax.set_title('SYNTHETIC DEMO ONLY' if args.demo else 'Supplied CSV: held-out performance')
    fig.tight_layout()
    fig.savefig(output / 'comparison.png', dpi=150)
    plt.close(fig)
    print(data_kind)
    print(results[['model', 'accuracy', 'f1_macro']].to_string(index=False))
    print(f'Outputs: {output}')
    return results


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--demo', action='store_true')
    p.add_argument('--train', type=Path)
    p.add_argument('--test', type=Path)
    p.add_argument('--label', default='label')
    p.add_argument('--features', help='Explicit comma-separated predictor columns, excluding IDs and all target proxies')
    p.add_argument('--positive-label', help='Exact attack class label for binary evaluation')
    p.add_argument('--models', help='Comma-separated model names; default all eight including dummy')
    p.add_argument('--test-size', type=float, default=.2)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--output', default='results/run-1')
    return p


if __name__ == '__main__':
    p = parser()
    try:
        run(p.parse_args())
    except ValueError as exc:
        p.error(str(exc))
