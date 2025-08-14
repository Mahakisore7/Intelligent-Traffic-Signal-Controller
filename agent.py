import traci
import sys
import os

# --- SUMO SETUP ---
# This part makes sure your Python script can find the SUMO tools.
if 'SUMO_HOME' in os.environ:
    # The corrected line 8
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# This is the command to start the SUMO simulation with a graphical interface.
# Change this line in agent.py
sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_lqf.xml"]

# --- CONTROLLER PARAMETERS ---
MIN_GREEN_TIME = 10  # A green light will stay for at least 10 seconds.
MAX_GREEN_TIME = 45  # A green light will not stay for more than 45 seconds.
YELLOW_TIME = 4      # The yellow light duration is 4 seconds.
TLS_ID = "J1"        # This is the ID of your traffic light from your cross.nod.xml file.

# --- PHASE DEFINITIONS ---
# These numbers represent the different light combinations (phases).
# SUMO usually creates them in this order by default.
NS_GREEN_PHASE = 0  # North-South is Green
NS_YELLOW_PHASE = 1 # North-South is Yellow
EW_GREEN_PHASE = 2  # East-West is Green
EW_YELLOW_PHASE = 3 # East-West is Yellow

# --- LANE ID DEFINITIONS (The "Eyes" of our Brain) ---
# These are the specific lane IDs for your intersection, grouped by direction.
NS_LANES =["N_in_0","N_in_1","N_in_2", "N_out_1","N_out_0","N_out_2", "S_in_1","S_in_0","S_in_2","S_out_0","S_out_1","S_out_2"]  # North-South lanes
EW_LANES =["E_in_1", "E_out_2", "E_in_0", "E_out_0", "E_in_2", "E_out_1", "W_in_0","W_out_0","W_in_1","W_out_1","W_in_2", "W_out_2"]  # East-West lanes

# --- MAIN SIMULATION LOGIC ---
print("Starting SUMO simulation with Longest Queue First controller...")
# This command starts SUMO and connects our Python script to it.
traci.start(sumo_cmd)

green_time_counter = 0
# Get the starting phase of the traffic light
current_phase = traci.trafficlight.getPhase(TLS_ID)

# This is the main loop that runs the simulation. It continues as long as there are cars.
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep() # This command tells SUMO to advance the simulation by one second.
    green_time_counter += 1

    # Only check for a phase switch if the light is currently green.
    is_green_phase = (current_phase == NS_GREEN_PHASE or current_phase == EW_GREEN_PHASE)

    # We only make a decision if the minimum green time has passed.
    if is_green_phase and green_time_counter > MIN_GREEN_TIME:
        # Using its "eyes", the brain counts the stopped cars in each direction.
        ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
        ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)

        # --- THE DECISION LOGIC ---
        # If the current green light is for North-South...
        if current_phase == NS_GREEN_PHASE:
            #...and the East-West queue is longer, OR the max green time is over...
            if ew_queue > ns_queue or green_time_counter > MAX_GREEN_TIME:
                #...then switch to the yellow light for North-South.
                traci.trafficlight.setPhase(TLS_ID, NS_YELLOW_PHASE)
                current_phase = NS_YELLOW_PHASE
                green_time_counter = 0 # Reset the timer for the new phase.

        # If the current green light is for East-West...
        elif current_phase == EW_GREEN_PHASE:
            #...and the North-South queue is longer, OR the max green time is over...
            if ns_queue > ew_queue or green_time_counter > MAX_GREEN_TIME:
                #...then switch to the yellow light for East-West.
                traci.trafficlight.setPhase(TLS_ID, EW_YELLOW_PHASE)
                current_phase = EW_YELLOW_PHASE
                green_time_counter = 0 # Reset the timer.

    # This part handles switching to the next green light after the yellow light is done.
    is_yellow_phase = (current_phase == NS_YELLOW_PHASE or current_phase == EW_YELLOW_PHASE)

    if is_yellow_phase and green_time_counter == YELLOW_TIME:
        # If the North-South light was just yellow, make the East-West light green.
        if current_phase == NS_YELLOW_PHASE:
            traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
            current_phase = EW_GREEN_PHASE
        # Otherwise, the East-West light was just yellow, so make the North-South light green.
        else:
            traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
            current_phase = NS_GREEN_PHASE
        green_time_counter = 0 # Reset the timer for the new green light.

# This command closes the connection to SUMO when the simulation is over.
traci.close()
print("Simulation finished.")