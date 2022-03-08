# Renode

 * **1** Clone the [custom Renode](https://github.com/bitcraze/renode) repository. Double check the submodule src/Infrastructure (see `.gitmodule`) for the renode repository should have url `https://github.com/bitcraze/renode-infrastructure.git`
 * **2** Install dependencies according to [Building Renode from source](https://renode.readthedocs.io/en/latest/advanced/building_from_sources.html#core-prerequisites).
 * **3** [Build](https://renode.readthedocs.io/en/latest/advanced/building_from_sources.html#building-renode) Renode.

# Set-up

Replace **renode/platforms/boards/cf2.repl** with the **cf2.repl** file provided in this directory.

Edit, in **renode/scripts/single-node/crazyflie.resc**, the line 

>`sysbus LoadELF @cf2.elf`

to

>`sysbus LoadELF @/path/to/cps-testing-abstractions/firmware/cf2.elf`
