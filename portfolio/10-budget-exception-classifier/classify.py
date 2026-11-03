"""Synthetic grouped budget-exception classification benchmark."""
import argparse
import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
FEATURES = ('variance_pct', 'absolute_variance', 'days_since_review', 'missing_evidence')


def fixture(seed=19):
    rng = np.random.default_rng(seed)
    rows = []
    for group in range(30):
        for period in range(8):
            variance = float(rng.uniform(-0.3, 0.4))
            amount = float(rng.uniform(50, 12000))
            days = int(rng.integers(0, 80))
            missing = int(rng.random() < 0.18)
            risk = 2.8 * abs(variance) + 0.000045 * amount + 0.009 * days + 0.6 * missing + rng.normal(0, .25)
            label = int(risk > 1.3)
            rows.append({'group': f'unit-{group:02d}', 'period': period,
                         'variance_pct': round(variance, 5), 'absolute_variance': round(amount, 2),
                         'days_since_review': days, 'missing_evidence': missing, 'exception': label})
    return rows


def evaluate(rows):
    if not rows or len({r['group'] for r in rows}) < 10:
        raise ValueError('At least ten groups required')
    x = np.array([[r[f] for f in FEATURES] for r in rows], dtype=float)
    y = np.array([r['exception'] for r in rows], dtype=int)
    groups = np.array([r['group'] for r in rows])
    if not np.isfinite(x).all() or not set(y).issubset({0, 1}):
        raise ValueError('Invalid features or labels')
    outer = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=73)
    tv_idx, test_idx = next(outer.split(x, y, groups))
    inner = GroupShuffleSplit(n_splits=1, test_size=.25, random_state=41)
    train_rel, val_rel = next(inner.split(x[tv_idx], y[tv_idx], groups[tv_idx]))
    train_idx, val_idx = tv_idx[train_rel], tv_idx[val_rel]
    partitions = {'train': train_idx, 'validation': val_idx, 'test': test_idx}
    if any(len(np.unique(y[ids])) < 2 for ids in partitions.values()):
        raise ValueError('Both classes required per partition')
    assert all(set(groups[partitions[a]]).isdisjoint(groups[partitions[b]])
               for a, b in [('train', 'validation'), ('train', 'test'), ('validation', 'test')])
    clf = make_pipeline(StandardScaler(), LogisticRegression(class_weight='balanced', max_iter=1000, random_state=7))
    clf.fit(x[train_idx], y[train_idx])
    val_prob = clf.predict_proba(x[val_idx])[:, 1]
    choices = []
    for threshold in np.arange(.1, .91, .05):
        precision, recall, f1, _ = precision_recall_fscore_support(y[val_idx], val_prob >= threshold,
                                                      average='binary', zero_division=0)
        choices.append((float(f1), float(recall), float(threshold)))
    _, _, threshold = max(choices)
    def score(ids):
        probs = clf.predict_proba(x[ids])[:, 1]
        pred = probs >= threshold
        precision, recall, f1, _ = precision_recall_fscore_support(y[ids], pred, average='binary', zero_division=0)
        return {'n': len(ids), 'positives': int(y[ids].sum()), 'precision': round(float(precision), 4),
                'recall': round(float(recall), 4), 'f1': round(float(f1), 4),
                'average_precision': round(float(average_precision_score(y[ids], probs)), 4),
                'confusion_matrix_tn_fp_fn_tp': confusion_matrix(y[ids], pred, labels=[0, 1]).ravel().tolist(),
                'groups': sorted(set(groups[ids]))}
    return {'scope': 'synthetic grouped baseline; no real invoice or budget decisions',
            'seed': 19, 'features': FEATURES, 'threshold_selected_on_validation': round(threshold, 3),
            'train': score(train_idx), 'validation': score(val_idx), 'test': score(test_idx),
            'limits': ['Synthetic labels derive from correlated features and are not independent expert judgements.',
                       'Test results are descriptive for this one seeded fixture; no generalization claim.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    output = json.dumps(evaluate(fixture()), indent=2) + '\n'
    if args.output:
        args.output.write_text(output)
    print(output, end='')
