# test_ambulance_definitive.py
# This script runs two controlled simulations to definitively test the ambulance preemption system.
# It ensures the ambulance faces a red light in the non-preemption scenario.

import traci
import sys
import os
import xml.etree.ElementTree as ET

# --- SUMO SETUP ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# --- SIMULATION PARAMETERS ---
AMBULANCE_DEPART_TIME = 100
HEAVY_TRAFFIC_END_TIME = 200 # Ensure heavy traffic when ambulance arrives

# --- HELPER FUNCTIONS (COPIED FROM OTHER SCRIPTS) ---
TLS_ID = "J1"
NS_GREEN_PHASE, NS_YELLOW_PHASE, EW_GREEN_PHASE, EW_YELLOW_PHASE = 0, 1, 2, 3
NS_LANES = ["N_in_0", "N_in_1", "N_in_2", "S_in_0", "S_in_1", "S_in_2"]
EW_LANES = ["E_in_0", "E_in_1", "E_in_2", "W_in_0", "W_in_1", "W_in_2"]

def is_ambulance_approaching():
    for lane in NS_LANES + EW_LANES:
        for veh_id in traci.lane.getLastStepVehicleIDs(lane):
            if traci.vehicle.getTypeID(veh_id) == 'ambulance':
                return 'NS' if lane in NS_LANES else 'EW'
    return None

def analyze_tripinfo(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for tripinfo in root.findall('tripinfo'):
        if tripinfo.get('id') == 'ambulance_1':
            return float(tripinfo.get('duration')), float(tripinfo.get('waitingTime'))
    return None, None

# --- SIMULATION RUNNERS ---
def run_lqf_simulation(output_filename):
    """Runs a standard LQF simulation."""
    traci.start(["sumo", "-c", "cross.sumocfg", "--tripinfo-output", output_filename])
    green_time_counter = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        green_time_counter += 1
        current_phase = traci.trafficlight.getPhase(TLS_ID)
        if green_time_counter > 10:
             ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
             ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)
             if current_phase == NS_GREEN_PHASE and ew_queue > ns_queue:
                 traci.trafficlight.setPhase(TLS_ID, NS_YELLOW_PHASE)
                 for _ in range(4): traci.simulationStep()
                 traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
                 green_time_counter = 0
             elif current_phase == EW_GREEN_PHASE and ns_queue > ew_queue:
                 traci.trafficlight.setPhase(TLS_ID, EW_YELLOW_PHASE)
                 for _ in range(4): traci.simulationStep()
                 traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
                 green_time_counter = 0
    traci.close()

def run_preemption_simulation(output_filename):
    """Runs the ambulance preemption simulation."""
    traci.start(["sumo", "-c", "cross.sumocfg", "--tripinfo-output", output_filename])
    green_time_counter = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        green_time_counter += 1
        ambulance_dir = is_ambulance_approaching()
        current_phase = traci.trafficlight.getPhase(TLS_ID)
        if ambulance_dir:
            if ambulance_dir == 'NS' and current_phase != NS_GREEN_PHASE:
                traci.trafficlight.setPhase(TLS_ID, EW_YELLOW_PHASE)
                for _ in range(4): traci.simulationStep()
                traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
                green_time_counter = 0
        elif green_time_counter > 10:
             ns_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in NS_LANES)
             ew_queue = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in EW_LANES)
             if current_phase == NS_GREEN_PHASE and ew_queue > ns_queue:
                 traci.trafficlight.setPhase(TLS_ID, NS_YELLOW_PHASE)
                 for _ in range(4): traci.simulationStep()
                 traci.trafficlight.setPhase(TLS_ID, EW_GREEN_PHASE)
                 green_time_counter = 0
             elif current_phase == EW_GREEN_PHASE and ns_queue > ew_queue:
                 traci.trafficlight.setPhase(TLS_ID, EW_YELLOW_PHASE)
                 for _ in range(4): traci.simulationStep()
                 traci.trafficlight.setPhase(TLS_ID, NS_GREEN_PHASE)
                 green_time_counter = 0
    traci.close()

def create_test_route_file():
    """Creates a specific route file for this test."""
    route_content = f"""<routes>
    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5" maxSpeed="15" />
    <vType id="ambulance" accel="3.5" decel="5.0" sigma="0.2" length="6" maxSpeed="25" color="blue" vClass="emergency" />

    <!-- Heavy, continuous East-West traffic to force a green light -->
    <flow id="jam_flow_EW" type="car" begin="0" end="{HEAVY_TRAFFIC_END_TIME}" vehsPerHour="1000" from="E_in" to="W_out" />
    <flow id="jam_flow_WE" type="car" begin="0" end="{HEAVY_TRAFFIC_END_TIME}" vehsPerHour="1000" from="W_in" to="E_out" />

    <!-- A single ambulance that will arrive during the traffic jam -->
    <vehicle id="ambulance_1" type="ambulance" depart="{AMBULANCE_DEPART_TIME}" departLane="0">
        <route edges="N_in S_out"/>
    </vehicle>
</routes>"""
    with open("cross_ambulance_test.rou.xml", "w") as f:
        f.write(route_content)

# --- MAIN ANALYSIS SCRIPT ---
if __name__ == "__main__":
    print("--- Definitive Ambulance Preemption Test ---")
    
    # 1. Create the special route file for this test
    create_test_route_file()
    print("Created 'cross_ambulance_test.rou.xml' for this test.")

    # 2. Update the .sumocfg to use this new route file
    # A simple way is to manually edit cross.sumocfg to point to this new file.
    # For this script, we'll assume the user does this.
    print("\nACTION REQUIRED: Please edit 'cross.sumocfg' and change the route-files value to 'cross_ambulance_test.rou.xml'")
    input("Press Enter to continue after you have edited the file...")

    # 3. Run simulation WITHOUT preemption
    print("\nRunning simulation WITHOUT preemption (standard LQF)...")
    run_lqf_simulation("tripinfo_no_preemption.xml")
    
    # 4. Run simulation WITH preemption
    print("Running simulation WITH preemption...")
    run_preemption_simulation("tripinfo_with_preemption.xml")
    
    # 5. Analyze results
    print("\n--- ANALYSIS COMPLETE ---")
    travel_no, wait_no = analyze_tripinfo('tripinfo_no_preemption.xml')
    travel_with, wait_with = analyze_tripinfo('tripinfo_with_preemption.xml')
    
    print("\nAmbulance Performance:")
    print(f"  - Travel Time WITHOUT Preemption: {travel_no:.2f}s (Wait Time: {wait_no:.2f}s)")
    print(f"  - Travel Time WITH Preemption:    {travel_with:.2f}s (Wait Time: {wait_with:.2f}s)")

    improvement = travel_no - travel_with
    print(f"\nConclusion: The preemption system reduced the ambulance's travel time by {improvement:.2f} seconds.")
