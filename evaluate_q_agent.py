# evaluate_q_agent.py
# This script loads a trained Q-Table and runs a simulation to evaluate its performance.

import traci
import sys
import os
import numpy as np
import pickle

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- AGENT & SIMULATION SETUP ---
# Load the trained Q-Table (the agent's "brain")
try:
    with open('q_table.pkl', 'rb') as f:
        q_table = pickle.load(f)
    print("Q-Table loaded successfully.")
except FileNotFoundError:
    sys.exit("Error: Could not find 'q_table.pkl'. Please run the training script 'q_learning_agent.py' first.")

# Set epsilon to 0 for pure exploitation (no random actions)
epsilon = 0

# Define actions and constants (must match the training script)
ACTION_STAY = 0
ACTION_SWITCH = 1
actions = [ACTION_STAY, ACTION_SWITCH]

TLS_ID = "J1"
NS_GREEN_PHASE = 0
NS_YELLOW_PHASE = 1
EW_GREEN_PHASE = 2
EW_YELLOW_PHASE = 3
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]

# --- HELPER FUNCTIONS (must be identical to the training script) ---
def get_state():
    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)
    ns_level = min(ns_queue // 5, 5)
    ew_level = min(ew_queue // 5, 5)
    current_phase = traci.trafficlight.getPhase(TLS_ID)
    phase_is_ns = 1 if current_phase == NS_GREEN_PHASE else 0
    return (ns_level, ew_level, phase_is_ns)

# --- MAIN EVALUATION SCRIPT ---
if __name__ == "__main__":
    # Command to run with GUI and generate the tripinfo report
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_q_learning.xml", "--no-step-log", "true", "-W", "true", "--duration-log.disable", "true"]
    
    traci.start(sumo_cmd)
    print("Starting evaluation...")
    
    while traci.simulation.getMinExpectedNumber() > 0:
        current_state = get_state()

        # Check if the agent has seen this state before during training
        if current_state in q_table:
            # Exploit: Choose the best action from the Q-Table
            action = np.argmax(q_table[current_state])
        else:
            # If state is unknown, default to a safe action (e.g., stay)
            action = ACTION_STAY

        # Perform the chosen action
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
    print("Evaluation finished. 'tripinfo_q_learning.xml' has been generated.")

