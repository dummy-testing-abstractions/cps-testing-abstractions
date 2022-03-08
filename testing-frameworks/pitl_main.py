import sys
import pitl.cfusdlog
from plot.Plot import Storage
import numpy as np

if len(sys.argv) != 2:
  print('\033[91mError:\033[0m please enter name of raw data log file')
  exit()

logData = pitl.cfusdlog.decode(sys.argv[1])
dataA = logData['stabilizerLoopA']
dataB = logData['stabilizerLoopB']
# Due to limitations the events occur with ~0.02 ms delay
t = dataA['timestamp']
n = len(t)
#t = logData['stabilizerLoopB']['timestamp']

storeObj = Storage()
storeObj.type = "pitl"
storeObj.t = np.linspace(0,len(t)/1000.0,len(t))

storeObj.u = np.zeros((4,n))
storeObj.u[0,:] = dataA['motor.m1']
storeObj.u[1,:] = dataA['motor.m2']
storeObj.u[2,:] = dataA['motor.m3']
storeObj.u[3,:] = dataA['motor.m4']

storeObj.acc = np.zeros((3,n))
storeObj.acc[0,:] = dataA['acc.x']
storeObj.acc[1,:] = dataA['acc.y']
storeObj.acc[2,:] = dataA['acc.z']

storeObj.gyro = np.zeros((3,n))
storeObj.gyro[0,:] = dataA['gyro.x']
storeObj.gyro[1,:] = dataA['gyro.y']
storeObj.gyro[2,:] = dataA['gyro.z']

storeObj.zrange = dataA['zranger.zrange']/1000.0
storeObj.pxCount = np.zeros((2,n))
storeObj.pxCount[0,:] = dataA['motion.deltaX']
storeObj.pxCount[1,:] = dataA['motion.deltaY']

storeObj.est_pos = np.zeros((3,n))
storeObj.est_pos[0,:] = dataB['stateEstimateZ.x']/1000.0
storeObj.est_pos[1,:] = dataB['stateEstimateZ.y']/1000.0
storeObj.est_pos[2,:] = dataB['stateEstimateZ.z']/1000.0

storeObj.est_vel = np.zeros((3,n))
storeObj.est_vel[0,:] = dataB['stateEstimateZ.vx']/1000.0
storeObj.est_vel[1,:] = dataB['stateEstimateZ.vy']/1000.0
storeObj.est_vel[2,:] = dataB['stateEstimateZ.vz']/1000.0

storeObj.set_pt = np.zeros((3,n))
storeObj.set_pt[0,:] = dataB['ctrltargetZ.x']/1000.0
storeObj.set_pt[1,:] = dataB['ctrltargetZ.y']/1000.0
storeObj.set_pt[2,:] = dataB['ctrltargetZ.z']/1000.0

storeObj.save("pitl/flightdata")
