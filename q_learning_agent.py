# q_learning_agent.py (Optimized Version)

import traci
import sys
import os
import random
import numpy as np
import pickle

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- OPTIMIZED Q-LEARNING PARAMETERS ---
# Hyperparameters have been tuned for better performance
alpha = 0.2          # Learning Rate: Increased to learn faster from new states.
gamma = 0.95         # Discount Factor: Kept the same.
epsilon = 1.0        # Exploration Rate (initial): Starts at 100% random.
epsilon_decay = 0.999 # Slower decay for more exploration over more episodes.
epsilon_min = 0.01
EPISODES = 100       # INCREASED: More training time to explore the larger state space.

# --- AGENT SETUP ---
q_table = {}
ACTION_STAY = 0
ACTION_SWITCH = 1
actions = [ACTION_STAY, ACTION_SWITCH]

# --- SIMULATION CONSTANTS ---
TLS_ID = "J1"
NS_GREEN_PHASE = 0
NS_YELLOW_PHASE = 1
EW_GREEN_PHASE = 2
EW_YELLOW_PHASE = 3
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]
ALL_LANES = NS_LANES + EW_LANES

# --- HELPER FUNCTIONS ---

def get_state():
    """
    IMPROVED: Retrieves a more granular state of the intersection.
    """
    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)

    # SHARPER VISION: Discretize queue lengths into smaller bins (of 3)
    # This creates more states but gives the agent a more precise view.
    ns_level = min(ns_queue // 3, 10)  # Bin into levels 0-10 (e.g., 0-2 cars -> 0, 3-5 -> 1, etc.)
    ew_level = min(ew_queue // 3, 10)

    current_phase = traci.trafficlight.getPhase(TLS_ID)
    phase_is_ns = 1 if current_phase == NS_GREEN_PHASE else 0

    return (ns_level, ew_level, phase_is_ns)

def run_step(action):
    """
    Performs the chosen action in SUMO and returns the reward.
    """
    old_total_wait_time = sum(traci.lane.getWaitingTime(lane) for lane in ALL_LANES)
    
    switching_penalty = -5 if action == ACTION_SWITCH else 0

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

    new_total_wait_time = sum(traci.lane.getWaitingTime(lane) for lane in ALL_LANES)
    
    reward = (old_total_wait_time - new_total_wait_time) + switching_penalty
    return reward

# --- MAIN TRAINING SCRIPT ---
if __name__ == "__main__":
    sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_q_learning_optimized.xml", "--no-step-log", "true", "-W", "true", "--duration-log.disable", "true"]
    
    for episode in range(EPISODES):
        traci.start(sumo_cmd)
        
        current_state = get_state()
        total_episode_reward = 0
        
        while traci.simulation.getMinExpectedNumber() > 0:
            
            if current_state not in q_table:
                q_table[current_state] = np.zeros(len(actions))

            if random.uniform(0, 1) < epsilon:
                action = random.choice(actions)
            else:
                action = np.argmax(q_table[current_state])

            reward = run_step(action)
            next_state = get_state()
            total_episode_reward += reward

            if next_state not in q_table:
                q_table[next_state] = np.zeros(len(actions))
            
            old_q_value = q_table[current_state][action]
            best_future_q = np.max(q_table[next_state])
            
            new_q_value = old_q_value + alpha * (reward + gamma * best_future_q - old_q_value)
            q_table[current_state][action] = new_q_value
            
            current_state = next_state

        traci.close()
        
        if epsilon > epsilon_min:
            epsilon *= epsilon_decay
            
        print(f"Episode: {episode + 1}/{EPISODES}, Total Reward: {total_episode_reward:.2f}, Epsilon: {epsilon:.4f}")

    print("\nTraining finished.")
    with open('q_table_optimized.pkl', 'wb') as f:
        pickle.dump(q_table, f)
    print("Optimized Q-Table saved to q_table_optimized.pkl")

