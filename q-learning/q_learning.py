import traci
from sumolib import checkBinary
import random
import numpy as np

class QLearningAgent:
    def __init__(self, actions, learning_rate=0.1, reward_decay=0.9):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.q_table = {}

    def choose_action(self, observation, explore_rate=0.1):
        if observation not in self.q_table:
            self.q_table[observation] = {action: 0.0 for action in self.actions}
        if random.random() < explore_rate:
            action = random.choice(self.actions)
        else:
            state_actions = self.q_table[observation]
            max_value = max(state_actions.values())
            best_actions = [a for a, v in state_actions.items() if v == max_value]
            action = random.choice(best_actions)
        return action

    def learn(self, state, action, reward, next_state):
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.actions}
        q_predict = self.q_table[state][action]
        q_target = reward + self.gamma * max(self.q_table[next_state].values())
        self.q_table[state][action] += self.lr * (q_target - q_predict)

class SumoRunner:
    def __init__(self, sumo_cfg, agent):
        self.sumo_cfg = sumo_cfg
        self.agent = agent
        self.sumo_binary = checkBinary('sumo-gui')
        
        self.metrics = {
            "steps": [],
            "total_vehicles": [],
            "avg_wait_time": [],
            "max_wait_time": [],
            "cumulative_wait_time": 0,
            "avg_queue_length": [],
            "max_queue_length": []
        }

    def get_state(self, tls_id):
        incoming_lanes = traci.trafficlight.getControlledLanes(tls_id)
        state = tuple(1 if traci.lane.getLastStepHaltingNumber(lane) > 0 else 0 for lane in incoming_lanes)
        return state

    def get_reward(self, tls_id):
        incoming_lanes = traci.trafficlight.getControlledLanes(tls_id)
        wait_time = sum(traci.lane.getWaitingTime(lane) for lane in incoming_lanes)
        return -wait_time

    def collect_metrics(self, step, tls_id):
        self.metrics["steps"].append(step)
        self.metrics["total_vehicles"].append(traci.vehicle.getIDCount())
        incoming_lanes = traci.trafficlight.getControlledLanes(tls_id)
        
        wait_times = [traci.lane.getWaitingTime(lane) for lane in incoming_lanes]
        max_wait = max(wait_times) if wait_times else 0
        avg_wait = np.mean(wait_times) if wait_times else 0
        
        self.metrics["max_wait_time"].append(max_wait)
        self.metrics["avg_wait_time"].append(avg_wait)
        self.metrics["cumulative_wait_time"] += sum(wait_times)
        
        queue_lengths = [traci.lane.getLastStepHaltingNumber(lane) for lane in incoming_lanes]
        self.metrics["avg_queue_length"].append(np.mean(queue_lengths) if queue_lengths else 0)
        self.metrics["max_queue_length"].append(max(queue_lengths) if queue_lengths else 0)

    def run(self):
        traci.start([self.sumo_binary, "-c", self.sumo_cfg, "--step-length", "1", "--no-warnings", "true"])
        
        tls_id = "center"  # Your traffic light ID from your network file
        green_phases = [0, 2, 4, 6]  # Phases where green lights occur
        self.agent.actions = green_phases
        
        last_state, last_action = None, None
        decision_interval, time_since_last_decision = 10, 0
        
        logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)[0]
        all_phase_definitions = logic.phases
        simulation_steps = 1800

        try:
            for step in range(simulation_steps):
                if traci.simulation.getMinExpectedNumber() == 0 and step > 10:
                    print(f"All vehicles have left at step {step}. Ending early.")
                    break

                traci.simulationStep()
                self.collect_metrics(step, tls_id)

                current_phase_index = traci.trafficlight.getPhase(tls_id)
                current_definition = all_phase_definitions[current_phase_index]

                # Skip decision during yellow light to avoid abrupt changes
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

        except Exception as e:
            print(f"A Python error occurred: {e}")
        
        finally:
            print("Simulation finished.")
            max_wait = max(self.metrics["max_wait_time"]) if self.metrics["max_wait_time"] else 0
            avg_wait = np.mean(self.metrics["avg_wait_time"]) if self.metrics["avg_wait_time"] else 0
            total_cum_wait = self.metrics["cumulative_wait_time"]
            max_queue = max(self.metrics["max_queue_length"]) if self.metrics["max_queue_length"] else 0

            print(f"Max Waiting Time observed: {max_wait:.2f} seconds")
            print(f"Average Waiting Time over simulation: {avg_wait:.2f} seconds")
            print(f"Total Cumulative Waiting Time: {total_cum_wait:.2f} seconds")
            print(f"Max Queue Length observed: {max_queue}")
            traci.close()

if __name__ == "__main__":
    config_file = "intersection.sumocfg"  # your SUMO configuration file
    q_agent = QLearningAgent(actions=[])  # will be set later dynamically
    runner = SumoRunner(sumo_cfg=config_file, agent=q_agent)
    runner.run()
