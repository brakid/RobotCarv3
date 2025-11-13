from board import Board
import threading
import time
import queue
from enum import Enum

SPEED = 500

class Direction(Enum):
    FORWARD = 'forward'
    LEFT = 'left'
    RIGHT = 'right'
    NONE = 'none'

class MotorController:
    def __init__(self, board):
        self.board = board
        self.board.stop()

        # Thread control
        self.running = False
        self.thread = None
        self.direction_queue = queue.Queue()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._control_loop, daemon=True)
            self.thread.start()
            print("Motor controller started")
    
    def stop(self):
        self.board.stop()
        self.running = False
        if self.thread:
            self.thread.join()
        print("Motor controller stopped")
    
    def send_direction(self, direction, duration: float = 0.5):
        self.direction_queue.put((direction, duration))

    def _control_loop(self):
        print("Motor control loop started")

        command_until = 0
        
        while self.running:
            # Process any pending commands
            try:
                direction, duration = None, None
                while not self.direction_queue.empty():
                    direction, duration = self.direction_queue.get_nowait()
                if direction:
                    print(f"Direction: {direction}, duration: {duration}ms")
                    if direction == Direction.FORWARD:
                        self.board.forward(SPEED)
                    elif direction == Direction.LEFT:
                        self.board.turn_left(SPEED)
                    elif direction == Direction.RIGHT:
                        self.board.turn_right(SPEED)
                    else:
                        self.board.stop()
                    command_until = time.time() + duration
            except queue.Empty:
                pass

            now = time.time()
            if now > command_until:
                self.board.stop()

            time.sleep(0.01)
        
        print("Motor control loop stopped")