# dqn_agent.py

import traci
import sys
import os
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from collections import deque # A special list with a fixed size

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- DQN AGENT CLASS ---
class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000) # Experience replay buffer stores the last 2000 experiences
        self.gamma = 0.95    # Discount rate
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model() # Main model for making decisions
        self.target_model = self._build_model() # Target model for calculating target Q-values
        self.update_target_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu')) # Input layer + 1st hidden layer
        model.add(Dense(24, activation='relu')) # 2nd hidden layer
        model.add(Dense(self.action_size, activation='linear')) # Output layer
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def update_target_model(self):
        # Copy weights from the main model to the target model
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state):
        # Store experience in memory
        self.memory.append((state, action, reward, next_state))

    def act(self, state):
        # Epsilon-greedy action selection
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size) # Take a random action
        act_values = self.model.predict(state, verbose=0)
        return np.argmax(act_values[0])  # Take the best action

    def replay(self, batch_size):
        # Train the model from a random batch of experiences
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state in minibatch:
            # Predict the Q-values for the next state using the stable target model
            target_q_values = self.target_model.predict(next_state, verbose=0)
            target = reward + self.gamma * np.amax(target_q_values[0])
            
            # Get the current Q-values from the main model
            current_q_values = self.model.predict(state, verbose=0)
            current_q_values[0][action] = target # Update the Q-value for the action we took
            
            # Train the main model
            self.model.fit(state, current_q_values, epochs=1, verbose=0)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# --- SIMULATION SETUP ---
STATE_SIZE = 4 # [NS_queue, EW_queue, NS_wait_time, EW_wait_time]
ACTION_SIZE = 2 # 0: stay, 1: switch
EPISODES = 50
UPDATE_TARGET_EVERY = 5 # episodes

# --- PHASE & LANE DEFINITIONS ---
TLS_ID = "J1"
NS_GREEN_PHASE = 0
NS_YELLOW_PHASE = 1
EW_GREEN_PHASE = 2
EW_YELLOW_PHASE = 3
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]

# --- HELPER FUNCTIONS ---
def get_state():
    """Gets a more detailed state of the intersection."""
    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)
    ns_wait = sum(traci.lane.getWaitingTime(lane) for lane in NS_LANES)
    ew_wait = sum(traci.lane.getWaitingTime(lane) for lane in EW_LANES)
    
    # Normalize the state values to be roughly between 0 and 1
    state = np.array([ns_queue / 50.0, ew_queue / 50.0, ns_wait / 1000.0, ew_wait / 1000.0])
    return np.reshape(state, [1, STATE_SIZE]) # Reshape for the neural network

# --- MAIN TRAINING SCRIPT ---
if __name__ == "__main__":
    agent = DQNAgent(STATE_SIZE, ACTION_SIZE)
    sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--no-step-log", "true", "-W", "true"]

    for e in range(EPISODES):
        traci.start(sumo_cmd)
        state = get_state()
        total_reward = 0
        
        while traci.simulation.getMinExpectedNumber() > 0:
            action = agent.act(state)

            # Perform action and get reward
            old_total_wait = state[0][2] * 1000 + state[0][3] * 1000 # Denormalize to get wait time

            current_phase = traci.trafficlight.getPhase(TLS_ID)
            is_ns_green = current_phase == NS_GREEN_PHASE

            if action == 1: # Switch
                yellow_phase = NS_YELLOW_PHASE if is_ns_green else EW_YELLOW_PHASE
                traci.trafficlight.setPhase(TLS_ID, yellow_phase)
                for _ in range(4): traci.simulationStep()
                next_green_phase = EW_GREEN_PHASE if is_ns_green else NS_GREEN_PHASE
                traci.trafficlight.setPhase(TLS_ID, next_green_phase)
                for _ in range(10): traci.simulationStep()
            else: # Stay
                for _ in range(10): traci.simulationStep()
            
            next_state = get_state()
            new_total_wait = next_state[0][2] * 1000 + next_state[0][3] * 1000
            reward = old_total_wait - new_total_wait
            total_reward += reward

            # Store this experience in the agent's memory
            agent.remember(state, action, reward, next_state)
            
            state = next_state

            # Train the agent if enough memories have been collected
            if len(agent.memory) > 32:
                agent.replay(32)

        traci.close()
        
        # Periodically update the target network
        if e % UPDATE_TARGET_EVERY == 0:
            agent.update_target_model()
            
        print(f"Episode: {e+1}/{EPISODES}, Total Reward: {total_reward:.2f}, Epsilon: {agent.epsilon:.4f}")

    print("\nTraining finished.")
    # Save the trained model's weights
    agent.model.save("dqn_model.h5")
    print("DQN model saved to dqn_model.h5")
