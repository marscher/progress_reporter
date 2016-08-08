Progress Reporter
=================

This library provides a simple interface to register different workloads and
visualize their progress with either a plain text progress bar or a jupyter
widget, depending on the current environment.

It optionally depends on Jupyter widgets to draw nice progress bars in the interactive
Jupyter notebook environment.

Installation
------------

with pip::

   pip install progress_reporter

If you use IPython/Jupyter, you are strongly encourage to also install the jupyter widgets::

    pip install ipywidgets


Examples
--------

Image you have a class doing some heavy calculations, which are split into several
jobs/tasks/threads etc.

In order to visualize the progress, one just needs to derive the worker class from
progress_reporter.ProgressReporter and invoke the **_progress_register** method
to tell the reporter how many pieces of work have to be done. Then the reporter
is instructed by **_progress_update(n)** how many of pieces of work have been
dispatched.

Note that these are "private" to use this class as a mixin class and not polute the
public interface.

.. code:: python

    from progress_reporter import ProgressReporter
    import time

    class ExampleWorker(ProgressReporter):
        def __init__(self, n_jobs=100):
            self.n_jobs = n_jobs
            """ register the amount of work with the given description """
            self._progress_register(n_jobs, description='Dispatching jobs')

        def work(self):
            """ do some fake work (sleep) and update the progress via the reporter
            """
            for job in (lambda: time.sleep(0.1) for _ in range(self.n_jobs)):
                job()
                # indicate we've finished one job, to update the progress bar
                self._progress_update(1)


It also supports multi-stage sequential work loads by setting the parameter **stage**.
This is just the dictionary key to the underlying process:

.. code:: python

    class MultiStageWorker(ProgressReporter):
        def __init__(self, n_jobs_init, n_jobs):
            self.n_jobs_init = n_jobs_init
            self.n_jobs = n_jobs
            """ register an expensive initialization routine """
            self._progress_register(self.n_jobs_init, description='initializing', stage=0)
            """ register the main computation """
            self._progress_register(self.n_jobs, description='main computation', stage=1)

        def work(self):
            """ do the initialization """
            for job in (lambda: time.sleep(0.1) for _ in range(self.n_jobs_init)):
                job()
                self._progress_update(1, stage=0)

            """ perform the next stage of the algorithm """
            for job in (lambda: time.sleep(0.2) for _ in range(self.n_jobs)):
                job()
                self._progress_update(1, stage=1)
