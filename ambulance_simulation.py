# ambulance_simulation.py
# This script demonstrates a traffic light preemption system for an emergency vehicle.
# It uses the Longest Queue First (LQF) logic as a base but overrides it
# when an ambulance is detected.

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
MIN_GREEN_TIME = 10
YELLOW_TIME = 4
TLS_ID = "J1"

# --- PHASE & LANE DEFINITIONS ---
NS_GREEN_PHASE = 0
NS_YELLOW_PHASE = 1
EW_GREEN_PHASE = 2
EW_YELLOW_PHASE = 3
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]
ALL_INCOMING_LANES = NS_LANES + EW_LANES

# --- HELPER FUNCTION ---
def is_ambulance_approaching():
    """
    Checks if an ambulance is on any of the incoming lanes.
    Returns the direction ('NS' or 'EW') if found, otherwise None.
    """
    vehicles_on_ns = []
    for lane in NS_LANES:
        vehicles_on_ns.extend(traci.lane.getLastStepVehicleIDs(lane))
    
    for veh_id in vehicles_on_ns:
        if traci.vehicle.getTypeID(veh_id) == 'ambulance':
            return 'NS' # Ambulance found on a North-South lane

    vehicles_on_ew = []
    for lane in EW_LANES:
        vehicles_on_ew.extend(traci.lane.getLastStepVehicleIDs(lane))

    for veh_id in vehicles_on_ew:
        if traci.vehicle.getTypeID(veh_id) == 'ambulance':
            return 'EW' # Ambulance found on an East-West lane
            
    return None # No ambulance found

# --- MAIN SIMULATION LOGIC ---
if __name__ == "__main__":
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_with_preemption.xml"]
    traci.start(sumo_cmd)
    
    green_time_counter = 0
    
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        green_time_counter += 1
        
        # --- PRIORITY CHECK: AMBULANCE DETECTION ---
        ambulance_direction = is_ambulance_approaching()
        current_phase = traci.trafficlight.getPhase(TLS_ID)
        
        if ambulance_direction:
            # If ambulance is detected, override normal logic
            if ambulance_direction == 'NS' and current_phase != NS_GREEN_PHASE:
                # Ambulance is NS, but light is not green for it. Force switch.
                traci.trafficlight.setPhase(TLS_ID, NS_YELLOW_PHASE)
                for _ in range(YELLOW_TIME): traci.simulationStep()
                traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
                green_time_counter = 0
                
            elif ambulance_direction == 'EW' and current_phase != EW_GREEN_PHASE:
                # Ambulance is EW, but light is not green for it. Force switch.
                traci.trafficlight.setPhase(TLS_ID, EW_YELLOW_PHASE)
                for _ in range(YELLOW_TIME): traci.simulationStep()
                traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
                green_time_counter = 0
            
            # If the light is already green for the ambulance, this block does nothing,
            # effectively holding the green light indefinitely until the ambulance passes.

        # --- NORMAL LOGIC: LONGEST QUEUE FIRST ---
        elif green_time_counter > MIN_GREEN_TIME:
            # (This is the same LQF logic from your agent.py)
            ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
            ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)

            if current_phase == NS_GREEN_PHASE and ew_queue > ns_queue:
                traci.trafficlight.setPhase(TLS_ID, NS_YELLOW_PHASE)
                for _ in range(YELLOW_TIME): traci.simulationStep()
                traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
                green_time_counter = 0
                
            elif current_phase == EW_GREEN_PHASE and ns_queue > ew_queue:
                traci.trafficlight.setPhase(TLS_ID, EW_YELLOW_PHASE)
                for _ in range(YELLOW_TIME): traci.simulationStep()
                traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
                green_time_counter = 0

    traci.close()
    print("Ambulance simulation finished.")
