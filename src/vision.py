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
from abc import ABC, abstractmethod

WIDTH = 640
HEIGHT = 480
FPS = 30

class TargetDetector(ABC):
    def __init__(self, camera_index: int = 0, confidence: float = 0.7, object_class: int = 1, logger_name: str = 'TargetDetector'):
        self.logger = logging.getLogger(logger_name)
        self.capture_thread = None
        self.detect_thread = None
        self.camera = None
        self.confidence = confidence
        self.object_class = object_class
        self.image: Optional[any] = None
        self.has_image: bool = False
        self.target: Optional[Tuple[int, int]] = None
        self.image_lock = Lock()
        self.target_lock = Lock()
        self.running = False

    def start(self):
        self._call_model(np.zeros((640, 480, 3)))
        
        self.running = True

        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        self.camera.set(cv2.CAP_PROP_FPS, FPS)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))

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
        counter = 0
        while self.running:
            try:
                for _ in range(2):
                    self.camera.grab()
                has_image, image = self.camera.retrieve()
                self.logger.debug("Retrieved: %s, %s, %s", has_image, type(image), counter)
                if has_image:
                    with self.image_lock:
                        self.image = image
                        self.has_image = True
            finally:
                time.sleep(1.0 / (FPS-1))

    @abstractmethod
    def _find_object(self, results, image, object_class: int, confidence_threshold: float) -> Optional[Tuple[int, int, int, int]]:
        pass

    @abstractmethod
    def _call_model(self, image):
        pass

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
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    results = self._call_model(image)
    
                    found_object = self._find_object(results, image, self.object_class, self.confidence)
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



# wget https://github.com/chuanqi305/MobileNet-SSD/raw/master/deploy.prototxt
# wget https://github.com/chuanqi305/MobileNet-SSD/raw/master/mobilenet_iter_73000.caffemodel

class TargetDetectorMobileNet(TargetDetector):
    def __init__(self, camera_index: int = 0, confidence: float = 0.7, object_class: int = 15):
        super().__init__(camera_index, confidence, object_class, 'TargetDetectorMobileNet')
        self.mobile_net = cv2.dnn.readNetFromCaffe(
            'deploy.prototxt',
            'mobilenet_iter_73000.caffemodel'
        )

    def _find_object(self, results, image, object_class: int, confidence_threshold: float) -> Optional[Tuple[int, int, int, int]]:
        for i in range(results.shape[2]):
            confidence = results[0, 0, i, 2]
            
            if confidence > confidence_threshold:
                object_class_id = int(results[0, 0, i, 1])
    
                if object_class_id == object_class:
                    height, width = image.shape[:2]
                    box = results[0, 0, i, 3:7] * np.array([width, height, width, height])
                    (x1, y1, x2, y2) = box.astype('int')
                    return (int((x2-x1)//2+x1), int((y2-y1)//2+y1), int(x2-x1), int(y2-y1)) #midpoint
        return None

    @timer
    def _call_model(self, image):
        blob = cv2.dnn.blobFromImage(image, 0.007843, (300, 300), 127.5)
        self.mobile_net.setInput(blob)
        return self.mobile_net.forward()



class TargetDetectorYolo(TargetDetector):
    def __init__(self, camera_index: int = 0, confidence: float = 0.5, object_class: int = 0):
        super().__init__(camera_index, confidence, object_class, 'TargetDetectorYolo')
        self.model = YOLO('yolo12n.pt')

    def _find_object(self, results: Results, image, object_class: int, confidence: float) -> Optional[Tuple[int, int, int, int]]:
        for result in results:
            boxes = result.boxes
            self.logger.debug('Boxes: %s', boxes)
            if (boxes.cls[0] == object_class) and (boxes.conf[0] >= confidence):
                (x, y, w, h) = boxes.xywh[0]
                return (int(x), int(y), int(w), int(h))
        return None

    @timer
    def _call_model(self, image):
        return self.model(image, verbose=False)[0]