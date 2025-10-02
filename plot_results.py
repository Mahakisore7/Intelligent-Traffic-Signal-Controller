# plot_results.py
import numpy as np
import matplotlib.pyplot as plt
import os  # Import the os module

def moving_average(data, window_size):
    """Computes moving average."""
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

# --- Models to plot ---
models = ['fixed', 'lqf', 'qlearn', 'dqn']
window = 100 # For smoothing the plot

plt.figure(figsize=(12, 8))

for model in models:
    try:
        # --- CHANGE 1: CONSTRUCT THE CORRECT FILE PATH AND FILENAME ---
        # Look inside the "results" folder and use the "_directional" suffix
        file_path = os.path.join("results", f'results_{model}_directional.npy')
        
        # Load the total waiting time data
        wait_times = np.load(file_path)
        
        # Calculate cumulative average waiting time
        cumulative_avg_wait_time = np.cumsum(wait_times) / (np.arange(len(wait_times)) + 1)
        
        # Smooth the curve for better visualization
        if len(cumulative_avg_wait_time) >= window:
            smoothed_data = moving_average(cumulative_avg_wait_time, window)
            x_axis = np.arange(len(smoothed_data)) + window -1
            plt.plot(x_axis, smoothed_data, label=f'{model.upper()} Controller')
        else:
            plt.plot(cumulative_avg_wait_time, label=f'{model.upper()} Controller (Raw)')

        print(f"Model: {model.upper()}, Final Average Wait Time: {cumulative_avg_wait_time[-1]:.2f}s")
        
    except FileNotFoundError:
        print(f"File not found for model '{model}'. Searched at: {file_path}. Skipping.")


plt.title('Comparison of Traffic Control Algorithms', fontsize=16)
plt.xlabel(f'Simulation Step (smoothed over {window} steps)', fontsize=12)
plt.ylabel('Cumulative Average Vehicle Waiting Time (s)', fontsize=12)
plt.legend()
plt.grid(True)
plt.show()