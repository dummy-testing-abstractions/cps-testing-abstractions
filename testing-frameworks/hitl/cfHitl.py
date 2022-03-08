"""
DESCRIPTION:
Class implementing communication with the cf hardware for hardware
in the loop testing. The communication is handled with the telnet
application layer - see super-class. The memory 
addresses of the variables of interest have to be defined in the 
initialize_registers() function.
"""

import telnetlib 
import time

class cfHITL(telnetlib.Telnet):

    def __init__(self, addresses):
        # Init Function: it established communication with openocd and initializes
        # the needed variables.
        super().__init__("localhost", 4444) # init telnet comm
        super().set_debuglevel(0)
        super().write(b"\n")                # TODO: check if this is needed
        self._addr_book = addresses         # dictionary memory addresses from above
        super().read_until(b"\r\n")         # read openocd header

        # arificial gyro bias
        # has to be an integer (despite this is not needed in the firmware) because
        # we will write the integer measurement to the hardware
        self.gyroBias = [0,0,0]

    def close(self):
        # Function to terminate telnet connection
        # need to sleep a bit before closing the connection 
        # otherwise the last command is usually not executed
        time.sleep(0.1) 
        super().close()

    def add_mem_addr(self, identifier: str, addr: str):
        # Function to add the memory addresses of the variables in the firmware
        self._addr_book[identifier] = addr

    ######################################
    ### LOW LEVEL READ/WRITE FUNCTIONS ###
    ######################################

    def read_mem_addr(self, addr: str):
        # Function to read from a given memory address as integer
        cmd = format("mdh %s \n" % addr)   # build openocd command
        super().write(cmd.encode())        # send command to openocd
        reply = format("%s: " % addr)      # expected reply from openocd
        super().read_until(reply.encode()) # flush openocd echo
        read = super().read_until(b"\r\n") # actual memory read and function return
        return int(read.decode('ascii').split()[0],16) # extract and convert to int

    def write_mem_addr(self, addr: str, message: str, write_full_word=False):
        # Function to write to a given memory address
        # half word (2 bytes) is written unless the optional argument is set to true
        if int(message)<0:
            print("negative write to "+addr)
        cmd = "mww " if write_full_word else "mwh "
        stringa = cmd + addr + ' ' + message + " \n" # build openocd command
        super().write(stringa.encode())              # send command
        super().read_until(b"\r\n")                  # no echo output to handle

    #################################
    ### SYNCHRONIZATION FUNCTIONS ###
    #################################

    def stop(self):
        # Function to make the microcontroller sleep 
        cmd = "halt \n"
        super().write(cmd.encode())    # send command
        super().read_until(b"\r\n")    # read empty line
        super().read_until(b"\r\n")    # read echo of halt command
        super().read_until(b"\r\n")    # read target halted message
        super().read_until(b"\r\n")    # read pxPSR pc and psp printout

    def resume(self):
        # Function to awake the microcontroller after a sleep call or a breakpoint
        cmd = "resume \n"
        super().write(cmd.encode())    # send command
        super().read_until(b"\r\n")    # read echo of resume command

    def startFlying(self):
        # Function to trigger the boolean that gets the drone out of the waiting 
        self.write_mem_addr(self._addr_book['start'], str(1))

    def waitBreakpointHit(self):
        # Function to wait until hit of breakpoint
        super().read_until(b"\r\n")    # read halted due to breakpoint
        super().read_until(b"\r\n")    # read pxPSR pc and psp printout

    def addIMUBreakpoint(self):
        # Function to add a breakpoint at the beginning of the sensors task loop address.
        # Hardware breakpoint is used but there is no significant speed
        # improvement
        cmd = "bp " + self._addr_book['sensorsTask'] + " 2 hw \n"
        super().write(cmd.encode())    # send command
        super().read_until(b"\r\n")    # read echo of bp command
        super().read_until(b"\r\n")    # read breakpoint set message
        
    def removeIMUBreakpoint(self):
        # Function to remove breakpoint at given address
        time.sleep(0.2) # not sure it is necessary but you never know
        cmd = "rbp " + self._addr_book['sensorsTask'] + " \n" #"rbp 0x801d2f2 \n" 
        super().write(cmd.encode())    # send command
        super().read_until(b"\r\n")    # read echo of rbp command

    #########################
    ### READING FUNCTIONS ###
    #########################

    def motors(self):
        # Function that reads all of the motor values and returns them
        m1 = self.read_mem_addr(self._addr_book['motor_ratios_m1'])
        m2 = self.read_mem_addr(self._addr_book['motor_ratios_m2'])
        m3 = self.read_mem_addr(self._addr_book['motor_ratios_m3'])
        m4 = self.read_mem_addr(self._addr_book['motor_ratios_m4'])
        return [m1, m2, m3, m4]

    def estimatedPosition(self):
        # Function that reads position estimated by the cf
        # stateCompressed is read since it is an integer (in mm to retain precision)
        x = self.c2ToInt16(self.read_mem_addr(self._addr_book['stateCompressed_x']))/1000
        y = self.c2ToInt16(self.read_mem_addr(self._addr_book['stateCompressed_y']))/1000
        z = self.c2ToInt16(self.read_mem_addr(self._addr_book['stateCompressed_z']))/1000
        return [x,y,z]

    def estimatedVelocity(self):
        # Function that reads velocity estimated by the cf
        # stateCompressed is read since it is an integer (in mm to retain precision)
        vx = self.c2ToInt16(self.read_mem_addr(self._addr_book['stateCompressed_vx']))/1000
        vy = self.c2ToInt16(self.read_mem_addr(self._addr_book['stateCompressed_vy']))/1000
        vz = self.c2ToInt16(self.read_mem_addr(self._addr_book['stateCompressed_vz']))/1000
        return [vx,vy,vz]

    def setPoint(self):
        # Function that reads setpoint from cf
        # stateCompressed is read since it is an integer (in mm to retain precision)
        x = self.c2ToInt16(self.read_mem_addr(self._addr_book['setpointCompressed_x']))/1000
        y = self.c2ToInt16(self.read_mem_addr(self._addr_book['setpointCompressed_y']))/1000
        z = self.c2ToInt16(self.read_mem_addr(self._addr_book['setpointCompressed_z']))/1000
        return [x,y,z]

    def flowErrors(self):
        # TODO: remove debugging variables from firmware
        etof = self.c2ToInt16(self.read_mem_addr(self._addr_book['error_tof']))/1000
        efx  = self.c2ToInt16(self.read_mem_addr(self._addr_book['error_flowx']))/1000
        efy  = self.c2ToInt16(self.read_mem_addr(self._addr_book['error_flowy']))/1000
        return [etof, efx, efy]

    def tickCount(self):
        # read FreeRTOS millisecond tick count
        return self.read_mem_addr(self._addr_book['xTickCount'])

    ##########################
    ### WRITING FUNCRTIONS ###
    ##########################

    def write_pressure(self, pressure:float):
        # Function to write pressure measurements
        # WARNING THIS IS BROKEN (CONVERSION TO FLOAT IS MISSING)
        # but it is not used when zrange measurements is availablbe
        # TODO: convert to float
        self.write_mem_addr(self._addr_book['data_pressure_hitl'], str(pressure),   write_full_word=True)

    def write_acc(self, acc):
        # Function to write accelerometer measurements
        self.write_mem_addr(self._addr_book['accelRaw_x'], str(self.accelToLSB(acc[0])))
        self.write_mem_addr(self._addr_book['accelRaw_y'], str(self.accelToLSB(acc[1])))
        self.write_mem_addr(self._addr_book['accelRaw_z'], str(self.accelToLSB(acc[2])))

    def write_gyro(self, gyro):
        # Function to write gyroscope measurements
        self.write_mem_addr(self._addr_book['gyroRaw_x'], str(self.gyroToLSB(gyro[0])+self.gyroBias[0]))
        self.write_mem_addr(self._addr_book['gyroRaw_y'], str(self.gyroToLSB(gyro[1])+self.gyroBias[1]))
        self.write_mem_addr(self._addr_book['gyroRaw_z'], str(self.gyroToLSB(gyro[2])+self.gyroBias[2]))

    def write_zranger(self, zm:float):
        # Function to write zrange measurement that is obtained with the flkowdeck
        # receivers value in meters but converts into millimiters before writing to the drone.
        # Value to be written is an uint16. Variable is defined in file zranger2.c
        zmm = int(zm*1000) # convert to millimeters
        self.write_mem_addr(self._addr_book['range_last'], str(zmm), write_full_word=False)
    
    def write_opticalflow(self, dpx):
        # Function to write optical flow measurements to the flowdeck thread
        # receives values directly in pixel count (TODO: move here the translation 
        # from [m/s] to pixelcount - currently in the physical model for debugging)
        # INPUT : a vector with two values, respectively pixel count for x and y
        # note that in firmware they are swapped and inverted in the sign
        self.write_mem_addr(self._addr_book['accpx'],str(self.int16ToC2(-dpx[1])), write_full_word=False)
        self.write_mem_addr(self._addr_book['accpy'],str(self.int16ToC2(-dpx[0])), write_full_word=False)

    ######################################
    ### UTILITY TRANSLATION FUNCRTIONS ###
    ######################################

    def accelToLSB(self, num) : 
        # Function translates an acceleration value to the format of the
        # accelRaw_hitl variable of the crazyflie firmware. 
        num = num/9.81             # acceleration is in g in the firmware
        num = num * 65536/(2*24)   # scale to LSB
        return self.int16ToC2(num)

    def gyroToLSB(self, num) : 
        # Function formats an gyro value to the format of the
        # gyroRaw_hitl variable of the crazyflie firmware. 
        num = (180/3.1415926)*num       # gyro is measured in degrees
        num = num * 65536/(2*2000)  # scale to LSB
        return self.int16ToC2(num)

    def c2ToInt16(self,num):
        # Function to translate unsigned integers in C2 to signed integers
        if num<=pow(2,15)-1 :
            return num
        else :
            return num - pow(2,16)

    def int16ToC2(self,num):
        # Function to translate signed integers to unsigned C2 representation
        # with saturation included
        # add 0.5 to improve rounding
        num = max(min(num+0.5,pow(2,15)-1),-pow(2,15)) # has to fit in int16
        if num<0 :
            num = (pow(2,16) + num) # C2 
        return int(num)

