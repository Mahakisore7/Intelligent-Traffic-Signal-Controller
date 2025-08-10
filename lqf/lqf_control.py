import traci
import sys
import os
import numpy as np

# ---------------------- CONFIG ----------------------
SUMO_GUI = True                       # set False to run headless (sumo instead of sumo-gui)
SUMOCFG = "intersection.sumocfg"      # your config file
JUNCTION_ID = "center"

GREEN_TIME = 20.0     # seconds green per chosen direction
YELLOW_TIME = 3.0     # seconds yellow
ALL_RED = 1.0         # seconds all red between phases

MAX_SIM_TIME = 54     # manual cutoff: max simulation time in seconds

# mapping directions -> incoming lanes (must match your net)
DIRECTION_LANES = {
    "north": ["N2C_0", "N2C_1", "N2C_2"],
    "east":  ["E2C_0", "E2C_1", "E2C_2"],
    "south": ["S2C_0", "S2C_1", "S2C_2"],
    "west":  ["W2C_0", "W2C_1", "W2C_2"]
}

# exact traffic-light state strings (12 chars) for your net's link order:
STATE_STRINGS = {
    "north_green": "GGGrrrrrrrrr",   # north lanes green (first 3)
    "north_yellow":"yyyrrrrrrrrr",
    "east_green":  "rrrGGGrrrrrr",   # east lanes (3-5) green
    "east_yellow": "rrryyyrrrrrr",
    "south_green": "rrrrrrGGGrrr",   # south lanes (6-8)
    "south_yellow":"rrrrrryyyrrr",
    "west_green":  "rrrrrrrrrGGG",   # west lanes (9-11)
    "west_yellow": "rrrrrrrrryyy",
    "all_red":     "rrrrrrrrrrrr"
}

# Metrics dictionary to store values each step
metrics = {
    "steps": [],
    "total_vehicles": [],
    "avg_wait_time": [],
    "max_wait_time": [],
    "avg_queue_length": [],
    "max_queue_length": [],
    "cumulative_wait_time": 0.0,
}

def sum_queues_for_direction(direction):
    lanes = DIRECTION_LANES[direction]
    q = 0
    for ln in lanes:
        try:
            q += traci.lane.getLastStepVehicleNumber(ln)
        except traci.exceptions.TraciException:
            print(f"[WARN] lane '{ln}' not found in network. Check names.")
    return q

def choose_longest_queue_direction():
    best_dir = None
    best_q = -1
    for d in DIRECTION_LANES:
        q = sum_queues_for_direction(d)
        if q > best_q:
            best_q = q
            best_dir = d
    return best_dir, best_q

def set_state_for_direction(direction, color="green"):
    if direction == "north":
        key = "north_green" if color == "green" else "north_yellow"
    elif direction == "east":
        key = "east_green" if color == "green" else "east_yellow"
    elif direction == "south":
        key = "south_green" if color == "green" else "south_yellow"
    elif direction == "west":
        key = "west_green" if color == "green" else "west_yellow"
    else:
        key = "all_red"
    state = STATE_STRINGS.get(key, STATE_STRINGS["all_red"])
    traci.trafficlight.setRedYellowGreenState(JUNCTION_ID, state)
    print(f"[{traci.simulation.getTime():.1f}s] SET {direction.upper()} -> {color.upper()} (state='{state}')")

def collect_metrics(step):
    metrics["steps"].append(step)
    metrics["total_vehicles"].append(traci.vehicle.getIDCount())

    all_lanes = []
    for lanes in DIRECTION_LANES.values():
        all_lanes.extend(lanes)
    
    wait_times = []
    queue_lengths = []
    for lane in all_lanes:
        try:
            wait_times.append(traci.lane.getWaitingTime(lane))
            queue_lengths.append(traci.lane.getLastStepHaltingNumber(lane))
        except traci.exceptions.TraciException:
            pass

    if wait_times:
        max_wait = max(wait_times)
        avg_wait = np.mean(wait_times)
        metrics["max_wait_time"].append(max_wait)
        metrics["avg_wait_time"].append(avg_wait)
        metrics["cumulative_wait_time"] += sum(wait_times)
    else:
        metrics["max_wait_time"].append(0)
        metrics["avg_wait_time"].append(0)

    if queue_lengths:
        metrics["max_queue_length"].append(max(queue_lengths))
        metrics["avg_queue_length"].append(np.mean(queue_lengths))
    else:
        metrics["max_queue_length"].append(0)
        metrics["avg_queue_length"].append(0)

def run():
    next_switch_time = 0.0
    yellow_time_scheduled = None
    all_red_time_scheduled = None
    current_direction = None

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        t = traci.simulation.getTime()

        if t >= MAX_SIM_TIME:
            print(f"Reached max simulation time {MAX_SIM_TIME}s. Ending simulation.")
            break

        if t >= next_switch_time:
            chosen_dir, q = choose_longest_queue_direction()
            if chosen_dir is None:
                chosen_dir = "north"
            set_state_for_direction(chosen_dir, color="green")
            current_direction = chosen_dir
            yellow_time_scheduled = t + GREEN_TIME
            all_red_time_scheduled = yellow_time_scheduled + YELLOW_TIME
            next_switch_time = all_red_time_scheduled + ALL_RED
            print(f"-> Chosen {chosen_dir} (queue={q}), green until {yellow_time_scheduled:.1f}s")
        else:
            if yellow_time_scheduled is not None and t >= yellow_time_scheduled and t < all_red_time_scheduled:
                set_state_for_direction(current_direction, color="yellow")
                yellow_time_scheduled = None
            if all_red_time_scheduled is not None and t >= all_red_time_scheduled:
                traci.trafficlight.setRedYellowGreenState(JUNCTION_ID, STATE_STRINGS["all_red"])
                print(f"[{t:.1f}s] ALL-RED")
                all_red_time_scheduled = None

        traci.simulationStep()
        collect_metrics(step)
        step += 1

    traci.close()

    # Print final metrics summary
    print("\n--- Simulation Metrics Summary ---")
    max_wait = max(metrics["max_wait_time"]) if metrics["max_wait_time"] else 0
    avg_wait = np.mean(metrics["avg_wait_time"]) if metrics["avg_wait_time"] else 0
    total_cum_wait = metrics["cumulative_wait_time"]
    max_queue = max(metrics["max_queue_length"]) if metrics["max_queue_length"] else 0

    print(f"Max Waiting Time observed: {max_wait:.2f} seconds")
    print(f"Average Waiting Time over simulation: {avg_wait:.2f} seconds")
    print(f"Total Cumulative Waiting Time: {total_cum_wait:.2f} seconds")
    print(f"Max Queue Length observed: {max_queue}")
    print("Simulation finished.")

if __name__ == "__main__":
    sumo_binary = "sumo-gui" if SUMO_GUI else "sumo"
    if "SUMO_HOME" not in os.environ:
        print("Warning: SUMO_HOME not set. Make sure 'sumo-gui' is in PATH or set SUMO_HOME.")
    sumo_cmd = [sumo_binary, "-c", SUMOCFG]

    print("Starting TraCI with:", " ".join(sumo_cmd))
    traci.start(sumo_cmd)
    try:
        run()
    except Exception as e:
        print("Controller error:", e)
        traci.close()
        sys.exit(1)
