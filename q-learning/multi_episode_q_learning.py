import traci
from sumolib import checkBinary
import random
import numpy as np
import time
import pickle
import os

class QLearningAgent:
    def __init__(self, actions, learning_rate=0.1, reward_decay=0.9, exploration_rate=0.1):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = exploration_rate
        self.q_table = {}

    def choose_action(self, observation):
        if observation not in self.q_table:
            self.q_table[observation] = {action: 0.0 for action in self.actions}
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        else:
            state_actions = self.q_table[observation]
            max_value = max(state_actions.values())
            best_actions = [a for a, v in state_actions.items() if v == max_value]
            return random.choice(best_actions)

    def learn(self, state, action, reward, next_state):
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.actions}
        q_predict = self.q_table[state][action]
        q_target = reward + self.gamma * max(self.q_table[next_state].values())
        self.q_table[state][action] += self.lr * (q_target - q_predict)
        
    def save_q_table(self, file_name):
        with open(file_name, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load_q_table(self, file_name):
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                self.q_table = pickle.load(f)

class SumoRunner:
    def __init__(self, sumo_cfg, agent, gui=False):
        self.sumo_cfg = sumo_cfg
        self.agent = agent
        # Use 'sumo-gui' for visuals or 'sumo' for fast, non-visual training
        self.sumo_binary = checkBinary('sumo-gui' if gui else 'sumo')
        self.metrics = None # Will be reset each episode

    def reset_metrics(self):
        self.metrics = {"total_steps": 0, "cumulative_wait_time": 0}

    def run_episode(self):
        self.reset_metrics()
        traci.start([self.sumo_binary, "-c", self.sumo_cfg, "--step-length", "1", "--no-warnings", "true"])
        
        tls_id = "center"
        self.agent.actions = [0, 2, 4, 6] # Green phases
        last_state, last_action = None, None
        time_since_last_decision, decision_interval = 0, 10
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)[0]
        all_phase_definitions = logic.phases
        
        step = 0
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                
                controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
                if controlled_lanes:
                    self.metrics["cumulative_wait_time"] += sum(traci.lane.getWaitingTime(lane) for lane in controlled_lanes)

                current_phase_index = traci.trafficlight.getPhase(tls_id)
                if 'y' in all_phase_definitions[current_phase_index].state.lower():
                    time_since_last_decision += 1
                    step += 1
                    continue

                if time_since_last_decision >= decision_interval:
                    current_state = tuple(1 if traci.lane.getLastStepHaltingNumber(lane) > 0 else 0 for lane in controlled_lanes)
                    if last_state is not None:
                        reward = -sum(traci.lane.getWaitingTime(lane) for lane in controlled_lanes)
                        self.agent.learn(last_state, last_action, reward, current_state)
                    
                    action = self.agent.choose_action(current_state)
                    if current_phase_index != action:
                        traci.trafficlight.setPhase(tls_id, action)
                    
                    last_state, last_action = current_state, action
                    time_since_last_decision = 0
                
                time_since_last_decision += 1
                step += 1
        except Exception as e:
            print(f"Error during episode: {e}")
        finally:
            traci.close()
            self.metrics["total_steps"] = step
            return self.metrics

if __name__ == "__main__":
    CONFIG_FILE = "intersection.sumocfg"
    Q_TABLE_FILE = "q_table.pkl"
    NUM_EPISODES = 10 # Set the number of training episodes

    q_agent = QLearningAgent(actions=[])
    q_agent.load_q_table(Q_TABLE_FILE) # Load previous knowledge if it exists

    # Use GUI for the last few episodes to visualize the trained agent
    for episode in range(NUM_EPISODES):
        use_gui = (episode >= NUM_EPISODES - 2)
        runner = SumoRunner(sumo_cfg=CONFIG_FILE, agent=q_agent, gui=use_gui)
        
        print(f"--- Starting Episode {episode + 1}/{NUM_EPISODES} ---")
        metrics = runner.run_episode()
        print(f"Episode {episode + 1} finished in {metrics['total_steps']} steps.")
        print(f"Total Cumulative Wait Time: {metrics['cumulative_wait_time']:.2f} s")
        
        # Save progress after each episode
        q_agent.save_q_table(Q_TABLE_FILE)

    print("\n--- Training Finished ---")