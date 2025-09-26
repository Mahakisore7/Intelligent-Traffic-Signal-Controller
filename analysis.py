# analysis.py
# Updated version to compare all three controllers: Fixed-Timer, LQF Agent, and Q-Learning Agent.

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import sys

def get_average_wait_time(xml_file):
    """Parses a SUMO tripinfo XML and returns the average waiting time."""
    try:
        tree = ET.parse(xml_file)
    except FileNotFoundError:
        print(f"Error: Cannot find file '{xml_file}'. Please run the corresponding simulation first.")
        return None

    root = tree.getroot()
    total_wait_time = 0.0
    vehicle_count = 0
    for tripinfo in root.findall('tripinfo'):
        wait_time_str = tripinfo.get('waitingTime')
        if wait_time_str:
            total_wait_time += float(wait_time_str)
            vehicle_count += 1
    if vehicle_count == 0:
        return 0
    return total_wait_time / vehicle_count

def plot_results(fixed_time, lqf_time, q_learning_time):
    """Creates and displays a bar chart comparing the results of all three controllers."""
    controllers = ['Fixed-Timer', 'LQF Agent', 'Q-Learning Agent']
    wait_times = [fixed_time, lqf_time, q_learning_time]
    colors = ['#d9534f', '#5cb85c', '#428bca'] # Red, Green, Blue

    plt.figure(figsize=(10, 7))
    bars = plt.bar(controllers, wait_times, color=colors)

    plt.ylabel('Average Waiting Time (seconds)')
    plt.title('Performance Comparison of Traffic Controllers')
    plt.ylim(0, max(wait_times) * 1.2)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f'{yval:.2f}s', ha='center', va='bottom')

    plt.show()

# --- Main Analysis ---
if __name__ == "__main__":
    # Get results for all three agents
    avg_wait_fixed = get_average_wait_time('tripinfo_fixed.xml')
    avg_wait_lqf = get_average_wait_time('tripinfo_lqf.xml')
    avg_wait_q_learning = get_average_wait_time('tripinfo_q_learning.xml')

    # Proceed only if all files were found and parsed
    if all(v is not None for v in [avg_wait_fixed, avg_wait_lqf, avg_wait_q_learning]):
        print("\n--- Traffic Control Performance Analysis ---")
        print(f"Fixed-Timer Controller Average Wait Time: {avg_wait_fixed:.2f} seconds")
        print(f"LQF Agent Controller Average Wait Time:   {avg_wait_lqf:.2f} seconds")
        print(f"Q-Learning Agent Average Wait Time:       {avg_wait_q_learning:.2f} seconds")
        print("------------------------------------------")

        # Call the plotting function with all three results
        plot_results(avg_wait_fixed, avg_wait_lqf, avg_wait_q_learning)
