# SCADA IED Simulator

A professional-grade Modbus TCP server simulator designed for power engineers. This system provides a comprehensive simulation environment for Intelligent Electronic Devices (IEDs) commonly used in electrical substations, generation facilities, and industrial power systems.

## Overview

This project simulates a complete power system IED using a Raspberry Pi 4 (or any Linux system). It includes a Python-based Modbus TCP server with over 260 pre-configured power industry variables and a web-based Human Machine Interface (HMI) for monitoring and control. Designed for testing SCADA systems, protection relay integration, and operator training.

## Features

### Core Functionality

- Full Modbus TCP server supporting all standard function codes (01, 02, 03, 04, 05, 06, 15, 16)
- 500 registers per type (Coils, Discrete Inputs, Holding Registers, Input Registers)
- Pre-configured with 260+ power industry variables
- Configurable Unit ID (default: 254)
- Real-time change tracking and activity logging

### Power Industry Variables

The simulator comes pre-loaded with comprehensive power system measurements:

| Category | Variables | Description |
|----------|-----------|-------------|
| Electrical Measurements | 50+ | Three-phase voltage, current, power, energy |
| Protection Elements | 40+ | Overcurrent, voltage, frequency protection status |
| Transformer Monitoring | 15+ | Temperature, DGA, tap changer, cooling |
| Generator Monitoring | 15+ | MW/MVAR output, excitation, temperatures |
| Breaker/Switch Status | 15+ | 52A/B, disconnect switches, lockout |
| Capacitor Bank | 10+ | Step status, VAR output, controls |
| DC System | 10+ | Battery voltage, charger status |
| Environmental | 6 | Temperature, humidity, wind |

### Web Interface

- **Dashboard**: Real-time measurements, equipment status, activity logging
- **Live Simulation**: Waveform generators for voltage, current, power, frequency, temperature
- **Variables Browser**: Complete register map with search, filtering, and CSV export
- **Scenario Presets**: Pre-configured test scenarios (normal, high load, fault, etc.)

## System Requirements

### Hardware

| Component | Requirement |
|-----------|-------------|
| Platform | Raspberry Pi 4 (recommended) or any Linux system |
| Memory | 2 GB RAM minimum (4 GB recommended) |
| Storage | 2 GB free disk space |
| Network | Ethernet or WiFi connectivity |

### Software

- Raspberry Pi OS (64-bit recommended) or Ubuntu/Debian Linux
- Python 3.7 or higher
- Flask 3.0.0 or higher
- pymodbus 3.6.0 or higher

## Installation

### Quick Start

```bash
# Create project directory
mkdir -p ~/power_ied_simulator/templates
cd ~/power_ied_simulator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask pymodbus

# Copy application files
# - enhanced_app.py to ~/power_ied_simulator/
# - templates/*.html to ~/power_ied_simulator/templates/

# Run the simulator
python3 enhanced_app.py
```

### Access Points

- **Web Interface**: `http://<device-ip>:5000`
- **Modbus TCP Server**: Port 5002, Unit ID 254

## Project Structure

```
power_ied_simulator/
├── enhanced_app.py              # Main application with power variables
├── requirements.txt             # Python dependencies
├── config.json                  # System configuration
├── custom_variables.json        # User-defined variables (auto-generated)
├── templates/
│   ├── index.html              # Dashboard interface
│   ├── simulation.html         # Live simulation interface
│   └── variables.html          # Register map browser
└── README.md                   # This file
```

## Register Map Reference

### Input Registers (Function Code 04) - Read Only

#### Voltage Measurements (Addresses 0-9)

| Address | Name | Description | Unit | Scale |
|---------|------|-------------|------|-------|
| 0 | V_L1_N | Phase L1-N Voltage | V | 0.1 |
| 1 | V_L2_N | Phase L2-N Voltage | V | 0.1 |
| 2 | V_L3_N | Phase L3-N Voltage | V | 0.1 |
| 3 | V_L1_L2 | Phase L1-L2 Voltage | V | 0.1 |
| 4 | V_L2_L3 | Phase L2-L3 Voltage | V | 0.1 |
| 5 | V_L3_L1 | Phase L3-L1 Voltage | V | 0.1 |
| 6 | V_AVG_LN | Average L-N Voltage | V | 0.1 |
| 7 | V_AVG_LL | Average L-L Voltage | V | 0.1 |
| 8 | V_UNBAL | Voltage Unbalance | % | 0.01 |

#### Current Measurements (Addresses 20-29)

