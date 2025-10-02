# controllers.py (Corrected for 4-phase operation)
import traci
import numpy as np

class FixedTimeController:
    def __init__(self, ts_id, green_duration=15, yellow_duration=4):
        self.ts_id = ts_id
        # Define the new 8 phases (4 green, 4 yellow)
        self.phases = [
            "GGGggrrrrrrrrrrrrrrr",  # 0: N Green
            "yyyyyrrrrrrrrrrrrrrr",  # 1: N Yellow
            "rrrrrGGGggrrrrrrrrrr",  # 2: E Green
            "rrrrryyyyyrrrrrrrrrr",  # 3: E Yellow
            "rrrrrrrrrrGGGggrrrrr",  # 4: S Green
            "rrrrrrrrrryyyyyrrrrr",  # 5: S Yellow
            "rrrrrrrrrrrrrrrGGGgg",  # 6: W Green
            "rrrrrrrrrrrrrrryyyyy",  # 7: W Yellow
        ]
        self.phase_durations = [green_duration, yellow_duration] * 4
        self.current_phase_index = 0
        self.time_in_current_phase = 0
        traci.trafficlight.setRedYellowGreenState(self.ts_id, self.phases[0])

    def update(self):
        self.time_in_current_phase += 1
        if self.time_in_current_phase >= self.phase_durations[self.current_phase_index]:
            self.time_in_current_phase = 0
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phases)
            traci.trafficlight.setRedYellowGreenState(self.ts_id, self.phases[self.current_phase_index])

class LongestQueueFirstController:
    def __init__(self, ts_id, min_green_time=10, yellow_duration=4):
        self.ts_id = ts_id
        self.min_green_time = min_green_time
        self.yellow_duration = yellow_duration
        self.time_in_current_phase = 0
        self.current_phase_is_green = True
        self.current_green_phase_index = 0 # 0:N, 1:E, 2:S, 3:W
        
        # Lanes for each of the 4 approaches
        self.incoming_lanes = {
            0: ['N2C_0', 'N2C_1'], # North
            1: ['E2C_0', 'E2C_1'], # East
            2: ['S2C_0', 'S2C_1'], # South
            3: ['W2C_0', 'W2C_1']  # West
        }
        # PHASES: 4 Green, 4 Yellow
        self.green_phases = [
            "GGGggrrrrrrrrrrrrrrr", "rrrrrGGGggrrrrrrrrrr", "rrrrrrrrrrGGGggrrrrr", "rrrrrrrrrrrrrrrGGGgg"
        ]
        self.yellow_phases = [
            "yyyyyrrrrrrrrrrrrrrr", "rrrrryyyyyrrrrrrrrrr", "rrrrrrrrrryyyyyrrrrr", "rrrrrrrrrrrrrrryyyyy"
        ]
        traci.trafficlight.setRedYellowGreenState(self.ts_id, self.green_phases[0])

    def get_queue_lengths(self):
        return [sum(traci.lane.getLastStepHaltingNumber(lane) for lane in self.incoming_lanes[i]) for i in range(4)]

    def update(self):
        self.time_in_current_phase += 1

        if self.current_phase_is_green and self.time_in_current_phase >= self.min_green_time:
            queues = self.get_queue_lengths()
            longest_queue_index = np.argmax(queues)
            
            if longest_queue_index != self.current_green_phase_index and queues[longest_queue_index] > 0:
                self.current_phase_is_green = False
                self.time_in_current_phase = 0
                traci.trafficlight.setRedYellowGreenState(self.ts_id, self.yellow_phases[self.current_green_phase_index])
        
        elif not self.current_phase_is_green and self.time_in_current_phase >= self.yellow_duration:
            self.current_phase_is_green = True
            self.time_in_current_phase = 0
            self.current_green_phase_index = np.argmax(self.get_queue_lengths())
            traci.trafficlight.setRedYellowGreenState(self.ts_id, self.green_phases[self.current_green_phase_index])