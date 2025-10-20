import smbus
import time
from threading import Lock

class Board:
    CMD_PWM1 = 4
    CMD_PWM2 = 5
    CMD_DIR1 = 6
    CMD_DIR2 = 7
    def __init__(self, addr=0x18):
        self.address = addr
        self.bus=smbus.SMBus(1)
        self.bus.open(1)
        self.mutex = Lock()

    def _write_registers(self, target: int, value: any):
        with self.mutex:
            value = int(value)
            data = [value>>8, value&0xff]
            try:
                self.bus.write_i2c_block_data(self.address, target, data)
                time.sleep(0.001)
                self.bus.write_i2c_block_data(self.address, target, data)
                time.sleep(0.001)
                self.bus.write_i2c_block_data(self.address, target, data)
                time.sleep(0.001)
            except Exception as e:
                print('I2C Error :', e)

    def stop(self):
        self._write_registers(self.CMD_DIR1, 1)
        self._write_registers(self.CMD_DIR2, 1)
        
        self._write_registers(self.CMD_PWM1, 0)
        self._write_registers(self.CMD_PWM2, 0)
    
    def forward(self, pwm: int = 500):
        self._write_registers(self.CMD_DIR1, 1)
        self._write_registers(self.CMD_DIR2, 1)

        self._write_registers(self.CMD_PWM1, 1000)
        self._write_registers(self.CMD_PWM2, 1000)
        self._write_registers(self.CMD_PWM1, pwm)
        self._write_registers(self.CMD_PWM2, pwm)

    def backward(self, pwm: int = 500):
        self._write_registers(self.CMD_DIR1, 0)
        self._write_registers(self.CMD_DIR2, 0)
        
        self._write_registers(self.CMD_PWM1, 1000)
        self._write_registers(self.CMD_PWM2, 1000)
        self._write_registers(self.CMD_PWM1, pwm)
        self._write_registers(self.CMD_PWM2, pwm)

    def turn_left(self, pwm: int = 500):
        self._write_registers(self.CMD_DIR1, 1)
        self._write_registers(self.CMD_DIR2, 0)
        
        self._write_registers(self.CMD_PWM1, 1000)
        self._write_registers(self.CMD_PWM2, 1000)
        self._write_registers(self.CMD_PWM1, pwm)
        self._write_registers(self.CMD_PWM2, pwm)
    
    def turn_right(self, pwm: int = 500):
        self._write_registers(self.CMD_DIR1, 0)
        self._write_registers(self.CMD_DIR2, 1)
        
        self._write_registers(self.CMD_PWM1, 1000)
        self._write_registers(self.CMD_PWM2, 1000)
        self._write_registers(self.CMD_PWM1, pwm)
        self._write_registers(self.CMD_PWM2, pwm)