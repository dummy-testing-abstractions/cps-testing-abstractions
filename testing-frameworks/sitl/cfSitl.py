"""
DESCRIPTION:
Class used for communication with the emulated CF system for software in the loop testing.
The communication is handled with the telnet application layer - see super-class.
The memory addresses in the initialize_registers() function  must manually be entered.

Based on cfhitl.py for hardware in the loop testing.
"""

import telnetlib 
import time
from struct import pack, unpack

class cfSITL(telnetlib.Telnet):

    def __init__(self, addresses, port):
        super().__init__("localhost", port, 10) # init telnet comm
        super().set_debuglevel(0)
        
        super().read_until(b"(monitor)", 2)
        super().write(b"\r")
        super().read_until(b"(monitor)", 1)

        self._addr_book = addresses # dictionary of addresses is provided

        # arificial gyro bias: has to be the same as the one injected in the firmware
        # has to be an integer (despite this is not needed in the firmware) because
        # we will write the integer measurement to the hardware
        self.gyroBias = [0,0,0]

    def initialize_emulation(self):
        super().write(b"i @scripts/single-node/crazyflie.resc\r")
        super().read_until(b"(CF2.1)")
        super().write(b"logLevel -1 sysbus.nrf\r")
        super().read_until(b"(CF2.1)")
        super().write(b"logLevel 3\r")
        super().read_until(b"(CF2.1)")
        super().write(b"emulation RunFor \"0:0:0.1\"\r")
        super().read_until(b"(CF2.1)", 20)

    def pass_startup(self):
        print("Writing to pass startup self tests...")
        super().write(b"emulation RunFor \"0:0:1.9\"\r")
        super().read_until(b"(CF2.1)")
        rdy = self.startReady()
        print(rdy)
        while rdy!=3:
            super().write(b"emulation RunFor \"0:0:3.0\"\r")
            super().read_until(b"(CF2.1)", 360)
            self.write_acc([0,0,9.81])
            self.write_gyro([0,0,0])
            rdy = self.startReady()
            print(rdy)
        print(rdy)
        print("Startup should be passed now")

    def close(self):
        # Function to terminate telnet connection
        # need to sleep a bit before closing the connection 
        # otherwise the last command is usually not executed
        time.sleep(0.1) 
        super().close()

    ######################################
    ### LOW LEVEL READ/WRITE FUNCTIONS ###
    ######################################

    def read_mem(self, addr: str, nbytes: int):
        #Returns an array of strings
        cmd = "sysbus.sram ReadBytes {} {}\r".format(addr, nbytes)
        super().write(cmd.encode())
        super().read_until(b"[\r\r\n")
        read = super().read_until(b", \r\r\n]").removesuffix(b', \r\r\n]').decode("ascii")
        super().read_until(b"(CF2.1)")
        return read

    def read_byte(self, addr: str):
        cmd = "sysbus.sram ReadByte {}\r".format(addr)
        super().write(cmd.encode())
        super().read_until(b"\n\r")
        read = super().read_until(b"\r\r\n").removesuffix(b'\r\r\n').decode("ascii")
        super().read_until(b"(CF2.1)")
        return read

    def read_word(self, addr: str):
        cmd = "sysbus.sram ReadWord {}\r".format(addr)
        super().write(cmd.encode())
        super().read_until(b"\n\r")
        read = super().read_until(b"\r\r\n").removesuffix(b'\r\r\n').decode("ascii")
        super().read_until(b"(CF2.1)")
        return read

    def read_double_word(self, addr: str):
        cmd = "sysbus.sram ReadDoubleWord {}\r".format(addr)
        super().write(cmd.encode())
        super().read_until(b"\n\r")
        read = super().read_until(b"\r\r\n").removesuffix(b'\r\r\n').decode("ascii")
        super().read_until(b"(CF2.1)")
        return read

    # Valid sizes are: "Byte", "Word", "DoubleWord" for 8, 16, 32 bits
    def write_mem(self, addr: str, data: int, size: str):
        super().write("sysbus.sram Write{} {} {}\r".format(size, addr, data).encode())
        super().read_until(b"(CF2.1)")


    #################################
    ### SYNCHRONIZATION FUNCTIONS ###
    #################################

    def stop(self):
        super().interact()

    def runTick(self, time:str):
        super().write(b"emulation RunFor \"0:0:"+time.encode()+b"\"\r")
        super().read_until(b"(CF2.1)")

    def startFlying(self):
        # Function to trigger the boolean that gets the drone out of the waiting 
        # loop in the hover_sitl.c demo app
        self.write_mem(self._addr_book['start'], 0x1, "Byte")

    #########################
    ### READING FUNCTIONS ###
    #########################

    def motors(self):
        # Function that reads all of the motor values and returns them
        # Reads a string of the form "0x00, 0x01, 0x02,". The motor power are the two least significant
        #  bytes of a 32 bit value. Note little endianness
        mP = [byte.strip() for byte in self.read_mem(self._addr_book['motor_ratios_m1'], 0x10).split(',')]
        return [int(msb+lsb.removeprefix('0x'),16) for lsb,msb in zip(mP[0::4], mP[1::4])]

    def startReady(self):
        return int(self.read_byte(self._addr_book['ready']),16) + 2*int(self.read_byte(self._addr_book['gyroBiasFound']),16) 

    def estimatedPosition(self):
        # Function that reads position estimated by the cf
        # stateCompressed is read since it is an integer (in mm to retain precision)
        est = [byte.strip() for byte in self.read_mem(self._addr_book['stateCompressed_x'], 0x6).split(',')]
        return [self.c2ToInt16(int(msb+lsb.removeprefix('0x'),16))/1000 for lsb,msb in zip(est[0::2], est[1::2])]

    def estimatedVelocity(self):
        # Function that reads velocity estimated by the cf
        # stateCompressed is read since it is an integer (in mm to retain precision)
        est = [byte.strip() for byte in self.read_mem(self._addr_book['stateCompressed_vx'], 0x6).split(',')]
        return [self.c2ToInt16(int(msb+lsb.removeprefix('0x'),16))/1000 for lsb,msb in zip(est[0::2], est[1::2])]

    def setPoint(self):
        # Function that reads setpoint from cf
        # stateCompressed is read since it is an integer (in mm to retain precision)
        sp = [byte.strip() for byte in self.read_mem(self._addr_book['setpointCompressed_x'], 0x6).split(',')]
        return [self.c2ToInt16(int(msb+lsb.removeprefix('0x'),16))/1000 for lsb,msb in zip(sp[0::2], sp[1::2])]

    def flowErrors(self):
        # TODO: remove debugging variables from firmware
        etof = self.c2ToInt16(int(self.read_word(self._addr_book['error_tof']),16))/1000
        efx  = self.c2ToInt16(int(self.read_word(self._addr_book['error_flowx']),16))/1000
        efy  = self.c2ToInt16(int(self.read_word(self._addr_book['error_flowy']),16))/1000
        return [etof, efx, efy]

    def readData(self):
        cmd = "sysbus.sram ReadBytes {} 0x6;\
                sysbus.sram ReadBytes {} 0x6;\
                sysbus.sram ReadBytes {} 0x6;\
                sysbus.sram ReadWord {};\
                sysbus.sram ReadWord {};\
                sysbus.sram ReadWord {}\r".format(\
                self._addr_book["stateCompressed_x"],\
                self._addr_book["stateCompressed_vx"],\
                self._addr_book["setpointCompressed_x"],\
                self._addr_book["error_tof"],\
                self._addr_book["error_flowx"],\
                self._addr_book["error_flowy"])
        super().write(cmd.encode())                   
        read = super().read_until(b"(CF2.1)")
        read = [byte.strip(b",") for byte in ((read.partition(b"\n\r"))[2].rpartition(b"\x1b"))[0].split()] # TODO Better way to do it?
        estp = [self.c2ToInt16(int(msb+lsb.removeprefix(b'0x'),16))/1000 for lsb,msb in zip(read[1:7:2], read[2:7:2])]
        estv = [self.c2ToInt16(int(msb+lsb.removeprefix(b'0x'),16))/1000 for lsb,msb in zip(read[9:15:2], read[10:15:2])]
        setp = [self.c2ToInt16(int(msb+lsb.removeprefix(b'0x'),16))/1000 for lsb,msb in zip(read[17:23:2], read[18:23:2])]
        eflw = [self.c2ToInt16(int(word,16))/1000 for word in read[24:27]]
        return (estp,estv,setp,eflw)

    def tickCount(self):
        # read FreeRTOS millisecond tick count
        return int(self.read_double_word(self._addr_book['xTickCount']),16)

    ##########################
    ### WRITING FUNCRTIONS ###
    ##########################

    def write_acc(self, acc):
        # Function to write accelerometer measurements
        cmd = "sysbus.i2c3.bmi_accel FeedAccSample {:f} {:f} {:f}\r".format(self.accelTomg(acc[0]), self.accelTomg(acc[1]), self.accelTomg(acc[2]))
        super().write(cmd.encode())
        super().read_until(b"(CF2.1)")

    def write_gyro(self, gyro):
        # Functin to write gyroscope measurements
        cmd = "sysbus.i2c3.bmi_gyro FeedGyroSample {:f} {:f} {:f}\r".format(self.gyroToDeg(gyro[0]), self.gyroToDeg(gyro[1]), self.gyroToDeg(gyro[2]))
        super().write(cmd.encode())
        super().read_until(b"(CF2.1)")
        cmd = "sysbus.i2c3.bmi_gyro TriggerDataInterrupt\r"
        super().write(cmd.encode())
        super().read_until(b"(CF2.1)")

    def write_opticalflow(self, dpx):
        # Function to write optical flow measurements to the flowdeck thread
        # receives values directly in pixel count (TODO: move here the translation 
        # from [m/s] to pixelcount - currently in the physical model for debugging)
        # INPUT : a vector with two values, respectively pixel count for x and y
        # int16_t accpx = -currentMotion.deltaY
        # int16_t accpy = -currentMotion.deltaX
        mdpxx = self.int16ToC2(-dpx[0])
        mdpxy = self.int16ToC2(-dpx[1])
        Delta = (mdpxx<<16)+mdpxy
        self.write_mem(self._addr_book['accpx'], Delta, "DoubleWord")

    def write_zranger(self, zm:float):
        # Function to write zrange measurement that is obtained with the flkowdeck
        # receivers value in meters but converts into millimiters before writing to the drone.
        # Value to be written is an uint16. Variable is defined in file zranger2.c
        zmm = int(zm*1000) # convert to millimeters
        self.write_mem(self._addr_book['range_last'], zmm, "Word")
    
    def write_sensors(self, acc, gyro, dpx, zm:float):
        mdpxx = self.int16ToC2(-dpx[0])
        mdpxy = self.int16ToC2(-dpx[1])
        Delta = (mdpxx<<16)+mdpxy

        zmm = int(zm*1000) # convert to millimeters

        super().write("sysbus.i2c3.bmi_accel FeedAccSample {:f} {:f} {:f};\
                sysbus.i2c3.bmi_gyro FeedGyroSample {:f} {:f} {:f};\
                sysbus.i2c3.bmi_gyro TriggerDataInterrupt;\
                sysbus.sram WriteDoubleWord {} {};\
                sysbus.sram WriteWord {} {}\r".format(\
                self.accelTomg(acc[0]), self.accelTomg(acc[1]), self.accelTomg(acc[2]),\
                self.gyroToDeg(gyro[0]), self.gyroToDeg(gyro[1]), self.gyroToDeg(gyro[2]),\
                self._addr_book['accpx'], Delta,\
                self._addr_book['range_last'], zmm).encode())
        super().read_until(b"(CF2.1)")

    def write_read(self, acc, gyro, dpx, zm:float, duration:str):
        mdpxx = self.int16ToC2(-dpx[0])
        mdpxy = self.int16ToC2(-dpx[1])
        Delta = (mdpxx<<16)+mdpxy
        zmm = int(zm*1000) # convert to millimeters

        cmd = "sysbus.i2c3.bmi_accel FeedAccSample {:f} {:f} {:f};\
                sysbus.i2c3.bmi_gyro FeedGyroSample {:f} {:f} {:f};\
                sysbus.i2c3.bmi_gyro TriggerDataInterrupt;\
                sysbus.sram WriteDoubleWord {} {};\
                sysbus.sram WriteWord {} {};\
                sysbus.sram ReadBytes {} 0x6;\
                sysbus.sram ReadBytes {} 0x6;\
                sysbus.sram ReadBytes {} 0x6;\
                sysbus.sram ReadWord {};\
                sysbus.sram ReadWord {};\
                sysbus.sram ReadWord {};\
                emulation RunFor \"0:0:{}\"\r".format(\
                self.accelTomg(acc[0]), self.accelTomg(acc[1]), self.accelTomg(acc[2]),\
                self.gyroToDeg(gyro[0]), self.gyroToDeg(gyro[1]), self.gyroToDeg(gyro[2]),\
                self._addr_book['accpx'], Delta,\
                self._addr_book['range_last'], zmm,\
                self._addr_book["stateCompressed_x"],\
                self._addr_book["stateCompressed_vx"],\
                self._addr_book["setpointCompressed_x"],\
                self._addr_book["error_tof"],\
                self._addr_book["error_flowx"],\
                self._addr_book["error_flowy"],\
                duration)
        super().write(cmd.encode())
        read = super().read_until(b"(CF2.1)")
        read = [byte.strip(b",") for byte in ((read.partition(b"\n\r"))[2].rpartition(b"\x1b"))[0].split()] # TODO Better way to do it?
        estp = [self.c2ToInt16(int(msb+lsb.removeprefix(b'0x'),16))/1000 for lsb,msb in zip(read[1:7:2], read[2:7:2])]
        estv = [self.c2ToInt16(int(msb+lsb.removeprefix(b'0x'),16))/1000 for lsb,msb in zip(read[9:15:2], read[10:15:2])]
        setp = [self.c2ToInt16(int(msb+lsb.removeprefix(b'0x'),16))/1000 for lsb,msb in zip(read[17:23:2], read[18:23:2])]
        eflw = [self.c2ToInt16(int(word,16))/1000 for word in read[24:27]]
        return (estp,estv,setp,eflw)

    def idle(self):
        super().write(b"sysbus.i2c3.bmi_gyro TriggerDataInterrupt; emulation RunFor \"0:0:0.001\"\r")
        super().read_until(b"(CF2.1)")

    ######################################
    ### UTILITY TRANSLATION FUNCRTIONS ###
    ######################################

    def accelTomg(self, num):
        num = num*1000/(9.81)
        return num#self.int16ToC2(num)

    def gyroToDeg(self, num) : 
        # Function formats an gyro value to the format of the
        # gyroRaw_hitl variable of the crazyflie firmware. 
        num = (180/3.1415926)*num       # gyro is measured in degrees
        return num#self.int16ToC2(num)

    def c2ToInt16(self,num):
        # Function to translate unsigned integers in C2 to signed integers
        if num<=pow(2,15)-1 :
            return num
        else :
            return num - pow(2,16)

    def int16ToC2(self,num):
        # Function to translate signed integers to unsigned C2 representation
        # with saturation included
        num = max(min(num,pow(2,15)-1),-pow(2,15)) # has to fit in int16
        if num<0 :
            num = (pow(2,16) + num) # C2 
        return int(num)
