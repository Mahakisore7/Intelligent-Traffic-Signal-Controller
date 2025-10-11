# ambulance_simulation.py
# This script demonstrates a priority preemption system for an emergency vehicle.
# It runs a standard LQF agent but overrides its logic when an ambulance is detected.

import traci
import sys
import os

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- CONTROLLER & SIMULATION PARAMETERS ---
TLS_ID = "J1"
AMBULANCE_ID = "ambulance_1"
APPROACH_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2", "E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]
NS_GREEN_PHASE = 0
EW_GREEN_PHASE = 2

# --- MAIN LOGIC ---
def run():
    """Executes the TraCI control loop with ambulance preemption."""
    
    # Main simulation loop
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # --- Ambulance Detection Logic ---
        ambulance_detected = False
        # Get a list of all vehicles currently in the simulation
        all_vehicle_ids = traci.vehicle.getIDList()
        
        if AMBULANCE_ID in all_vehicle_ids:
            # If the ambulance exists, check its current location
            ambulance_road = traci.vehicle.getRoadID(AMBULANCE_ID)
            # Check if the ambulance is on one of the approach roads to the intersection
            if any(lane in ambulance_road for lane in ["N_in", "S_in", "E_in", "W_in"]):
                ambulance_detected = True
        
        # --- Control Logic ---
        if ambulance_detected:
            # --- OVERRIDE MODE ---
            # Get the ambulance's current road
            road = traci.vehicle.getRoadID(AMBULANCE_ID)
            
            # Force the light green for the ambulance's direction
            if 'N_in' in road or 'S_in' in road:
                # If ambulance is on N-S axis, force N-S green
                if traci.trafficlight.getPhase(TLS_ID) != NS_GREEN_PHASE:
                    traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
            elif 'E_in' in road or 'W_in' in road:
                # If ambulance is on E-W axis, force E-W green
                if traci.trafficlight.getPhase(TLS_ID) != EW_GREEN_PHASE:
                    traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
        else:
            # --- DEFAULT MODE (LQF Logic) ---
            # This is a simplified LQF logic for demonstration
            ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in traci.trafficlight.getControlledLanes(TLS_ID) if 'N_in' in lane or 'S_in' in lane)
            ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in traci.trafficlight.getControlledLanes(TLS_ID) if 'E_in' in lane or 'W_in' in lane)
            
            current_phase = traci.trafficlight.getPhase(TLS_ID)
            
            if current_phase == NS_GREEN_PHASE and ew_queue > ns_queue:
                traci.trafficlight.setPhase(TLS_ID, 1) # Switch to N-S Yellow
            elif current_phase == EW_GREEN_PHASE and ns_queue > ew_queue:
                traci.trafficlight.setPhase(TLS_ID, 3) # Switch to E-W Yellow
            
            # Handle yellow phase transitions
            if current_phase == 1 and traci.trafficlight.getPhaseDuration(TLS_ID) > 3:
                traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
            if current_phase == 3 and traci.trafficlight.getPhaseDuration(TLS_ID) > 3:
                traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)

    traci.close()
    sys.stdout.flush()

# --- SCRIPT ENTRY POINT ---
if __name__ == "__main__":
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_with_preemption.xml"]
    
    # Make sure the <additional-files> line is commented out in cross.sumocfg
    traci.start(sumo_cmd)
    print("Starting simulation with Ambulance Preemption System...")
    run()
    print("Simulation finished.")