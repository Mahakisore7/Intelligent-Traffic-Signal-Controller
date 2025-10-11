# dqn_agent_final.py
# This is the final, optimized training script designed for the best possible performance.
# It uses tuned hyperparameters and a more aggressive reward function.

import traci
import sys
import os
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam
from collections import deque
import pickle
import time

# --- SUMO SETUP ---
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
        
        # --- TUNED HYPERPARAMETERS ---
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99  # Faster decay to exploit good strategies sooner
        self.learning_rate = 0.001
        
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

    def _build_model(self):
        """Builds a Keras neural network model."""
        model = Sequential([
            Input(shape=(self.state_size,)),
            Dense(32, activation='relu'),
            Dense(32, activation='relu'),
            Dense(self.action_size, activation='linear')
        ])
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state, verbose=0)
        return np.argmax(act_values[0])

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return

        minibatch = random.sample(self.memory, batch_size)
        
        states = np.array([transition[0] for transition in minibatch]).reshape(batch_size, self.state_size)
        next_states = np.array([transition[3] for transition in minibatch]).reshape(batch_size, self.state_size)

        current_q_values_list = self.model.predict(states, verbose=0)
        future_q_values_list = self.target_model.predict(next_states, verbose=0)
        
        X = []
        y = []

        for index, (state, action, reward, next_state, done) in enumerate(minibatch):
            if not done:
                target = reward + self.gamma * np.amax(future_q_values_list[index])
            else:
                target = reward
            
            current_q_values = current_q_values_list[index]
            current_q_values[action] = target

            X.append(state.flatten())
            y.append(current_q_values)

        self.model.fit(np.array(X), np.array(y), batch_size=batch_size, epochs=1, verbose=0)
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# --- CONSTANTS AND PARAMETERS ---
STATE_SIZE = 4
ACTION_SIZE = 2
EPISODES = # A reasonable number of episodes for the final run
UPDATE_TARGET_EVERY = 5
BATCH_SIZE = 32

TLS_ID = "J1"
ALL_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2", "E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]

# --- HELPER FUNCTION TO GET STATE FROM SUMO ---
def get_state():
    ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ALL_LANES if 'N_in' in lane or 'S_in' in lane)
    ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ALL_LANES if 'E_in' in lane or 'W_in' in lane)
    
    current_phase = traci.trafficlight.getPhase(TLS_ID)
    phase_is_ns = 1 if current_phase in [0, 1] else 0
    time_since_switch = traci.trafficlight.getPhaseDuration(TLS_ID) # Time in current phase

    state = np.array([ns_queue / 50.0, ew_queue / 50.0, phase_is_ns, time_since_switch / MAX_GREEN_TIME])
    return np.reshape(state, [1, STATE_SIZE])

# A new global constant needed for the state
MAX_GREEN_TIME = 60

# --- MAIN TRAINING SCRIPT ---
if __name__ == "__main__":
    print("Initializing FINAL Optimized DQN Training Run...")
    agent = DQNAgent(STATE_SIZE, ACTION_SIZE)
    sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--no-step-log", "true", "-W", "true", "--duration-log.disable", "true"]

    learning_history = []

    for e in range(EPISODES):
        traci.start(sumo_cmd)
        state = get_state()
        
        total_episode_reward = 0
        step = 0
        done = False
        start_time = time.time()
        
        print(f"Episode: {e+1}/{EPISODES} -> Running...", end='', flush=True)
        
        while not done:
            action = agent.act(state)

            # Perform Action
            current_phase = traci.trafficlight.getPhase(TLS_ID)
            is_ns_green = current_phase in [0, 1]
            if action == 1: # Switch
                if traci.trafficlight.getPhaseDuration(TLS_ID) > 10: # Min green time before switch
                    yellow_phase = 1 if is_ns_green else 3
                    traci.trafficlight.setPhase(TLS_ID, yellow_phase)
                    for _ in range(4): traci.simulationStep()
            traci.simulationStep() # Step once
            
            next_state = get_state()
            
            # --- MORE AGGRESSIVE REWARD FUNCTION ---
            # The penalty is now the SQUARE of the total waiting cars.
            # This heavily punishes the agent for letting queues grow.
            total_waiting_cars = (next_state[0][0] * 50) + (next_state[0][1] * 50)
            reward = -((total_waiting_cars / 10.0) ** 2)
            
            total_episode_reward += reward
            done = traci.simulation.getMinExpectedNumber() == 0
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            step += 1
            agent.replay(BATCH_SIZE)

        traci.close()
        
        if e > 0 and e % UPDATE_TARGET_EVERY == 0:
            agent.update_target_model()
        
        episode_time = time.time() - start_time
        learning_history.append(total_episode_reward)
        print(f"\n   ...Done! Steps: {step}, Total Reward: {total_episode_reward:.2f}, Epsilon: {agent.epsilon:.4f}, Time: {episode_time:.2f}s")

    print("\n--- Final Training finished ---")
    agent.model.save("dqn_model_final.h5")
    print("Final Trained DQN model saved to 'dqn_model_final.h5'")
    with open('dqn_learning_history_final.pkl', 'wb') as f:
        pickle.dump(learning_history, f)
    print("Final Learning history saved to 'dqn_learning_history_final.pkl'")
