import logging
from board import Board
import time
from typing import Callable, Optional
from timer import timer
import numpy as np
from collections import defaultdict
from threading import Thread, Lock

'''
# simple logic
def get_distance_ahead(reverse: bool = False, min_angle: float = 45, max_angle: float = 135, lower_threshold: float = 5, upper_threshold: float = 70) -> np.array:
    distances= []
    angle_range = range(min_angle, max_angle + 1, 1) if not reverse else range(max_angle, min_angle - 1, -1)
    for angle in angle_range:
        board.set_servo_angle(board.CMD_SERVO1, angle)
        distance = get_distance()
        if (distance > lower_threshold and distance < upper_threshold):
            distances.append((angle, distance))
    coordinates = np.array([ [ np.cos(np.radians(angle)) * distance, np.sin(np.radians(angle)) * distance ] for (angle, distance) in distances ])
    return coordinates
'''

class DistanceSensor:
    def __init__(self, board: Board, emergency_stop_distance_threshold: float, emergency_stop_callback: Callable[[], None]):
        self.logger = logging.getLogger('DistanceSensor')
        self.board = board
        self.servo = board.CMD_SERVO1

        # Thread control
        self.running = False
        self.thread = None
        self.distances: Optional[np.array] = None
        self.lock = Lock()
        self.emergency_stop_distance_threshold = emergency_stop_distance_threshold
        self.emergency_stop_callback = emergency_stop_callback


    def start(self):
        if not self.running:
            self.running = True
            self.thread = Thread(target=self._distance_loop, daemon=True)
            self.thread.start()
            logging.info('Distance sensor started')
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        logging.info('Distance sensor stopped')

    def _get_distance(self, attempts: int = 2) -> float:
        sum = 0.0
        for _ in range(attempts):
            sum += self.board.get_sonic_distance()
            time.sleep(0.005) # enough time to have sound pass ~1.7m
        return sum / attempts

    @timer
    def _get_distance_ahead_smoothed(self, reverse: bool = False, min_angle: float = 75, max_angle: float = 105, lower_threshold: float = 5, upper_threshold: float = 70, variance_threshold: float = 0.3, measuring_range: int = 7) -> np.array:
        distances = defaultdict(list)
        angle_range = range(min_angle, max_angle + 1, 1) if not reverse else range(max_angle, min_angle - 1, -1)
        for angle in angle_range:
            self.board.set_servo_angle(self.board.CMD_SERVO1, angle)
            distance = self._get_distance()
            if (distance >= lower_threshold and distance <= upper_threshold):
                for a in range(angle + (-1) * measuring_range, angle + measuring_range + 1):
                    distances[a].append(distance)
        smoothed_distances = [ (k, np.array(v).mean()) for k, v in distances.items() if np.array(v).var() < variance_threshold ]
        coordinates = np.array([ [ np.cos(np.radians(angle)) * distance, np.sin(np.radians(angle)) * distance ] for (angle, distance) in smoothed_distances ])
        return coordinates
    
    def _distance_loop(self):
        self.logger.info('Distance sensor loop started')

        is_reversed = False
        
        while self.running:
            distances = self._get_distance_ahead_smoothed(is_reversed)
            if len(distances.shape) == 2:
                with self.lock:
                    self.distances = distances
                is_reversed = not is_reversed
                
                if np.median(distances[:, 1]) < self.emergency_stop_distance_threshold:
                    self.emergency_stop_callback()
        
        self.logger.info('Distance sensor loop started')

    def get_distances(self) -> Optional[np.array]:
        with self.lock:
            try:
                return self.distances
            finally:
                self.distances = None