# fixed_timer.py
# This script runs the simulation with the "dumb" fixed-time traffic light.
# The actual signal logic is defined in 'cross.add.xml'. This script's
# main purpose is to launch SUMO and generate the results file.

import traci
import sys
import os

# --- SUMO SETUP ---
# This block ensures that the script can find the traci library in your SUMO installation.
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- MAIN SIMULATION LOGIC ---
def run():
    """Executes the TraCI control loop for the fixed-time simulation."""
    step = 0
    # The simulation loop continues as long as there are cars in the simulation.
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()  # Advance the simulation by one second.
        step += 1

    # Close the TraCI connection once the simulation is over.
    traci.close()
    sys.stdout.flush()

# --- SCRIPT ENTRY POINT ---
if __name__ == "__main__":
    
    # Define the SUMO command to run the simulation with a GUI.
    # --tripinfo-output generates the XML file with performance metrics for each car.
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_fixed.xml"]

    # Start the SUMO simulation and connect to it with TraCI.
    traci.start(sumo_cmd)
    print("Starting simulation with Fixed-Time Controller...")
    run()
    print("Simulation finished. Results saved to 'tripinfo_fixed.xml'.")