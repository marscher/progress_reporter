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


if __name__ == '__main__':
    w = ExampleWorker()
    w.work()
