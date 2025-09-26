# view_q_table.py
# A simple utility to load and print the contents of the trained Q-Table.

import pickle
import sys

# Define state meanings for readability
QUEUE_LEVELS = {0: "Low", 1: "Medium", 2: "High"}
PHASE_MEANING = {1: "N/S Green", 0: "E/W Green"}

if __name__ == "__main__":
    try:
        with open('q_table.pkl', 'rb') as f:
            q_table = pickle.load(f)
    except FileNotFoundError:
        sys.exit("Error: q_table.pkl not found. Please run q_learning_agent.py to train the agent first.")

    print("--- Learned Q-Table ---")
    print("State is (NS_Queue, EW_Queue, Current_Green_Phase)")
    print("Q-Values are [Q for Action 'Stay', Q for Action 'Switch']\n")
    
    # Sort the table items for cleaner viewing
    sorted_q_table = sorted(q_table.items(), key=lambda item: item[0])
    
    for state, q_values in sorted_q_table:
        ns_level, ew_level, phase_is_ns = state
        
        # Make the state human-readable
        readable_state = (
            f"NS:{QUEUE_LEVELS[ns_level]}",
            f"EW:{QUEUE_LEVELS[ew_level]}",
            f"Phase:{PHASE_MEANING[phase_is_ns]}"
        )
        
        # Format Q-values to 2 decimal places
        formatted_q_values = [f"{q:.2f}" for q in q_values]
        
        print(f"State: {readable_state} -> Q-Values: {formatted_q_values}")

    print(f"\nTotal states learned: {len(q_table)}")
