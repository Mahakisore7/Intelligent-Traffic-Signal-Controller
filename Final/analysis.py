# analysis.py (Final All-in-One Visualization Suite)
# This script generates all the advanced plots for the final project report.

import traci
import sys
import os
import random
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import pickle
import seaborn as sns
import pandas as pd

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- 1. FUNCTIONS FOR PARSING & PLOTTING ---

def get_trip_data(xml_file):
    """Parses a tripinfo file and returns a list of all waiting times."""
    try:
        tree = ET.parse(xml_file)
    except (FileNotFoundError, ET.ParseError):
        print(f"Warning: Could not find or parse '{xml_file}'. It will be skipped.")
        return None

    root = tree.getroot()
    waiting_times = [float(tripinfo.get('waitingTime')) for tripinfo in root.findall('tripinfo')]
    return waiting_times

def plot_learning_curve(history_file):
    """Plots the agent's total reward per episode during training."""
    try:
        with open(history_file, 'rb') as f:
            history = pickle.load(f)
        
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(history) + 1), history, marker='o', linestyle='-')
        plt.title('DQN Agent Learning Curve', fontsize=16)
        plt.xlabel('Episode', fontsize=12)
        plt.ylabel('Total Reward per Episode', fontsize=12)
        plt.grid(True)
        print("\nDisplaying Plot 1: DQN Learning Curve...")
        plt.show()

    except FileNotFoundError:
        print(f"Warning: Cannot find '{history_file}'. Skipping learning curve plot.")

def collect_queue_data(controller_type):
    """Runs a short, headless simulation to collect queue length data at each second."""
    queue_lengths = []
    
    if controller_type == 'Fixed-Timer':
        sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--additional-files", "cross.add.xml", "--duration-log.disable", "true"]
        traci.start(sumo_cmd)
    elif controller_type == 'DQN':
        sumo_cmd = ["sumo", "-c", "cross.sumocfg", "--duration-log.disable", "true"]
        try:
            model = tf.keras.models.load_model('dqn_model_final.h5', compile=False)
            traci.start(sumo_cmd)
        except (IOError, ImportError):
             print("Warning: 'dqn_model_final.h5' not found or TensorFlow not installed. Skipping DQN for queue plot.")
             return []
    else:
        return []

    while traci.simulation.getMinExpectedNumber() > 0:
        if controller_type == 'DQN':
            state = get_state_for_dqn()
            action = np.argmax(model.predict(state, verbose=0)[0])
            
            current_phase = traci.trafficlight.getPhase("J1")
            is_ns_green = current_phase in [0, 1]
            if action == 1 and traci.trafficlight.getPhaseDuration("J1") > 10:
                yellow_phase = 1 if is_ns_green else 3
                traci.trafficlight.setPhase("J1", yellow_phase)
                for _ in range(4): traci.simulationStep()
            traci.simulationStep()
        else:
             traci.simulationStep()

        total_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ALL_LANES)
        queue_lengths.append(total_queue)
        
    traci.close()
    return queue_lengths

def plot_queue_over_time(fixed_timer_queues, dqn_queues):
    """Plots the total number of waiting cars over time for two controllers."""
    plt.figure(figsize=(12, 6))
    plt.plot(fixed_timer_queues, label='Fixed-Timer', color='#d9534f', alpha=0.8)
    plt.plot(dqn_queues, label='DQN Agent', color='#f0ad4e', alpha=0.8)
    plt.title('Congestion Over Time: Fixed-Timer vs. DQN Agent', fontsize=16)
    plt.xlabel('Simulation Time (seconds)', fontsize=12)
    plt.ylabel('Total Waiting Cars (Queue Length)', fontsize=12)
    plt.legend()
    plt.grid(True)
    print("\nDisplaying Plot 2: Congestion Over Time...")
    plt.show()

def plot_wait_time_distribution(all_data):
    """Creates a violin plot to show the distribution of waiting times."""
    df = pd.DataFrame(all_data)
    
    plt.figure(figsize=(12, 7))
    sns.violinplot(data=df, palette={'Fixed-Timer': '#d9534f', 'LQF Agent': '#5cb85c', 'Q-Learning': '#428bca', 'DQN Agent': '#f0ad4e'}, cut=0)
    plt.title('Distribution of Vehicle Waiting Times', fontsize=16)
    plt.ylabel('Waiting Time (seconds)', fontsize=12)
    plt.xlabel('Controller Type', fontsize=12)
    plt.grid(True)
    print("\nDisplaying Plot 3: Waiting Time Distribution (Violin Plot)...")
    plt.show()

# --- HELPER VARS & FUNCS FOR DATA COLLECTION ---
ALL_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2", "E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]
try:
    import tensorflow as tf
    MAX_GREEN_TIME = 60
    def get_state_for_dqn():
        ns_lanes = [lane for lane in traci.trafficlight.getControlledLanes("J1") if 'N_in' in lane or 'S_in' in lane]
        ew_lanes = [lane for lane in traci.trafficlight.getControlledLanes("J1") if 'E_in' in lane or 'W_in' in lane]
        ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ns_lanes)
        ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in ew_lanes)
        current_phase = traci.trafficlight.getPhase("J1")
        phase_is_ns = 1 if current_phase in [0, 1] else 0
        time_since_switch = traci.trafficlight.getPhaseDuration("J1")
        state = np.array([ns_queue / 50.0, ew_queue / 50.0, phase_is_ns, time_since_switch / MAX_GREEN_TIME])
        return np.reshape(state, [1, 4])
except ImportError:
    tf = None

# --- MAIN ANALYSIS SCRIPT ---
if __name__ == "__main__":
    
    # 1. Plot Learning Curve
    plot_learning_curve('dqn_learning_history_final.pkl')

    # 2. Collect and Plot Queue Data
    print("\nStarting data collection for Queue Length plot...")
    print("(This will run two short, headless simulations in the background. This may take a minute.)")
    fixed_timer_queues = collect_queue_data('Fixed-Timer')
    
    dqn_queues = []
    if tf and os.path.exists('dqn_model_final.h5'):
        dqn_queues = collect_queue_data('DQN')
    
    if fixed_timer_queues and dqn_queues:
        plot_queue_over_time(fixed_timer_queues, dqn_queues)

    # 3. Analyze all tripinfo files for distribution plot and final summary
    print("\nAnalyzing all tripinfo files for final comparison...")
    all_wait_data = {}
    summary_stats = {}
    
    files_to_analyze = {
        'Fixed-Timer': 'tripinfo_fixed.xml',
        'LQF Agent': 'tripinfo_lqf.xml',
        'Q-Learning': 'tripinfo_q_learning.xml',
        'DQN Agent': 'tripinfo_dqn_final.xml'
    }

    for name, filename in files_to_analyze.items():
        wait_times = get_trip_data(filename)
        if wait_times is not None:
            all_wait_data[name] = wait_times
            summary_stats[name] = {
                'avg_wait': np.mean(wait_times),
                'throughput': len(wait_times)
            }
            
    if all_wait_data:
        plot_wait_time_distribution(all_wait_data)

        print("\n--- Final Performance Summary ---")
        for name, data in sorted(summary_stats.items(), key=lambda item: item[1]['avg_wait']):
            print(f"{name:<15}: Avg Wait: {data['avg_wait']:.2f}s | Throughput: {data['throughput']} vehicles")
    else:
        print("No tripinfo files found to analyze.")