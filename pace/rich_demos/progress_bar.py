"""Progress bar demo for PACE."""

import time
from random import randint
from threading import Thread

from rich.progress import Progress, TaskID


def _task(progress: Progress, task_id: TaskID, sleep_time: float) -> None:
    """Advance a single progress bar task with a fixed sleep interval."""
    for _ in range(100):
        progress.update(task_id, advance=1)
        time.sleep(sleep_time / 100)


def run() -> None:
    """Run the progress bar demo.

    This demo includes 8 different progress bars, each executing tasks on different threads.
    """
    with Progress() as progress:
        threads: list[Thread] = []
        for i in range(8):
            task_id: TaskID = progress.add_task(f"Task {i + 1}", total=100)
            sleep_time = randint(1, 10)
            thread = Thread(target=_task, args=(progress, task_id, sleep_time))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
