
'''
Created on 16.07.2015

@author: marscher
'''

from __future__ import absolute_import, print_function

from .bar import ProgressBar as _ProgressBar
from .bar import show_progressbar as _show_progressbar
from .bar.gui import hide_progressbar as _hide_progressbar
from numbers import Integral


class ProgressReporter(object):
    """ Derive from this class to make some protected methods available to register
    and update status of different stages of an algorithm.
    """
    _pg_threshold = 2

    # Note: this class has intentionally no constructor, because it is more
    # comfortable for the user of this class (who is then not in the need to call it).

    @property
    def show_progress(self):
        """ whether to show the progress of heavy calculations on this object. """
        if not hasattr(self, "_show_progress"):
            self._show_progress = True
        return self._show_progress

    @show_progress.setter
    def show_progress(self, val):
        self._show_progress = bool(val)

    @property
    def _prog_rep_progressbars(self):
        # stores progressbar representation per stage
        if not hasattr(self, '_ProgressReporter__prog_rep_progressbars'):
            self.__prog_rep_progressbars = {}
        return self.__prog_rep_progressbars

    @property
    def _prog_rep_descriptions(self):
        # stores progressbar description strings per stage. Can contain format parameters
        if not hasattr(self, '_ProgressReporter__prog_rep_descriptions'):
            self.__prog_rep_descriptions = {}
        return self.__prog_rep_descriptions

    @property
    def _prog_rep_callbacks(self):
        # store callback by stage
        if not hasattr(self, '_ProgressReporter__prog_rep_callbacks'):
            self.__prog_rep_callbacks = {}
        return self.__prog_rep_callbacks

    def _progress_register(self, amount_of_work, description='', stage=0):
        """ Registers a progress which can be reported/displayed via a progress bar.

        Parameters
        ----------
        amount_of_work : int
            Amount of steps the underlying algorithm has to perform.
        description : str, optional
            This string will be displayed in the progress bar widget.
        stage : int, optional, default=0
            If the algorithm has multiple different stages (eg. calculate means
            in the first pass over the data, calculate covariances in the second),
            one needs to estimate different times of arrival.
        """
        if not self.show_progress:
            return

        if not isinstance(amount_of_work, Integral):
            raise ValueError("amount_of_work has to be of integer type. But is %s"
                             % type(amount_of_work))

        # if we do not have enough work to do for the overhead of a progress bar,
        # we just define a dummy here
        if amount_of_work <= ProgressReporter._pg_threshold:
            class dummy(object):
                pass
            pg = dummy()
            pg.__str__ = lambda: description
            pg.__repr__ = pg.__str__
            pg._dummy = None
            pg.description = ''
        else:
            pg = _ProgressBar(amount_of_work, description=description)

        self._prog_rep_progressbars[stage] = pg
        self._prog_rep_descriptions[stage] = description

    def _progress_set_description(self, stage, description):
        """ set description of an already existing progress """
        assert hasattr(self, '_prog_rep_progressbars')
        assert stage in self._prog_rep_progressbars

        self._prog_rep_progressbars[stage].description = description

    def register_progress_callback(self, call_back, stage=0):
        """ Registers the progress reporter.

        Parameters
        ----------
        call_back : function
            This function will be called with the following arguments:

            1. stage (int)
            2. instance of pyemma.utils.progressbar.ProgressBar
            3. optional \*args and named keywords (\*\*kw), for future changes

        stage: int, optional, default=0
            The stage you want the given call back function to be fired.
        """
        if not self.show_progress:
            return

        assert callable(call_back), "given call_back is not callable: {}".format(call_back)

        if stage not in self._prog_rep_callbacks:
            self._prog_rep_callbacks[stage] = []

        self._prog_rep_callbacks[stage].append(call_back)

    def _progress_update(self, numerator_increment, stage=0, show_eta=True, **kw):
        """ Updates the progress. Will update progress bars or other progress output.

        Parameters
        ----------
        numerator : int
            numerator of partial work done already in current stage
        stage : int, nonnegative, default=0
            Current stage of the algorithm, 0 or greater

        """
        if not self.show_progress:
            return

        if stage not in self._prog_rep_progressbars:
            raise RuntimeError(
                "call _progress_register(amount_of_work, stage=x) on this instance first!")

        if hasattr(self._prog_rep_progressbars[stage], '_dummy'):
            return

        pg = self._prog_rep_progressbars[stage]
        pg.numerator += numerator_increment
        # we are done
        if pg.numerator == pg.denominator:
            if stage in self._prog_rep_callbacks:
                for callback in self._prog_rep_callbacks[stage]:
                    callback(stage, pg, **kw)
            self._progress_force_finish(stage)
            return
        elif pg.numerator > pg.denominator:
            import warnings
            warnings.warn("This should not happen. An caller pretended to have "
                          "achieved more work than registered")
            return

        desc = self._prog_rep_descriptions[stage].format(**kw)
        pg.description = desc

        _show_progressbar(pg, show_eta=show_eta, description=desc)

        if stage in self._prog_rep_callbacks:
            for callback in self._prog_rep_callbacks[stage]:
                callback(stage, pg, **kw)

    def _progress_force_finish(self, stage=0, description=None):
        """ forcefully finish the progress for given stage """
        if not self.show_progress:
            return
        if stage not in self._prog_rep_progressbars:
            raise RuntimeError(
                "call _progress_register(amount_of_work, stage=x) on this instance first!")
        pg = self._prog_rep_progressbars[stage]
        if not isinstance(pg, _ProgressBar):
            return

        if pg.numerator < pg.denominator:
            pg.numerator = pg.denominator

        pg._eta.eta_epoch = 0

        if description is not None:
            pg.description = description
        else:
            description = self._prog_rep_descriptions[stage]

        _show_progressbar(pg, description=description)
        _hide_progressbar(pg)
