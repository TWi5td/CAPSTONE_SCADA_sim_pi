# SCADA IED Simulator

A professional-grade Modbus TCP server simulator designed for Raspberry Pi 4. This system provides a complete simulation environment for Intelligent Electronic Devices (IEDs) commonly used in industrial control systems and SCADA networks.

## Overview

This project simulates a SCADA (Supervisory Control and Data Acquisition) system using a Raspberry Pi 4. It includes a Python-based Modbus TCP server and a web-based Human Machine Interface (HMI) for monitoring and control. Designed for testing, development, and training purposes, the system mimics Modbus-compatible RTUs and supports various I/O signal types.

## Features

### Core Functionality
- Full Modbus TCP server implementation supporting all standard function codes
- 100 registers per type (Coils, Discrete Inputs, Holding Registers, Input Registers)
- Configurable Unit ID (default: 254)
- JSON-based configuration management

### Web Interface
- Real-time dashboard with system statistics and activity logging
- Live data simulation with configurable waveform generators
- Custom variable management with engineering unit scaling
- Configuration export and import functionality
- Responsive design for desktop and mobile access

### Simulation Capabilities
- Sine wave generator for AC signal simulation
- Ramp/sawtooth generator for level and counter simulation
- Random walk generator for noisy sensor simulation
- Square wave generator for digital cycling simulation
- Digital pulse controls for discrete input toggling

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
mkdir -p ~/scada_simulator/templates
cd ~/scada_simulator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask pymodbus

# Copy application files to the directory
# (enhanced_app.py, templates/index.html, templates/simulation.html, templates/variables.html)

# Run the simulator
python3 enhanced_app.py
```

### Access Points
- **Web Interface:** `http://<device-ip>:5000`
- **Modbus TCP Server:** Port 5002, Unit ID 254

## Project Structure

```
scada_simulator/
├── enhanced_app.py              # Main application server
├── requirements.txt             # Python dependencies
├── config.json                  # System configuration
├── custom_variables.json        # User-defined variables (auto-generated)
├── templates/
│   ├── index.html              # Dashboard interface
│   ├── simulation.html         # Live simulation interface
│   └── variables.html          # Custom variables interface
└── README.md                    # Project documentation
```

## Configuration

### Network Settings

Default configuration values in `enhanced_app.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| MODBUS_ADDRESS | 254 | Modbus Unit ID |
| SERVER_IP | 0.0.0.0 | Listen on all interfaces |
| SERVER_PORT | 5002 | Modbus TCP port |
| FLASK_PORT | 5000 | Web interface port |

### Firewall Configuration

If using UFW firewall, allow the required ports:

```bash
sudo ufw allow 5000/tcp    # Web interface
sudo ufw allow 5002/tcp    # Modbus TCP
```

## Modbus Register Reference

### Register Types

| Register Type | Function Codes | Address Range | Access |
|---------------|----------------|---------------|--------|
| Coils | 01, 05, 15 | 0-99 | Read/Write |
| Discrete Inputs | 02 | 0-99 | Read Only |
| Holding Registers | 03, 06, 16 | 0-99 | Read/Write |
| Input Registers | 04 | 0-99 | Read Only |

### Supported Function Codes

| Code | Function | Description |
|------|----------|-------------|
| 01 | Read Coils | Read digital output status |
| 02 | Read Discrete Inputs | Read digital input status |
| 03 | Read Holding Registers | Read analog output values |
| 04 | Read Input Registers | Read analog input values |
| 05 | Write Single Coil | Write single digital output |
| 06 | Write Single Register | Write single analog value |
| 15 | Write Multiple Coils | Write multiple digital outputs |
| 16 | Write Multiple Registers | Write multiple analog values |

## API Reference

### Status Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Returns current register values |
| GET | `/api/system_status` | Returns system statistics |

### Register Write Endpoints

| Method | Endpoint | Request Body |
|--------|----------|--------------|
| POST | `/api/set_coil` | `{"address": 0, "value": 1}` |
| POST | `/api/set_discrete_input` | `{"address": 0, "value": 1}` |
| POST | `/api/set_holding_register` | `{"address": 0, "value": 1000}` |
| POST | `/api/set_input_register` | `{"address": 0, "value": 1000}` |

### Configuration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export_config` | Export system configuration |
| POST | `/api/import_config` | Import configuration from JSON |
| GET | `/api/custom_variables` | List custom variables |
| POST | `/api/custom_variables` | Create/update custom variable |
| DELETE | `/api/custom_variables/<name>` | Delete custom variable |

## Usage Examples

### Python Client

```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.100', port=5002)
client.connect()

# Read 10 input registers starting at address 0
result = client.read_input_registers(0, 10, slave=254)
print(result.registers)

# Write value 1000 to holding register 0
client.write_register(0, 1000, slave=254)

client.close()
```

### SCADA Integration

Configure your SCADA system with the following parameters:

| Parameter | Value |
|-----------|-------|
| Protocol | Modbus TCP |
| IP Address | Device IP address |
| Port | 5002 |
| Unit ID | 254 |
| Scan Rate | 1000ms (recommended) |

## Running as a System Service

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/scada-simulator.service
```

Add the following content:

```ini
[Unit]
Description=SCADA IED Simulator
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/scada_simulator
Environment="PATH=/home/pi/scada_simulator/venv/bin"
ExecStart=/home/pi/scada_simulator/venv/bin/python3 enhanced_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable scada-simulator
sudo systemctl start scada-simulator
```

## Troubleshooting

### Web Interface Not Accessible

1. Verify the application is running: `ps aux | grep enhanced_app`
2. Check the port is listening: `sudo netstat -tlnp | grep 5000`
3. Verify firewall rules: `sudo ufw status`
4. Test locally: `curl http://localhost:5000`

### Modbus Connection Failed

1. Check port 5002 is listening: `sudo netstat -tlnp | grep 5002`
2. Verify firewall allows port 5002: `sudo ufw allow 5002/tcp`
3. Confirm correct Unit ID (254) is configured in your client
4. Test network connectivity: `ping <device-ip>`

### Finding Device IP Address

```bash
hostname -I
```

## Roadmap

- [ ] Modbus RTU over RS-232/RS-485 support
- [ ] DNP3 protocol simulation
- [ ] IEC 61850 simulation
- [ ] Database logging (SQLite/PostgreSQL)
- [ ] REST API authentication
- [ ] MQTT integration
- [ ] Docker containerization
- [ ] Multi-device simulation
- [ ] Historical data playback

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Author

**Thomas Schmidt**

- GitHub: [TWi5td](https://github.com/TWi5td)
- Project: [CAPSTONE_SCADA_sim_pi](https://github.com/TWi5td/CAPSTONE_SCADA_sim_pi)

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Modbus implementation using [pymodbus](https://github.com/pymodbus-dev/pymodbus)
- Designed for Raspberry Pi hardware

## References

- [Modbus Protocol Specification](https://modbus.org/specs.php)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [pymodbus Documentation](https://pymodbus.readthedocs.io/)
