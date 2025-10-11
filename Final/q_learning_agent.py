# q_learning_agent.py
# This script TRAINS a Q-Learning agent.
# It runs multiple simulations in the background to build a "Q-Table" (the agent's brain),
# which it then saves to a file.

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

# --- Q-LEARNING PARAMETERS ---
# These are the "control knobs" for the learning process.
alpha = 0.1          # Learning Rate
gamma = 0.95         # Discount Factor
epsilon = 1.0        # Initial Exploration Rate
epsilon_decay = 0.999 # Rate of reducing exploration
epsilon_min = 0.01
EPISODES = 100       # Total number of simulations to run for training

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
    """Retrieves and discretizes the state of the intersection."""
    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)
    
    # Discretize queue lengths into bins of 3 to give the agent "sharper vision".
    ns_level = min(ns_queue // 3, 10)
    ew_level = min(ew_queue // 3, 10)

    current_phase = traci.trafficlight.getPhase(TLS_ID)
    phase_is_ns = 1 if current_phase == NS_GREEN_PHASE else 0

    return (ns_level, ew_level, phase_is_ns)

def run_step_and_get_reward(action):
    """Performs an action in SUMO and returns the calculated reward."""
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
    # We use "sumo" (no GUI) for fast training. A tripinfo file is still generated for the last episode.
    sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--tripinfo-output", "tripinfo_q_learning.xml", "--no-step-log", "true", "-W", "true", "--duration-log.disable", "true"]
    
    # The main training loop
    for episode in range(EPISODES):
        traci.start(sumo_cmd)
        
        current_state = get_state()
        total_episode_reward = 0
        
        while traci.simulation.getMinExpectedNumber() > 0:
            
            if current_state not in q_table:
                q_table[current_state] = np.zeros(len(actions))

            if random.uniform(0, 1) < epsilon:
                action = random.choice(actions) # Explore
            else:
                action = np.argmax(q_table[current_state]) # Exploit

            reward = run_step_and_get_reward(action)
            next_state = get_state()
            total_episode_reward += reward

            if next_state not in q_table:
                q_table[next_state] = np.zeros(len(actions))
            
            old_q_value = q_table[current_state][action]
            best_future_q = np.max(q_table[next_state])
            
            # The Q-Learning formula
            new_q_value = old_q_value + alpha * (reward + gamma * best_future_q - old_q_value)
            q_table[current_state][action] = new_q_value
            
            current_state = next_state

        traci.close()
        
        if epsilon > epsilon_min:
            epsilon *= epsilon_decay
            
        print(f"Episode: {episode + 1}/{EPISODES}, Total Reward: {total_episode_reward:.2f}, Epsilon: {epsilon:.4f}")

    print("\n--- Training finished ---")
    
    # Save the final, trained Q-Table to a file
    with open('q_table.pkl', 'wb') as f:
        pickle.dump(q_table, f)
    print("Trained Q-Table saved to 'q_table.pkl'")