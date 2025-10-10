# analysis.py (Final All-in-One Version)
# This script generates all the plots needed for the final project report.

import traci
import sys
import os
import random
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import pickle

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- 1. FUNCTIONS FOR PARSING & PLOTTING ---

def get_trip_stats(xml_file):
    """Parses a tripinfo file and returns avg waiting time and total throughput."""
    try:
        tree = ET.parse(xml_file)
    except (FileNotFoundError, ET.ParseError):
        return None, None # Return None if file is missing or corrupt

    root = tree.getroot()
    total_wait_time = 0.0
    vehicle_count = 0
    for tripinfo in root.findall('tripinfo'):
        total_wait_time += float(tripinfo.get('waitingTime'))
        vehicle_count += 1
    
    avg_wait = total_wait_time / vehicle_count if vehicle_count > 0 else 0
    return avg_wait, vehicle_count

def plot_learning_curve(history_file):
    """Plots the agent's average reward per episode during training."""
    try:
        with open(history_file, 'rb') as f:
            history = pickle.load(f)
    except FileNotFoundError:
        print(f"Warning: Cannot find '{history_file}'. Skipping learning curve plot.")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(history) + 1), history, marker='o', linestyle='-')
    plt.title('DQN Agent Learning Curve')
    plt.xlabel('Episode')
    plt.ylabel('Average Reward per Episode')
    plt.grid(True)
    print("Displaying DQN Learning Curve Plot...")
    plt.show()

def collect_queue_data(controller_type):
    """Runs a short simulation and collects queue length data at each step."""
    queue_lengths = []
    
    if controller_type == 'Fixed-Timer':
        # Must enable the .add.xml file for this run
        sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--additional-files", "cross.add.xml", "--duration-log.disable", "true"]
    elif controller_type == 'DQN':
        # Assumes dqn_model.h5 is present
        # Must disable the .add.xml file for this run
        sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--duration-log.disable", "true"]
        model = tf.keras.models.load_model('dqn_model.h5', compile=False)
    else:
        return []

    traci.start(sumo_cmd)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        if controller_type == 'DQN':
            # Simplified DQN logic for data collection
            state = get_state_for_dqn()
            action = np.argmax(model.predict(state, verbose=0)[0])
            # Perform action (simplified for speed)
            current_phase = traci.trafficlight.getPhase("J1")
            is_ns_green = current_phase in [0, 1]
            if action == 1: # Switch
                yellow_phase = 1 if is_ns_green else 3
                traci.trafficlight.setPhase("J1", yellow_phase)
                for _ in range(4): traci.simulationStep()
                next_green_phase = 2 if is_ns_green else 0
                traci.trafficlight.setPhase("J1", next_green_phase)
                for _ in range(10): traci.simulationStep()
            else: # Stay
                for _ in range(10): traci.simulationStep()
        else:
             traci.simulationStep()

        # Record total queue length
        total_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ALL_LANES)
        queue_lengths.append(total_queue)
        
    traci.close()
    return queue_lengths

def plot_queue_over_time(fixed_timer_queues, dqn_queues):
    """Plots the total number of waiting cars over time for two controllers."""
    plt.figure(figsize=(12, 6))
    plt.plot(fixed_timer_queues, label='Fixed-Timer', color='#d9534f')
    plt.plot(dqn_queues, label='DQN Agent', color='#f0ad4e')
    plt.title('Congestion Over Time: Fixed-Timer vs. DQN Agent')
    plt.xlabel('Simulation Time (seconds)')
    plt.ylabel('Total Waiting Cars (Queue Length)')
    plt.legend()
    plt.grid(True)
    print("Displaying Queue Length Over Time Plot...")
    plt.show()

def plot_performance_metrics(results):
    """Creates a grouped bar chart for wait time and throughput."""
    labels = list(results.keys())
    wait_times = [res['wait'] for res in results.values()]
    throughputs = [res['throughput'] for res in results.values()]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Bar chart for waiting time
    color = 'tab:red'
    ax1.set_xlabel('Controller Type')
    ax1.set_ylabel('Average Waiting Time (s)', color=color)
    ax1.bar(x - width/2, wait_times, width, label='Avg. Wait Time', color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    # Instantiate a second axes that shares the same x-axis
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Total Throughput (vehicles)', color=color)
    ax2.bar(x + width/2, throughputs, width, label='Throughput', color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    fig.suptitle('Overall Performance Comparison of Traffic Controllers')
    fig.tight_layout()
    print("Displaying Final Performance Metrics Plot...")
    plt.show()

# --- HELPER VARS & FUNCS FOR DATA COLLECTION ---
# Must match the DQN training script
ALL_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2", "E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]
try:
    import tensorflow as tf
    def get_state_for_dqn():
        ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ALL_LANES if 'N_in' in lane or 'S_in' in lane)
        ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ALL_LANES if 'E_in' in lane or 'W_in' in lane)
        ns_wait = sum(traci.lane.getWaitingTime(lane) for lane in ALL_LANES if 'N_in' in lane or 'S_in' in lane)
        ew_wait = sum(traci.lane.getWaitingTime(lane) for lane in ALL_LANES if 'E_in' in lane or 'W_in' in lane)
        state = np.array([ns_queue / 50.0, ew_queue / 50.0, ns_wait / 1000.0, ew_wait / 1000.0])
        return np.reshape(state, [1, 4])
except ImportError:
    print("Warning: TensorFlow not found. DQN data collection will be skipped.")
    tf = None

# --- MAIN ANALYSIS SCRIPT ---
if __name__ == "__main__":
    
    # 1. Plot Learning Curve
    plot_learning_curve('dqn_learning_history.pkl')

    # 2. Collect and Plot Queue Data
    print("\nStarting data collection for Queue Length plot...")
    print("(This will run two short, headless simulations in the background)")
    fixed_timer_queues = collect_queue_data('Fixed-Timer')
    
    dqn_queues = []
    if tf: # Only run if tensorflow is installed
        try:
            dqn_queues = collect_queue_data('DQN')
        except (IOError, ImportError):
             print("Warning: 'dqn_model.h5' not found. Skipping DQN for queue plot.")

    if fixed_timer_queues and dqn_queues:
        plot_queue_over_time(fixed_timer_queues, dqn_queues)

    # 3. Analyze Tripinfo files and Plot Final Metrics
    print("\nAnalyzing all tripinfo files for final comparison...")
    final_results = {}
    files_to_analyze = {
        'Fixed-Timer': 'tripinfo_fixed.xml',
        'LQF Agent': 'tripinfo_lqf.xml',
        'Q-Learning': 'tripinfo_q_learning_optimized.xml', # Assuming you used the optimized one
        'DQN Agent': 'tripinfo_dqn.xml'
    }

    for name, filename in files_to_analyze.items():
        avg_wait, throughput = get_trip_stats(filename)
        if avg_wait is not None:
            final_results[name] = {'wait': avg_wait, 'throughput': throughput}
            
    if final_results:
        print("\n--- Final Performance Summary ---")
        for name, data in final_results.items():
            print(f"{name:<15}: Avg Wait: {data['wait']:.2f}s | Throughput: {data['throughput']} vehicles")
        
        plot_performance_metrics(final_results)
    else:
        print("No tripinfo files found to analyze.")

