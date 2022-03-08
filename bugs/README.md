# Bugs
 * *voltageCompCast* reproduction of https://github.com/bitcraze/crazyflie-firmware/pull/774
 * *initialPos* same as https://github.com/bitcraze/crazyflie-firmware/issues/760
 * *flowGyroData* to compensate angular rotation in optical flow, use gyro data from another queue rather than the local variable in estimator kalman
 * *motorRatioDef* different definition of motor ratio in different parts of the firmware. Injected as: motorsGetRatio returns percentage instead of absolute, inspired by the [Mars Climate Orbiter](https://en.wikipedia.org/wiki/Mars_Climate_Orbiter) bug
 * *simUpdate* assumed simultaneous update of different elements of a vector
 * *byteSwap* bug in accelerometer firmware where least significant and most significant bytes are inverted
 * *gyroAxesSwap* bug in gyroscope firmware where axes readings are swapped
 * *timingKalman* timing of kalman thread based on rtos tick rather than sensor interrupt
 * *flowDeckdtTiming* flowdeck data dt based microsecond counter, rather than hard-coded
 * *slowTick* slower RTOS tick rate: 800Hz instead of 1000Hz
