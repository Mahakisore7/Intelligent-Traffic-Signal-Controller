# 🚦 Intelligent Traffic Signal Controller using SUMO and Reinforcement Learning

## 🧠 Overview
This project explores **intelligent traffic management** through simulation, reinforcement learning, and data analysis.  
It demonstrates the design, implementation, and performance comparison of multiple traffic signal control strategies — from a simple **Fixed-Timer Controller** to an advanced **Deep Q-Network (DQN)** agent.  

All simulations are conducted using **SUMO (Simulation of Urban MObility)**, and results show that the **DQN agent** reduces average vehicle waiting times by over **71%** compared to traditional systems.

---

## 📑 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Features](#-key-features)
3. [The Controllers](#-the-controllers)
4. [Technologies Used](#-technologies-used)
5. [Project Structure](#-project-structure)
6. [Setup and Installation](#-setup-and-installation)
7. [How to Run the Project](#-how-to-run-the-project-complete-workflow)
8. [Results and Discussion](#-results-and-discussion)
9. [Future Improvements](#-future-improvements)
10. [Credits](#-credits)

---

## 🚩 Project Overview
Traditional traffic lights rely on **fixed-time cycles**, which cannot adapt to real-time traffic conditions.  
This results in unnecessary delays and congestion.  

This project addresses this issue by developing and evaluating **four intelligent controllers**:
1. **Fixed-Timer Controller** — baseline.
2. **Longest Queue First (LQF) Agent** — heuristic-based.
3. **Q-Learning Agent** — reinforcement learning (tabular).
4. **DQN Agent** — deep reinforcement learning (neural network-based).

A separate module demonstrates **emergency vehicle preemption**, where an ambulance is given automatic priority using intelligent overrides.

---

## ✨ Key Features

- **Realistic Traffic Simulation**  
  A detailed four-way intersection modeled in SUMO, including multi-lane and turning traffic.

- **Four Distinct Control Strategies**  
  From static to fully adaptive — allows direct performance comparison.

- **Reinforcement Learning Implementation**  
  Includes training and evaluation for both Q-Learning and DQN agents using TensorFlow/Keras.

- **Emergency Vehicle Preemption**  
  Demonstrates how an intelligent controller dynamically clears a route for ambulances.

- **Comprehensive Performance Analysis**  
  Generates key plots using Matplotlib:
  - DQN learning curve (training progress)
  - Congestion-over-time graph
  - Grouped bar chart comparing waiting time and throughput across all controllers

---

## 🕹️ The Controllers

| Controller | Type | Description |
|-------------|------|--------------|
| **Fixed-Timer** | Baseline | Follows a rigid, pre-set 68-second cycle without adapting to traffic conditions. |
| **LQF Agent** | Heuristic | Chooses the direction with the most waiting vehicles to receive the green signal. |
| **Q-Learning Agent** | RL (Tabular) | Learns a Q-table mapping states to actions, discovering adaptive control strategies. |
| **DQN Agent** | RL (Neural Network) | Uses Deep Q-Network to learn optimal control patterns directly from complex state data. |

---

## 🛠️ Technologies Used

| Category | Tools / Libraries |
|-----------|-------------------|
| **Simulation** | SUMO (Simulation of Urban MObility) |
| **Programming Language** | Python 3 |
| **AI / Deep Learning** | TensorFlow, Keras |
| **Data Processing & Visualization** | NumPy, Matplotlib |
| **SUMO Control Interface** | Traci (Traffic Control Interface) |

---

## 📁 Project Structure

├── training/
│ ├── q_learning_agent.py # Trains the Q-Learning agent
│ └── dqn_agent.py # Trains the DQN agent
│
├── evaluation/
│ ├── fixed_timer.py # Evaluates Fixed-Timer controller
│ ├── evaluate_q_agent.py # Evaluates trained Q-Learning agent
│ └── evaluate_dqn_agent.py # Evaluates trained DQN agent
│
├── analysis.py # Analyzes and visualizes performance results
├── ambulance_simulation.py # Demonstrates emergency vehicle preemption
│
├── sumo_files/
│ ├── cross.nod.xml # Defines intersection nodes
│ ├── cross.edg.xml # Defines roads (edges)
│ ├── cross.rou.xml # Defines vehicle routes and traffic flow
│ ├── cross.add.xml # Defines fixed-timer traffic light logic
│ └── cross.sumocfg # Main SUMO configuration file
│
├── requirements.txt # Python dependencies
└── README.md # Project documentation (this file)


---

## ⚙️ Setup and Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repository-name>.git
cd <your-repository-name>


2️⃣ Install SUMO

Download from: https://www.eclipse.org/sumo

Set the environment variable SUMO_HOME to your SUMO installation directory.

3️⃣ Set Up a Python Environment
python -m venv faienv
# On Linux/Mac
source faienv/bin/activate
# On Windows
faienv\Scripts\activate

4️⃣ Install Python Dependencies

requirements.txt should include:

matplotlib
tensorflow
traci
numpy


Then install them:

pip install -r requirements.txt


🚀 How to Run the Project (Complete Workflow)
Step 1: Train the Learning Agents

Train the Q-Learning Agent:

python training/q_learning_agent.py


→ Generates q_table.pkl

Train the DQN Agent:

python training/dqn_agent.py


→ Generates dqn_model.h5 and dqn_learning_history.pkl

Step 2: Evaluate All Controllers

Evaluate the Fixed-Timer Controller:

python evaluation/fixed_timer.py


(Ensure <additional-files value="cross.add.xml"/> is active in cross.sumocfg)

Evaluate the LQF Agent:

python evaluation/agent.py


(Comment out <additional-files.../> in cross.sumocfg)

Evaluate the Q-Learning Agent:

python evaluation/evaluate_q_agent.py


Evaluate the DQN Agent:

python evaluation/evaluate_dqn_agent.py

Step 3: Analyze Results

Run the master analysis script to generate all charts:

python analysis.py


It will produce:

Learning Curve: DQN agent’s reward improvement over episodes

Congestion Curve: Vehicles waiting vs. simulation time

Grouped Comparison: Waiting time and throughput across all controllers

(Optional) Step 4: Ambulance Priority Simulation

To visualize emergency vehicle preemption:

python ambulance_simulation.py


📊 Results and Discussion
Controller	Avg. Waiting Time ↓	Throughput ↑	Remarks
Fixed-Timer	❌ High	Low	Rigid, no adaptability
LQF Agent	✅ Improved	Moderate	Simple but effective heuristic
Q-Learning	✅✅ Better	High	Learns adaptively, still limited
DQN Agent	🌟 Best (−71%)	Highest	Deep RL outperforms all others

Conclusion:
The DQN Agent achieved the most efficient traffic flow, demonstrating that deep reinforcement learning can autonomously discover and optimize real-world control policies.

💡 Future Improvements

Multi-Intersection Coordination:
Extend to multiple intersections using Multi-Agent Reinforcement Learning (MARL) for synchronized control.

Traffic Density Sensitivity Analysis:
Test system robustness under varying traffic loads (light to heavy congestion).

Hybrid RL-Heuristic Models:
Use heuristic logic like LQF as an initial policy, refined by deep reinforcement learning.

Integration with IoT and Edge Computing:
Connect real-time traffic sensors or vehicle telemetry for live adaptive control.

🧩 Credits

Developed by: [Your Name / Team Name]
Institution: [Your University / Department]
Course: Intelligent Systems / AI for Smart Cities
Simulation Platform: Eclipse SUMO

Deep Learning Framework: TensorFlow

📜 License

This project is licensed under the MIT License
.

🌟 Acknowledgements

Special thanks to:

The SUMO and TraCI developers for their open-source tools.

TensorFlow/Keras community for deep learning frameworks.

Mentors and instructors who guided this research.

🖼️ Example Result Visualization

(Example chart generated by analysis.py)

🤝 Contributing

Pull requests, suggestions, and improvements are welcome!
Feel free to open an issue or fork the repository to experiment with new controllers.

"Intelligence is not just learning — it’s learning when to wait and when to move." 🚦


---

Would you like me to include **a sample `requirements.txt`** and **example plots folder structure** (for easy setup and presentation)?  
That can make your GitHub repository instantly runnable and visually complete.