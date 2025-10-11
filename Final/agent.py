# agent.py
# This script implements our first "smart" controller.
# It follows a simple heuristic rule: "Longest Queue First" (LQF).
# It adapts to real-time traffic data to make decisions.

import traci
import sys
import os

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- CONTROLLER PARAMETERS ---
MIN_GREEN_TIME = 10  # seconds
MAX_GREEN_TIME = 45  # seconds
YELLOW_TIME = 4      # seconds
TLS_ID = "J1"        # The ID of our traffic light in SUMO

# --- PHASE DEFINITIONS ---
# We give nicknames to the phase numbers for readability.
# These indices MUST match the logic SUMO generates.
NS_GREEN_PHASE = 0
NS_YELLOW_PHASE = 1
EW_GREEN_PHASE = 2
EW_YELLOW_PHASE = 3

# --- LANE ID DEFINITIONS (The "Eyes" of our agent) ---
# These are the specific lane IDs for our intersection, grouped by direction.
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]

# --- MAIN SIMULATION LOGIC ---
def run():
    """Executes the TraCI control loop for the LQF agent."""
    green_time_counter = 0
    # Ask SUMO what the current light phase is at the start.
    current_phase = traci.trafficlight.getPhase(TLS_ID)

    # Main simulation loop.
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        green_time_counter += 1

        # Only check for a phase switch if the light is currently green.
        is_green_phase = (current_phase == NS_GREEN_PHASE or current_phase == EW_GREEN_PHASE)

        # We only make a decision if the minimum green time has passed.
        if is_green_phase and green_time_counter > MIN_GREEN_TIME:
            # Get the number of stopped cars for each direction.
            ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
            ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)

            # --- THE DECISION LOGIC ---
            # If the current green light is for North-South...
            if current_phase == NS_GREEN_PHASE:
                # ...and the East-West queue is longer, OR if max green time is reached...
                if ew_queue > ns_queue or green_time_counter > MAX_GREEN_TIME:
                    # ...then switch to the yellow light for North-South.
                    traci.trafficlight.setPhase(TLS_ID, NS_YELLOW_PHASE)
                    current_phase = NS_YELLOW_PHASE
                    green_time_counter = 0 # Reset the timer for the new phase.

            # If the current green light is for East-West...
            elif current_phase == EW_GREEN_PHASE:
                # ...and the North-South queue is longer, OR if max green time is reached...
                if ns_queue > ew_queue or green_time_counter > MAX_GREEN_TIME:
                    # ...then switch to the yellow light for East-West.
                    traci.trafficlight.setPhase(TLS_ID, EW_YELLOW_PHASE)
                    current_phase = EW_YELLOW_PHASE
                    green_time_counter = 0

        # Logic to switch to the next green phase after the yellow light has finished.
        is_yellow_phase = (current_phase == NS_YELLOW_PHASE or current_phase == EW_YELLOW_PHASE)

        if is_yellow_phase and green_time_counter == YELLOW_TIME:
            if current_phase == NS_YELLOW_PHASE:
                traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
                current_phase = EW_GREEN_PHASE
            else: # It must be the East-West Yellow phase
                traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
                current_phase = NS_GREEN_PHASE
            green_time_counter = 0

    traci.close()
    sys.stdout.flush()

# --- SCRIPT ENTRY POINT ---
if __name__ == "__main__":
    # The SUMO command for this agent. We generate a different tripinfo file.
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_no_preemption.xml"]

    traci.start(sumo_cmd)
    print("Starting simulation with Longest Queue First (LQF) Agent...")
    run()
    print("Simulation finished. Results saved to 'tripinfo_lqf.xml'.")