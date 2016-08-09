'''
Created on 29.07.2015

@author: marscher
'''

from __future__ import absolute_import

import unittest

from progress_reporter import ProgressReporter


class TestProgress(unittest.TestCase):
    def test_callback(self):
        self.has_been_called = 0

        def call_back(stage, progressbar, *args, **kw):
            self.has_been_called += 1
            assert isinstance(stage, int)

        amount_of_work = 100
        worker = ProgressReporter()
        worker._progress_register(
            amount_of_work, description="hard working", stage=0)
        worker.register_progress_callback(call_back, stage=0)
        for _ in range(amount_of_work):
            worker._progress_update(1, stage=0)
        self.assertEqual(self.has_been_called, amount_of_work)

    def test_force_finish(self):
        import warnings
        worker = ProgressReporter()
        worker._progress_register(100)
        # intentionally overshoot registered work
        with warnings.catch_warnings(record=True) as cm:
            worker._progress_update(101)
        assert len(cm) == 1
        self.assertIn("more work than registered", cm[0].message.args[0])
        worker._progress_force_finish()


if __name__ == "__main__":
    unittest.main()
