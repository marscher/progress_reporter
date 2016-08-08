from progress_reporter import ProgressReporter
import time


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


if __name__ == '__main__':
    w = MultiStageWorker(50, 100)
    w.work()
