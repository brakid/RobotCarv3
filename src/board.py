import smbus
import time
from threading import Lock

class Board:
    CMD_SERVO1 = 0
    CMD_PWM1 = 4
    CMD_PWM2 = 5
    CMD_DIR1 = 6
    CMD_DIR2 = 7
    CMD_SONIC = 12
    SONIC_MAX_HIGH_BYTE = 50
    SERVO_MAX_PULSE_WIDTH = 2500
    SERVO_MIN_PULSE_WIDTH = 500
    
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

    def _read_register(self, target: int) -> int:		
        with self.mutex:
            self.bus.write_byte(self.address, target)
            high_byte = self.bus.read_byte_data(self.address, target)
            
            self.bus.write_byte(self.address, target + 1)
            low_byte = self.bus.read_byte_data(self.address, target + 1)
            
            if(high_byte < self.SONIC_MAX_HIGH_BYTE):
                return high_byte << 8 | low_byte
            else:
                return 0

    def _convert_angle_to_servo_pwm(self, angle: float) -> int:
        return int((self.SERVO_MAX_PULSE_WIDTH - self.SERVO_MIN_PULSE_WIDTH) * angle / 180.0 + self.SERVO_MIN_PULSE_WIDTH)

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

    def set_servo_angle(self, servo: int, angle: float):
        self._write_registers(servo, self._convert_angle_to_servo_pwm(angle))

    def get_sonic_distance(self):
        sonic_time = self._read_register(self.CMD_SONIC)
        distance = sonic_time * 0.5 * 343.0 / 10000.0
        return distance