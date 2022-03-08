# Firmware

Put in this directory the binaries that you want to test.
For both abstractions the `cf2.map` file is used to retrieve the memory addresses.
For SitL the `cf2.elf` file is the one flashed to the emulated hardware.
**Remember to compile the firmware with the target associated to the setup**.

## SitL
For SitL testing are needed the `cf2.elf` file and the `cf2.map` file.

## HitL
For HitL testing only the `cf2.map` file is needed in this directory. Make sure the harware is flashed with the corresponding firmware. 
