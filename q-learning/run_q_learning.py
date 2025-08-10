import traci
from sumolib import checkBinary
import random
import numpy as np
import time

class QLearningAgent:
    """
    The agent that implements the Q-learning algorithm.
    """
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
            self.q_table[next_state] = {action: 0.0 for a in self.actions}
        q_predict = self.q_table[state][action]
        q_target = reward + self.gamma * max(self.q_table[next_state].values())
        self.q_table[state][action] += self.lr * (q_target - q_predict)

# ---

class SumoRunner:
    """
    Manages the SUMO simulation and the interaction with the agent.
    """
    def __init__(self, sumo_cfg, agent):
        self.sumo_cfg = sumo_cfg
        self.agent = agent
        self.sumo_binary = checkBinary('sumo-gui')
        # MODIFIED: Changed the metrics we are tracking
        self.metrics = {
            "total_steps": 0,
            "cumulative_wait_time": 0,
            "max_individual_wait_time": 0, 
            "max_queue_length": 0
        }

    def get_state(self, tls_id):
        incoming_lanes = traci.trafficlight.getControlledLanes(tls_id)
        return tuple(1 if traci.lane.getLastStepHaltingNumber(lane) > 0 else 0 for lane in incoming_lanes)

    def get_reward(self, tls_id):
        incoming_lanes = traci.trafficlight.getControlledLanes(tls_id)
        return -sum(traci.lane.getWaitingTime(lane) for lane in incoming_lanes)

    # MODIFIED: This function now correctly finds the max waiting time for a single car
    def update_metrics(self):
        """
        Updates metrics at each simulation step.
        """
        vehicle_ids = traci.vehicle.getIDList()
        if not vehicle_ids:
            return

        # Total cumulative wait time (sum of wait times for all cars)
        total_wait_time_this_step = sum(traci.vehicle.getWaitingTime(vehID) for vehID in vehicle_ids)
        self.metrics["cumulative_wait_time"] += total_wait_time_this_step
        
        # Max individual car waiting time
        individual_wait_times = [traci.vehicle.getWaitingTime(vehID) for vehID in vehicle_ids]
        current_max_wait = max(individual_wait_times)
        if current_max_wait > self.metrics["max_individual_wait_time"]:
            self.metrics["max_individual_wait_time"] = current_max_wait

        # Max queue length
        controlled_lanes = traci.trafficlight.getControlledLanes("center")
        queues = [traci.lane.getLastStepHaltingNumber(lane) for lane in controlled_lanes]
        current_max_queue = max(queues)
        if current_max_queue > self.metrics["max_queue_length"]:
            self.metrics["max_queue_length"] = current_max_queue


    def run(self):
        """
        Executes the main simulation loop.
        """
        start_time = time.time()
        traci.start([self.sumo_binary, "-c", self.sumo_cfg, "--step-length", "1", "--no-warnings", "true"])
        
        tls_id = "center"
        green_phases = [0, 2, 4, 6]
        self.agent.actions = green_phases
        
        last_state, last_action = None, None
        time_since_last_decision, decision_interval = 0, 10
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)[0]
        all_phase_definitions = logic.phases
        
        step = 0
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()

                self.update_metrics() # Call the updated metrics function

                current_phase_index = traci.trafficlight.getPhase(tls_id)
                current_definition = all_phase_definitions[current_phase_index]

                if 'y' in current_definition.state.lower():
                    time_since_last_decision += 1
                    continue

                if time_since_last_decision >= decision_interval:
                    current_state = self.get_state(tls_id)
                    if last_state is not None:
                        reward = self.get_reward(tls_id)
                        self.agent.learn(last_state, last_action, reward, current_state)

                    action = self.agent.choose_action(current_state)
                    if current_phase_index != action:
                        traci.trafficlight.setPhase(tls_id, action)
                    
                    last_state, last_action = current_state, action
                    time_since_last_decision = 0
                
                time_since_last_decision += 1
                step += 1

        except Exception as e:
            print(f"An error occurred: {e}")
        
        finally:
            end_time = time.time()
            self.metrics["total_steps"] = step
            self.metrics["real_world_time"] = end_time - start_time
            
            # MODIFIED: The final summary now shows the correct metrics
            print("\n--- Q-Learning Simulation Summary ---")
            print(f"Total Simulation Steps: {self.metrics['total_steps']}")
            print(f"Real-World Execution Time: {self.metrics['real_world_time']:.2f} seconds")
            print(f"Max Individual Waiting Time: {self.metrics['max_individual_wait_time']:.2f} s")
            print(f"Max Queue Length observed: {self.metrics['max_queue_length']} vehicles")
            print(f"Total Cumulative Waiting Time (All Cars): {self.metrics['cumulative_wait_time']:.2f} s")
            print("------------------------------------------\n")
            traci.close()

# ---

if __name__ == "__main__":
    CONFIG_FILE = "intersection.sumocfg" 
    
    q_agent = QLearningAgent(actions=[]) 
    runner = SumoRunner(sumo_cfg=CONFIG_FILE, agent=q_agent)
    runner.run()