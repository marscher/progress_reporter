'''
Created on 29.07.2015

@author: marscher
'''

from __future__ import absolute_import

import unittest
from time import sleep
import sys

if sys.version_info[0] == 3:
    from io import StringIO
else:
    from cStringIO import StringIO

from progress_reporter import ProgressReporter, ProgressReporter_


class TestProgress(unittest.TestCase):

    def setUp(self):
        self.out = StringIO()

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
        worker.show_progress = False
        worker._progress_register(10, tqdm_args={'file': self.out})
        worker._progress_update(5)
        self.assertEqual(self.out.getvalue().strip(), '')

    def test_show(self):
        worker = ProgressReporter()
        worker.show_progress = True
        worker._progress_register(10, tqdm_args={'file': self.out})
        worker._progress_update(5)
        worker._progress_refresh()
        pg_str = self.out.getvalue().strip()
        self.assertIn('50%', pg_str)
        self.assertIn('5/10', pg_str)

    def test_dummy(self):
        worker = ProgressReporter()
        worker._progress_register(ProgressReporter._pg_threshold, tqdm_args={'file': self.out})
        worker._progress_update(ProgressReporter._pg_threshold)

        self.assertEqual(self.out.getvalue().strip(), '')

    def test_change_description(self):
        worker = ProgressReporter()
        worker._progress_register(100, description="test1", tqdm_args={'file': self.out})
        worker._progress_update(1)
        self.assertIn('test1', self.out.getvalue().strip())

        worker._progress_set_description(stage=0, description='foobar')
        worker._progress_update(1)

        self.assertIn("foobar", self.out.getvalue().strip())

    def test_ctx(self):
        pg = ProgressReporter_()
        pg.register(100, 'test')
        pg.register(40, 'test2')
        try:
            with pg.context():
                pg.update(50, stage='test')
                raise Exception()
        except Exception:
            assert pg.num_registered == 0

    def test_ctx2(self):
        pg = ProgressReporter_()
        assert pg.show_progress
        pg.register(100, stage='test')
        pg.register(40, stage='test2')
        try:
            with pg.context(stage='test'):
                pg.update(50, stage='test')
                raise Exception()
        except Exception:
            assert pg.num_registered == 1
            assert 'test2' in pg.registered_stages

    def test_ctx3(self):
        pg = ProgressReporter_()
        assert pg.show_progress
        pg.register(100, stage='test')
        pg.register(40, stage='test2')
        pg.register(25, stage='test3')
        try:
            with pg.context(stage=('test', 'test3')):
                pg.update(50, stage='test')
                pg.update(2, stage='test3')
                raise Exception()
        except Exception:
            assert pg.num_registered == 1
            assert 'test2' in pg.registered_stages

    def test_ctx4(self):
        pg = ProgressReporter_()
        pg.register(100, 'test')
        pg.register(40, 'test2')
        try:
            with pg.context():
                pg.update(50, stage='all')
                raise Exception()
        except Exception:
            assert pg.num_registered == 0

    def test_below_threshold(self):
        # show not raise
        pg = ProgressReporter_()
        pg.register(2)
        pg.update(1)
        pg.set_description('dummy')


if __name__ == "__main__":
    unittest.main()
