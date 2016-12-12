'''
Created on 29.07.2015

@author: marscher
'''

from __future__ import absolute_import

import unittest
from contextlib import contextmanager

from progress_reporter import ProgressReporter


@contextmanager
def captured_output():
    import sys
    if sys.version_info[0] == 3:
        from io import StringIO
    else:
        from cStringIO import StringIO
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


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

    def test_show_hide(self):
        worker = ProgressReporter()
        worker._progress_register(10)
        worker.show_progress = False
        with captured_output() as (out, _):
            worker._progress_update(5)

        self.assertEqual(out.getvalue().strip(), '')

    def test_show(self):
        worker = ProgressReporter()
        worker._progress_register(10)
        worker.show_progress = True
        with captured_output() as (out, _):
            worker._progress_update(5)

        self.assertIn('50%', out.getvalue().strip())
        self.assertIn('5/10', out.getvalue().strip())

    def test_dummy(self):
        worker = ProgressReporter()
        with captured_output() as (out, _):
            worker._progress_register(ProgressReporter._pg_threshold)
            worker._progress_update(ProgressReporter._pg_threshold)

        self.assertEqual(out.getvalue().strip(), '')

    def test_change_description(self):
        worker = ProgressReporter()
        worker._progress_register(100, description="test1")
        with captured_output() as (out, _):
            worker._progress_update(1)
            self.assertIn('test1', out.getvalue().strip())

        with captured_output() as (out, _):
            worker._progress_set_description(stage=0, description='foobar')
            worker._progress_update(1)

        self.assertIn("foobar", out.getvalue().strip())

if __name__ == "__main__":
    unittest.main()
