# 🚦 Intelligent Traffic Signal Controller

## 📌 Overview

This project leverages [**SUMO (Simulation of Urban MObility)**](https://www.eclipse.org/sumo/) to simulate a **four-way intersection** and evaluate different traffic light control algorithms.  
The main objective is to compare **traditional controllers** with **Reinforcement Learning (RL)** agents to identify the most effective strategy for **reducing vehicle waiting times**.  

The system also includes an **emergency vehicle (ambulance) preemption mechanism**, giving ambulances priority passage.
This project simulates and evaluates various traffic signal control algorithms at a four-way intersection using the **SUMO (Simulation of Urban MObility)** package. The goal is to compare the performance of different strategies, from a traditional fixed-time controller to advanced machine learning-based systems like Q-learning, DQN, and DDPG.

---

## ✅ Prerequisites

Before running the project, make sure you have the following installed:

- **SUMO** – [Install here](https://www.eclipse.org/sumo/)
- **SUMO_HOME Environment Variable** – Point it to your SUMO installation directory
- **Python 3** – [Download here](https://www.python.org/)

---

## ⚙️ Setup (with Virtual Environment)

It’s recommended to run the project inside a Python virtual environment.

1. **Clone the Repository**
```bash
git clone <your-repo-link>
cd Intelligent-Traffic-Signal-Controller
```

2. **Create and Activate Virtual Environment**
```bash
# Create venv
python -m venv venv  

# Activate venv
# On Windows
venv\Scripts\activate  
# On Linux/Mac
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Navigate to a Strategy Folder** (e.g., `fixed_time`, `lqf`, `q-learning`, or `dqn_ddpg`).

5. **Run the desired script** (see details below).

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

## 🚀 Control Strategies Implemented

This repository contains **four distinct traffic control strategies** that can be simulated and compared.

---

### 1. Fixed-Time Controller (Baseline)
A pre-defined, fixed cycle without feedback from traffic conditions.

- **How it works:** Traffic light timing is hard-coded into `intersection.net.xml`. Cycle lengths and phases are static and repeat continuously.  
- **Run:**
```bash
cd fixed_time
python run_fixed_time.py
```

---

### 2. Longest-Queue-First (LQF) Controller
A dynamic, rule-based controller that prioritizes the most congested direction.

- **How it works:** `lqf_control.py` uses the SUMO TraCI API to monitor waiting vehicles. At each cycle, it assigns green light to the lane with the longest queue.  
- **Run:**
```bash
python runner_emergency.py --model lqf --steps 1000 --gui
cd lqf
python lqf_control.py
```

---

---

### 2. Train the Q-Learning Agent

#### 🔹 Step 1: Train over multiple runs
Run **without GUI** for faster training. The agent will update `q_table_directional.csv` after each run.  

**a) Training the Agent**  
- **How it works:** `multi_episode_q_learning.py` runs multiple episodes, updating the Q-table (`q_table.pkl`).  
- **Run:**
```bash
python runner_emergency.py --model qlearn --steps 3600
cd q-learning
python multi_episode_q_learning.py
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

**b) Running the Trained Agent**  
- **How it works:** `run_trained_agent.py` loads the trained Q-table and applies the learned policy.  
- **Run:**
```bash
python runner_emergency.py --model qlearn --steps 3600 --gui
```

---

### 3. Plot Results

After simulations, run:

### 4. Deep Reinforcement Learning (DQN & DDPG)

Two advanced DRL algorithms, **Deep Q-Network (DQN)** and **Deep Deterministic Policy Gradient (DDPG)**, are implemented for more complex state-action spaces.

- **How it works:**
  - `dqn_controller.py` – DQN with a neural network to approximate the Q-function  
  - `ddpg_controller.py` – DDPG for continuous action space control  
  - Both interact with SUMO through TraCI, learning policies that reduce waiting times  

- **Run:**
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


cd dqn_ddpg
python dqn_controller.py      # Run DQN Agent
python ddpg_controller.py     # Run DDPG Agent
```

---

## 📂 Project Structure

```
.
├── fixed_time/
│   ├── run_fixed_time.py
│   ├── intersection.*.xml
│   └── ...
│
├── lqf/
│   ├── lqf_control.py
│   ├── intersection.*.xml
│   └── ...
│
├── q-learning/
│   ├── multi_episode_q_learning.py
│   ├── run_trained_agent.py
│   ├── q_table.pkl
│   └── ...
│
├── dqn_ddpg/
│   ├── dqn_controller.py
│   ├── ddpg_controller.py
│   ├── intersection.*.xml
│   └── ...
│
├── requirements.txt
└── README.md
```

---

## 📊 Evaluation

Each controller prints performance metrics such as:
- Average wait time
- Maximum wait time
- Total wait time

Additionally, DRL controllers can log training rewards and performance graphs for deeper analysis.

---

✨ With this setup, you can **compare classical, rule-based, and reinforcement learning strategies** for intelligent traffic signal control!
