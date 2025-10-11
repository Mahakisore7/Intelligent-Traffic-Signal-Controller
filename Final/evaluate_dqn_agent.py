# evaluate_dqn_agent.py (Final Version)
# This script loads the FINAL trained DQN model and evaluates its performance.

import traci
import sys
import os
import numpy as np
import tensorflow as tf

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- AGENT & SIMULATION SETUP ---
STATE_SIZE = 4
ACTION_SIZE = 2

# Load the FINAL trained neural network model
try:
    model = tf.keras.models.load_model('dqn_model_final.h5', compile=False)
    print("Final DQN model loaded successfully.")
except (IOError, ImportError):
    sys.exit("Error: Could not find 'dqn_model_final.h5'. Please run 'dqn_agent_final.py' first.")

# Define constants (must match the final training script)
TLS_ID = "J1"
MAX_GREEN_TIME = 60

# --- HELPER FUNCTION (must be identical to the final training script) ---
def get_state():
    """Gets the detailed, normalized state from the simulation for the final DQN."""
    ns_lanes = [lane for lane in traci.trafficlight.getControlledLanes(TLS_ID) if 'N_in' in lane or 'S_in' in lane]
    ew_lanes = [lane for lane in traci.trafficlight.getControlledLanes(TLS_ID) if 'E_in' in lane or 'W_in' in lane]

    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ns_lanes)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ew_lanes)
    
    current_phase = traci.trafficlight.getPhase(TLS_ID)
    phase_is_ns = 1 if current_phase in [0, 1] else 0
    time_since_switch = traci.trafficlight.getPhaseDuration(TLS_ID)

    state = np.array([ns_queue / 50.0, ew_queue / 50.0, phase_is_ns, time_since_switch / MAX_GREEN_TIME])
    return np.reshape(state, [1, STATE_SIZE])

# --- MAIN EVALUATION SCRIPT ---
if __name__ == "__main__":
    sumo_cmd = ["sumo-gui", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_dqn_final.xml", "--no-step-log", "true", "-W", "true", "--duration-log.disable", "true"]
    
    traci.start(sumo_cmd)
    print("Starting evaluation of FINAL trained DQN Agent...")
    
    while traci.simulation.getMinExpectedNumber() > 0:
        current_state = get_state()
        act_values = model.predict(current_state, verbose=0)
        action = np.argmax(act_values[0])

        # Perform the chosen action
        current_phase = traci.trafficlight.getPhase(TLS_ID)
        is_ns_green = current_phase in [0, 1]

        if action == 1: # Switch action
            if traci.trafficlight.getPhaseDuration(TLS_ID) > 10:
                yellow_phase = 1 if is_ns_green else 3
                traci.trafficlight.setPhase(TLS_ID, yellow_phase)
                for _ in range(4): traci.simulationStep()
        
        traci.simulationStep()

    traci.close()
    print("Evaluation finished. Results saved to 'tripinfo_dqn_final.xml'.")