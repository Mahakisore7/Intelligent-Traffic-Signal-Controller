import traci
from sumolib import checkBinary
import sys

# --- Configuration ---
# MODIFIED: Changed 'sumo' to 'sumo-gui' to launch the visual interface
SUMO_BINARY = checkBinary('sumo-gui') 
SUMO_CONFIG = "intersection.sumocfg"


# --- Simulation Runner ---
def run_simulation():
    """
    Starts SUMO and runs the simulation for the specified duration.
    The traffic lights are controlled by the settings in the .net.xml or .tllogic.xml files.
    """
    try:
        # Start SUMO as a subprocess
        traci.start([SUMO_BINARY, "-c", SUMO_CONFIG])
        print("Simulation started. The SUMO GUI window should now be open.")

        # Main loop to step through the simulation
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

        print("Simulation finished.")

    except traci.exceptions.TraCIException as e:
        print(f"An error occurred with TraCI: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure TraCI is always closed
        traci.close()


# --- Main Execution Block ---
if __name__ == "__main__":
    run_simulation()