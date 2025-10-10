# evaluate_dqn_agent.py

import traci
import sys
import os
import numpy as np
import tensorflow as tf

# --- ENSURE SUMO IS IN THE PATH ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- CONSTANTS AND PARAMETERS ---
STATE_SIZE = 4
ACTION_SIZE = 2
TLS_ID = "J1"
NS_GREEN_PHASE = 0
NS_YELLOW_PHASE = 1
EW_GREEN_PHASE = 2
EW_YELLOW_PHASE = 3
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]

# --- HELPER FUNCTION TO GET STATE FROM SUMO ---
def get_state():
    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)
    ns_wait = sum(traci.lane.getWaitingTime(lane) for lane in NS_LANES)
    ew_wait = sum(traci.lane.getWaitingTime(lane) for lane in EW_LANES)
    state = np.array([ns_queue / 50.0, ew_queue / 50.0, ns_wait / 1000.0, ew_wait / 1000.0])
    return np.reshape(state, [1, STATE_SIZE])

# --- MAIN EVALUATION SCRIPT ---
if __name__ == "__main__":
    try:
        # Load the trained neural network model
        # UPDATED LINE: Added compile=False to fix the loading error
        model = tf.keras.models.load_model('dqn_model.h5', compile=False)
        print("DQN model loaded successfully.")
    except (IOError, ImportError) as e:
        sys.exit(f"Error loading model: {e}. Please run dqn_agent.py to train and save the model first.")

    # Command to run SUMO with GUI and generate a trip report
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_dqn.xml", "--no-step-log", "true", "-W", "true"]
    
    traci.start(sumo_cmd)
    
    state = get_state()
    
    while traci.simulation.getMinExpectedNumber() > 0:
        # --- Make a decision using the trained brain ---
        # Ask the model to predict the Q-values for the current state
        act_values = model.predict(state, verbose=0)
        
        # Choose the action with the highest Q-value (no randomness!)
        action = np.argmax(act_values[0])

        # --- Perform the chosen action in SUMO ---
        current_phase = traci.trafficlight.getPhase(TLS_ID)
        is_ns_green = current_phase in [NS_GREEN_PHASE, NS_YELLOW_PHASE]

        if action == 1: # Switch action
            yellow_phase = NS_YELLOW_PHASE if is_ns_green else EW_YELLOW_PHASE
            traci.trafficlight.setPhase(TLS_ID, yellow_phase)
            for _ in range(4): traci.simulationStep()
            next_green_phase = EW_GREEN_PHASE if is_ns_green else NS_GREEN_PHASE
            traci.trafficlight.setPhase(TLS_ID, next_green_phase)
            for _ in range(10): traci.simulationStep()
        else: # Stay action
            for _ in range(10): traci.simulationStep()
        
        # Get the next state
        state = get_state()

    traci.close()
    print("DQN evaluation finished. Trip info saved to tripinfo_dqn.xml")

