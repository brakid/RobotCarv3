# https://github.com/e-Gizmo/QMC5883L-GY-271-Compass-module/blob/master/QMC5883L%20Datasheet%201.0%20.pdf
import smbus
import time
from threading import Lock
import ctypes
import math

class Compass:
    CONFIG_REGISTER_1 =     0x09
    CONFIG_REGISTER_2 =     0x0A
    RESET_REGISTER =        0x0B
    
    STANDBY_MODE =          0b00 << 0
    CONTINUOUS_MODE =       0b01 << 0
    DATA_RATE_10 =          0b00 << 2
    DATA_RATE_50 =          0b01 << 2
    DATA_RATE_100 =         0b10 << 2
    DATA_RATE_200 =         0b11 << 2
    GAUSS_2 =               0b00 << 4
    GAUSS_8 =               0b01 << 4
    OVERSAMPLING_512 =      0b00 << 6
    OVERSAMPLING_256 =      0b01 << 6
    OVERSAMPLING_128 =      0b10 << 6
    OVERSAMPLING_64 =       0b11 << 6
    CONFIG_REGISTER_VALUE = CONTINUOUS_MODE | DATA_RATE_200 | GAUSS_2 | OVERSAMPLING_512
    
    def __init__(self, addr=0x0d):
        self.address = addr
        self.bus = smbus.SMBus(1)
        self.bus.open(1)
        self.mutex = Lock()

        with self.mutex:
            try:
                self.bus.write_byte_data(self.address, self.RESET_REGISTER, 0x01) # reset
                self.bus.write_byte_data(self.address, self.CONFIG_REGISTER_1, self.CONFIG_REGISTER_VALUE)
                self.bus.write_byte_data(self.address, self.CONFIG_REGISTER_2, 0x00)
                time.sleep(0.05)
            except IOError as err:
                print(err)

    def get_heading(self, heading_correction: float = 2.88) -> float: # https://www.magnetic-declination.com/Luxembourg/Letzeburg/1528005.html
        with self.mutex:
            x = self.bus.read_byte_data(self.address, 0x01) << 8
            x |= self.bus.read_byte_data(self.address, 0x00)
            x = ctypes.c_int16(x).value
            y = self.bus.read_byte_data(self.address, 0x03) << 8
            y |= self.bus.read_byte_data(self.address, 0x02)
            y = ctypes.c_int16(y).value
            z = self.bus.read_byte_data(self.address, 0x05) << 8
            z |= self.bus.read_byte_data(self.address, 0x04)
            z = ctypes.c_int16(z).value
            temp = self.bus.read_byte_data(self.address, 0x08) << 8
            temp |= self.bus.read_byte_data(self.address, 0x07)
            temp = ctypes.c_int16(temp).value
            status = self.bus.read_byte_data(self.address, 0x06)
            #print(x, y, z, temp)
    
            heading = math.degrees(math.atan2(y, x))
            heading += 2.88 # https://www.magnetic-declination.com/Luxembourg/Letzeburg/1528005.html
            heading %= 360
            return heading