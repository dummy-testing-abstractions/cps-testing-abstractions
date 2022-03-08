"""
This class is used to get the addresses of interest for the 
hitl and sitl testing automatically from the .map file.
"""

import os

class cfAddresses():

    def __init__(self, keepOffset=True):
        self.myDir = "getaddresses/"
        self.addresses = dict() # init dictionary memory addresses 
        
        # call tcl script
        os.system("tclsh " + self.myDir + "getaddresses.tcl")
        # open addresses file and 
        with open(self.myDir+"addresses.txt") as f:
            lines = f.readlines()

        #iterate over retrieve addresses and store in dictionary
        for line in lines:
            line = line.split(" ")
            #the sitl set up doesn't need the offset of the addresses
            if not(keepOffset):
                line[2]=line[2][1:len(line[2])]
            #handle addresses next to each other and then single ones (else branch)
            #this leverages that dictionary uses same names as firmware
            if (line[0]=="motor_ratios"):
                self.addresses["motor_ratios_m1"] = "0x{:x}".format(int(line[2],16)+0x0)
                self.addresses["motor_ratios_m2"] = "0x{:x}".format(int(line[2],16)+0x4)
                self.addresses["motor_ratios_m3"] = "0x{:x}".format(int(line[2],16)+0x8)
                self.addresses["motor_ratios_m4"] = "0x{:x}".format(int(line[2],16)+0xc)
            elif (line[0]=="accelRaw"):
                self.addresses["accelRaw_x"] = "0x{:x}".format(int(line[2],16)+0x0)
                self.addresses["accelRaw_y"] = "0x{:x}".format(int(line[2],16)+0x2)
                self.addresses["accelRaw_z"] = "0x{:x}".format(int(line[2],16)+0x4)
            elif (line[0]=="gyroRaw"):
                self.addresses["gyroRaw_x"] = "0x{:x}".format(int(line[2],16)+0x0)
                self.addresses["gyroRaw_y"] = "0x{:x}".format(int(line[2],16)+0x2)
                self.addresses["gyroRaw_z"] = "0x{:x}".format(int(line[2],16)+0x4)
            elif (line[0]=="currentMotion"):
                # In motionBurst_t, bytes 2-3 are for deltaX and 4-5 for deltaY
                #TODO rename
                self.addresses["accpx"] = "0x{:x}".format(int(line[2],16)+0x2)
                self.addresses["accpy"] = "0x{:x}".format(int(line[2],16)+0x4)
            elif (line[0]=="stateCompressed"):
                self.addresses["stateCompressed_x"] = "0x{:x}".format(int(line[2],16)+0x0)
                self.addresses["stateCompressed_y"] = "0x{:x}".format(int(line[2],16)+0x2)
                self.addresses["stateCompressed_z"] = "0x{:x}".format(int(line[2],16)+0x4)
                self.addresses["stateCompressed_vx"] = "0x{:x}".format(int(line[2],16)+0x6)
                self.addresses["stateCompressed_vy"] = "0x{:x}".format(int(line[2],16)+0x8)
                self.addresses["stateCompressed_vz"] = "0x{:x}".format(int(line[2],16)+0xa)
                self.addresses["stateCompressed_ax"] = "0x{:x}".format(int(line[2],16)+0xc)
                self.addresses["stateCompressed_ay"] = "0x{:x}".format(int(line[2],16)+0xe)
                self.addresses["stateCompressed_az"] = "0x{:x}".format(int(line[2],16)+0x10)
            elif (line[0]=="setpointCompressed"):
                self.addresses["setpointCompressed_x"] = "0x{:x}".format(int(line[2],16)+0x0)
                self.addresses["setpointCompressed_y"] = "0x{:x}".format(int(line[2],16)+0x2)
                self.addresses["setpointCompressed_z"] = "0x{:x}".format(int(line[2],16)+0x4)
            elif (line[0]=="sensorsTask"):
                # we want the breakpoint right after the start of the sensors task
                # the shift of 24 addresses is empirically obtained. If the breakpoint 
                # is never hit, set this address manually, for example with the address 
                # of "b sensors_bmi088_bmp388.c:320" when using gdb
                self.addresses["sensorsTask"] = "0x{:x}".format(int(line[2],16)+0x24)
            else :
                self.addresses[line[0]] = "0x{:x}".format(int(line[2],16))
        
    def get(self):
        return self.addresses


