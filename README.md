# 🚦 Intelligent Traffic Signal Controller

## 📌 Overview

This project leverages [**SUMO (Simulation of Urban MObility)**](https://www.eclipse.org/sumo/) to simulate a **four-way intersection** and evaluate different traffic light control algorithms.  
The main objective is to compare **traditional controllers** with **Reinforcement Learning (RL)** agents to identify the most effective strategy for **reducing vehicle waiting times**.  

The system also includes an **emergency vehicle (ambulance) preemption mechanism**, giving ambulances priority passage.

---

## ✨ Features

- **Four Control Models**
  - 🕑 **Fixed-Time** → Rigid, non-adaptive schedule  
  - 🚦 **Longest-Queue-First (LQF)** → Prioritizes the most congested direction  
  - 🤖 **Q-Learning** → Basic RL agent using a Q-table  
  - 🧠 **Deep Q-Network (DQN)** → Advanced RL agent using a neural network  

- **Emergency Vehicle Preemption**  
  Automatically detects an approaching ambulance and overrides the active controller to give a green signal.  

- **Persistent RL Training**  
  The Q-learning agent saves its **Q-table** to file, allowing it to **learn across runs**.  

- **Performance Metrics**  
  The key metric is **average waiting time per vehicle**, computed using SUMO’s trip info output.  

- **Visualization**  
  Built-in plotting script to compare results of all models.  

---

## 📂 File Structure

```
.
├── results/                  # Simulation outputs
│   ├── results_*.npy         # Saved waiting time data
│   └── tripinfo.xml          # Vehicle trip details
├── controllers.py            # Fixed-Time & LQF controllers
├── dqn_agent.py              # Q-Learning & DQN agents
├── intersection.nod.xml      # Nodes (junctions)
├── intersection.edg.xml      # Edges (roads)
├── intersection.net.xml      # Compiled SUMO network
├── intersection.rou.xml      # Vehicle routes & traffic flow
├── intersection.sumocfg      # SUMO main config file
├── plot_results.py           # Script to plot comparisons
├── q_table_directional.csv   # Saved Q-table (Q-learning)
├── runner_emergency.py       # Main simulation (4-phase + emergency preemption)
├── runner_original.py        # Original 2-phase simulation
└── README.md                 # This file
```

---

## ⚙️ Prerequisites

1. **SUMO** → Install and set the `SUMO_HOME` environment variable  
2. **Python 3** → All scripts use Python 3  
3. **Dependencies**:  
   ```bash
   pip install numpy tensorflow matplotlib
   ```

---

## ▶️ How to Run

### 1. Run a Single Simulation
Run the simulation with your desired controller. Add `--gui` for a visual interface.  

```bash
python runner_emergency.py --model lqf --steps 1000 --gui
```

---

### 2. Train the Q-Learning Agent

#### 🔹 Step 1: Train over multiple runs
Run **without GUI** for faster training. The agent will update `q_table_directional.csv` after each run.  

```bash
python runner_emergency.py --model qlearn --steps 3600
```

Repeat this **20–50 times** for good performance.

#### 🔹 Step 2: Test the trained agent
- Open `dqn_agent.py`  
- In `load_q_table`, change:  
  ```python
  self.epsilon = 0.1
  ```  
  to:  
  ```python
  self.epsilon = 0.0
  ```
- Run with GUI to visualize performance:  

```bash
python runner_emergency.py --model qlearn --steps 3600 --gui
```

---

### 3. Plot Results

After simulations, run:

```bash
python plot_results.py
```

This will generate a **graph comparing performance** across models.

---

## 📊 Example Output

- **Average waiting time per vehicle** across all models  
- **Graphs** showing improvement of RL agents over fixed methods  

---

## 🏗️ Future Work

- Optimize **DQN hyperparameters** for better convergence  
- Extend to **grid-based intersections**  
- Incorporate **multi-agent reinforcement learning** for city-scale traffic management  

---


