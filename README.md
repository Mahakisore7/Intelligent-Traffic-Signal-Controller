# 🚦 Intelligent Traffic Signal Controller

This project simulates and evaluates various traffic signal control algorithms at a four-way intersection using the **SUMO (Simulation of Urban MObility)** package. The goal is to compare the performance of different strategies, from a traditional fixed-time controller to an advanced machine learning-based system like Q-learning.

---

## 🚀 Control Strategies Implemented

This repository contains three distinct traffic control strategies that can be simulated and compared.

### 1. Fixed-Time Controller (Baseline)

This is the most basic strategy, operating on a pre-defined, fixed cycle without any feedback from the traffic conditions.

- **How it works**: The traffic light timing is hard-coded directly into the `intersection.net.xml` file. The cycle lengths and phases are static and repeat continuously, regardless of how many vehicles are waiting.
- **How to run**:
```bash
python run_fixed_time.py
```

### 2. Longest-Queue-First (LQF) Controller

A dynamic, rule-based controller that adapts to changing traffic conditions by prioritizing the most congested direction.

- **How it works**: The `lqf_control.py` script uses the SUMO TraCI API to monitor the number of vehicles waiting in each incoming lane. At the end of each green phase, it identifies the direction with the longest queue and gives it the next green light.
- **How to run**:
```bash
python lqf_control.py
```

### 3. Q-Learning Reinforcement Learning Agent

A machine learning approach where an agent learns the optimal traffic light control policy through trial and error.

#### a) Training the Agent
- **How it works**: The `multi_episode_q_learning.py` script runs multiple simulation episodes. In each episode, the agent makes decisions and updates its **Q-table** based on the reward received, gradually learning the best action for a given traffic state. The learned Q-table is stored in `q_table.pkl`.
- **How to run**:
```bash
python multi_episode_q_learning.py
```

#### b) Running the Trained Agent
- **How it works**: The `run_trained_agent.py` script loads `q_table.pkl` and uses the learned policy to control the intersection without exploration, always choosing the highest-reward action.
- **How to run**:
```bash
python run_trained_agent.py
```

---

## 🛠️ Simulation Environment

- **Network**: Four-way intersection with three lanes per approach, defined in `intersection.net.xml`.
- **Traffic Flow**: Vehicle routes are defined in `routes.rou.xml`. Adjust this file to simulate different traffic loads.
- **Simulation Time**: Each run lasts for 1800 seconds (30 minutes), set in `intersection.sumocfg`.

---

## ✅ Prerequisites

- **SUMO** – Install from the [official website](https://sumo.dlr.de/docs/Downloads.php).
- **SUMO_HOME Environment Variable** – Point it to your SUMO installation directory.
- **Python 3** – Install from the [official Python site](https://www.python.org/downloads/).
- **Python Libraries**:
```bash
pip install numpy
```
Other dependencies (`traci`, `sumolib`, etc.) come with SUMO or Python.

---

## ⚙️ How to Run the Simulations

1. Clone this repository.
2. Navigate to the project directory in terminal.
3. Use:
   - **Fixed-Time**:
     ```bash
     cd fixed_time
     python run_fixed_time.py
     ```
   - **Longest-Queue-First**:
     ```bash
     cd lqf
     python lqf_control.py
     ```
   - **Q-Learning**:
     ```bash
     cd q-learning
     python multi_episode_q_learning.py
     python run_trained_agent.py
     ```

---

## 📂 Project Structure

```
.
├── fixed_time/
│   ├── additional.tllogic.xml
│   ├── connections.conn.xml
│   ├── edges.edg.xml
│   ├── intersection.net.xml
│   ├── intersection.sumocfg
│   ├── nodes.nod.xml
│   ├── routes.rou.xml
│   ├── run_fixed_time.py
│   └── types.type.xml
│
├── lqf/
│   ├── connections.conn.xml
│   ├── edges.edg.xml
│   ├── intersection.net.xml
│   ├── intersection.sumocfg
│   ├── lqf_control.py
│   ├── nodes.nod.xml
│   ├── routes.rou.xml
│   └── types.type.xml
│
├── q-learning/
│   ├── intersection.net.xml
│   ├── intersection.sumocfg
│   ├── multi_episode_q_learning.py
│   ├── q_table.pkl
│   ├── routes.rou.xml
│   ├── run_trained_agent.py
│   ├── simulation_metrics.png
│   ├── trace.xml
│   └── intersection.sumocfg
│
└── README.md
```

---

## 📊 Evaluation

The dynamic controllers (`lqf_control.py` and `run_trained_agent.py`) print performance metrics like **average wait time**, **max wait time**, and **total wait time** after each run. These allow for quantitative comparison of strategies.
