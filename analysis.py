import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt # Import the plotting library

def get_average_wait_time(xml_file):
    """Parses a SUMO tripinfo XML and returns the average waiting time."""
    tree = ET.parse(xml_file)
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

def plot_results(fixed_time, lqf_time):
    """Creates and displays a bar chart comparing the results."""
    controllers = ['Fixed-Timer', 'LQF Agent']
    wait_times = [fixed_time, lqf_time]

    plt.figure(figsize=(8, 6)) # Create a figure to draw on
    bars = plt.bar(controllers, wait_times, color=['#d9534f', '#5cb85c']) # Red for bad, green for good

    plt.ylabel('Average Waiting Time (seconds)') # Set the Y-axis label
    plt.title('Performance Comparison of Traffic Controllers') # Set the chart's title
    plt.ylim(0, max(wait_times) * 1.1) # Set the Y-axis limit to be a bit taller than the tallest bar

    # Add the wait time value on top of each bar
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f'{yval:.2f}s', ha='center', va='bottom')

    plt.show() # Display the chart in a new window

# --- Main Analysis ---
if __name__ == "__main__":
    try:
        avg_wait_fixed = get_average_wait_time('tripinfo_fixed.xml')
        avg_wait_lqf = get_average_wait_time('tripinfo_lqf.xml')

        print("\n--- Traffic Control Performance Analysis ---")
        print(f"Fixed-Timer Controller Average Wait Time: {avg_wait_fixed:.2f} seconds")
        print(f"LQF Agent Controller Average Wait Time:   {avg_wait_lqf:.2f} seconds")
        print("------------------------------------------")

        if avg_wait_fixed > 0:
            improvement = ((avg_wait_fixed - avg_wait_lqf) / avg_wait_fixed) * 100
            print(f"\nYour smart agent reduced the average waiting time by {improvement:.2f}%.")

        # Call the new plotting function
        plot_results(avg_wait_fixed, avg_wait_lqf)

    except FileNotFoundError as e:
        print(f"\nError: Could not find a results file. Did you run both simulations first?")
        print(f"Missing file: {e.filename}")