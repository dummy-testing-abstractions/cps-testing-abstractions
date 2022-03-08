# for testing
import numpy as np
from mitl.Model  import cfSim
from hitl.cfHitl import cfHITL
from getaddresses.Addresses import cfAddresses

# import class for storing
from plot.Plot import Storage 

# for measuring test duration
import time

if __name__ == "__main__":
	start_test = time.perf_counter()

	# initialization of objects
	addresses = cfAddresses()
	physics = cfSim()           # initialize physics simulator
	cyber   = cfHITL(addresses.get()) # connect to hardware

	# simulation parameters
	t_init  = 0
	t_final = 10
	t_resolution = 0.001
	noise  = 0 # if non-zero includes measurement noise with given gains
	t_curr = t_init
	n_steps = int((t_final-t_init)/t_resolution)


	# storage variables
	t       = np.zeros((n_steps))
	tick    = np.zeros((n_steps))
	u_store = np.zeros((physics.n_inputs, n_steps))
	x_store = np.zeros((physics.n_states, n_steps))
	acc     = np.zeros((3,n_steps)) # inertial measurement
	gyro    = np.zeros((3,n_steps)) # inertial measurement
	pxCount = np.zeros((2,n_steps)) # pixel count measurement
	zrange  = np.zeros((n_steps))   # z ranging measurement
	est_pos = np.zeros((3,n_steps)) # position estimated by cf
	est_vel = np.zeros((3,n_steps)) # speed estimated by cf
	set_pt  = np.zeros((3,n_steps)) # setpoint in cf
	err_fd  = np.zeros((3,n_steps)) # kalman innovation from flow measurements

	# add breakpoint in stabilizer loop and go to it
	cyber.stop()
	cyber.addIMUBreakpoint()
	time.sleep(0.05) # to make sure message went through
	cyber.resume()

	i = 0 # counter

	# first iteration , only used to send start signal and initialize tick count
	cyber.waitBreakpointHit()
	tick[i] = cyber.tickCount()
	cyber.startFlying()
	time.sleep(0.05) # to make sure message went through
	cyber.resume()
	i = i+1

	# main loop
	while i<n_steps: 
		# compute time progress from ticks
		cyber.waitBreakpointHit()
		tick_curr = cyber.tickCount()
		dt        = (tick_curr-tick[i-1])/1000 
		if dt > 0: #time has progressed in the firmware: sim physics
			if not i%100:                     # progress printout
				print("time " + str(t_curr))
			t_curr  = t_curr+dt           # make time move forward
			tick[i] = tick_curr           # store only ticks at which time progresses
			t[i]    = t_curr              # used for plotting

			u_store[:,i] = cyber.motors() # read motor values and store control action
			x_store[:,i] = physics.simulate(t_curr, u_store[:,i]) # simulate physics

			# store measurements
			acc[:,i]     = physics.readAcc(Noise=noise)
			gyro[:,i]    = physics.readGyro(Noise=noise)
			pxCount[:,i] = physics.readPixelcount(Noise=noise)
			zrange[i]    = physics.readZRanging(Noise=noise)
			# close loop
			cyber.write_acc(acc[:,i])
			cyber.write_gyro(gyro[:,i])
			cyber.write_opticalflow(pxCount[:,i])
			cyber.write_zranger(zrange[i])
			# store data from drone
			est_pos[:,i] = cyber.estimatedPosition()
			est_vel[:,i] = cyber.estimatedVelocity()
			set_pt[:,i]  = cyber.setPoint()
			err_fd[:,i]  = cyber.flowErrors()

			i = i+1 # increase counter

		cyber.resume()    # unlock microcontroller		

	cyber.removeIMUBreakpoint()
	cyber.resume()
	cyber.close()

	end_test = time.perf_counter()
	print("This test took " + str(end_test-start_test) + " seconds")

	##############################################
	# store data as object attributes of storage #
	##############################################

	storeObj = Storage()
	storeObj.type    = "hitl"
	storeObj.t       = t
	storeObj.x       = x_store
	storeObj.u       = u_store

	# extract states
	storeObj.pos     = x_store[0:3,:]
	storeObj.vel     = x_store[3:6,:]
	storeObj.gyro    = x_store[10:13,:]

	# extract euler angles
	eta = np.zeros((3, n_steps))
	for j in range(0,n_steps):
		eta[:,j] = physics.quaternionToEuler(x_store[6:10,j])
	storeObj.eta     = eta

	# measurements and other cf data
	storeObj.acc     = acc
	storeObj.pxCount = pxCount
	storeObj.est_pos = est_pos
	storeObj.set_pt  = set_pt
	storeObj.zrange  = zrange
	storeObj.err_fd  = err_fd
	storeObj.tick    = tick 
	storeObj.est_vel = est_vel

	# save file
	storeObj.save("hitl/flightdata")


