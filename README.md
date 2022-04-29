# CS6490 Project - CCN Simulation

This repository contains code to run a CCN simulation and visualize the resulting network load during a DDoS attack.

The project makes use of the [SimPy](https://simpy.readthedocs.io/en/latest/) discrete-event simulator to run the network simulation. [Plotnine](https://plotnine.readthedocs.io/en/stable/) is used to generate the plots.

## Install dependencies

Make sure you have python 3.9 and poetry install and then run `poetry install`. Then you can run `poetry shell` to get into the environment.

## Running the simulation

Use the following command to run the simulation: `python -m ccn_sim.simulations.star.simple_star_1`. This will run a series of simulations store recorded simulation results in the `output/` directory.

After simulations have been run, the `visualization/visualize.py` script can be used with the command, `python visualization/visualize.py star_1_cache100`, to plot the generated outputs. You can vary the `cache100` value to one of `cache0`, `cache25`, `cache50`, `cache75`, `cache100`, or `ip`.
