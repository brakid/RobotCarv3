from ultralytics.engine.results import Results
from ultralytics import YOLO
import cv2
from matplotlib import pyplot as plt
import numpy as np
from typing import Optional, Tuple
from collections.abc import Callable
from threading import Thread, Lock
import time
import logging
from timer import timer

WIDTH = 640
HEIGHT = 480
FPS = 15

class TargetDetector:
    def __init__(self, camera_index: int = 0, confidence: float = 0.7, object_class: int = 0):
        self.logger = logging.getLogger('TargetDetector')
        self.capture_thread = None
        self.detect_thread = None
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        self.camera.set(cv2.CAP_PROP_FPS, FPS)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.model = YOLO('yolo12n.pt')
        self.model(np.zeros((640, 480, 3)))
        self.confidence = confidence
        self.object_class = object_class
        self.image: Optional[any] = None
        self.has_image: bool = False
        self.target: Optional[Tuple[int, int]] = None
        self.image_lock = Lock()
        self.target_lock = Lock()
        self.running = False

    def start(self):
        self.running = True

        # Start capture thread
        self.camera_thread = Thread(target=self._capture)
        self.camera_thread.daemon = True
        self.camera_thread.start()
        # Start detection thread
        self.detect_thread = Thread(target=self._detect)
        self.detect_thread.daemon = True
        self.detect_thread.start()

    def _capture(self):
        self.logger.info('Capture thread started')
        while self.running:
            try:
                has_image, image = self.camera.read()
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                with self.image_lock:
                    self.image = image
                    self.has_image = has_image
                
            finally:
                time.sleep(1.0 / FPS)

    def _find_object(self, yolo_results: Results, object_class: int, confidence: float) -> Optional[Tuple[int, int, int, int]]:
        for result in yolo_results:
            boxes = result.boxes
            self.logger.debug('Boxes: %s', boxes)
            if (boxes.cls[0] == object_class) and (boxes.conf[0] >= confidence):
                (x, y, w, h) = boxes.xywh[0]
                return (int(x), int(y), int(w), int(h))
        return None

    @timer
    def _call_model(self, image):
        return self.model(image, verbose=False)[0]

    def _detect(self):
        self.logger.info('Detect thread started')
        while self.running:
            try:
                image = None
                has_image = False
                with self.image_lock:
                    if self.has_image:
                        image = self.image.copy()
                        has_image = True
                        self.has_image = False

                if has_image:
                    results = self._call_model(image)
    
                    found_object = self._find_object(results, self.object_class, self.confidence)
                    if found_object:
                        x, y, _, _ = found_object
                        self.logger.debug('Finding: %s %s', x, y)
                        with self.target_lock:
                            self.target = (x, y)                
            except Exception as e:
                print('Error', e)

    def get_target(self):
        with self.target_lock:
            try:
                return self.target
            finally:
                self.target = None

    def stop(self):
        self.running = False
        del self.camera