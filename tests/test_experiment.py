import unittest
import numpy as np
import pandas as pd
from experiment import prepare, unique_rows, validate_split, preprocessor, metrics

class ResearchChecks(unittest.TestCase):
    def test_target_leakage_rejected(self):
        f = pd.DataFrame({'x': [1, 2], 'label': [0, 1], 'attack_cat': ['normal', 'attack']})
        with self.assertRaises(ValueError): prepare(f, 'label', ['x', 'attack_cat'])
        with self.assertRaises(ValueError): prepare(f, 'label', ['label'])

    def test_duplicate_conflicting_labels_rejected(self):
        with self.assertRaises(ValueError):
            unique_rows(pd.DataFrame({'x': [1, 1]}), pd.Series(['a', 'b']))

    def test_overlap_rejected(self):
        x = pd.DataFrame({'x': range(8)})
        y = pd.Series(['a', 'b'] * 4)
        with self.assertRaises(ValueError): validate_split(x, x, y, y)

    def test_preprocessing_fits_training_only_and_handles_unseen(self):
        train = pd.DataFrame({'x': [0., 2., np.nan], 'proto': ['tcp', 'udp', 'tcp']})
        test = pd.DataFrame({'x': [100., np.nan], 'proto': ['new', np.nan]})
        p = preprocessor(train)
        p.fit(train)
        self.assertEqual(p.named_transformers_['numeric']['imputer'].statistics_[0], 1.)
        self.assertTrue(np.isfinite(p.transform(test)).all())
        self.assertEqual(p.named_transformers_['numeric']['imputer'].statistics_[0], 1.)

    def test_positive_class_not_lexical_order(self):
        classes = np.array(['attack', 'normal'])
        out = metrics(np.array(['normal', 'normal', 'attack', 'attack']),
                      np.array(['normal', 'attack', 'attack', 'attack']),
                      np.array([[.1, .9], [.6, .4], [.8, .2], [.9, .1]]), classes, 'attack')
        self.assertEqual(out['false_positive_rate'], .5)
        self.assertEqual(out['attack_recall'], 1.)
        self.assertEqual(out['roc_auc'], 1.)

if __name__ == '__main__': unittest.main()
