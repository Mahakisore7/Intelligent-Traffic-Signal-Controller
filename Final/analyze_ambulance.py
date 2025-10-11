# analyze_ambulance.py (Final Version with Visualization)
# This script analyzes the ambulance experiment data and generates a comparative bar chart.

import xml.etree.ElementTree as ET
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# --- ANALYSIS FUNCTION ---
def get_ambulance_stats(xml_file, ambulance_id="ambulance_1"):
    """
    Parses a tripinfo XML file and finds the specific stats for the ambulance.
    Returns its waiting time and total travel time (duration).
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        for tripinfo in root.findall('tripinfo'):
            if tripinfo.get('id') == ambulance_id:
                wait_time = float(tripinfo.get('waitingTime'))
                duration = float(tripinfo.get('duration'))
                return wait_time, duration
                
        return None, None
        
    except (FileNotFoundError, ET.ParseError):
        print(f"Error: Cannot find or parse the file '{xml_file}'.")
        return None, None

def plot_ambulance_results(stats):
    """Creates and displays a bar chart comparing ambulance performance."""
    labels = ['Without Preemption', 'With Preemption']
    travel_times = [stats['no_preempt']['duration'], stats['with_preempt']['duration']]
    wait_times = [stats['no_preempt']['wait'], stats['with_preempt']['wait']]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 7))
    rects1 = ax.bar(x - width/2, travel_times, width, label='Total Travel Time', color='#5bc0de')
    rects2 = ax.bar(x + width/2, wait_times, width, label='Waiting Time', color='#f0ad4e')

    ax.set_ylabel('Time (seconds)')
    ax.set_title('Ambulance Performance: With vs. Without Preemption System')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    # Add labels on top of the bars
    ax.bar_label(rects1, padding=3, fmt='%.2fs')
    ax.bar_label(rects2, padding=3, fmt='%.2fs')

    fig.tight_layout()
    plt.show()


# --- SCRIPT ENTRY POINT ---
if __name__ == "__main__":
    print("\n--- Ambulance Preemption Analysis ---")
    
    file_no_preemption = 'tripinfo_no_preemption.xml'
    file_with_preemption = 'tripinfo_with_preemption.xml'

    if not os.path.exists(file_no_preemption) or not os.path.exists(file_with_preemption):
        print("\nERROR: Required result files not found.")
        sys.exit()

    wait_no, duration_no = get_ambulance_stats(file_no_preemption)
    wait_with, duration_with = get_ambulance_stats(file_with_preemption)

    if wait_no is None or wait_with is None:
        sys.exit("Could not find ambulance data in one or both result files.")

    print("\n--- RESULTS ---")
    print(f"  - Travel Time WITHOUT Preemption: {duration_no:.2f}s (Wait Time: {wait_no:.2f}s)")
    print(f"  - Travel Time WITH Preemption:    {duration_with:.2f}s (Wait Time: {wait_with:.2f}s)")
    
    time_saved = duration_no - duration_with
    print(f"\nConclusion: The preemption system reduced the ambulance's total travel time by {time_saved:.2f} seconds.")

    # Prepare data for plotting
    plot_data = {
        'no_preempt': {'duration': duration_no, 'wait': wait_no},
        'with_preempt': {'duration': duration_with, 'wait': wait_with}
    }
    plot_ambulance_results(plot_data)