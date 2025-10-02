# dqn_agent.py
import numpy as np
import random
from collections import deque
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import traci
import os

class QLearningAgent:
    def __init__(self, actions, state_size, learning_rate=0.1, discount_factor=0.95, exploration_rate=1.0, exploration_decay=0.995, min_exploration_rate=0.01): # CHANGED
        self.actions = actions
        self.q_table = np.zeros((state_size, len(actions)))
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.epsilon_decay = exploration_decay  # Standardized to match DQN
        self.epsilon_min = min_exploration_rate

    def get_state(self, incoming_lanes):
        state = []
        for lanes in incoming_lanes.values():
            queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
            if queue < 5:
                state.append(0)
            elif queue < 10:
                state.append(1)
            else:
                state.append(2)
        state_index = 0
        for i, s in enumerate(state):
            state_index += s * (3**i)
        return state_index

    def choose_action(self, state):
        if np.random.rand() <= self.epsilon:
            return random.choice(self.actions)
        return np.argmax(self.q_table[state])

    def update_q_table(self, state, action, reward, next_state):
        old_value = self.q_table[state, action]
        next_max = np.max(self.q_table[next_state])
        
        new_value = old_value + self.lr * (reward + self.gamma * next_max - old_value)
        self.q_table[state, action] = new_value

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def save_q_table(self, file_path):
        print(f"Saving Q-table to {file_path}...")
        np.savetxt(file_path, self.q_table, delimiter=",")
        print("Save complete.")

    def load_q_table(self, file_path):
        if os.path.exists(file_path):
            print(f"Loading Q-table from {file_path}...")
            self.q_table = np.loadtxt(file_path, delimiter=",")
            self.epsilon = 0.1
            print("Load complete.")
        else:
            print("No existing Q-table found. Starting fresh.")

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
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state):
        self.memory.append((state, action, reward, next_state))
    
    def get_state(self, incoming_lanes):
        state = []
        for lanes in incoming_lanes.values():
            queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
            state.append(queue / 20.0)
        return np.reshape(state, [1, self.state_size])
    
    def choose_action(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state, verbose=0)
        return np.argmax(act_values[0])
    
    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state in minibatch:
            target = reward + self.gamma * np.amax(self.model.predict(next_state, verbose=0)[0])
            target_f = self.model.predict(state, verbose=0)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay