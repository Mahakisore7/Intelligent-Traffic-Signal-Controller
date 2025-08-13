import os
import sys
import traci
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Concatenate, Lambda
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from collections import deque
import random

# --- SUMO Configuration ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME'")

SUMO_CONFIG_FILE = "intersection.sumocfg"

# --- Ornstein-Uhlenbeck Noise for Exploration ---
class OUActionNoise:
    def __init__(self, mean, std_deviation, theta=0.15, dt=1e-2, x_initial=None):
        self.theta = theta
        self.mean = mean
        self.std_dev = std_deviation
        self.dt = dt
        self.x_initial = x_initial
        self.reset()

    def __call__(self):
        x = (self.x_prev + self.theta * (self.mean - self.x_prev) * self.dt +
             self.std_dev * np.sqrt(self.dt) * np.random.normal(size=self.mean.shape))
        self.x_prev = x
        return x

    def reset(self):
        self.x_prev = self.x_initial if self.x_initial is not None else np.zeros_like(self.mean)

# --- DDPG Agent ---
class DDPGAgent:
    def __init__(self, state_size, action_size, action_low, action_high):
        self.state_size = state_size
        self.action_size = action_size
        self.action_low = action_low
        self.action_high = action_high
        self.memory = deque(maxlen=100000)
        self.gamma = 0.99
        self.tau = 0.005 # Soft update parameter

        # Actor Model
        self.actor_local = self._build_actor()
        self.actor_target = self._build_actor()
        self.actor_target.set_weights(self.actor_local.get_weights())

        # Critic Model
        self.critic_local = self._build_critic()
        self.critic_target = self._build_critic()
        self.critic_target.set_weights(self.critic_local.get_weights())

        self.actor_optimizer = Adam(learning_rate=0.0001)
        self.critic_optimizer = Adam(learning_rate=0.001)
        
        self.noise = OUActionNoise(mean=np.zeros(1), std_deviation=float(0.2) * np.ones(1))

    def _build_actor(self):
        state_input = Input(shape=(self.state_size,))
        x = Dense(256, activation='relu')(state_input)
        x = Dense(256, activation='relu')(x)
        # Output is a continuous value for the action (green light duration)
        # Scaled to the action range [action_low, action_high]
        output = Dense(self.action_size, activation='tanh')(x)
        output = Lambda(lambda i: i * (self.action_high - self.action_low) / 2 + (self.action_high + self.action_low) / 2)(output)
        return Model(state_input, output)

    def _build_critic(self):
        state_input = Input(shape=(self.state_size,))
        action_input = Input(shape=(self.action_size,))
        # Concatenate state and action as input for the critic
        x = Concatenate()([state_input, action_input])
        x = Dense(256, activation='relu')(x)
        x = Dense(256, activation='relu')(x)
        output = Dense(1, activation='linear')(x)
        return Model([state_input, action_input], output)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, add_noise=True):
        state = tf.expand_dims(tf.convert_to_tensor(state), 0)
        action = self.actor_local(state)
        if add_noise:
            action += self.noise()
        # Clip the action to be within the valid range
        return np.clip(action, self.action_low, self.action_high)

    def learn(self, batch_size):
        if len(self.memory) < batch_size:
            return

        minibatch = random.sample(self.memory, batch_size)
        states = np.array([i[0] for i in minibatch])
        actions = np.array([i[1] for i in minibatch])
        rewards = np.array([i[2] for i in minibatch])
        next_states = np.array([i[3] for i in minibatch])
        dones = np.array([i[4] for i in minibatch])

        # --- Train Critic ---
        with tf.GradientTape() as tape:
            target_actions = self.actor_target(next_states)
            target_q = self.critic_target([next_states, target_actions])
            y = rewards + self.gamma * target_q * (1 - dones)
            critic_q = self.critic_local([states, actions])
            critic_loss = tf.reduce_mean(tf.square(y - critic_q))
        critic_grad = tape.gradient(critic_loss, self.critic_local.trainable_variables)
        self.critic_optimizer.apply_gradients(zip(critic_grad, self.critic_local.trainable_variables))

        # --- Train Actor ---
        with tf.GradientTape() as tape:
            actor_actions = self.actor_local(states)
            q_values = self.critic_local([states, actor_actions])
            actor_loss = -tf.reduce_mean(q_values)
        actor_grad = tape.gradient(actor_loss, self.actor_local.trainable_variables)
        self.actor_optimizer.apply_gradients(zip(actor_grad, self.actor_local.trainable_variables))
        
        self.soft_update()

    def soft_update(self):
        # Blend the weights of local and target networks
        critic_weights = self.critic_local.get_weights()
        target_critic_weights = self.critic_target.get_weights()
        for i in range(len(critic_weights)):
            target_critic_weights[i] = self.tau * critic_weights[i] + (1 - self.tau) * target_critic_weights[i]
        self.critic_target.set_weights(target_critic_weights)

        actor_weights = self.actor_local.get_weights()
        target_actor_weights = self.actor_target.get_weights()
        for i in range(len(actor_weights)):
            target_actor_weights[i] = self.tau * actor_weights[i] + (1 - self.tau) * target_actor_weights[i]
        self.actor_target.set_weights(target_actor_weights)

# --- Main Execution ---
if __name__ == "__main__":
    traci.start(["sumo-gui", "-c", SUMO_CONFIG_FILE])

    TRAFFIC_LIGHT_ID = "center" # Change this to your junction ID
    
    # These phases are now just for cycling through directions
    # 0=North, 1=East, 2=South, 3=West
    green_phases = ["Gggrrrrrrrrr", "rrrGggrrrrrr", "rrrrrrGggrrr", "rrrrrrrrrGgg"]
    yellow_phases = ["yyyrrrrrrrrr", "rrryyyrrrrrr", "rrrrrryyyrrr", "rrrrrrrrryyy"]
    
    incoming_lanes = list(dict.fromkeys(traci.trafficlight.getControlledLanes(TRAFFIC_LIGHT_ID)))
    state_size = len(incoming_lanes)
    action_size = 1 # The action is a single continuous value (duration)
    
    # Min and Max green light duration
    MIN_GREEN_TIME = 5
    MAX_GREEN_TIME = 40

    agent = DDPGAgent(state_size, action_size, MIN_GREEN_TIME, MAX_GREEN_TIME)
    
    episodes = 100
    batch_size = 64
    
    for e in range(episodes):
        traci.load(["-c", SUMO_CONFIG_FILE])
        
        step = 0
        total_reward = 0
        current_direction = 0
        
        while step < 3600:
            state_list = [traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes]
            state = np.array(state_list)
            
            # Actor decides the green light duration
            green_duration = agent.act(state)[0][0]
            
            # --- Apply Green and Yellow Phases ---
            traci.trafficlight.setRedYellowGreenState(TRAFFIC_LIGHT_ID, green_phases[current_direction])
            reward = 0
            for _ in range(int(green_duration)):
                if step >= 3600: break
                traci.simulationStep()
                step += 1
                reward -= sum(traci.lane.getWaitingTime(lane) for lane in incoming_lanes)

            traci.trafficlight.setRedYellowGreenState(TRAFFIC_LIGHT_ID, yellow_phases[current_direction])
            for _ in range(4): # Fixed yellow time
                if step >= 3600: break
                traci.simulationStep()
                step += 1
                reward -= sum(traci.lane.getWaitingTime(lane) for lane in incoming_lanes)
            
            # --- Observe new state and learn ---
            next_state_list = [traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes]
            next_state = np.array(next_state_list)
            done = step >= 3600
            
            agent.remember(state, green_duration, reward, next_state, done)
            agent.learn(batch_size)
            
            total_reward += reward
            
            # Move to the next direction in a fixed cycle
            current_direction = (current_direction + 1) % 4
            
        print(f"Episode: {e + 1}/{episodes}, Total Reward: {total_reward:.2f}")
        
    traci.close()