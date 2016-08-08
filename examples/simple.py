from progress_reporter import ProgressReporter
import time


class ExampleWorker(ProgressReporter):
    def __init__(self, n_jobs=100):
        self.n_jobs = n_jobs
        self._progress_register(n_jobs, description='Dispatching jobs')

    def work(self):
        for job in (lambda: time.sleep(0.1) for _ in range(self.n_jobs)):
            job()
            # indicate we've finished one job, to update the progress bar
            self._progress_update(1)


if __name__ == '__main__':
    w = ExampleWorker()
    w.work()
