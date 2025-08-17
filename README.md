# 🚦 Intelligent Traffic Signal Controller

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
cd lqf
python lqf_control.py
```

---

### 3. Q-Learning Reinforcement Learning Agent

**a) Training the Agent**  
- **How it works:** `multi_episode_q_learning.py` runs multiple episodes, updating the Q-table (`q_table.pkl`).  
- **Run:**
```bash
cd q-learning
python multi_episode_q_learning.py
```

**b) Running the Trained Agent**  
- **How it works:** `run_trained_agent.py` loads the trained Q-table and applies the learned policy.  
- **Run:**
```bash
python run_trained_agent.py
```

---

### 4. Deep Reinforcement Learning (DQN & DDPG)

Two advanced DRL algorithms, **Deep Q-Network (DQN)** and **Deep Deterministic Policy Gradient (DDPG)**, are implemented for more complex state-action spaces.

- **How it works:**
  - `dqn_controller.py` – DQN with a neural network to approximate the Q-function  
  - `ddpg_controller.py` – DDPG for continuous action space control  
  - Both interact with SUMO through TraCI, learning policies that reduce waiting times  

- **Run:**
```bash
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
