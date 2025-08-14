import traci
import sys
import os

# This script is for running a simulation with a fixed-time traffic light.
# The timings are defined in the 'cross.add.xml' file.

# --- Main Simulation Logic ---
def run():
    """Executes the TraCI control loop for a fixed-time simulation."""
    step = 0
    # The simulation loop continues as long as there are cars in the simulation.
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()  # Advance the simulation by one step.
        step += 1

    # Close the TraCI connection once the simulation is over.
    traci.close()
    sys.stdout.flush()

# --- SUMO Configuration ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Define the SUMO command to run the simulation with GUI.
# It uses the configuration file you created.
# Change this line in fixed_timer.py
sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_fixed.xml"]
# --- Script Entry Point ---
if __name__ == "__main__":
    # Start the SUMO simulation and connect to it with TraCI.
    traci.start(sumo_cmd)
    print("Starting simulation with Fixed-Time Controller...")
    run()
    print("Simulation finished.")