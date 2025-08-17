import os
import sys
import traci
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, InputLayer
from tensorflow.keras.optimizers import Adam
from collections import deque
import random

# --- SUMO Configuration ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME'")

sumoBinary = "sumo-gui"
sumoCmd = [sumoBinary, "-c", "intersection.sumocfg"]

# --- Deep Q-Network Agent ---
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

    def _build_model(self):
        model = Sequential()
        model.add(InputLayer(batch_input_shape=(1, self.state_size)))
        model.add(Dense(48, activation='relu'))
        model.add(Dense(48, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma * np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

# --- Main Execution ---
if __name__ == "__main__":
    state_size = 12
    action_size = 4
    agent = DQNAgent(state_size, action_size)
    batch_size = 32
    episodes = 50

    phases = [
        "Gggrrrrrrrrr", "yyyrrrrrrrrr", "rrrGggrrrrrr", "rrryyyrrrrrr",
        "rrrrrrGggrrr", "rrrrrryyyrrr", "rrrrrrrrrGgg", "rrrrrrrrryyy"
    ]
    
    # --- Simulation Loop ---
    for e in range(episodes):
        traci.start(sumoCmd)
        
        step = 0
        min_green_time = 10
        yellow_time = 4
        
        incoming_lanes = [
            "N2C_0", "N2C_1", "N2C_2", "E2C_0", "E2C_1", "E2C_2",
            "S2C_0", "S2C_1", "S2C_2", "W2C_0", "W2C_1", "W2C_2"
        ]
        state_list = [traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes]
        state = np.array(state_list).reshape(1, state_size)
        
        total_reward = 0
        
        while step < 3600:
            
            # ================================================================= #
            # ===== NEW: INTELLIGENT ACTION SELECTION ========================= #
            # ================================================================= #
            # If we are in the exploration phase...
            if np.random.rand() <= agent.epsilon:
                # ...choose the most congested direction instead of a random one.
                # Sum up the queues for each of the 4 directions
                north_queue = state[0][0] + state[0][1] + state[0][2]
                east_queue = state[0][3] + state[0][4] + state[0][5]
                south_queue = state[0][6] + state[0][7] + state[0][8]
                west_queue = state[0][9] + state[0][10] + state[0][11]
                
                # Find the direction with the longest queue (0=N, 1=E, 2=S, 3=W)
                action = np.argmax([north_queue, east_queue, south_queue, west_queue])
            else:
                # Otherwise, use the neural network to decide (exploit)
                act_values = agent.model.predict(state)
                action = np.argmax(act_values[0])
            # ================================================================= #

            # --- Apply Green Phase ---
            green_phase_index = action * 2
            traci.trafficlight.setRedYellowGreenState("center", phases[green_phase_index])
            
            # Run simulation for the minimum green time
            current_reward = 0
            for _ in range(min_green_time):
                if step >= 3600: break
                traci.simulationStep()
                step += 1
                current_reward -= sum(traci.lane.getWaitingTime(lane) for lane in incoming_lanes)

            # --- Apply Yellow Phase ---
            yellow_phase_index = green_phase_index + 1
            traci.trafficlight.setRedYellowGreenState("center", phases[yellow_phase_index])
            
            for _ in range(yellow_time):
                if step >= 3600: break
                traci.simulationStep()
                step += 1
                current_reward -= sum(traci.lane.getWaitingTime(lane) for lane in incoming_lanes)
            
            # --- Observe new state and remember ---
            next_state_list = [traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes]
            next_state = np.array(next_state_list).reshape(1, state_size)
            
            total_reward += current_reward
            done = step >= 3600
            agent.remember(state, action, current_reward, next_state, done)
            
            state = next_state
            
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)

        print(f"Episode: {e + 1}/{episodes}, Total Reward: {total_reward:.2f}, Epsilon: {agent.epsilon:.2f}")
        traci.close()