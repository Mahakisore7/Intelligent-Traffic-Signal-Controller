# runner_with_vehicle_avg_wait.py
import os
import sys
import traci
import argparse
import numpy as np
import xml.etree.ElementTree as ET # Library to read the XML output file
from controllers import FixedTimeController, LongestQueueFirstController
from dqn_agent import QLearningAgent, DQNAgent

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

AMBULANCE_DEPART_STEP = 150

def get_options():
    parser = argparse.ArgumentParser(description="SUMO Traffic Light Control Simulation")
    parser.add_argument("--model", type=str, choices=['fixed', 'lqf', 'qlearn', 'dqn'], default='dqn', help="Controller model to use")
    parser.add_argument("--gui", action="store_true", default=False, help="Run with SUMO GUI")
    parser.add_argument("--steps", type=int, default=3600, help="Number of simulation steps")
    args = parser.parse_args()
    return args

def calculate_avg_wait_time_per_vehicle(tripinfo_file):
    """
    Parses the tripinfo.xml file to calculate the average time loss (waiting time) per vehicle.
    """
    try:
        tree = ET.parse(tripinfo_file)
        root = tree.getroot()
        
        total_time_loss = 0
        num_vehicles = 0
        
        for trip in root.findall('tripinfo'):
            time_loss = float(trip.get('timeLoss'))
            total_time_loss += time_loss
            num_vehicles += 1
            
        if num_vehicles == 0:
            return 0
            
        return total_time_loss / num_vehicles
    except ET.ParseError:
        print(f"Warning: Could not parse {tripinfo_file}. It might be empty or malformed.")
        return 0
    except FileNotFoundError:
        print(f"Warning: {tripinfo_file} not found. Returning 0.")
        return 0


def run():
    args = get_options()
    
    os.makedirs("results", exist_ok=True)
    tripinfo_filepath = os.path.join("results", "tripinfo.xml")

    sumo_binary = "sumo-gui" if args.gui else "sumo"
    # Make sure SUMO writes the tripinfo file to the results folder
    sumo_cmd = [sumo_binary, "-c", "intersection.sumocfg", "--tripinfo-output", tripinfo_filepath]
    
    traci.start(sumo_cmd)
    
    ts_id = 'C'
    
    incoming_lanes = {
        'N': ['N2C_0', 'N2C_1'], 'E': ['E2C_0', 'E2C_1'],
        'S': ['S2C_0', 'S2C_1'], 'W': ['W2C_0', 'W2C_1']
    }
    
    green_phases = [
        "GGGggrrrrrrrrrrrrrrr", "rrrrrGGGggrrrrrrrrrr",
        "rrrrrrrrrrGGGggrrrrr", "rrrrrrrrrrrrrrrGGGgg"
    ]
    yellow_phases = [
        "yyyyyrrrrrrrrrrrrrrr", "rrrrryyyyyrrrrrrrrrr",
        "rrrrrrrrrryyyyyrrrrr", "rrrrrrrrrrrrrrryyyyy"
    ]
    
    controller = None
    if args.model == 'fixed':
        controller = FixedTimeController(ts_id)
    elif args.model == 'lqf':
        controller = LongestQueueFirstController(ts_id)
    elif args.model == 'qlearn':
        controller = QLearningAgent(actions=[0, 1, 2, 3], state_size=81)
        if hasattr(controller, 'load_q_table'):
            controller.load_q_table("q_table_directional.csv")
    elif args.model == 'dqn':
        controller = DQNAgent(state_size=4, action_size=4)
        
    step = 0
    last_action = -1
    last_state = None
    last_wait_time = 0 
    time_in_yellow = 0
    emergency_active = False
    
    # --- FIX: ADD THIS LINE BACK ---
    yellow_duration = 4
    
    while step < args.steps:
        traci.simulationStep()

        ambulance_id = None
        # This logic is simplified to just check for the presence of any ambulance
        for i, direction in enumerate(['N', 'E', 'S', 'W']):
            for lane in incoming_lanes[direction]:
                if any(traci.vehicle.getTypeID(veh_id) == 'ambulance' for veh_id in traci.lane.getLastStepVehicleIDs(lane)):
                    ambulance_id = "ambulance_1"
                    ambulance_direction_index = i
                    break
            if ambulance_id:
                break
        
        if ambulance_id:
            if not emergency_active:
                print(f"Step {step}: Ambulance detected! Overriding traffic light.")
                emergency_active = True
            traci.trafficlight.setRedYellowGreenState(ts_id, green_phases[ambulance_direction_index])
            last_action = -1
            time_in_yellow = 0
        else:
            if emergency_active:
                print(f"Step {step}: Ambulance has cleared. Resuming normal control.")
                emergency_active = False

            if args.model in ['fixed', 'lqf']:
                controller.update()
            else:
                current_total_wait = sum(traci.lane.getWaitingTime(l) for lanes in incoming_lanes.values() for l in lanes)

                if time_in_yellow > 0:
                    time_in_yellow -= 1
                    if time_in_yellow == 0:
                        traci.trafficlight.setRedYellowGreenState(ts_id, green_phases[last_action])
                else: 
                    current_state = controller.get_state(incoming_lanes)
                    if last_action != -1:
                        reward = last_wait_time - current_total_wait
                        if isinstance(controller, QLearningAgent):
                            controller.update_q_table(last_state, last_action, reward, current_state)
                        elif isinstance(controller, DQNAgent):
                            controller.remember(last_state, last_action, reward, current_state)
                            if len(controller.memory) > 32:
                                controller.replay(32)
                    action = controller.choose_action(current_state)
                    if action != last_action and last_action != -1:
                        traci.trafficlight.setRedYellowGreenState(ts_id, yellow_phases[last_action])
                        time_in_yellow = yellow_duration
                    else:
                        traci.trafficlight.setRedYellowGreenState(ts_id, green_phases[action])
                    last_action = action
                    last_state = current_state
                last_wait_time = current_total_wait
        step += 1

    if isinstance(controller, QLearningAgent) and hasattr(controller, 'save_q_table'):
        controller.save_q_table("q_table_directional.csv")
    traci.close()
    
    avg_wait_time = calculate_avg_wait_time_per_vehicle(tripinfo_filepath)
    
    print(f"\n--- Simulation Results ---")
    print(f"Controller Model: {args.model.upper()}")
    print(f"Average waiting time per vehicle: {avg_wait_time:.2f} seconds.")
    print(f"--------------------------")

if __name__ == "__main__":
    run()