| Address | Name | Description | Unit | Scale |
|---------|------|-------------|------|-------|
| 20 | I_L1 | Phase L1 Current | A | 0.01 |
| 21 | I_L2 | Phase L2 Current | A | 0.01 |
| 22 | I_L3 | Phase L3 Current | A | 0.01 |
| 23 | I_N | Neutral Current | A | 0.01 |
| 24 | I_G | Ground Current | A | 0.01 |
| 25 | I_AVG | Average Phase Current | A | 0.01 |

#### Power Measurements (Addresses 40-55)

| Address | Name | Description | Unit | Scale |
|---------|------|-------------|------|-------|
| 40-42 | P_L1/L2/L3 | Phase Active Power | kW | 0.1 |
| 43 | P_TOTAL | Total Active Power | kW | 0.1 |
| 44-46 | Q_L1/L2/L3 | Phase Reactive Power | kVAR | 0.1 |
| 47 | Q_TOTAL | Total Reactive Power | kVAR | 0.1 |
| 48-50 | S_L1/L2/L3 | Phase Apparent Power | kVA | 0.1 |
| 51 | S_TOTAL | Total Apparent Power | kVA | 0.1 |
| 52-54 | PF_L1/L2/L3 | Phase Power Factor | - | 0.001 |
| 55 | PF_TOTAL | Total Power Factor | - | 0.001 |

#### Frequency (Addresses 70-72)

| Address | Name | Description | Unit | Scale |
|---------|------|-------------|------|-------|
| 70 | FREQ | System Frequency | Hz | 0.01 |
| 71 | FREQ_DEV | Frequency Deviation | Hz | 0.001 |
| 72 | ROCOF | Rate of Change of Freq | Hz/s | 0.001 |

#### Transformer Measurements (Addresses 100-114)

| Address | Name | Description | Unit | Scale |
|---------|------|-------------|------|-------|
| 100 | XFMR_OIL_TEMP | Oil Temperature | °C | 0.1 |
| 101 | XFMR_WNDG_TEMP | Winding Temperature | °C | 0.1 |
| 102 | XFMR_AMB_TEMP | Ambient Temperature | °C | 0.1 |
| 103 | XFMR_LOAD_PCT | Load Percent | % | 0.1 |
| 104 | XFMR_OIL_LEVEL | Oil Level | % | 0.1 |
| 106 | XFMR_TAP_POS | Tap Position | - | 1 |
| 108-113 | XFMR_*_PPM | Dissolved Gas (H2, CH4, etc.) | ppm | 1 |

### Discrete Inputs (Function Code 02) - Read Only

#### Breaker Status (Addresses 0-12)

| Address | Name | Description |
|---------|------|-------------|
| 0 | BKR_52A | Breaker Closed Status |
| 1 | BKR_52B | Breaker Open Status |
| 2 | BKR_READY | Breaker Ready |
| 3 | BKR_SPRING_CHRG | Spring Charged |
| 4 | BKR_LOCKOUT | Breaker Lockout |
| 5 | BKR_LOCAL | Local Control Mode |
| 6 | BKR_REMOTE | Remote Control Mode |

#### Protection Status (Addresses 30-55)

| Address | Name | Description |
|---------|------|-------------|
| 30 | PROT_ENABLED | Protection Enabled |
| 31 | PROT_50_PICKUP | 50 Inst OC Pickup |
| 32 | PROT_51_PICKUP | 51 TOC Pickup |
| 35 | PROT_27_PICKUP | 27 UV Pickup |
| 36 | PROT_59_PICKUP | 59 OV Pickup |
| 37 | PROT_81U_PICKUP | 81U UF Pickup |
| 42-49 | PROT_*_TRIP | Element Trip Status |
| 50 | PROT_LOCKOUT | Protection Lockout |

### Coils (Function Codes 01/05/15) - Read/Write

#### Breaker Controls (Addresses 0-7)

| Address | Name | Description |
|---------|------|-------------|
| 0 | CMD_BKR_CLOSE | Close Breaker Command |
| 1 | CMD_BKR_TRIP | Trip Breaker Command |
| 2 | CMD_BKR_RESET | Reset Breaker Command |
| 3 | CMD_LOCKOUT_RESET | Reset Lockout Command |

#### Transformer Controls (Addresses 40-51)

| Address | Name | Description |
|---------|------|-------------|
| 40 | CMD_TAP_RAISE | Tap Changer Raise |
| 41 | CMD_TAP_LOWER | Tap Changer Lower |
| 42 | CMD_TAP_AUTO | Auto Mode Enable |
| 44-49 | CMD_FAN*/PUMP* | Cooling Controls |

### Holding Registers (Function Codes 03/06/16) - Read/Write

