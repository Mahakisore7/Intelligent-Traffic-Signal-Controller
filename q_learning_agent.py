# evaluate_q_agent.py

import traci
import sys
import os
import numpy as np
import pickle # Used to load the saved Q-Table
import xml.etree.ElementTree as ET # Used for final analysis

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- AGENT SETUP ---
# We don't need learning parameters here, just the trained brain.
try:
    with open('q_table.pkl', 'rb') as f:
        q_table = pickle.load(f)
except FileNotFoundError:
    sys.exit("Error: q_table.pkl not found. Please run q_learning_agent.py to train the agent first.")

# Define the actions: 0 = stay, 1 = switch
ACTION_STAY = 0
ACTION_SWITCH = 1
actions = [ACTION_STAY, ACTION_SWITCH]

# --- PHASE & LANE DEFINITIONS (FROM YOUR PROJECT) ---
TLS_ID = "J1"
NS_GREEN_PHASE = 0
NS_YELLOW_PHASE = 1
EW_GREEN_PHASE = 2
EW_YELLOW_PHASE = 3
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]

# --- HELPER FUNCTIONS ---

def get_state():
    """Gets the state of the intersection (same as in the training script)."""
    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)
    ns_level = 0
    if ns_queue > 15: ns_level = 2
    elif ns_queue > 5: ns_level = 1
    ew_level = 0
    if ew_queue > 15: ew_level = 2
    elif ew_queue > 5: ew_level = 1
    current_phase = traci.trafficlight.getPhase(TLS_ID)
    phase_is_ns = 1 if current_phase == NS_GREEN_PHASE else 0
    return (ns_level, ew_level, phase_is_ns)

def get_average_wait_time(xml_file):
    """Parses a SUMO tripinfo XML and returns the average waiting time."""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    total_wait_time = 0.0
    vehicle_count = 0
    for tripinfo in root.findall('tripinfo'):
        wait_time_str = tripinfo.get('waitingTime')
        if wait_time_str:
            total_wait_time += float(wait_time_str)
            vehicle_count += 1
    if vehicle_count == 0:
        return 0
    return total_wait_time / vehicle_count

# --- MAIN EVALUATION SCRIPT ---
if __name__ == "__main__":
    # The command now uses the GUI and creates a new tripinfo file for this agent
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_q_learning.xml"]
    
    traci.start(sumo_cmd)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        # 1. GET CURRENT STATE
        current_state = get_state()
        
        # 2. CHOOSE ACTION (EXPLOITATION ONLY)
        # Check if the state exists in the Q-Table, if not, default to a safe action (stay)
        if current_state in q_table:
            # We set epsilon=0, so we ALWAYS choose the action with the highest Q-value.
            action = np.argmax(q_table[current_state])
        else:
            # If the agent has never seen this state before, take a default action.
            action = ACTION_STAY

        # 3. PERFORM ACTION
        current_phase = traci.trafficlight.getPhase(TLS_ID)
        is_ns_green = current_phase == NS_GREEN_PHASE

        if action == ACTION_SWITCH:
            yellow_phase = NS_YELLOW_PHASE if is_ns_green else EW_YELLOW_PHASE
            traci.trafficlight.setPhase(TLS_ID, yellow_phase)
            for _ in range(4): traci.simulationStep()
            
            next_green_phase = EW_GREEN_PHASE if is_ns_green else NS_GREEN_PHASE
            traci.trafficlight.setPhase(TLS_ID, next_green_phase)
            for _ in range(10): traci.simulationStep()
        else: # ACTION_STAY
            for _ in range(10): traci.simulationStep()

    traci.close()
    
    # --- FINAL ANALYSIS ---
    avg_wait_time = get_average_wait_time('tripinfo_q_learning.xml')
    print(f"\n--- Q-Learning Agent Evaluation Finished ---")
    print(f"Average Waiting Time: {avg_wait_time:.2f} seconds")
    print("------------------------------------------")
