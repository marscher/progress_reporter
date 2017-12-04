from numbers import Integral


def _simple_memorize(f):
    # cache function f result (takes no arguments)
    from functools import wraps
    @wraps(f)
    def wrapper():
        if not hasattr(f, 'res'):
            f.res = f()
        return f.res
    return wrapper


@_simple_memorize
def _attached_to_ipy_notebook_with_widgets():
    try:
        # check for widgets
        import ipywidgets
        if ipywidgets.version_info[0] < 4:
            raise ImportError()
        # check for ipython kernel
        from IPython import get_ipython
        ip = get_ipython()
        if ip is None:
            return False
        if not getattr(ip, 'kernel', None):
            return False
        # No further checks are feasible
        return True
    except ImportError:
        return False


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

    def _progress_context(self, stage='all'):
        """

        Parameters
        ----------
        stage: str, iterable of keys, dict_key

        Returns
        -------
        context manager
        """
        from contextlib import contextmanager
        @contextmanager
        def ctx():
            try:
                yield
            finally:
                if stage == 'all':
                    keys = tuple(self._prog_rep_progressbars.keys())
                    for s in keys:
                        self._progress_force_finish(stage=s)
                elif isinstance(stage, (tuple, list)):
                    for s in stage:
                        self._progress_force_finish(s)
                else:
                    self._progress_force_finish(stage)
        return ctx()

    def __check_stage_registered(self, stage):
        if stage not in self._prog_rep_progressbars:
            raise RuntimeError('call _progress_register(amount_of_work, stage={}) on this instance first!'.format(stage))
        return self._prog_rep_progressbars[stage]

    def _progress_register(self, amount_of_work, description='', stage=0, tqdm_args=None):
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

        if tqdm_args is None:
            tqdm_args = {}

        if not isinstance(amount_of_work, Integral):
            raise ValueError('amount_of_work has to be of integer type. But is {}'.format(type(amount_of_work)))

        # if we do not have enough work to do for the overhead of a progress bar just dont create a bar.
        if amount_of_work <= ProgressReporter._pg_threshold:
            pg = None
        else:
            import sys
            # progress_reporter < 2.0 print to stdout.
            if 'file' not in tqdm_args:
                tqdm_args['file'] = sys.stdout
            if 'dynamic_ncols' not in tqdm_args:
                tqdm_args['dynamic_ncols'] = True
            if 'description' in tqdm_args:
                tqdm_args.pop('description')
            args = dict(total=amount_of_work, desc=description, **tqdm_args)
            if _attached_to_ipy_notebook_with_widgets():
                from .notebook import my_tqdm_notebook
                pg = my_tqdm_notebook(leave=False, **args)
            else:
                import tqdm
                pg = tqdm.tqdm(leave=True, **args)

        self._prog_rep_progressbars[stage] = pg
        self._prog_rep_descriptions[stage] = description
        assert stage in self._prog_rep_progressbars
        assert stage in self._prog_rep_descriptions

    def _progress_set_description(self, stage, description):
        """ set description of an already existing progress """
        pg = self.__check_stage_registered(stage)
        self._prog_rep_descriptions[stage] = description
        if pg:
            pg.set_description(description, refresh=True)

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

        pg = self.__check_stage_registered(stage)
        if not pg:
            return

        diff = pg.total - numerator_increment
        if diff < 0:
            import warnings
            warnings.warn("This should not happen. An caller pretended to have "
                          "achieved more work than registered")
        else:
            pg.update(numerator_increment)
            if stage in self._prog_rep_callbacks:
                for callback in self._prog_rep_callbacks[stage]:
                    callback(stage, pg, **kw)

    def _progress_force_finish(self, stage=0, description=None):
        """ forcefully finish the progress for given stage """
        if not self.show_progress:
            return

        pg = self.__check_stage_registered(stage)

        if not pg:
            return

        pg.desc = description
        diff = pg.total - pg.n
        if diff > 0:
            pg.update(diff)
        pg.refresh(nolock=True)
        pg.close()
        self._prog_rep_progressbars.pop(stage, None)
        self._prog_rep_descriptions.pop(stage, None)
        self._prog_rep_callbacks.pop(stage, None)

    def _progress_refresh(self, stage=0):
        if not self.show_progress:
            return

        pg = self.__check_stage_registered(stage)
        if not pg:
            return
        pg.refresh()

    @property
    def _progress_num_registered(self):
        return len(self._prog_rep_progressbars)

    @property
    def _progress_registered_stages(self):
        return tuple(self._prog_rep_progressbars.keys())


ProgressReporterMixIn = ProgressReporter

class ProgressReporter_(ProgressReporter):
    """ class to report progress for multiple stages. Suitable for composition.
    """

    def context(self, stage='all'):
        return self._progress_context(stage=stage)

    def register(self, amount_of_work, description='', stage=0, tqdm_args=None):
        self._progress_register(amount_of_work=amount_of_work, description=description, stage=stage, tqdm_args=tqdm_args)

    def update(self, increment, stage=0):
        self._progress_update(increment, stage=stage)

    def set_description(self, description, stage=0):
        self._progress_set_description(description=description, stage=stage)

    def finish(self, description=None, stage=0):
        self._progress_force_finish(description=description, stage=stage)

    def refresh(self, stage=0):
        """ this does not need to be called manually, but can be useful in certain situations. """
        self._progress_refresh(stage)

    @property
    def num_registered(self):
        return self._progress_num_registered

    @property
    def registered_stages(self):
        return self._progress_registered_stages
