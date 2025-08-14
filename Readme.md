# Intelligent Traffic Signal Controller with SUMO

This project demonstrates the development and comparison of an intelligent, adaptive traffic signal controller against a standard fixed-time controller using the **SUMO (Simulation of Urban MObility)** environment. The goal is to show a quantifiable reduction in traffic congestion and vehicle waiting times by using a simple, rule-based intelligent agent.



## 📖 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Technologies Used](#-technologies-used)
- [Project Structure](#-project-structure)
- [Setup and Installation](#-setup-and-installation)
- [How to Run](#-how-to-run)
- [Results](#-results)
- [Future Improvements](#-future-improvements)


---

## 🚩 Project Overview

Traditional traffic lights operate on fixed timers, which are often inefficient as they don't adapt to real-time traffic conditions. This leads to unnecessary waiting times and increased congestion, especially during fluctuating traffic flow.

This project addresses this problem by implementing a **"Longest Queue First" (LQF)** adaptive controller. This smart agent monitors the number of waiting vehicles on each approach and gives priority (a green light) to the direction with the most significant traffic queue. Its performance is then scientifically compared to a traditional fixed-time controller using the same traffic scenario to highlight the benefits of adaptive control.

---

## ✨ Key Features

- **Realistic Traffic Simulation:** A four-way, multi-lane intersection model built in SUMO.
- **Two Controller Models:**
    1.  **Fixed-Timer Controller:** A baseline "dumb" controller that follows a rigid, pre-set cycle.
    2.  **Longest Queue First (LQF) Agent:** A smart, heuristic-based controller that adapts to live traffic data.
- **Performance Data Collection:** Automatically generates trip summary reports for each simulation run.
- **Quantitative Analysis:** A Python script that parses simulation outputs to calculate and compare key performance metrics (e.g., average vehicle waiting time).
- **Data Visualization:** Generates a bar chart using Matplotlib for a clear, visual comparison of the two controllers.

---

## 🛠️ Technologies Used

- **Simulation:** [SUMO (Simulation of Urban MObility)](https://www.eclipse.org/sumo/)
- **Programming Language:** [Python 3](https://www.python.org/)
- **Python Libraries:**
    - `Traci` (for interfacing with SUMO)
    - `Matplotlib` (for data visualization)

---

## 📁 Project Structure

```
/
├── agent.py               # Main script for the Longest Queue First (LQF) agent
├── fixed_timer.py         # Script to run the fixed-time simulation
├── analysis.py            # Script to analyze results and generate the plot
├── cross.nod.xml          # Defines the intersection nodes
├── cross.edg.xml          # Defines the roads (edges)
├── cross.rou.xml          # Defines the vehicle routes and traffic flow
├── cross.add.xml          # Defines the fixed-timer traffic light logic
├── cross.sumocfg          # Main SUMO configuration file
├── requirements.txt       # Lists the Python dependencies
└── README.md              # This file
```

---

## ⚙️ Setup and Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
    cd your-repository-name
    ```

2.  **Install SUMO**
    - Download and install SUMO from the [official website](https://www.eclipse.org/sumo/docs/Downloads.html).
    - Make sure to add SUMO to your system's PATH environment variable, or create a `SUMO_HOME` variable pointing to the installation directory.

3.  **Set Up a Python Environment**
    - It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4.  **Create `requirements.txt`**
    - Create a file named `requirements.txt` and add the following lines:
    ```
    matplotlib
    traci
    ```

5.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 How to Run

To get the final comparison, you must run three scripts in order.

### Step 1: Run the Fixed-Timer (Baseline) Simulation
- **Ensure the fixed-timer is enabled in `cross.sumocfg`:** The line `<additional-files value="cross.add.xml"/>` should be active (not commented out).
- **Run the script:**
  ```bash
  python fixed_timer.py
  ```
- Let the simulation run to completion. This will generate a `tripinfo_fixed.xml` file.

### Step 2: Run the Smart Agent (LQF) Simulation
- **Disable the fixed-timer in `cross.sumocfg`:** Comment out the line like this: ``.
- **Run the script:**
  ```bash
  python agent.py
  ```
- Let the simulation run to completion. This will generate a `tripinfo_lqf.xml` file.

### Step 3: Analyze the Results
- Once both simulation reports have been generated, run the analysis script:
  ```bash
  python analysis.py
  ```
- This will print the numerical comparison to your terminal and display a pop-up window with the performance bar chart.

---

## 📊 Results

The analysis script compares the average vehicle waiting time between the two controllers. As expected, the **Longest Queue First (LQF) agent significantly outperforms the Fixed-Timer**, drastically reducing the average time cars spend idle at the intersection.

The generated bar chart provides a clear visual confirmation of this improvement, demonstrating the value of adaptive traffic control systems.

---

## 💡 Future Improvements

This project serves as a strong foundation. Future enhancements could include:
- **Reinforcement Learning:** Implementing a more advanced Q-Learning or Deep Q-Network (DQN) agent that can learn optimal policies beyond simple heuristics.
- **Complex Scenarios:** Expanding the simulation to a grid of multiple intersections to see how local policies affect the entire network.
- **Multi-modal Traffic:** Adding pedestrians, cyclists, and public transport to the simulation.
- **3D Visualization:** Integrating the SUMO simulation with a game engine like Unity or Unreal Engine for a high-fidelity 3D visualization of the traffic flow.

---

