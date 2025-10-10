# dqn_agent.py (Final Training Version with History Logging)

# --- IMPORTS ---
import traci
import sys
import os
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from collections import deque
import pickle

# --- ENSURE SUMO IS IN THE PATH ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- DEEP Q-NETWORK (DQN) AGENT CLASS ---
class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

    def _build_model(self):
        model = Sequential()
        model.add(Dense(24, input_shape=(self.state_size,), activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state):
        self.memory.append((state, action, reward, next_state))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state, verbose=0)
        return np.argmax(act_values[0])

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state in minibatch:
            target_q_values = self.target_model.predict(next_state, verbose=0)
            target = reward + self.gamma * np.amax(target_q_values[0])
            current_q_values = self.model.predict(state, verbose=0)
            current_q_values[0][action] = target
            self.model.fit(state, current_q_values, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# --- CONSTANTS AND PARAMETERS ---
STATE_SIZE = 4
ACTION_SIZE = 2
# Set to a higher number for a final, thorough training run.
# You can reduce this to ~20 for quick tests.
EPISODES = 5
UPDATE_TARGET_EVERY = 5

TLS_ID = "J1"
NS_GREEN_PHASE, NS_YELLOW_PHASE, EW_GREEN_PHASE, EW_YELLOW_PHASE = 0, 1, 2, 3
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

# --- MAIN TRAINING SCRIPT ---
if __name__ == "__main__":
    print("Initializing DQN Agent and TensorFlow... This may take a moment.")
    agent = DQNAgent(STATE_SIZE, ACTION_SIZE)
    sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--no-step-log", "true", "-W", "true", "--duration-log.disable", "true"]

    learning_history = [] # To store the average reward of each episode

    for e in range(EPISODES):
        traci.start(sumo_cmd)
        state = get_state()
        episode_rewards = []
        step = 0
        
        print(f"Episode: {e+1}/{EPISODES} -> Running...", end='', flush=True)
        
        while traci.simulation.getMinExpectedNumber() > 0:
            action = agent.act(state)
            old_total_wait = (state[0][2] * 1000) + (state[0][3] * 1000)

            current_phase = traci.trafficlight.getPhase(TLS_ID)
            is_ns_green = current_phase in [NS_GREEN_PHASE, NS_YELLOW_PHASE]

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
            new_total_wait = (next_state[0][2] * 1000) + (next_state[0][3] * 1000)
            reward = old_total_wait - new_total_wait
            episode_rewards.append(reward)
            agent.remember(state, action, reward, next_state)
            state = next_state
            step += 1
            
            if step % 100 == 0:
                print(".", end='', flush=True)

            if len(agent.memory) > 32:
                agent.replay(32)

        traci.close()
        
        if e > 0 and e % UPDATE_TARGET_EVERY == 0:
            agent.update_target_model()
        
        avg_reward = np.mean(episode_rewards) if episode_rewards else 0
        learning_history.append(avg_reward) # Log the average reward for this episode
        print(f"\n   ...Done! Steps: {step}, Avg Reward: {avg_reward:.2f}, Epsilon: {agent.epsilon:.4f}")

    print("\nTraining finished.")
    agent.model.save("dqn_model.h5")
    print("DQN model saved to dqn_model.h5")
    
    # Save the learning history for plotting
    with open('dqn_learning_history.pkl', 'wb') as f:
        pickle.dump(learning_history, f)
    print("DQN learning history saved to dqn_learning_history.pkl")

