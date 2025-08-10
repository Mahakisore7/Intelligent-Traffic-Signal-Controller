import traci
from sumolib import checkBinary
import random
import os
import pickle
import numpy as np
import time

class QLearningAgent:
    """
    A simplified agent that only uses a pre-trained Q-table.
    """
    def __init__(self, actions):
        self.actions = actions
        self.q_table = {}

    def choose_action(self, observation):
        """
        Chooses the best action from the Q-table (no exploration).
        """
        if observation not in self.q_table:
            # If state is unknown, choose a random action
            return random.choice(self.actions)
        else:
            # Always exploit: choose the best known action
            state_actions = self.q_table[observation]
            max_value = max(state_actions.values())
            best_actions = [a for a, v in state_actions.items() if v == max_value]
            return random.choice(best_actions)

    def load_q_table(self, file_name):
        """
        Loads the Q-table from a file.
        """
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                self.q_table = pickle.load(f)
            print(f"Trained Q-table loaded from {file_name}")
        else:
            print(f"Warning: Q-table file not found at {file_name}. Agent will act randomly.")

class SumoRunner:
    """
    Runs a single simulation using the trained agent and collects metrics.
    """
    def __init__(self, sumo_cfg, agent):
        self.sumo_cfg = sumo_cfg
        self.agent = agent
        self.sumo_binary = checkBinary('sumo-gui')
        # MODIFIED: Added metrics dictionary
        self.metrics = {
            "total_steps": 0,
            "real_world_time": 0,
            "cumulative_wait_time": 0,
            "max_individual_wait_time": 0,
            "max_queue_length": 0
        }

    def update_metrics(self):
        """
        Updates metrics at each simulation step, focusing on individual cars.
        """
        vehicle_ids = traci.vehicle.getIDList()
        if not vehicle_ids:
            return

        # Max individual car waiting time
        individual_wait_times = [traci.vehicle.getWaitingTime(vehID) for vehID in vehicle_ids]
        if individual_wait_times:
            current_max_wait = max(individual_wait_times)
            if current_max_wait > self.metrics["max_individual_wait_time"]:
                self.metrics["max_individual_wait_time"] = current_max_wait

        # Other metrics
        self.metrics["cumulative_wait_time"] += sum(individual_wait_times)
        controlled_lanes = traci.trafficlight.getControlledLanes("center")
        if controlled_lanes:
            queues = [traci.lane.getLastStepHaltingNumber(lane) for lane in controlled_lanes]
            current_max_queue = max(queues) if queues else 0
            if current_max_queue > self.metrics["max_queue_length"]:
                self.metrics["max_queue_length"] = current_max_queue
    
    def summarize_results(self):
        """
        Prints a final summary of the collected performance metrics.
        """
        print("\n--- Trained Agent Performance Summary ---")
        print(f"Total Simulation Steps: {self.metrics['total_steps']}")
        print(f"Real-World Execution Time: {self.metrics['real_world_time']:.2f} seconds")
        print(f"Max Individual Waiting Time: {self.metrics['max_individual_wait_time']:.2f} s")
        print(f"Max Queue Length observed: {self.metrics['max_queue_length']} vehicles")
        print(f"Total Cumulative Waiting Time (All Cars): {self.metrics['cumulative_wait_time']:.2f} s")
        print("-----------------------------------------\n")

    def run(self):
        start_time = time.time()
        traci.start([self.sumo_binary, "-c", self.sumo_cfg, "--step-length", "1", "--no-warnings", "true"])
        
        tls_id = "center"
        self.agent.actions = [0, 2, 4, 6]
        
        time_since_last_decision = 0
        decision_interval = 10

        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)[0]
        all_phase_definitions = logic.phases
        
        step = 0
        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()
                self.update_metrics() # Collect metrics at each step

                current_phase_index = traci.trafficlight.getPhase(tls_id)
                current_definition = all_phase_definitions[current_phase_index]

                if 'y' in current_definition.state.lower():
                    time_since_last_decision += 1
                    continue

                if time_since_last_decision >= decision_interval:
                    controlled_lanes = traci.trafficlight.getControlledLanes(tls_id)
                    current_state = tuple(1 if traci.lane.getLastStepHaltingNumber(lane) > 0 else 0 for lane in controlled_lanes)
                    
                    action = self.agent.choose_action(current_state)
                    if current_phase_index != action:
                        traci.trafficlight.setPhase(tls_id, action)
                    
                    time_since_last_decision = 0
                
                time_since_last_decision += 1
                step += 1
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            end_time = time.time()
            self.metrics["total_steps"] = step
            self.metrics["real_world_time"] = end_time - start_time
            print("Simulation finished.")
            self.summarize_results() # Print the final summary
            traci.close()

if __name__ == "__main__":
    CONFIG_FILE = "intersection.sumocfg"
    Q_TABLE_FILE = "q_table.pkl"
    
    q_agent = QLearningAgent(actions=[0, 2, 4, 6])
    q_agent.load_q_table(Q_TABLE_FILE)
    
    runner = SumoRunner(sumo_cfg=CONFIG_FILE, agent=q_agent)
    runner.run()