#### Setpoints (Addresses 0-5)

| Address | Name | Description | Unit | Scale |
|---------|------|-------------|------|-------|
| 0 | SP_V_TARGET | Voltage Setpoint | V | 0.1 |
| 1 | SP_PF_TARGET | Power Factor Setpoint | - | 0.001 |
| 2 | SP_MW_TARGET | MW Setpoint | MW | 0.1 |

#### Protection Settings (Addresses 50-68)

| Address | Name | Description | Unit | Scale |
|---------|------|-------------|------|-------|
| 50 | SET_50_PICKUP | 50 Inst OC Pickup | A | 0.01 |
| 51 | SET_51_PICKUP | 51 TOC Pickup | A | 0.01 |
| 52 | SET_51_TD | 51 Time Dial | - | 0.01 |
| 57 | SET_27_PICKUP | 27 UV Pickup | V | 0.1 |
| 59 | SET_59_PICKUP | 59 OV Pickup | V | 0.1 |

## API Reference

### Status Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Common measurements (voltage, current, power) |
| GET | `/api/system_status` | System statistics and recent changes |
| GET | `/api/register_map` | Complete power industry register map |
| GET | `/api/category/<category>` | All values for a category |

### Register Operations

| Method | Endpoint | Request Body |
|--------|----------|--------------|
| POST | `/api/set_coil` | `{"address": 0, "value": 1}` |
| POST | `/api/set_discrete_input` | `{"address": 0, "value": 1}` |
| POST | `/api/set_holding_register` | `{"address": 0, "value": 1000}` |
| POST | `/api/set_input_register` | `{"address": 0, "value": 1000}` |
| POST | `/api/reset_defaults` | Reset all to power industry defaults |

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export_config` | Export complete configuration |
| POST | `/api/import_config` | Import configuration from JSON |
| GET | `/api/custom_variables` | List custom variables |
| POST | `/api/custom_variables` | Create/update custom variable |

## Integration Examples

### Python Client

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.100', port=5002)
client.connect()

# Read three-phase voltages (addresses 0-2, scaled by 0.1)
result = client.read_input_registers(0, 3, slave=254)
voltages = [v * 0.1 for v in result.registers]
print(f"L1-N: {voltages[0]:.1f}V, L2-N: {voltages[1]:.1f}V, L3-N: {voltages[2]:.1f}V")

# Read total power (address 43, scaled by 0.1)
result = client.read_input_registers(43, 1, slave=254)
power_kw = result.registers[0] * 0.1
print(f"Total Power: {power_kw:.1f} kW")

# Read breaker status
result = client.read_discrete_inputs(0, 2, slave=254)
print(f"Breaker Closed: {result.bits[0]}, Breaker Open: {result.bits[1]}")

# Send breaker close command (pulse)
client.write_coil(0, True, slave=254)
time.sleep(0.5)
client.write_coil(0, False, slave=254)

client.close()
```

### SEL RTAC Configuration

Configure the following in your SEL RTAC client definition:

| Parameter | Value |
|-----------|-------|
| Protocol | Modbus TCP |
| IP Address | Device IP |
| Port | 5002 |
| Unit ID | 254 |
| Scan Rate | 1000ms |

## Running as a System Service

```bash
sudo nano /etc/systemd/system/power-ied-simulator.service
```

```ini
[Unit]
Description=Power Industry IED Simulator
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/power_ied_simulator
Environment="PATH=/home/pi/power_ied_simulator/venv/bin"
ExecStart=/home/pi/power_ied_simulator/venv/bin/python3 enhanced_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable power-ied-simulator
sudo systemctl start power-ied-simulator
```

## Troubleshooting

### Web Interface Not Accessible

1. Verify application running: `ps aux | grep enhanced_app`
2. Check port listening: `sudo netstat -tlnp | grep 5000`
3. Verify firewall: `sudo ufw allow 5000/tcp`

### Modbus Connection Failed

1. Check port 5002: `sudo netstat -tlnp | grep 5002`
2. Allow in firewall: `sudo ufw allow 5002/tcp`
3. Confirm Unit ID 254 in client configuration
4. Test connectivity: `ping <device-ip>`

### Find Device IP

```bash
hostname -I
```

## License

This project is licensed under the MIT License.

## Author

**Thomas Schmidt**
- GitHub: [TWi5td](https://github.com/TWi5td)
- Project: [CAPSTONE_SCADA_sim_pi](https://github.com/TWi5td/CAPSTONE_SCADA_sim_pi)

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) and [pymodbus](https://github.com/pymodbus-dev/pymodbus)
- Designed for power industry testing and training
