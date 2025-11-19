from compass import Compass
import logging
import time
from typing import Optional
from timer import timer
import numpy as np
from collections import defaultdict
from threading import Thread, Lock

class CompassSensor:
    def __init__(self, compass: Compass):
        self.logger = logging.getLogger('CompassSensor')
        self.compass = compass

        # Thread control
        self.running = False
        self.thread = None
        self.heading: Optional[float] = None
        self.lock = Lock()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = Thread(target=self._compass_loop, daemon=True)
            self.thread.start()
            logging.info('Compass sensor started')
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        logging.info('Compass sensor stopped')

    #@timer
    def _get_heading(self, attempts: int = 5) -> float:
        sum = 0.0
        for _ in range(attempts):
            sum += self.compass.get_heading()
            time.sleep(0.005) # 200 HZ compass
        return sum / attempts
    
    def _compass_loop(self):
        self.logger.info('Compass sensor loop started')
        
        while self.running:
            with self.lock:
                self.heading = self._get_heading()
                
        self.logger.info('Compass sensor loop stopped')

    def get_heading(self) -> Optional[float]:
        with self.lock:
            try:
                return self.heading
            finally:
                self.heading = None