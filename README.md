# SCADA Simulation with Flask and Modbus – Raspberry Pi 4

This project simulates a basic SCADA (Supervisory Control and Data Acquisition) system using a **Raspberry Pi 4**. It includes a Python-based Modbus TCP simulation and a lightweight Flask web server for configuration access. Designed for prototyping and learning, the system mimics Modbus-compatible RTUs and I/O signals such as analog inputs, binary states, counters, and outputs.

## 🚀 Project Goals

- Simulate Modbus TCP server behavior
- Serve SCADA configuration via a Flask web interface
- Accept configuration via JSON for flexible simulation
- Operate on headless Raspberry Pi 4 via SSH

---

## ⚙️ Features

- **Modbus TCP** simulation using `pymodbus`
- **Flask web interface** for easy access to current configuration
- Supports various signal types:
  - Analog inputs/outputs
  - Binary inputs/outputs
  - Counters
- JSON-based configuration file (`config.json`)
- SSH-compatible (headless operation)

---

## 🧱 Folder Structure
scada_project/
├── app.py              # Flask server serving configuration as JSON
├── config_reader.py    # Configuration loading utility (optional modularization)
├── modbus_sim.py       # Modbus server simulation logic (in progress)
├── scada_config/
│   └── config.json     # JSON configuration file for simulation
├── .gitignore          # Ignores virtual envs, logs, __pycache__, etc.
└── README.md           # Project overview and documentation

⚙️ Setup Instructions (Raspberry Pi)

1. Install Raspberry Pi OS 64-bit

2. SSH into the Pi

3. Create a Python virtual environment:
  sudo apt update
  sudo apt install python3-pip python3-venv
  python3 -m venv modbus_env
  source modbus_env/bin/activate

4. Install dependencies:
  pip install flask pymodbus

5. Run the Flask server:
  python3 app.py

6. Visit the Flask server in a browser:
  http://<raspberry-pi-ip>:5000

📄 Sample config.json
  {
    "protocol": "modbus",
    "connection": "tcp",
    "ip": "192.168.254.66",
    "port": 502,
    "data_points": {
      "analog_inputs": [100, 200],
      "binary_inputs": [0, 1],
      "counters": [10],
      "analog_outputs": [50]
    },
    "writeback": true
  }

🧠 Future Plans
-Add Modbus RTU over RS-232 support
-Add DNP3 protocol simulation
-Upload and activate new config files via the web UI
-Add data logging and export (CSV or API)
-Integrate basic authentication or access control

🧑‍💻 Author
  Thomas Schmidt
  GitHub: https://github.com/TWi5td
