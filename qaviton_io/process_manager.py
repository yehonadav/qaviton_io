from qaviton_io.async_manager import AsyncManager
from multiprocessing import cpu_count, Queue
from qaviton_processes import Task
from qaviton_io.utils.types import Tasks
from typing import List
from qaviton_io.logger import Log


def worker(tasks: Tasks, queue: Queue):
    logger = Log()
    logger.queue = queue
    async_manager = AsyncManager()
    try:
        async_manager.run(tasks)
    finally:
        queue.put(logger.log)


class ProcessManager:
    def __init__(self, worker=worker):
        self.CPUs = cpu_count()
        self.queue = Queue()
        self.worker = worker

    def distribute(self, tasks: Tasks)->List[Tasks]:
        cpus = self.CPUs
        number_of_tasks = len(tasks)
        processes = [list() for _ in range(cpus if cpus < number_of_tasks else number_of_tasks)]
        for i, task in enumerate(tasks): processes[i % cpus].append(task)
        return processes

    def run(self, tasks: Tasks) -> List[Task]:
        processes = self.distribute(tasks)
        return [Task(target=self.worker, args=(tasks, self.queue)) for tasks in processes]

    def run_until_complete(self, tasks: Tasks):
        processes = self.run(tasks)
        self.wait_until_tasks_are_done(processes)

    @staticmethod
    def wait_until_tasks_are_done(tasks: List[Task]):
        finished_sessions = 0
        while finished_sessions < len(tasks):
            finished_sessions = 0
            for session in tasks:
                if session.is_finished():
                    finished_sessions += 1
