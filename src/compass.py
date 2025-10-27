from collections import defaultdict
import random
import statistics
from threading import Lock, Thread
import time
from typing import Callable, Dict, List
from collections import deque

type Callback = Callable[[int], None]

class Compass:
    def __init__(self, granularity: int = 5):
        self.granularity = granularity
        self.lock = Lock()
        self.callbacks: Dict[int, List[Callback]] = defaultdict(list)
        self.thread = None
        self.running = False
        self.headings = deque([], maxlen=5)

    def register_callback(self, heading: int, callback: Callback):
        with self.lock:
            self.callbacks[heading].append(callback)

    def _run_callbacks(self, current_heading: int):
        start_heading = (current_heading - self.granularity // 2)
        stop_heading = (current_heading + self.granularity // 2)
        with self.lock:
            for raw_heading in range(start_heading, stop_heading + 1, 1):
                heading = (raw_heading + 360) % 360
                callbacks = self.callbacks[heading]
                for callback in callbacks:
                    callback(current_heading)
                self.callbacks[heading] = []

    def start(self):
        self.running = True

        self.thread = Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            heading = random.randrange(-360, 360, 1)
            with self.lock:
                self.headings.append(heading)
            self._run_callbacks(self.get_heading())
            time.sleep(0.1)

    def get_heading(self):
        with self.lock:
            return statistics.mean(self.headings)